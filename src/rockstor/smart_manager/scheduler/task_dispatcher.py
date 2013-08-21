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

"""
IR from systemtap

First implementation:
Have a predefined set of stap scripts (saved as script files?)
User can turn a script on to collect data and turn off to stop
"""

from multiprocessing import (Process, Queue)
import zmq
import os
import time
from datetime import datetime
from smart_manager.models import SProbe
from django.conf import settings
from django.core.serializers import serialize
from task_worker import TaskWorker


import logging
logger = logging.getLogger(__name__)

class TaskDispatcher(Process):

    def __init__(self, address):
        self.address = address
        self.ppid = os.getpid()
        self.workers = {}
        super(TaskDispatcher, self).__init__()

    def run(self):
        context = zmq.Context()
        pull_socket = context.socket(zmq.PULL)
        pull_socket.RCVTIMEO = 500
        pull_socket.bind('tcp://%s:%d' % self.address)
        sink_socket = context.socket(zmq.PUSH)
        sink_socket.connect('tcp://%s:%d' % settings.SPROBE_SINK)
        while True:
            if (os.getppid() != self.ppid):
                logger.info('ppids: %d, %d' % (os.getppid(), self.ppid))
                for w in self.workers.keys():
                    worker = self.workers[w]
                    if (worker.is_alive()):
                        worker.task['queue'].put('stop')
                break

            for w in self.workers.keys():
                if (not self.workers[w].is_alive()):
                    ro = SProbe.objects.get(id=w)
                    ro.state = 'error'
                    ro.end = datetime.utcnow()
                    data = serialize("json", (ro,))
                    sink_socket.send_json(data)
                    del(self.workers[w])

            task = None
            try:
                task = pull_socket.recv_json()
                logger.info('received task: %s' % (repr(task)))
            except:
                #will sleeping here help? or some other zmq based wakeup?
                continue

            if (task['action'] == 'start'):
                #wait a little till the recipe instance is saved by the
                #API. non-issue most of the time.
                num_tries = 0
                while True:
                    try:
                        ro = SProbe.objects.get(id=task['roid'])
                        start_tap = True
                        logger.info('start_tap is true')
                        break
                    except:
                        logger.error('waiting for recipe object. num_tries '
                                     '= %d' % num_tries)
                        time.sleep(1)
                        num_tries = num_tries + 1
                        if (num_tries > 20):
                            break

                if (not start_tap):
                    logger.error('not starting the tap')
                    ro.state = 'error'
                    ro.end = datetime.utcnow()
                    data = serialize("json", (ro,))
                    sink_socket.send_json(data)
                    continue

                task['queue'] = Queue()
                task['ro'] = ro
                sworker = StapWorker(task)
                self.workers[task['roid']] = sworker
                sworker.daemon = True
                sworker.start()
                if (sworker.is_alive()):
                    ro.state = 'running'
                    data = serialize("json", (ro,))
                    sink_socket.send_json(data)
                else:
                    ro.state = 'error'
                    ro.end = datetime.utcnow()
                    data = serialize("json", (ro,))
                    sink_socket.send_json(data)

            elif (task['action'] == 'stop'):
                if (task['roid'] in self.workers):
                    sworker = self.workers[task['roid']]
                    #stop the worker, make sure it's stopped
                    sworker.task['queue'].put('stop')
                    del(self.workers[task['roid']])
                ro = SProbe.objects.get(id=task['roid'])
                ro.state = 'stopped'
                ro.end = datetime.utcnow()
                data = serialize("json", (ro,))
                sink_socket.send_json(data)

        pull_socket.close()
        sink_socket.close()
        context.term()
        logger.info('terminated context. exiting')

