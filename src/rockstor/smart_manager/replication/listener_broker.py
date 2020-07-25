"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
This file is part of RockStor.

RockStor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

RockStor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from multiprocessing import Process
import zmq
import os
import json
import time
from storageadmin.models import NetworkConnection, Appliance
from smart_manager.models import ReplicaTrail, ReplicaShare, Replica, Service
from django.conf import settings
from sender import Sender
from receiver import Receiver
from util import ReplicationMixin
from cli import APIWrapper
import logging

logger = logging.getLogger(__name__)


class ReplicaScheduler(ReplicationMixin, Process):
    def __init__(self):
        self.ppid = os.getpid()
        self.senders = {}  # Active Sender(outgoing) process map.
        self.receivers = {}  # Active Receiver process map.
        self.remote_senders = {}  # Active incoming/remote Sender/client map.
        self.MAX_ATTEMPTS = settings.REPLICATION.get("max_send_attempts")
        self.uuid = self.listener_interface = self.listener_port = None
        self.trail_prune_time = None
        super(ReplicaScheduler, self).__init__()

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if wd[w].exitcode is not None:
                    del wd[w]
                    logger.debug("deleted worker: %s" % w)
        return workers

    def _prune_senders(self):
        for s in self.senders.keys():
            ecode = self.senders[s].exitcode
            if ecode is not None:
                del self.senders[s]
                logger.debug("Sender(%s) exited. exitcode: %s" % (s, ecode))
        if len(self.senders) > 0:
            logger.debug("Active Senders: %s" % self.senders.keys())

    def _delete_receivers(self):
        active_msgs = []
        for r in self.local_receivers.keys():
            msg_count = self.remote_senders.get(r, 0)
            ecode = self.local_receivers[r].exitcode
            if ecode is not None:
                del self.local_receivers[r]
                if r in self.remote_senders:
                    del self.remote_senders[r]
                logger.debug(
                    "Receiver(%s) exited. exitcode: %s. Total "
                    "messages processed: %d. Removing from the list."
                    % (r, ecode, msg_count)
                )
            else:
                active_msgs.append(
                    "Active Receiver: %s. Total messages "
                    "processed: %d" % (r, msg_count)
                )
        for m in active_msgs:
            logger.debug(m)

    def _get_receiver_ip(self, replica):
        if replica.replication_ip is not None:
            return replica.replication_ip
        try:
            appliance = Appliance.objects.get(uuid=replica.appliance)
            return appliance.ip
        except Exception as e:
            msg = (
                "Failed to get receiver ip. Is the receiver "
                "appliance added?. Exception: %s" % e.__str__()
            )
            logger.error(msg)
            raise Exception(msg)

    def _process_send(self, replica):
        sender_key = "%s_%s" % (self.uuid, replica.id)
        if sender_key in self.senders:
            # If the sender exited but hasn't been removed from the dict,
            # remove and proceed.
            ecode = self.senders[sender_key].exitcode
            if ecode is not None:
                del self.senders[sender_key]
                logger.debug(
                    "Sender(%s) exited. exitcode: %s. Forcing "
                    "removal." % (sender_key, ecode)
                )
            else:
                raise Exception(
                    "There is live sender for(%s). Will not start "
                    "a new one." % sender_key
                )

        receiver_ip = self._get_receiver_ip(replica)
        rt_qs = ReplicaTrail.objects.filter(replica=replica).order_by("-id")
        last_rt = rt_qs[0] if (len(rt_qs) > 0) else None
        if last_rt is None:
            logger.debug("Starting a new Sender(%s)." % sender_key)
            self.senders[sender_key] = Sender(self.uuid, receiver_ip, replica)
        elif last_rt.status == "succeeded":
            logger.debug("Starting a new Sender(%s)" % sender_key)
            self.senders[sender_key] = Sender(self.uuid, receiver_ip, replica, last_rt)
        elif last_rt.status == "pending":
            msg = (
                "Replica trail shows a pending Sender(%s), but it is not "
                "alive. Marking it as failed. Will not start a new one." % sender_key
            )
            logger.error(msg)
            data = {
                "status": "failed",
                "error": msg,
            }
            self.update_replica_status(last_rt.id, data)
            raise Exception(msg)
        elif last_rt.status == "failed":
            #  if num_failed attempts > 10, disable the replica
            num_tries = 0
            for rto in rt_qs:
                if (
                    rto.status != "failed"
                    or num_tries >= self.MAX_ATTEMPTS
                    or rto.end_ts < replica.ts
                ):
                    break
                num_tries = num_tries + 1
            if num_tries >= self.MAX_ATTEMPTS:
                msg = (
                    "Maximum attempts(%d) reached for Sender(%s). "
                    "A new one "
                    "will not be started and the Replica task will be "
                    "disabled." % (self.MAX_ATTEMPTS, sender_key)
                )
                logger.error(msg)
                self.disable_replica(replica.id)
                raise Exception(msg)

            logger.debug(
                "previous backup failed for Sender(%s). "
                "Starting a new one. Attempt %d/%d."
                % (sender_key, num_tries, self.MAX_ATTEMPTS)
            )
            try:
                last_success_rt = ReplicaTrail.objects.filter(
                    replica=replica, status="succeeded"
                ).latest("id")
            except ReplicaTrail.DoesNotExist:
                logger.debug(
                    "No record of last successful ReplicaTrail for "
                    "Sender(%s). Will start a new Full Sender." % sender_key
                )
                last_success_rt = None
            self.senders[sender_key] = Sender(
                self.uuid, receiver_ip, replica, last_success_rt
            )
        else:
            msg = (
                "Unexpected ReplicaTrail status(%s) for Sender(%s). "
                "Will not start a new one." % (last_rt.status, sender_key)
            )
            raise Exception(msg)

        # to kill all senders in case scheduler dies.
        self.senders[sender_key].daemon = True
        self.senders[sender_key].start()

    def run(self):
        self.law = APIWrapper()

        try:
            so = Service.objects.get(name="replication")
            config_d = json.loads(so.config)
            self.listener_port = int(config_d["listener_port"])
            nco = NetworkConnection.objects.get(name=config_d["network_interface"])
            self.listener_interface = nco.ipaddr
        except NetworkConnection.DoesNotExist:
            self.listener_interface = "0.0.0.0"
        except Exception as e:
            msg = (
                "Failed to fetch network interface for Listner/Broker. "
                "Exception: %s" % e.__str__()
            )
            return logger.error(msg)

        try:
            self.uuid = Appliance.objects.get(current_appliance=True).uuid
        except Exception as e:
            msg = (
                "Failed to get uuid of current appliance. Aborting. "
                "Exception: %s" % e.__str__()
            )
            return logger.error(msg)

        ctx = zmq.Context()
        frontend = ctx.socket(zmq.ROUTER)
        frontend.set_hwm(10)
        frontend.bind("tcp://%s:%d" % (self.listener_interface, self.listener_port))

        backend = ctx.socket(zmq.ROUTER)
        backend.bind("ipc://%s" % settings.REPLICATION.get("ipc_socket"))

        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)
        self.local_receivers = {}

        iterations = 10
        poll_interval = 6000  # 6 seconds
        msg_count = 0
        while True:
            # This loop may still continue even if replication service
            # is terminated, as long as data is coming in.
            socks = dict(poller.poll(timeout=poll_interval))
            if frontend in socks and socks[frontend] == zmq.POLLIN:
                address, command, msg = frontend.recv_multipart()
                if address not in self.remote_senders:
                    self.remote_senders[address] = 1
                else:
                    self.remote_senders[address] += 1
                msg_count += 1
                if msg_count == 1000:
                    msg_count = 0
                    for rs, count in self.remote_senders.items():
                        logger.debug(
                            "Active Receiver: %s. Messages processed:"
                            "%d" % (rs, count)
                        )
                if command == "sender-ready":
                    logger.debug("initial greeting from %s" % address)
                    # Start a new receiver and send the appropriate response
                    try:
                        start_nr = True
                        if address in self.local_receivers:
                            start_nr = False
                            ecode = self.local_receivers[address].exitcode
                            if ecode is not None:
                                del self.local_receivers[address]
                                logger.debug(
                                    "Receiver(%s) exited. exitcode: "
                                    "%s. Forcing removal from broker "
                                    "list." % (address, ecode)
                                )
                                start_nr = True
                            else:
                                msg = (
                                    "Receiver(%s) already exists. "
                                    "Will not start a new one." % address
                                )
                                logger.error(msg)
                                # @todo: There may be a different way to handle
                                # this. For example, we can pass the message to
                                # the active receiver and factor into it's
                                # retry/robust logic. But that is for later.
                                frontend.send_multipart(
                                    [address, "receiver-init-error", msg]
                                )
                        if start_nr:
                            nr = Receiver(address, msg)
                            nr.daemon = True
                            nr.start()
                            logger.debug("New Receiver(%s) started." % address)
                            self.local_receivers[address] = nr
                        continue
                    except Exception as e:
                        msg = (
                            "Exception while starting the "
                            "new receiver for %s: %s" % (address, e.__str__())
                        )
                        logger.error(msg)
                        frontend.send_multipart([address, "receiver-init-error", msg])
                else:
                    # do we hit hwm? is the dealer still connected?
                    backend.send_multipart([address, command, msg])

            elif backend in socks and socks[backend] == zmq.POLLIN:
                address, command, msg = backend.recv_multipart()
                if command == "new-send":
                    rid = int(msg)
                    logger.debug("new-send request received for %d" % rid)
                    rcommand = "ERROR"
                    try:
                        replica = Replica.objects.get(id=rid)
                        if replica.enabled:
                            self._process_send(replica)
                            msg = (
                                "A new Sender started successfully for "
                                "Replication Task(%d)." % rid
                            )
                            rcommand = "SUCCESS"
                        else:
                            msg = (
                                "Failed to start a new Sender for "
                                "Replication "
                                "Task(%d) because it is disabled." % rid
                            )
                    except Exception as e:
                        msg = (
                            "Failed to start a new Sender for Replication "
                            "Task(%d). Exception: %s" % (rid, e.__str__())
                        )
                        logger.error(msg)
                    finally:
                        backend.send_multipart([address, rcommand, str(msg)])
                elif address in self.remote_senders:
                    if command in (
                        "receiver-ready",
                        "receiver-error",
                        "btrfs-recv-finished",
                    ):  # noqa E501
                        logger.debug("Identitiy: %s command: %s" % (address, command))
                        backend.send_multipart([address, b"ACK", ""])
                        # a new receiver has started. reply to the sender that
                        # must be waiting
                    frontend.send_multipart([address, command, msg])

            else:
                iterations -= 1
                if iterations == 0:
                    iterations = 10
                    self._prune_senders()
                    self._delete_receivers()
                    cur_time = time.time()
                    if (
                        self.trail_prune_time is None
                        or (cur_time - self.trail_prune_time) > 3600
                    ):
                        # prune send/receive trails every hour or so.
                        self.trail_prune_time = cur_time
                        map(self.prune_replica_trail, Replica.objects.filter())
                        map(self.prune_receive_trail, ReplicaShare.objects.filter())
                        logger.debug("Replica trails are truncated successfully.")

                    if os.getppid() != self.ppid:
                        logger.error("Parent exited. Aborting.")
                        ctx.destroy()
                        # do some cleanup of senders before quitting?
                        break


def main():
    rs = ReplicaScheduler()
    rs.start()
    rs.join()
