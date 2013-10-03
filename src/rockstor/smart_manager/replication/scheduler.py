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
from smart_manager.models import (Replica, ReplicaTrail)
from django.conf import settings
from django.core.serializers import serialize
from sender import Sender
from receiver import Receiver
from django.utils.timezone import utc
from cli.rest_util import api_call
import logging
logger = logging.getLogger(__name__)

class ReplicaScheduler(Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.senders = {}
        self.receivers = {}
        self.data_port = settings.REPLICA_DATA_PORT
        self.meta_port = settings.REPLICA_META_PORT
        self.recv_meta = None
        self.pubq = Queue()
        super(ReplicaScheduler, self).__init__()

    def _replication_interface(self):
        url = 'https://localhost/api/network'
        interfaces = api_call(url, save_error=False)
        logger.info('interfaces: %s' % interfaces)
        return interfaces['results'][0]['ipaddr']

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if (wd[w].exitcode is not None):
                    del(wd[w])
        return workers

    def run(self):
        sleep_time = 0
        while True:
            try:
                self.rep_ip = self._replication_interface()
                break
            except:
                time.sleep(1)
                sleep_time = sleep_time + 1
                if (sleep_time % 30 == 0):
                    msg = ('Failed to get replication interface for last %d'
                           ' seconds' % sleep_time)
                    logger.info('failed to get replication interface')

        ctx = zmq.Context()
        #fs diffs are sent via this publisher.
        rep_pub = ctx.socket(zmq.PUB)
        rep_pub.bind('tcp://%s:%d' % (self.rep_ip, self.data_port))

        #synchronization messages are received in this pull socket
        meta_pull = ctx.socket(zmq.PULL)
        meta_pull.RCVTIMEO = 100
        meta_pull.bind('tcp://%s:%d' % (self.rep_ip, self.meta_port))

        total_sleep = 0
        while True:
            if (os.getppid() != self.ppid):
                logger.info('parent exited. aborting.')
                break

            while(not self.pubq.empty()):
                msg = self.pubq.get()
                rep_pub.send(msg)

            #check for any recv's coming
            try:
                self.recv_meta = meta_pull.recv_json()
                snap_id = self.recv_meta['id']
                if (self.recv_meta['msg'] == 'begin'):
                    logger.info('begin received. meta: %s' % self.recv_meta)
                    rw = Receiver(self.recv_meta, Queue())
                    self.receivers[snap_id] = rw
                    rw.start()
                elif (self.recv_meta['msg'] == 'begin_ok'):
                    self.senders[snap_id].q.put('send')
                elif (self.recv_meta['msg'] == 'receive_ok' or
                      self.recv_meta['msg'] == 'receive_error'):
                    self.senders[snap_id].q.put(self.recv_meta['msg'])
            except zmq.error.Again:
                pass

            self._prune_workers((self.receivers, self.senders))

            if (total_sleep >= 60 and len(self.senders) < 50):
                logger.info('scanning for replicas')
                for r in Replica.objects.filter(enabled=True):
                    rt = ReplicaTrail.objects.filter(replica=r).order_by('-snapshot_created')
                    now = datetime.utcnow().replace(second=0,
                                                    microsecond=0,
                                                    tzinfo=utc)
                    sw = None
                    snap_name = ('%s_replica_snap' % r.share)
                    if (len(rt) == 0):
                        snap_name = ('%s_1' % snap_name)
                        sw = Sender(r, self.rep_ip, self.pubq, Queue(),
                                    snap_name)
                    elif (rt[0].status == 'succeeded' and
                          (now - rt[0].end_ts).total_seconds() >
                          r.frequency):
                        snap_name = ('%s_%d' % (snap_name, rt[0].id + 1))
                        sw = Sender(r, self.rep_ip, self.pubq, Queue(),
                                    snap_name, rt[0])
                    else:
                        continue
                    snap_id = ('%s_%s_%s_%s' %
                               (self.rep_ip, r.pool, r.share, snap_name))
                    self.senders[snap_id] = sw
                    sw.daemon = True
                    sw.start()
                total_sleep = 0

            time.sleep(1)
            total_sleep = total_sleep + 1

def main():
    rs = ReplicaScheduler()
    rs.start()
    logger.info('started replica scheduler')
    rs.join()
