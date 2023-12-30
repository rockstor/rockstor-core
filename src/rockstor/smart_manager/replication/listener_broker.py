"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from multiprocessing import Process
import zmq
import os
import json
import time
from storageadmin.models import NetworkConnection, Appliance
from smart_manager.models import ReplicaTrail, ReplicaShare, Replica, Service
from django.conf import settings
from smart_manager.replication.sender import Sender
from smart_manager.replication.receiver import Receiver
from smart_manager.replication.util import ReplicationMixin
from cli import APIWrapper
import logging

logger = logging.getLogger(__name__)


class ReplicaScheduler(ReplicationMixin, Process):
    def __init__(self):
        self.law = None
        self.local_receivers = None
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
            for w in list(wd.keys()):
                if wd[w].exitcode is not None:
                    del wd[w]
                    logger.debug(f"deleted worker: {w}")
        return workers

    def _prune_senders(self):
        for s in list(self.senders.keys()):
            ecode = self.senders[s].exitcode
            if ecode is not None:
                del self.senders[s]
                logger.debug(f"Sender({s}) exited. exitcode: {ecode}")
        if len(self.senders) > 0:
            logger.debug(f"Active Senders: {self.senders.keys()}")

    def _delete_receivers(self):
        active_msgs = []
        # We modify during iteration, and so require explicit list.
        for r in list(self.local_receivers.keys()):
            msg_count = self.remote_senders.get(r, 0)
            ecode = self.local_receivers[r].exitcode
            if ecode is not None:
                del self.local_receivers[r]
                if r in self.remote_senders:
                    del self.remote_senders[r]
                logger.debug(
                    f"Receiver({r}) exited. exitcode: {ecode}. Total messages processed: {msg_count}. "
                    "Removing from the list."
                )
            else:
                active_msgs.append(
                    f"Active Receiver: {r}. Total messages processed: {msg_count}"
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
            msg = f"Failed to get receiver ip. Is the receiver appliance added?. Exception: {e.__str__()}"
            logger.error(msg)
            raise Exception(msg)

    def _process_send(self, replica):
        sender_key = f"{self.uuid}_{replica.id}"
        if sender_key in self.senders:
            # If the sender exited but hasn't been removed from the dict, remove and proceed.
            ecode = self.senders[sender_key].exitcode
            if ecode is not None:
                del self.senders[sender_key]
                logger.debug(
                    f"Sender({sender_key}) exited. Exitcode: {ecode}. Forcing removal."
                )
            else:
                raise Exception(
                    f"There is live sender for({sender_key}). Will not start a new one."
                )

        receiver_ip = self._get_receiver_ip(replica)
        rt_qs = ReplicaTrail.objects.filter(replica=replica).order_by("-id")
        last_rt = rt_qs[0] if (len(rt_qs) > 0) else None
        if last_rt is None:
            logger.debug(f"Starting a new Sender({sender_key}).")
            self.senders[sender_key] = Sender(self.uuid, receiver_ip, replica)
        elif last_rt.status == "succeeded":
            logger.debug(f"Starting a new Sender({sender_key}).")
            self.senders[sender_key] = Sender(self.uuid, receiver_ip, replica, last_rt)
        elif last_rt.status == "pending":
            msg = (
                f"Replica trail shows a pending Sender({sender_key}), but it is not alive. "
                "Marking it as failed. Will not start a new one."
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
                    f"Maximum attempts({self.MAX_ATTEMPTS}) reached for Sender({sender_key}). "
                    "A new one will not be started and the Replica task will be disabled."
                )
                logger.error(msg)
                self.disable_replica(replica.id)
                raise Exception(msg)

            logger.debug(
                f"previous backup failed for Sender({sender_key}). "
                f"Starting a new one. Attempt {num_tries}/{self.MAX_ATTEMPTS}."
            )
            try:
                last_success_rt = ReplicaTrail.objects.filter(
                    replica=replica, status="succeeded"
                ).latest("id")
            except ReplicaTrail.DoesNotExist:
                logger.debug(
                    f"No record of last successful ReplicaTrail for Sender({sender_key}). "
                    f"Will start a new Full Sender."
                )
                last_success_rt = None
            self.senders[sender_key] = Sender(
                self.uuid, receiver_ip, replica, last_success_rt
            )
        else:
            msg = (
                f"Unexpected ReplicaTrail status({last_rt.status}) for Sender({sender_key}). "
                f"Will not start a new one."
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
            msg = f"Failed to fetch network interface for Listener/Broker. Exception: {e.__str__()}"
            return logger.error(msg)

        try:
            self.uuid = Appliance.objects.get(current_appliance=True).uuid
        except Exception as e:
            msg = f"Failed to get uuid of current appliance. Aborting. Exception: {e.__str__()}"
            return logger.error(msg)

        ctx = zmq.Context()
        frontend = ctx.socket(zmq.ROUTER)
        frontend.set_hwm(value=10)
        frontend.bind(f"tcp://{self.listener_interface}:{ self.listener_port}")

        backend = ctx.socket(zmq.ROUTER)
        ipc_socket = settings.REPLICATION.get("ipc_socket")
        backend.bind(f"ipc://{ipc_socket}")

        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)
        self.local_receivers = {}

        iterations = 3
        poll_interval = 6000  # 6 seconds
        msg_count = 0
        while True:
            # This loop may still continue even if replication service
            # is terminated, as long as data is coming in.
            socks = dict(poller.poll(timeout=poll_interval))
            if frontend in socks and socks[frontend] == zmq.POLLIN:
                # frontend.recv_multipart() returns all as type <class 'bytes'>
                address, command, msg = frontend.recv_multipart()
                logger.debug("frontend.recv_multipart() returns")
                logger.debug(f"address = {address}, type {type(address)}")
                logger.debug(f"command = {command}, type {type(command)}")
                logger.debug(f"msg = {msg}, type {type(msg)}")
                if address not in self.remote_senders:
                    self.remote_senders[address] = 1
                else:
                    self.remote_senders[address] += 1
                msg_count += 1
                if msg_count == 1000:
                    msg_count = 0
                    for rs, count in self.remote_senders.items():
                        logger.debug(
                            f"Active Receiver: {rs}. Messages processed: {count}"
                        )
                if command == b"sender-ready":
                    logger.debug(f"initial greeting from {address}")
                    # Start a new receiver and send the appropriate response
                    try:
                        start_nr = True
                        if address in self.local_receivers:
                            start_nr = False
                            ecode = self.local_receivers[address].exitcode
                            if ecode is not None:
                                del self.local_receivers[address]
                                logger.debug(
                                    f"Receiver({address}) exited. exitcode: {ecode}. Forcing removal from broker list."
                                )
                                start_nr = True
                            else:
                                msg = f"Receiver({address}) already exists. Will not start a new one.".encode("utf-8")
                                logger.error(msg)
                                # TODO: There may be a different way to handle
                                #  this. For example, we can pass the message to
                                #  the active receiver and factor into its
                                #  retry/robust logic. But that is for later.
                                frontend.send_multipart(
                                    [
                                        address,
                                        b"receiver-init-error",
                                        msg,
                                    ]
                                )
                        if start_nr:
                            nr = Receiver(address, msg)
                            nr.daemon = True
                            nr.start()
                            logger.debug(f"New Receiver({address}) started.")
                            self.local_receivers[address] = nr
                        continue
                    except Exception as e:
                        msg = f"Exception while starting the new receiver for {address}: {e.__str__()}"
                        logger.error(msg)
                        frontend.send_multipart(
                            [address, b"receiver-init-error", msg.encode("utf-8")]
                        )
                else:
                    # do we hit hwm? is the dealer still connected?
                    backend.send_multipart([address, command, msg.encode("utf-8")])

            elif backend in socks and socks[backend] == zmq.POLLIN:
                address, command, msg = backend.recv_multipart()
                if command == b"new-send":
                    rid = int(msg)
                    logger.debug(f"new-send request received for {rid}")
                    rcommand = b"ERROR"
                    try:
                        replica = Replica.objects.get(id=rid)
                        if replica.enabled:
                            self._process_send(replica)
                            msg = f"A new Sender started successfully for Replication Task({rid})."
                            rcommand = b"SUCCESS"
                        else:
                            msg = f"Failed to start a new Sender for Replication Task({rid}) because it is disabled."
                    except Exception as e:
                        msg = f"Failed to start a new Sender for Replication Task({rid}). Exception: {e.__str__()}"
                        logger.error(msg)
                    finally:
                        backend.send_multipart([address, rcommand, msg.encode("utf-8")])
                elif address in self.remote_senders:
                    if (
                        command == b"receiver-ready"
                        or command == b"receiver-error"
                        or command == b"btrfs-recv-finished"
                    ):
                        logger.debug(f"Identity: {address} command: {command}")
                        backend.send_multipart([address, b"ACK", b""])
                        # a new receiver has started. reply to the sender that
                        # must be waiting
                    frontend.send_multipart([address, command, msg.encode("utf-8")])

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
