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
Extracting data from procfs
"""

import re
from multiprocessing import Process
import time
import os

from models import (CPUMetric, LoadAvg, MemInfo, PoolUsage)
from storageadmin.models import (Disk, Pool)
from fs.btrfs import pool_usage


class ProcRetreiver(Process):

    def __init__(self, q):
        self.q = q
        self.ppid = os.getpid()
        super(ProcRetreiver, self).__init__()

    def run(self):
        #extract metrics and put in q
        pu_time = time.mktime(time.gmtime())
        while (True):
            if (os.getppid() != self.ppid):
                return

            if (self.q.qsize() < 1000):
                self.cpu_stats()
                self.loadavg()
                self.meminfo()
                pu_time = self.pools_usage(pu_time)
            time.sleep(5)

    def cpu_stats(self):
        stats_file = '/proc/stat'
        with open(stats_file) as sfo:
            for line in sfo.readlines():
                if (re.match('cpu\d', line) is not None):
                    fields = line.split()
                    cm = CPUMetric(name=fields[0], umode=fields[1],
                                    umode_nice=fields[2], smode=fields[3],
                                    idle=fields[4])
                    self.q.put(cm)

    def disk_stats(self):
        stats_file = '/proc/diskstats'
        pass

    def loadavg(self):
        stats_file = '/proc/loadavg'
        with open(stats_file) as sfo:
            line = sfo.readline()
            fields = line.split()
            thread_fields = fields[3].split('/')
            la = LoadAvg(load_1=fields[0], load_5=fields[1], load_15=fields[2],
                         active_threads=thread_fields[0],
                         total_threads=thread_fields[1], latest_pid=fields[4])
            self.q.put(la)

    def meminfo(self):
        stats_file = '/proc/meminfo'
        with open(stats_file) as sfo:
            mem_total = sfo.readline().split()[1]
            mem_free = sfo.readline().split()[1]
            mi = MemInfo(total=mem_total, free=mem_free)
            self.q.put(mi)

    def vmstat(self):
        stats_file = '/proc/vmstat'
        pass

    def pools_usage(self, last_ts):
        """
        This info is not from proc atm, but will eventually be.
        """
        #collect usage only if the data is more than 30 seconds old
        now = time.mktime(time.gmtime())
        if (now - last_ts < 30):
            return last_ts
        for p in Pool.objects.all():
            arb_disk = Disk.objects.filter(pool=p)[0].name
            usage = pool_usage(arb_disk)
            pu = PoolUsage(pool=p.name, usage=usage[1])
            self.q.put(pu)
        return now
