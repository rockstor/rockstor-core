"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
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
import json
import time
from django.conf import settings
from django import db
from contextlib import contextmanager
from smart_manager.replication.util import ReplicationMixin
from fs.btrfs import (
    get_oldest_snap,
    remove_share,
    set_property,
    is_subvol,
    mount_share,
    BTRFS,
)
from system.osi import run_command
from storageadmin.models import Pool, Share, Appliance
from smart_manager.models import ReplicaShare, ReceiveTrail
from cli import APIWrapper
import logging

logger = logging.getLogger(__name__)


class Receiver(ReplicationMixin, Process):
    total_bytes_received: int
    sname: str

    def __init__(self, identity: bytes, meta: bytes):
        self.sender_ip = None
        self.poller = None
        self.dealer = None
        self.law = None
        self.identity = identity  # Otherwise knows as address.
        self.meta = json.loads(meta)
        self.src_share = self.meta["share"]
        self.dest_pool = self.meta["pool"]
        self.incremental = self.meta["incremental"]
        self.snap_name = self.meta["snap"]
        self.sender_id = self.meta["uuid"]
        self.sname = f"{self.sender_id}_{self.src_share}"
        self.snap_dir = f"{settings.MNT_PT}{self.dest_pool}/.snapshots/{self.sname}"
        self.ppid = os.getpid()
        self.kb_received = 0
        self.rid = None
        self.rtid = None
        # We mirror senders max_snap_retain via settings.REPLICATION
        self.num_retain_snaps = settings.REPLICATION.get("max_snap_retain")
        # https://pyzmq.readthedocs.io/en/latest/api/zmq.html#zmq.Context
        self.ctx = zmq.Context()
        self.zmq_version = zmq.__version__
        self.libzmq_version = zmq.zmq_version()
        self.rp = None
        self.raw = None
        self.ack = False
        self.total_bytes_received = 0
        # close all db connections prior to fork.
        db.close_old_connections()
        super(Receiver, self).__init__()

    def _sys_exit(self, code):
        if self.rp is not None and self.rp.returncode is None:
            try:
                self.rp.terminate()
            except Exception as e:
                logger.error(
                    f"Id: {self.identity}. Exception while terminating the btrfs-recv process: {e.__str__()}"
                )
        self.ctx.destroy(linger=0)
        if code == 0:
            logger.debug(f"Id: {self.identity}. meta: {self.meta} Receive successful")
        sys.exit(code)

    @contextmanager
    def _clean_exit_handler(self):
        try:
            yield
        except Exception as e:
            logger.error(f"{self.msg}. Exception: {e.__str__()}")
            if self.rtid is not None:
                try:
                    data = {
                        "status": "failed",
                        "error": self.msg,
                    }
                    self.update_receive_trail(self.rtid, data)
                except Exception as e:
                    msg = f"Id: {self.identity}. Exception while updating receive trail for rtid({self.rtid})."
                    logger.error(f"{msg}. Exception: {e.__str__()}")
            if self.ack is True:
                try:
                    command = b"receiver-error"
                    self.dealer.send_multipart(
                        [
                            b"receiver-error",
                            f"{self.msg}. Exception: {e.__str__()}".encode("utf-8"),
                        ]
                    )
                    # Retry logic here is overkill atm.
                    events = dict(self.poller.poll(60000))  # 60 seconds
                    if events.get(self.dealer) == zmq.POLLIN:
                        msg = self.dealer.recv()
                        logger.debug(
                            f"Id: {self.identity}. Response from the broker: {msg}"
                        )
                    else:
                        logger.debug(
                            f"Id: {self.identity}. No response received from the broker"
                        )
                except Exception as e:
                    msg = f"Id: {self.identity}. Exception while sending {command} back to the broker. Aborting"
                    logger.error(f"{msg}. Exception: {e.__str__()}")
            self._sys_exit(3)

    def _delete_old_snaps(self, share_name, share_path, num_retain):
        oldest_snap = get_oldest_snap(share_path, num_retain, regex="_replication_")
        if oldest_snap is not None:
            if self.delete_snapshot(share_name, oldest_snap):
                return self._delete_old_snaps(share_name, share_path, num_retain)

    def _send_recv(self, command: bytes, msg: bytes = b""):
        logger.debug(
            f"_send_recv called with command: {command}, msg: {msg}."
        )
        rcommand = rmsg = b""
        tracker = self.dealer.send_multipart([command, msg], copy=False, track=True)
        if not tracker.done:
            logger.debug(f"Waiting max 2 seconds for send of commmand ({command})")
            tracker.wait(timeout=2)  # seconds as float
            # Note: And exception here would inform the receiver within the WebUI record.
        events = dict(self.poller.poll(timeout=5000))
        if events.get(self.dealer) == zmq.POLLIN:
            rcommand, rmsg = self.dealer.recv_multipart()
        logger.debug(
            f"Id: {self.identity} _send_recv command: {command} rcommand: {rcommand}"
        )
        logger.debug(f"remote message: {rmsg}")
        return rcommand, rmsg

    def _latest_snap_name(self, rso) -> str | None:
        for snap in ReceiveTrail.objects.filter(
            rshare=rso, status="succeeded"
        ).order_by("-id"):
            if is_subvol(f"{self.snap_dir}/{snap.snap_name}"):
                return str(snap.snap_name)
        logger.error(
            f"Id: {self.identity}. There are no replication snapshots on the system for Share({rso.share})."
        )
        # This would mean, a full backup transfer is required.
        return None

    def run(self):
        logger.debug(
            f"Id: {self.identity}. Starting a new Receiver for meta: {self.meta}"
        )

        self.msg = b"Top level exception in receiver"
        latest_snap = None
        with self._clean_exit_handler():
            self.law = APIWrapper()
            self.poller = zmq.Poller()
            # https://pyzmq.readthedocs.io/en/latest/api/zmq.html#socket
            self.dealer = self.ctx.socket(
                zmq.DEALER, copy_threshold=0
            )  # Setup OUTPUT socket type.
            # self.dealer.set_hwm(10)
            ipc_socket = settings.REPLICATION.get("ipc_socket")
            # Identity must be set before connection.
            self.dealer.setsockopt(zmq.IDENTITY, self.identity)
            self.dealer.connect(f"ipc://{ipc_socket}")
            # Register our poller, for OUTPUT socket, to monitor for POLLIN events.
            self.poller.register(self.dealer, zmq.POLLIN)

            self.ack = True
            self.msg = (
                f"Failed to get the sender ip for appliance: {self.sender_id}. "
                "Ensure receiver has sender in System -> Appliances.".encode("utf-8")
            )
            self.sender_ip = Appliance.objects.get(uuid=self.sender_id).ip

            if not self.incremental:
                self.msg = f"Failed to verify/create share: {self.sname}.".encode(
                    "utf-8"
                )
                self.create_share(self.sname, self.dest_pool)

                self.msg = f"Failed to create the replica metadata object for share: {self.sname}.".encode(
                    "utf-8"
                )
                data = {
                    "share": self.sname,
                    "appliance": self.sender_ip,
                    "src_share": self.src_share,
                }
                self.rid = self.create_rshare(data)
            else:
                self.msg = f"Failed to retreive the replica metadata object for share: {self.sname}.".encode(
                    "utf-8"
                )
                rso = ReplicaShare.objects.get(share=self.sname)
                self.rid = rso.id
                # Find and send the current snapshot to the sender. This will
                # be used as the start by btrfs-send diff.
                self.msg = (
                    b"Failed to verify latest replication snapshot on the system."
                )
                latest_snap = self._latest_snap_name(rso)

            self.msg = f"Failed to create receive trail for rid: {self.rid}".encode(
                "utf-8"
            )
            data = {
                "snap_name": self.snap_name,
            }
            self.rtid = self.create_receive_trail(self.rid, data)

            # delete the share, move the oldest snap to share
            self.msg = b"Failed to promote the oldest Snapshot to Share."
            oldest_snap = get_oldest_snap(
                self.snap_dir, self.num_retain_snaps, regex="_replication_"
            )
            if oldest_snap is not None:
                self.update_repclone(self.sname, oldest_snap)
                self.refresh_share_state()
                self.refresh_snapshot_state()

            self.msg = b"Failed to prune old Snapshots"
            self._delete_old_snaps(self.sname, self.snap_dir, self.num_retain_snaps + 1)

            # TODO: The following should be re-instantiated once we have a
            #  working method for doing so. see validate_src_share.
            # self.msg = (
            #     f"Failed to validate the source share ({self.src_share}) on sender uuid: ({self.sender_id}). "
            #     f"Did the ip of the sender change?"
            # ).encode("utf-8")
            # self.validate_src_share(self.sender_id, self.src_share)

            sub_vol = f"{settings.MNT_PT}{self.dest_pool}/{self.sname}"
            if not is_subvol(sub_vol):
                self.msg = f"Failed to create parent subvolume {sub_vol}".encode(
                    "utf-8"
                )
                run_command([BTRFS, "subvolume", "create", sub_vol])

            self.msg = f"Failed to create snapshot directory: {self.snap_dir}".encode(
                "utf-8"
            )
            run_command(["/usr/bin/mkdir", "-p", self.snap_dir])
            snap_fp = f"{self.snap_dir}/{self.snap_name}"

            # If the snapshot already exists, presumably from the previous
            # attempt and the sender tries to send the same, reply back with
            # snap_exists and do not start the btrfs-receive
            if is_subvol(snap_fp):
                logger.debug(
                    f"Id: {self.identity}. Snapshot to be sent({snap_fp}) already exists. Not starting a new receive process"
                )
                self._send_recv(b"snap-exists")
                self._sys_exit(0)

            cmd = [BTRFS, "receive", self.snap_dir]
            self.msg = f"Failed to start the low level btrfs receive command({cmd}). Aborting.".encode(
                "utf-8"
            )
            self.rp = subprocess.Popen(
                cmd,
                shell=False,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            self.msg = b"Failed to send receiver-ready"
            # Previously our second parameter was (latest_snap or b"")
            if latest_snap is None:
                snap_name = b""
            else:
                snap_name = latest_snap.encode("utf8")
            rcommand, rmsg = self._send_recv(b"receiver-ready", snap_name)
            if rcommand == b"":
                logger.error(
                    f"Id: {self.identity}. No response from the broker for receiver-ready command. Aborting."
                )
                self._sys_exit(3)

            num_tries = 10
            num_msgs = 0
            start_time = time.time()
            while True:
                events = dict(self.poller.poll(timeout=6000))  # 6 seconds
                logger.debug(f"Events dict = {events}")
                if events.get(self.dealer) == zmq.POLLIN:
                    num_tries = 10
                    command, message = self.dealer.recv_multipart()
                    logger.debug(f"command = {command}")
                    if command == b"btrfs-send-stream-finished":
                        # this command concludes fsdata transfer. After this,
                        # btrfs-recev process should be
                        # terminated(.communicate).
                        # poll() returns None while process is running: rc otherwise.
                        if self.rp.poll() is None:
                            self.msg = b"Failed to terminate btrfs-recv command"
                            out, err = self.rp.communicate()
                            out = out.split(b"\n")
                            err = err.split(b"\n")
                            logger.debug(
                                f"Id: {self.identity}. Terminated btrfs-recv. cmd = {cmd} out = {out} err: {err} rc: {self.rp.returncode}"
                            )
                        if self.rp.returncode != 0:
                            self.msg = f"btrfs-recv exited with unexpected exitcode({self.rp.returncode}).".encode(
                                "utf-8"
                            )
                            raise Exception(self.msg)
                        total_kb_received = int(self.total_bytes_received / 1024)
                        data = {
                            "status": "succeeded",
                            "kb_received": total_kb_received,
                        }
                        self.msg = f"Failed to update receive trail for rtid: {self.rtid}".encode(
                            "utf-8"
                        )
                        self.update_receive_trail(self.rtid, data)

                        self._send_recv(b"btrfs-recv-finished")
                        self.refresh_share_state()
                        self.refresh_snapshot_state()

                        dsize, drate = self.size_report(
                            self.total_bytes_received, start_time
                        )
                        logger.debug(
                            f"Id: {self.identity}. Receive complete. Total data transferred: {dsize}. Rate: {drate}/sec."
                        )
                        self._sys_exit(0)

                    if (
                        command == b"btrfs-send-init-error"
                        or command == b"btrfs-send-unexpected-termination-error"
                        or command == b"btrfs-send-nonzero-termination-error"
                    ):
                        self.msg = f"Terminal command({command}) received from the sender. Aborting.".encode(
                            "utf-8"
                        )
                        raise Exception(self.msg)

                    # poll() returns None while process is running: return code otherwise.
                    if self.rp.poll() is None:
                        self.rp.stdin.write(message)
                        self.rp.stdin.flush()
                        # @todo: implement advanced credit request system.
                        self.dealer.send_multipart([b"send-more", b""])
                        num_msgs += 1
                        self.total_bytes_received += len(message)
                        if num_msgs == 1000:
                            num_msgs = 0
                            total_kb_received = int(self.total_bytes_received / 1024)
                            data = {
                                "status": "pending",
                                "kb_received": total_kb_received,
                            }
                            self.update_receive_trail(self.rtid, data)

                            dsize, drate = self.size_report(
                                self.total_bytes_received, start_time
                            )
                            logger.debug(
                                f"Id: {self.identity}. Receiver alive. Data transferred: {dsize}. Rate: {drate}/sec."
                            )
                    else:  # receive process has stopped:
                        out, err = self.rp.communicate()
                        out = out.split(b"\n")
                        err = err.split(b"\n")
                        logger.error(
                            f"Id: {self.identity}. btrfs-recv died unexpectedly. "
                            f"cmd: {cmd} out: {out}. err: {err}"
                        )
                        msg = (
                            f"Low level system error from btrfs receive command. "
                            f"cmd: {cmd} out: {out} err: {err} for rtid: {self.rtid}"
                        ).encode("utf-8")
                        data = {
                            "status": "failed",
                            "error": msg,
                        }
                        self.msg = (
                            f"Failed to update receive trail for rtid: {self.rtid}."
                        ).encode("utf-8")
                        self.update_receive_trail(self.rtid, data)
                        self.msg = msg
                        raise Exception(self.msg)
                else:
                    num_tries -= 1
                    msg = f"No response received from the broker. remaining tries: {num_tries}"
                    logger.error(f"Id: {self.identity}. {msg}")
                    if num_tries == 0:
                        self.msg = f"{msg}. Terminating the receiver.".encode("utf-8")
                        raise Exception(self.msg)
