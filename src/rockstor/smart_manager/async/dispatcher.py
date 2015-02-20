"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

from multiprocessing import (Process, Queue)
import zmq
import os
import time
from datetime import datetime
from django.conf import settings
from django.utils.timezone import utc
from worker import JobWorker


import logging
logger = logging.getLogger(__name__)


class JobDispatcher(Process):

    def __init__(self, pull_port, push_port):
        self.pull_port = pull_port
        self.push_port = push_port
        self.ppid = os.getpid()
        self.workers = {}
        super(JobDispatcher, self).__init__()

    def run(self):
        try:
            context = zmq.Context()
            pull_socket = context.socket(zmq.PULL)
            pull_socket.bind('tcp://localhost:%d' % self.pull_port)
            push_socket = context.socket(zmq.PUSH)
            push_socket.connect('tcp://localhost:%d' % self.push_port)
        except Exception, e:
            msg = ('Exception while creating initial sockets. Aborting.')
            logger.error(msg)
            logger.exception(e)
            raise e

        jw = JobWorker()
        jw.start()

        while (True):
            if (os.getppid() != self.ppid):
                logger.error('Parent of Job dispatcher exited. Aborting.')
                break
            try:
                job = pull_socket.recv_json()
                push_socket.send_json(job)
            except Exception, e:
                logger.exception(e)
        pull_socket.close()
        push_socket.close()
        context.term()


def main():
    jd = JobDispatcher(10000, 10001)
    jd.start()
    logger.debug('Job dispatcher started')
    jd.join()
