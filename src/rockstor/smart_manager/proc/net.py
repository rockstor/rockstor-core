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

from datetime import datetime
from django.utils.timezone import utc

from storageadmin.models import NetworkInterface
from smart_manager.models import NetStat

def network_stats(prev_stats, interval, logger, q):
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
                q.put(ns)
    return cur_stats
