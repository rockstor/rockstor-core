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
from storageadmin.models import (Share, Snapshot)
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
            if ((now - last_task.start).total_seconds() > (td.frequency * 60)):
                return True
        elif (now > td.ts):
            return True
        return False

    def _validate_snap_meta(self, meta):
        if (type(meta) != dict):
            raise Exception('meta must be a dictionary, not %s' % type(meta))
        if ('prefix' not in meta):
            raise Exception('prefix missing from meta. %s' % meta)
        if ('share' not in meta):
            raise Exception('share missing from meta. %s' % meta)
        if (not Share.objects.filter(name=meta['share']).exists()):
            raise Exception('Non-existent Share(%s) in meta. %s' %
                            (meta['share'], meta))
        if ('max_count' not in meta):
            raise Exception('max_count missing from meta. %s' % meta)
        try:
            max_count = int(float(meta['max_count']))
        except:
            raise Exception('max_count is not an integer. %s' % meta)
        if (max_count < 1):
            raise Exception('max_count must atleast be 1, not %d' % max_count)
        return meta

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
                        stype = 'task_scheduler'
                        try:
                            self._validate_snap_meta(meta)
                            name = ('%s_%s' %
                                    (meta['prefix'],
                                     datetime.utcnow().replace(
                                         tzinfo=utc).strftime('%m%d%Y%H%M%S')))
                            url = ('%sshares/%s/snapshots/%s' %
                                   (baseurl, meta['share'], name))
                            api_call(url, data={'snap_type': stype},
                                     calltype='post')
                            t.state = 'finished'
                        except Exception, e:
                            t.state = 'error'
                            logger.exception(e)
                        finally:
                            t.end = datetime.utcnow().replace(tzinfo=utc)
                            t.save()

                        max_count = int(float(meta['max_count']))
                        share = Share.objects.get(name=meta['share'])
                        prefix = ('%s_' % meta['prefix'])
                        snapshots = Snapshot.objects.filter(
                            share=share, snap_type=stype,
                            name__startswith=prefix).order_by('-id')
                        if (len(snapshots) > max_count):
                            for snap in snapshots[max_count:]:
                                url = ('%s/shares/%s/snapshots/%s' %
                                       (baseurl, meta['share'], snap.name))
                                try:
                                    api_call(url, data=None, calltype='delete')
                                except Exception, e:
                                    logger.error('Failed to delete old '
                                                 'snapshot(%s)' % snap.name)
                                    logger.exception(e)

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
                logger.debug('sleeping another 60')
                time.sleep(60)


def main():
    td = TaskDispatcher(settings.SCHEDULER)
    td.start()
    logger.debug('Started Task Scheduler')
    td.join()
