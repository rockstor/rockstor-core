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
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from smart_manager.models import (CPUMetric, LoadAvg, MemInfo, PoolUsage,
                                  DiskStat, ShareUsage, NetStat, ServiceStatus)
from storageadmin.models import (Disk, Pool, Share, Snapshot, NetworkInterface)
from fs.btrfs import pool_usage, shares_usage

import logging
logger = logging.getLogger(__name__)


class ProcRetreiver(Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.sleep_time = 1
        self._num_ts_records = 0
        super(ProcRetreiver, self).__init__()

    def _save_wrapper(self, ro):
        ro.save()
        self._num_ts_records = self._num_ts_records + 1

    def _truncate_ts_data(self, max_records=settings.MAX_TS_RECORDS):
        """
        cleanup ts tables: CPUMetric, LoadAvg, MemInfo, PoolUsage,
        DiskStat and ShareUsage, ServiceStatus
        Discard all records older than last max_records.
        """
        ts_models = (CPUMetric, LoadAvg, MemInfo, PoolUsage, DiskStat,
                     ShareUsage, ServiceStatus)
        try:
            for m in ts_models:
                try:
                    latest_id = m.objects.latest('id').id
                except ObjectDoesNotExist, e:
                    msg = ('Unable to get latest id for the model: %s. '
                           'Moving on' % (m.__name__))
                    logger.error(msg)
                    continue
                m.objects.filter(id__lt=latest_id-max_records).delete()
        except Exception, e:
            logger.error('Unable to truncate time series data')
            logger.exception(e)
            raise e

    def run(self):
        #  extract metrics and put in q
        pu_time = time.mktime(time.gmtime())
        loadavg_time = pu_time
        cur_disk_stats = None
        cur_net_stats = None
        cur_cpu_stats = {}
        try:
            self._truncate_ts_data()
            while (True):
                if (os.getppid() != self.ppid):
                    msg = ('Parent process(smd) exited. I am exiting too.')
                    return logger.error(msg)

                if (self._num_ts_records > (settings.MAX_TS_RECORDS *
                                            settings.MAX_TS_MULTIPLIER)):
                    self._truncate_ts_data()
                    self._num_ts_records = 0

                with transaction.atomic(using='smart_manager'):
                    cur_cpu_stats = self.cpu_stats(cur_cpu_stats)
                    loadavg_time = self.loadavg(loadavg_time)
                    self.meminfo()
                    pu_time = self.pools_usage(pu_time)
                    cur_disk_stats = self.disk_stats(cur_disk_stats,
                                                     self.sleep_time)
                    cur_net_stats = self.network_stats(cur_net_stats,
                                                       self.sleep_time)
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
                    self._save_wrapper(cm)
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
                            #  special case for pending ios
                            #  just take average
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
                    self._save_wrapper(ds)
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
            self._save_wrapper(la)
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
                    break  # no need to look at lines after dirty.
        ts = datetime.utcnow().replace(tzinfo=utc)
        mi = MemInfo(total=total, free=free, buffers=buffers, cached=cached,
                     swap_total=swap_total, swap_free=swap_free, active=active,
                     inactive=inactive, dirty=dirty, ts=ts)
        self._save_wrapper(mi)

    def vmstat(self):
        stats_file = '/proc/vmstat'
        pass

    def network_stats(self, prev_stats, interval):
        interfaces = [i.name for i in NetworkInterface.objects.all()]
        cur_stats = {}
        with open('/proc/net/dev') as sfo:
            sfo.readline()
            sfo.readline()
            for l in sfo.readlines():
                fields = l.split()
                if (fields[0][:-1] not in interfaces):
                    continue
                cur_stats[fields[0][:-1]] = fields[1:]
        ts = datetime.utcnow().replace(tzinfo=utc)
        if (isinstance(prev_stats, dict)):
            for interface in cur_stats.keys():
                if (interface in prev_stats):
                    data = map(lambda x, y: float(x)/interval if x < y else
                               (float(x) - float(y))/interval,
                               cur_stats[interface], prev_stats[interface])

                    ns = NetStat(device=interface, kb_rx=data[0],
                                 packets_rx=data[1], errs_rx=data[2],
                                 drop_rx=data[3], fifo_rx=data[4],
                                 frame=data[5], compressed_rx=data[6],
                                 multicast_rx=data[7], kb_tx=data[8],
                                 packets_tx=data[9], errs_tx=data[10],
                                 drop_tx=data[11], fifo_tx=data[12],
                                 colls=data[13], carrier=data[14],
                                 compressed_tx=data[15], ts=ts)
                    self._save_wrapper(ns)
        return cur_stats

    def pools_usage(self, last_ts):
        """
        This info is not from proc atm, but will eventually be.
        """
        #  collect usage only if the data is more than 30 seconds old
        now = time.mktime(time.gmtime())
        if (now - last_ts < 30):
            return last_ts
        ts = datetime.utcnow().replace(tzinfo=utc)
        for p in Pool.objects.all():
            total_reclaimable = 0
            try:
                #  get usage of all shares in this pool
                share_map = {}
                snap_map = {}
                for share in Share.objects.filter(pool=p):
                    share_map[share.qgroup] = share.name
                    for snap in Snapshot.objects.filter(share=share):
                        snap_map[snap.qgroup] = snap.real_name
                usaged = shares_usage(p, share_map, snap_map)
                for s in usaged.keys():
                    try:
                        total_reclaimable += (
                            Share.objects.get(name=s).size - usaged[s][1])
                    except:
                        pass
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
                    #  we check for changed in both referenced and exclusive
                    #  usage because in rare cases it's possible for only one
                    #  to change.
                    if ((su is None or su.r_usage != usaged[s][0] or
                         su.e_usage != usaged[s][1])):
                        su = ShareUsage(name=s, r_usage=usaged[s][0],
                                        e_usage=usaged[s][1], ts=ts)
                    else:
                        su.ts = ts
                        su.count = su.count + 1
                    self._save_wrapper(su)
            except Exception, e:
                logger.debug('command exception while getting shares usage '
                             'for pool: %s' % (p.name))
                logger.exception(e)
            try:
                usage = pool_usage('/%s/%s' % (settings.MNT_PT, p.name))
                total_free = usage[2]  # free + reclaimable
                pu = None
                try:
                    pu = PoolUsage.objects.filter(pool=p.name).latest('id')
                    if ((ts - pu.ts).total_seconds() > 90):
                        pu = None
                except Exception, e:
                    e_msg = ('Unable to get latest pool usage object for '
                             'pool(%s). A new one will be created.' % p.name)
                    logger.error(e_msg)
                if ((pu is None or
                     p.size - (pu.free + pu.reclaimable) != usage[1])):
                    pu = PoolUsage(pool=p.name,
                                   free=total_free-total_reclaimable,
                                   reclaimable=total_reclaimable, ts=ts)
                else:
                    pu.ts = ts
                    pu.count = pu.count + 1
                self._save_wrapper(pu)
            except Exception, e:
                logger.debug('command exception while getting pool usage '
                             'for: %s' % (p.name))
                logger.exception(e)
        return now


def main():
    pr = ProcRetreiver()
    pr.start()
    logger.debug('Started Proc Retreiver')
    pr.join()
