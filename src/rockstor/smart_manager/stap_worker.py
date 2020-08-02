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
import os
import zmq
import time
import subprocess
import fcntl

from django.conf import settings
from smart_manager.taplib.probe_config import TAP_MAP
import logging

logger = logging.getLogger(__name__)

STAP_RUN = "/usr/bin/staprun"


class StapWorker(Process):
    def __init__(self, task):
        self.task = task
        self.ppid = os.getpid()
        super(StapWorker, self).__init__()

    def run(self):
        try:
            ctx = zmq.Context()
            sink_socket = ctx.socket(zmq.PUSH)
            sink_socket.connect("tcp://%s:%d" % settings.SPROBE_SINK)
        except Exception as e:
            msg = "Exception while creating initial sockets. Aborting."
            logger.error(msg)
            logger.exception(e)
            raise e
        try:
            return self._run_worker(sink_socket)
        except Exception as e:
            msg = "Unhandled exception in smart probe worker. Exiting."
            logger.error(msg)
            logger.exception(e)
            sink_socket.close()
            ctx.term()
            raise e

    def _run_worker(self, sink_socket):
        retval = 0
        cmd = [
            STAP_RUN,
            self.task["module"],
        ]
        rp = subprocess.Popen(
            cmd, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        fcntl.fcntl(rp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        probe_stopped = False
        sink_data = {
            "cb": TAP_MAP[self.task["tap"]]["cb"],
            "rid": self.task["roid"],
        }
        while True:
            if os.getppid() != self.ppid:
                logger.error("Parent process(stap dispatcher) exited.")
                rp.terminate()
                logger.error(
                    "Terminated the probe process for rid: %s" % self.task["roid"]
                )
                logger.error("I am exiting too.")
                retval = -1
                break
            try:
                sink_data["part_out"] = rp.stdout.read()
                sink_socket.send_json(sink_data)
            except IOError:
                pass
            finally:
                if not self.task["queue"].empty():
                    # stop or pause received.
                    msg = self.task["queue"].get()
                    # @todo: handle pause.
                    rp.terminate()
                    probe_stopped = True
                    break

            if rp.poll() is not None:
                if probe_stopped is not True:
                    msg = "Probe process died. returncode: %s. stderr: %s" % (
                        rp.returncode,
                        rp.stderr.read(),
                    )
                    logger.error(msg)
                break
            time.sleep(0.5)
        return retval
