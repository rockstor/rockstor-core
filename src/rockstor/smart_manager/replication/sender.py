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
import os
import sys
import zmq
import subprocess
import fcntl
import json
import time
from django.conf import settings
from contextlib import contextmanager
from smart_manager.replication.util import ReplicationMixin
from fs.btrfs import get_oldest_snap, is_subvol
from smart_manager.models import ReplicaTrail
from cli import APIWrapper
from django import db
import logging

logger = logging.getLogger(__name__)

BTRFS = "/sbin/btrfs"


class Sender(ReplicationMixin, Process):
    def __init__(self, uuid, receiver_ip, replica, rt=None):
        self.law = None
        self.poll = None
        self.uuid = uuid
        self.receiver_ip = receiver_ip
        self.receiver_port = replica.data_port
        self.replica = replica
        # TODO: may need to send local shareId so it can be verifed remotely
        self.snap_name = f"{replica.share}_{replica.id}_replication"
        self.snap_name += "_1" if (rt is None) else f"_{rt.id + 1}"
        self.snap_id = f"{self.uuid}_{self.snap_name}"
        self.rt = rt
        self.rt2 = None
        self.rt2_id = None
        self.rid = replica.id
        self.identity = f"{self.uuid}-{self.rid}"
        self.sp = None
        # Latest snapshot per Receiver(comes along with receiver-ready)
        self.rlatest_snap = None
        self.ctx = zmq.Context()
        self.msg = b""
        self.update_trail = False
        self.total_bytes_sent = 0
        self.ppid = os.getpid()
        self.max_snap_retain = settings.REPLICATION.get("max_snap_retain")
        db.close_old_connections()
        super(Sender, self).__init__()

    @contextmanager
    def _clean_exit_handler(self):
        try:
            yield
        except Exception as e:
            logger.error(f"Id: {self.identity}. {self.msg}. Exception: {e.__str__()}")
            if self.update_trail:
                try:
                    data = {
                        "status": "failed",
                        "error": f"{self.msg}. Exception: {e.__str__()}",
                    }  # noqa E501
                    self.update_replica_status(self.rt2_id, data)
                except Exception as e:
                    logger.error(
                        f"Id: {self.identity}. Exception occurred while updating replica status: {e.__str__()}"
                    )
            self._sys_exit(3)

    def _sys_exit(self, code):
        if self.sp is not None and self.sp.poll() is None:
            self.sp.terminate()
        self.ctx.destroy(linger=0)
        sys.exit(code)

    def _init_greeting(self):
        self.send_req = self.ctx.socket(zmq.DEALER)
        self.send_req.setsockopt_string(zmq.IDENTITY, self.identity)
        self.send_req.connect(f"tcp://{self.receiver_ip}:{self.receiver_port}")
        msg = {
            "pool": self.replica.dpool,
            "share": self.replica.share,
            "snap": self.snap_name,
            "incremental": self.rt is not None,
            "uuid": self.uuid,
        }
        msg_str = json.dumps(msg)
        self.send_req.send_multipart([b"sender-ready", msg_str.encode("utf-8")])
        logger.debug(f"Id: {self.identity} Initial greeting: {msg}")
        self.poll.register(self.send_req, zmq.POLLIN)

    def _send_recv(self, command: bytes, msg: bytes = b""):
        self.msg = f"Failed while send-recv-ing command({command})".encode("utf-8")
        rcommand = rmsg = None
        self.send_req.send_multipart([command, msg])
        # There is no retry logic here because it's an overkill at the moment.
        # If the stream is interrupted, we can only start from the beginning
        # again.  So we wait patiently, but only once. Perhaps we can implement
        # a buffering or temporary caching strategy to make this part robust.
        socks = dict(self.poll.poll(60000))  # 60 seconds.
        if socks.get(self.send_req) == zmq.POLLIN:
            rcommand, rmsg = self.send_req.recv_multipart()
        if (
            len(command) > 0 or (rcommand is not None and rcommand != b"send-more")
        ) or (  # noqa E501
            len(command) > 0 and rcommand is None
        ):
            logger.debug(
                f"Id: {self.identity} Server: {self.receiver_ip}:{self.receiver_port} scommand: {command} rcommand: {rcommand}"
            )
        return rcommand, rmsg

    def _delete_old_snaps(self, share_path: str):
        oldest_snap = get_oldest_snap(
            share_path, self.max_snap_retain, regex="_replication_"
        )
        if oldest_snap is not None:
            logger.debug(f"Id: {self.identity}. Deleting old snapshot: {oldest_snap}")
            self.msg = f"Failed to delete snapshot: {oldest_snap}. Aborting.".encode(
                "utf-8"
            )
            if self.delete_snapshot(self.replica.share, oldest_snap):
                return self._delete_old_snaps(share_path)

    def _refresh_rt(self):
        # for incremental sends, the receiver tells us the latest successful
        # snapshot on it. This should match self.rt in most cases. Sometimes,
        # it may not be the one refered by self.rt(latest) but a previous one.
        # We need to make sure to *only* send the incremental send that
        # receiver expects.
        self.msg = "Failed to validate/refresh ReplicaTrail.".encode("utf-8")
        if self.rlatest_snap is None:
            # Validate/update self.rt to the one that has the expected Snapshot
            # on the system.
            for rt in ReplicaTrail.objects.filter(
                replica=self.replica, status="succeeded"
            ).order_by("-id"):
                snap_path = f"{settings.MNT_PT}{self.replica.pool}/.snapshots/{self.replica.share}/{self.rt.snap_name}"
                if is_subvol(snap_path):
                    return rt
            # Snapshots from previous succeeded ReplicaTrails don't actually
            # exist on the system. So we send a Full replication instead of
            # incremental.
            return None

        if len(self.rlatest_snap) == 0:
            # Receiver sends empty string when it fails to reply back to an
            # incremental send request with an appropriate parent snapshot
            # name.
            return None

        if self.rt.snap_name != self.rlatest_snap:
            self.msg = (
                "Mismatch on starting snapshot for "
                f"btrfs-send. Sender picked {self.rt.snap_name} but Receiver wants "
                f"{self.rlatest_snap}, which takes precedence."
            ).encode("utf-8")
            for rt in ReplicaTrail.objects.filter(
                replica=self.replica, status="succeeded"
            ).order_by("-id"):
                if rt.snap_name == self.rlatest_snap:
                    self.msg = f"{self.msg}. successful trail found for {self.rlatest_snap}".encode(
                        "utf-8"
                    )
                    snap_path = f"{settings.MNT_PT}{self.replica.pool}.snapshots/{self.replica.share}/{self.rlatest_snap}"
                    if is_subvol(snap_path):
                        self.msg = f"Snapshot({snap_path}) exists in the system and will be used as the parent".encode(
                            "utf-8"
                        )
                        logger.debug(f"Id: {self.identity}. {self.msg}")
                        return rt
                    self.msg = f"Snapshot({snap_path}) does not exist on the system. So cannot use it.".encode(
                        "utf-8"
                    )
                    raise Exception(self.msg)
            raise Exception(
                f"{self.msg}. No succeeded trail found for {self.rlatest_snap}."
            )

        snap_path = f"{settings.MNT_PT}{self.replica.pool}/.snapshots/{self.replica.share}/{self.rlatest_snap}"
        if is_subvol(snap_path):
            return self.rt
        raise Exception(
            f"Parent Snapshot({snap_path}) to use in btrfs-send does not exist in the system."
        )

    def run(self):
        self.msg = f"Top level exception in sender: {self.identity}".encode("utf-8")
        with self._clean_exit_handler():
            self.law = APIWrapper()
            self.poll = zmq.Poller()
            self._init_greeting()

            # Create a new replica trail if it's the very first time,
            # or if the last one succeeded
            self.msg = f"Failed to create local replica trail for snap_name: {self.snap_name}. Aborting.".encode(
                "utf-8"
            )
            self.rt2 = self.create_replica_trail(self.replica.id, self.snap_name)
            self.rt2_id = self.rt2["id"]

            # prune old snapshots.
            self.update_trail = True
            self.msg = "Failed to prune old snapshots".encode("utf-8")
            share_path = (
                f"{settings.MNT_PT}{self.replica.pool}/.snapshots/{self.replica.share}"
            )
            self._delete_old_snaps(share_path)

            # Refresh replica trail.
            if self.rt is not None:
                self.rt = self._refresh_rt()

            #  create a snapshot only if it's not already from a previous
            #  failed attempt.
            # TODO: If one does exist we fail which seems harsh as we may be
            #  able to pickup where we left of depending on the failure.
            self.msg = f"Failed to create snapshot: {self.snap_name}. Aborting.".encode(
                "utf-8"
            )
            self.create_snapshot(self.replica.share, self.snap_name)

            retries_left = settings.REPLICATION.get("max_send_attempts")

            self.msg = (
                "Place-holder message just after sender snapshot creation".encode(
                    "utf-8"
                )
            )

            poll_interval = 6000  # 6 seconds
            while True:
                socks = dict(self.poll.poll(poll_interval))
                logger.debug(f"Sender socks dict = {socks}")
                if socks.get(self.send_req) == zmq.POLLIN:
                    # not really necessary because we just want one reply for
                    # now.
                    command, reply = self.send_req.recv_multipart()
                    logger.debug(f"command = {command}, of type", type(command))
                    if command == b"receiver-ready":
                        if self.rt is not None:
                            self.rlatest_snap = reply
                            self.rt = self._refresh_rt()
                        logger.debug(
                            f"Id: {self.identity}. command({command}) and message({reply}) received. Proceeding to send fsdata."
                        )
                        break
                    else:
                        if command == b"receiver-init-error":
                            self.msg = f"{command} received for {self.identity}. extended reply: {reply}. Aborting.".encode(
                                "utf-8"
                            )
                        elif command == b"snap-exists":
                            logger.debug(
                                f"Id: {self.identity}. {command} received. Not sending fsdata"
                            )
                            data = {
                                "status": "succeeded",
                                "error": "snapshot already exists on the receiver",
                            }  # noqa E501
                            self.msg = f"Failed to  update replica status for {self.snap_id}".encode(
                                "utf-8"
                            )
                            self.update_replica_status(self.rt2_id, data)
                            self._sys_exit(0)
                        else:
                            self.msg = f"unexpected reply({command}) for {self.identity}. extended reply: {reply}. Aborting".encode(
                                "utf-8"
                            )
                        raise Exception(self.msg)
                else:
                    retries_left -= 1
                    logger.debug(
                        f"Id: {self.identity}. No response from receiver. Number of retry attempts left: {retries_left}"
                    )
                    if retries_left == 0:
                        self.msg = f"Receiver({self.receiver_ip}:{self.receiver_port}) is unreachable. Aborting.".encode(
                            "utf-8"
                        )
                        raise Exception(self.msg)
                    self.send_req.setsockopt(zmq.LINGER, 0)
                    self.send_req.close()
                    self.poll.unregister(self.send_req)
                    self._init_greeting()

            snap_path = f"{settings.MNT_PT}{self.replica.pool}/.snapshots/{self.replica.share}/{self.snap_name}"
            cmd = [BTRFS, "send", snap_path]
            logger.debug(f"init btrfs 'send' cmd {cmd}")
            if self.rt is not None:
                prev_snap = f"{settings.MNT_PT}{self.replica.pool}/.snapshots/{self.replica.share}/{self.rt.snap_name}"
                logger.info(
                    f"Id: {self.identity}. Sending incremental replica between {prev_snap} -- {snap_path}"
                )
                cmd = [BTRFS, "send", "-p", prev_snap, snap_path]
                logger.debug(f"differential btrfs 'send' cmd {cmd}")
            else:
                logger.info(f"Id: {self.identity}. Sending full replica: {snap_path}")

            try:
                self.sp = subprocess.Popen(
                    cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                fcntl.fcntl(self.sp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            except Exception as e:
                self.msg = f"Failed to start the low level btrfs send command({cmd}). Aborting. Exception: {e.__str__()}".encode(
                    "utf-8"
                )
                logger.error(f"Id: {self.identity}. {self.msg}")
                self._send_recv(b"btrfs-send-init-error")
                self._sys_exit(3)

            alive = True
            num_msgs = 0
            t0 = time.time()
            while alive:
                try:
                    if self.sp.poll() is not None:
                        logger.debug(
                            f"Id: {self.identity}. send process finished for {self.snap_id}. "
                            f"rc: {self.sp.returncode}. stderr: {self.sp.stderr.read()}"
                        )
                        alive = False
                    fs_data = self.sp.stdout.read()
                except IOError:
                    continue
                except Exception as e:
                    self.msg = f"Exception occurred while reading low level btrfs send data for {self.snap_id}. Aborting.".encode(
                        "utf-8"
                    )
                    if alive:
                        self.sp.terminate()
                    self.update_trail = True
                    self._send_recv(b"btrfs-send-unexpected-termination-error")
                    self._sys_exit(3)

                self.msg = f"Failed to send fsdata to the receiver for {self.snap_id}. Aborting.".encode(
                    "utf-8"
                )
                self.update_trail = True
                command, message = self._send_recv(b"", fs_data)
                self.total_bytes_sent += len(fs_data)
                num_msgs += 1
                if num_msgs == 1000:
                    num_msgs = 0
                    dsize, drate = self.size_report(self.total_bytes_sent, t0)
                    logger.debug(
                        f"Id: {self.identity} Sender alive. Data transferred: {dsize}. Rate: {drate}/sec."
                    )
                if command is None or command == b"receiver-error":
                    # command is None when the remote side vanishes.
                    self.msg = (
                        f"Got null or error command({command}) message({message}) "
                        "from the Receiver while "
                        "transmitting fsdata. Aborting."
                    ).encode("utf-8")
                    raise Exception(message)

                if not alive:
                    if self.sp.returncode != 0:
                        # do we mark failed?
                        command, message = self._send_recv(
                            b"btrfs-send-nonzero-termination-error"
                        )
                    else:
                        command, message = self._send_recv(
                            b"btrfs-send-stream-finished"
                        )

                if os.getppid() != self.ppid:
                    logger.error(
                        f"Id: {self.identity}. Scheduler exited. Sender for {self.snap_id} cannot go on. Aborting."
                    )
                    self._sys_exit(3)

            data = {
                "status": "succeeded",
                "kb_sent": self.total_bytes_sent / 1024,
            }
            self.msg = f"Failed to update final replica status for {self.snap_id}. Aborting.".encode(
                "utf-8"
            )
            self.update_replica_status(self.rt2_id, data)
            dsize, drate = self.size_report(self.total_bytes_sent, t0)
            logger.debug(
                f"Id: {self.identity}. Send complete. Total data transferred: {dsize}. Rate: {drate}/sec."
            )
            self._sys_exit(0)
