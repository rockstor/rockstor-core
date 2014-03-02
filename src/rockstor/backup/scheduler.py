"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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
from django.utils.timezone import utc
from django.conf import settings
from backup.models import (BackupPolicy, PolicyTrail)
from backup.util import create_trail
from backup.worker import BackupPluginWorker

import logging
logger = logging.getLogger(__name__)

class BackupPluginScheduler(Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.workers = {}
        super(BackupPluginScheduler, self).__init__()

    def _start_new_worker(self, po, initial=False):
        tid = create_trail(po.id, logger)
        worker = BackupPluginWorker(tid, initial=initial)
        worker.start()
        self.workers[po.id] = worker

    def run(self):
        while True:
            if (os.getppid() != self.ppid):
                logger.error('Parent exited. Aborting.')
                break

            for pid,w in self.workers.items():
                if (w.exitcode is not None):
                    logger.debug('worker: %d pruned' % pid)
                    del(self.workers[pid])

            for p in BackupPolicy.objects.filter(enabled=True):
                pt = PolicyTrail.objects.filter(policy=p).order_by('-start')
                now = datetime.utcnow().replace(second=0, microsecond=0,
                                                tzinfo=utc)
                if (len(pt) == 0):
                    self._start_new_worker(p, initial=True)
                elif (p.id in self.workers):
                    logger.debug('previous execution still in progress. not'
                                 ' starting a new one.')
                elif (pt[0].status != 'succeeded'):
                    logger.debug('previous execution failed. not starting'
                                 ' a new one.')
                elif ((now - pt[0].start).total_seconds() < p.frequency):
                    logger.debug('not time yet for this policy execution.')
                else:
                    self._start_new_worker(p)
            time.sleep(1)

def main():
    bs = BackupPluginScheduler()
    bs.start()
    logger.debug('Started Backup Scheduler')
    bs.join()
