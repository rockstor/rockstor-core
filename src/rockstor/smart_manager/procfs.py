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
from datetime import datetime
from django.utils.timezone import utc
from django.db import transaction

from models import (CPUMetric, LoadAvg, MemInfo, PoolUsage, DiskStat,
                    ShareUsage)
from storageadmin.models import (Disk, Pool, Share, Snapshot)
from fs.btrfs import pool_usage, shares_usage
from proc.net import network_stats

import logging
logger = logging.getLogger(__name__)
from django.core.serializers import serialize
import zmq
from django.conf import settings


class ProcRetreiver(Process):

    def __init__(self):
        #self.q = q
        self.ppid = os.getpid()
        self.sleep_time = 1
        super(ProcRetreiver, self).__init__()

    def _sink_put(self, sink, ro):
        ro.save()
        #data = serialize("json", (ro,))
        #sink.send_json(data)

    def run(self):
        context = zmq.Context()
        self.sink_socket = context.socket(zmq.PUSH)
        self.sink_socket.connect('tcp://%s:%d' % settings.SPROBE_SINK)
        #extract metrics and put in q
        pu_time = time.mktime(time.gmtime())
        loadavg_time = pu_time
        cur_disk_stats = None
        cur_net_stats = None
        cur_cpu_stats = {}
        try:
            while (True):
                if (os.getppid() != self.ppid):
                    msg = ('Parent process(smd) exited. I am exiting too.')
                    return logger.error(msg)

                cur_cpu_stats = self.cpu_stats(cur_cpu_stats)
                loadavg_time = self.loadavg(loadavg_time)
                self.meminfo()
                pu_time = self.pools_usage(pu_time)
                cur_disk_stats = self.disk_stats(cur_disk_stats,
                                                 self.sleep_time)
                cur_net_stats = network_stats(cur_net_stats, self.sleep_time,
                                              logger, self.sink_socket)
                time.sleep(self.sleep_time)
        except Exception, e:
            logger.error('unhandled exception in %s. Exiting' % self.name)
            logger.exception(e)
            raise e

    def cpu_stats(self, prev_stats):
        stats_file = '/proc/stat'
        cur_stats = {}
        with open(stats_file) as sfo:
            ts = datetime.utcnow().replace(tzinfo=utc)
            for line in sfo.readlines():
                if (re.match('cpu\d', line) is not None):
                    fields = line.split()
                    fields[1:] = map(int, fields[1:])
                    cm = None
                    if (fields[0] not in prev_stats):
                        cm = CPUMetric(name=fields[0], umode=fields[1],
                                       umode_nice=fields[2], smode=fields[3],
                                       idle=fields[4], ts=ts)
                    else:
                        prev = prev_stats[fields[0]]
                        cm = CPUMetric(name=fields[0], umode=fields[1]-prev[1],
                                       umode_nice=fields[2]-prev[2],
                                       smode=fields[3]-prev[3],
                                       idle=fields[4]-prev[4], ts=ts)
                    cur_stats[fields[0]] = fields
                    self._sink_put(self.sink_socket, cm)
        return cur_stats

    def disk_stats(self, prev_stats, interval):
        stats_file = '/proc/diskstats'
        cur_stats = {}
        disks = [d.name for d in Disk.objects.all()]
        with open(stats_file) as sfo:
            for line in sfo.readlines():
                fields = line.split()
                if (fields[2] not in disks):
                    continue
                cur_stats[fields[2]] = fields[2:]
        if (isinstance(prev_stats, dict)):
            ts = datetime.utcnow().replace(tzinfo=utc)
            for disk in cur_stats.keys():
                if (disk in prev_stats):
                    prev = prev_stats[disk]
                    cur = cur_stats[disk]
                    data = []
                    for i in range(1, len(prev)):
                        if (i == 9):
                            #special case for pending ios
                            #just take average
                            avg_ios = (float(cur[i]) + float(prev[i]))/2
                            data.append(avg_ios)
                            continue
                        datum = None
                        if (cur[i] < prev[i]):
                            datum = float(cur[i])/interval
                        else:
                            datum = (float(cur[i]) - float(prev[i]))/interval
                        data.append(datum)
                    ds = DiskStat(name=disk, reads_completed=data[0],
                                  reads_merged=data[1],
                                  sectors_read=data[2],
                                  ms_reading=data[3],
                                  writes_completed=data[4],
                                  writes_merged=data[5],
                                  sectors_written=data[6],
                                  ms_writing=data[7],
                                  ios_progress=data[8],
                                  ms_ios=data[9],
                                  weighted_ios=data[10],
                                  ts=ts)
                    self._sink_put(self.sink_socket, ds)
        return cur_stats

    def loadavg(self, last_ts):
        now = time.mktime(time.gmtime())
        if (now - last_ts < 30):
            return last_ts

        stats_file = '/proc/loadavg'
        with open(stats_file) as sfo, open('/proc/uptime') as ufo:
            line = sfo.readline()
            fields = line.split()
            thread_fields = fields[3].split('/')
            idle_seconds = int(float(ufo.readline().split()[1]))
            ts = datetime.utcnow().replace(tzinfo=utc)
            la = LoadAvg(load_1=fields[0], load_5=fields[1], load_15=fields[2],
                         active_threads=thread_fields[0],
                         total_threads=thread_fields[1], latest_pid=fields[4],
                         idle_seconds=idle_seconds, ts=ts)
            self._sink_put(self.sink_socket, la)
        return now

    def meminfo(self):
        stats_file = '/proc/meminfo'
        (total, free, buffers, cached, swap_total, swap_free, active, inactive,
         dirty,) = (None,) * 9
        with open(stats_file) as sfo:
            for l in sfo.readlines():
                if (re.match('MemTotal:', l) is not None):
                    total = int(l.split()[1])
                elif (re.match('MemFree:', l) is not None):
                    free = int(l.split()[1])
                elif (re.match('Buffers:', l) is not None):
                    buffers = int(l.split()[1])
                elif (re.match('Cached:', l) is not None):
                    cached = int(l.split()[1])
                elif (re.match('SwapTotal:', l) is not None):
                    swap_total = int(l.split()[1])
                elif (re.match('SwapFree:', l) is not None):
                    swap_free = int(l.split()[1])
                elif (re.match('Active:', l) is not None):
                    active = int(l.split()[1])
                elif (re.match('Inactive:', l) is not None):
                    inactive = int(l.split()[1])
                elif (re.match('Dirty:', l) is not None):
                    dirty = int(l.split()[1])
                    break # no need to look at lines after dirty.
        ts = datetime.utcnow().replace(tzinfo=utc)
        mi = MemInfo(total=total, free=free, buffers=buffers, cached=cached,
                     swap_total=swap_total, swap_free=swap_free, active=active,
                     inactive=inactive, dirty=dirty, ts=ts)
        self._sink_put(self.sink_socket, mi)

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
        ts = datetime.utcnow().replace(tzinfo=utc)
        for p in Pool.objects.all():
            arb_disk = Disk.objects.filter(pool=p)[0].name
            try:
                usage = pool_usage(arb_disk)
                pu = None
                try:
                    pu = PoolUsage.objects.filter(pool=p.name).latest('id')
                    if ((ts - pu.ts).total_seconds() > 90):
                        pu = None
                except Exception, e:
                    e_msg = ('Unable to get latest pool usage object for '
                             'pool(%s). A new one will be created.' % p.name)
                    logger.error(e_msg)
                if (pu is None or pu.usage != usage[1]):
                    pu = PoolUsage(pool=p.name, usage=usage[1], ts=ts)
                else:
                    pu.ts = ts
                    pu.count = pu.count + 1
                self._sink_put(self.sink_socket, pu)
            except Exception, e:
                logger.debug('command exception while getting pool usage '
                             'for: %s' % (p.name))
                logger.exception(e)
            try:
                #get usage of all shares in this pool
                pool_device = Disk.objects.filter(pool=p)[0].name
                share_map = {}
                snap_map = {}
                for share in Share.objects.filter(pool=p):
                    share_map[share.qgroup] = share.name
                    for snap in Snapshot.objects.filter(share=share):
                        snap_map[snap.qgroup] = snap.real_name
                usaged = shares_usage(p.name, pool_device, share_map, snap_map)
                for s in usaged.keys():
                    su = None
                    try:
                        su = ShareUsage.objects.filter(name=s).latest('id')
                        if ((ts - su.ts).total_seconds() > 90):
                            su = None
                    except Exception, e:
                        e_msg = ('Unable to get latest share usage object '
                                 'for share(%s). A new one will be created.'
                                 % s)
                        logger.error(e_msg)
                    #we check for changed in both referenced and exclusive
                    #usage because in rare cases it's possible for only one to
                    #change.
                    if (su is None or su.r_usage != usaged[s][0] or
                        su.e_usage != usaged[s][1]):
                        su = ShareUsage(name=s, r_usage=usaged[s][0],
                                        e_usage=usaged[s][1], ts=ts)
                    else:
                        su.ts = ts
                        su.count = su.count + 1
                    self._sink_put(self.sink_socket, su)
            except Exception, e:
                logger.debug('command exception while getting shares usage '
                             'for pool: %s' % (p.name))
                logger.exception(e)
        return now
