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

from multiprocessing import Process
import zmq
import os

import logging
logger = logging.getLogger(__name__)


class JobWorker(Process):

    def __init__(self, port):
        self.port = port
        self.ppid = os.getpid()
        super(JobWorker, self).__init__()

    def run(self):
        context = zmq.Context()
        socket = context.socket(zmq.PULL)
        socket.connect('tcp://localhost:%d' % self.port)

        while (True):
            if (os.getppid() != self.ppid):
                logger.error('Job dispatcher exited. Aborting.')
                break

            try:
                job = socket.recv_json()
                logger.debug('job done')
            except Exception, e:
                logger.exception(e)

        socket.close()
        context.term()
