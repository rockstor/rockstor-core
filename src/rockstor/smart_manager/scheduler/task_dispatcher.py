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
from smart_manager.models import (Task, TaskDefinition)
from django.conf import settings
from django.core.serializers import serialize
from task_worker import TaskWorker
from django.utils.timezone import utc

import logging
logger = logging.getLogger(__name__)

class TaskDispatcher(Process):

    def __init__(self, address):
        self.address = address
        self.ppid = os.getpid()
        self.workers = {}
        super(TaskDispatcher, self).__init__()

    def _schedulable(self, td, now):
        if (td.ts > now):
            return False
        if (td.ts == now):
            logger.info('Event: %s is now' % td.name)
            return True
        delta = (now - td.ts).total_seconds()
        if (delta % td.frequency == 0):
            return True
        return False

    def run(self):
        context = zmq.Context()
        sink_socket = context.socket(zmq.PUSH)
        sink_socket.connect('tcp://%s:%d' % settings.SPROBE_SINK)
        total_sleep = 0
        while True:
            if (os.getppid() != self.ppid):
                logger.info('ppids: %d, %d' % (os.getppid(), self.ppid))
                for w in self.workers.keys():
                    worker = self.workers[w]
                    if (worker.is_alive()):
                        #@todo: signal worker to cleanup and exit.
                        worker.task['queue'].put('stop')
                break

            for w in self.workers.keys():
                if (not self.workers[w].is_alive()):
                    to = Task.objects.get(id=w)
                    if (self.workers[w].exitcode == 0):
                        to.state = 'finished'
                    else:
                        to.state = 'error'
                    to.end = datetime.utcnow().replace(tzinfo=utc)
                    data = serialize("json", (to,))
                    sink_socket.send_json(data)
                    del(self.workers[w])

            if (total_sleep == 60):
                for td in TaskDefinition.objects.filter(enabled=True):
                    now = datetime.utcnow().replace(second=0, microsecond=0,
                                                    tzinfo=utc)
                    if (self._schedulable(td, now)):
                        t = Task(task_def=td, state='scheduled', start=now)
                        data = serialize("json", (t,))
                        sink_socket.send_json(data)
                total_sleep = 0

            for t in Task.objects.filter(state='scheduled'):
                worker = TaskWorker(t)
                self.workers[t.id] = worker
                worker.daemon = True
                worker.start()

                if (worker.is_alive()):
                    t.state = 'running'
                    data = serialize("json", (t,))
                    sink_socket.send_json(data)
                else:
                    t.state = 'error'
                    t.end = datetime.utcnow().replace(tzinfo=utc)
                    data = serialize("json", (t,))
                    sink_socket.send_json(data)
            time.sleep(1)
            total_sleep = total_sleep + 1

        sink_socket.close()
        context.term()
        logger.info('terminated context. exiting')

