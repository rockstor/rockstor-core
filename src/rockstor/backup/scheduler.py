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
import logging
logger = logging.getLogger(__name__)
from backup.models import (BackupPolicy, PolicyTrail)

class BackupPluginScheduler(Process):

    def __init__(self):
        self.ppid = os.getpid()
        super(BackupPluginScheduler, self).__init__()

    def run(self):
        while True:
            if (os.getppid() != self.ppid):
                logger.error('Parent exited. Aborting.')
                break

            for p in BackupPolicy.objects.filter(enabled=True):
                pt = PolicyTrail.objects.filter(policy=p).order_by('-start')
                now = datetime.utcnow().replace(second=0, microsecond=0,
                                                tzinfo=utc)
                if (len(pt) == 0 or
                    (now - pt[0].start).total_seconds() > p.frequency):
                    new_pt = PolicyTrail(policy=p, start=now)
                    new_pt.save()
            time.sleep(1)

def main():
    bs = BackupPluginScheduler()
    bs.start()
    logger.debug('Started Replica Scheduler')
    bs.join()
