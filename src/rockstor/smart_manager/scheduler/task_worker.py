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
import sys
import logging
logger = logging.getLogger(__name__)
from cli.rest_util import api_call
import json
import time


class TaskWorker(Process):
    baseurl = 'https://localhost/api/'

    def __init__(self, task):
        self.task = task
        self.ppid = os.getpid()
        super(TaskWorker, self).__init__()

    def run(self):

        meta = json.loads(self.task.task_def.json_meta)
        url = None
        if (self.task.task_def.task_type == 'snapshot'):
            name = ('%s_%d' % (meta['prefix'], int(time.time())))
            url = ('%sshares/%s/snapshots/%s' % (self.baseurl, meta['share'],
                                                 name))
        elif (self.task.task_def.task_type == 'scrub'):
            url = ('%spools/%s/scrub' % (self.baseurl, meta['pool']))

        try:
            api_call(url, data=None, calltype='post')
            if (self.task.task_def.task_type == 'scrub'):
                url = ('%spools/%s/scrub/status' % (self.baseurl,
                                                    meta['pool']))
                while (True):
                    status = api_call(url, data=None, calltype='post')
                    logger.info('scrub status: %s' % status)
                    if (status['status'] == 'finished'):
                        break
                    time.sleep(10)

        except Exception, e:
            logger.exception(e)
            sys.exit(3)

