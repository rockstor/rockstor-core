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
import os
import time
from datetime import datetime
from smart_manager.models import (Task, TaskDefinition)
from django.conf import settings
from django.utils.timezone import utc
from cli.rest_util import api_call
import json

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
        if (Task.objects.filter(task_def=td).exists()):
            last_task = Task.objects.filter(task_def=td).order_by('-id')[0]
            if ((now - last_task.start).total_seconds() > td.frequency):
                return True
        elif (now > td.ts):
            return True
        return False

    def run(self):
        running_tasks = {}
        baseurl = 'https://localhost/api/'
        while True:
            if (os.getppid() != self.ppid):
                break
            try:
                for td in TaskDefinition.objects.filter(enabled=True):
                    now = datetime.utcnow().replace(second=0,
                                                    microsecond=0,
                                                    tzinfo=utc)
                    if (self._schedulable(td, now)):
                        if (Task.objects.filter(
                                task_def=td,
                                state__regex=r'(scheduled|started|running)').exists()):
                            logger.debug('there is already a task scheduled or running for this definition')
                        else:
                            t = Task(task_def=td, state='scheduled',
                                     start=now)
                            t.save()

                for t in Task.objects.filter(state='scheduled'):
                    meta = json.loads(t.task_def.json_meta)
                    if (t.task_def.task_type == 'scrub'):
                        url = ('%spools/%s/scrub' % (baseurl, meta['pool']))
                        try:
                            api_call(url, data=None, calltype='post')
                            t.state = 'running'
                        except:
                            t.state = 'error'
                        finally:
                            t.save()
                            if (t.state == 'running'):
                                running_tasks[t.id] = True
                    elif (t.task_def.task_type == 'snapshot'):
                        name = ('%s_%d' % (meta['prefix'], int(time.time())))
                        url = ('%sshares/%s/snapshots/%s' %
                               (baseurl, meta['share'], name))
                        try:
                            api_call(url, data=None, calltype='post')
                            t.state = 'finished'
                        except:
                            t.state = 'error'
                        finally:
                            t.end = datetime.utcnow().replace(tzinfo=utc)
                            t.save()

                for t in Task.objects.filter(
                        state__regex=r'(started|running)'):
                    meta = json.loads(t.task_def.json_meta)
                    if (t.id not in running_tasks):
                        logger.debug('Task(%d) is not in running tasks. '
                                     'marking as error' % t.id)
                        t.state = 'error'
                        t.end = datetime.utcnow().replace(tzinfo=utc)
                        t.save()
                    else:
                        if (t.task_def.task_type == 'scrub'):
                            url = ('%spools/%s/scrub/status' %
                                   (baseurl, meta['pool']))
                            try:
                                status = api_call(url, data=None,
                                                  calltype='post')
                                t.state = status['status']
                            except:
                                t.state = 'error'
                            if (t.state == 'finished' or t.state == 'error'):
                                t.end = datetime.utcnow().replace(tzinfo=utc)
                                del(running_tasks[t.id])
                            t.save()

            except Exception, e:
                e_msg = ('Error getting the list of scheduled tasks. Moving'
                         ' on')
                logger.error(e_msg)
                logger.exception(e)
            finally:
                time.sleep(60)


def main():
    td = TaskDispatcher(settings.SCHEDULER)
    td.start()
    logger.debug('Started Task Scheduler')
    td.join()
