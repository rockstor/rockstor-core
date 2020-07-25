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

from multiprocessing import Process, Queue
import zmq
import os
import time
from datetime import datetime
from smart_manager.models import SProbe
from django.conf import settings
from django.utils.timezone import utc
from stap_worker import StapWorker
import logging

logger = logging.getLogger(__name__)


class Stap(Process):
    def __init__(self, address):
        self.address = address
        self.ppid = os.getpid()
        self.workers = {}
        super(Stap, self).__init__()

    def _prune_workers(self, workers, sink_socket):
        for w in workers.keys():
            # reading exitcode of properly exited child relieves it from being
            # a zombie.
            ec = workers[w].exitcode
            if ec is not None:
                if ec != 0:
                    ro = SProbe.objects.get(id=w)
                    ro.state = "error"
                    ro.end = datetime.utcnow().replace(tzinfo=utc)
                    self._sink_put(sink_socket, ro)
                del self.workers[w]

    def _sink_put(self, sink, ro):
        ro.save()
        # data = serialize("json", (ro,))
        # sink.send_json(data)

    def _get_ro(self, rid, num_tries):
        for i in range(num_tries):
            try:
                return SProbe.objects.get(id=rid)
            except:
                logger.error("waiting for probe object. num_tries = %d" % i)
                time.sleep(1)
        return None

    def run(self):
        try:
            context = zmq.Context()
            pull_socket = context.socket(zmq.PULL)
            pull_socket.RCVTIMEO = 1000
            pull_socket.bind("tcp://%s:%d" % self.address)
            sink_socket = context.socket(zmq.PUSH)
            sink_socket.connect("tcp://%s:%d" % settings.SPROBE_SINK)
        except Exception as e:
            msg = "Exception while creating initial sockets. Aborting."
            logger.error(msg)
            logger.exception(e)
            raise e
        try:
            while True:
                if os.getppid() != self.ppid:
                    msg = "Parent process(smd) exited. I am exiting too."
                    logger.error(msg)
                    return -1
                self.run_dispatcher(pull_socket, sink_socket)
        except Exception as e:
            msg = "Unhandled exception in smart probe dispatcher. Exiting."
            logger.error(msg)
            logger.exception(e)
            pull_socket.close()
            sink_socket.close()
            context.term()
            raise e

    def run_dispatcher(self, pull_socket, sink_socket):
        self._prune_workers(self.workers, sink_socket)
        task = None
        try:
            task = pull_socket.recv_json()
        except:
            return

        if task["action"] == "start":
            # wait a little till the recipe instance is saved by the
            # API. non-issue most of the time.
            ro = self._get_ro(task["roid"], 20)
            if ro is None:
                return logger.error("Unable to retreive rid: %d. giving up.")
            task["queue"] = Queue()
            task["ro"] = ro
            sworker = StapWorker(task)
            self.workers[task["roid"]] = sworker
            sworker.start()
            if sworker.is_alive():
                ro.state = "running"
            else:
                ro.state = "error"
                ro.end = datetime.utcnow().replace(tzinfo=utc)
            return self._sink_put(sink_socket, ro)

        if task["action"] == "stop":
            if task["roid"] in self.workers:
                sworker = self.workers[task["roid"]]
                sworker.task["queue"].put("stop")
            ro = SProbe.objects.get(id=task["roid"])
            ro.state = "stopped"
            ro.end = datetime.utcnow().replace(tzinfo=utc)
            return self._sink_put(sink_socket, ro)
