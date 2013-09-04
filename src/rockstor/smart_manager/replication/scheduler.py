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
        super(ReplicaScheduler, self).__init__()

    def _replication_interface(self):
        url = 'https://localhost/api/network'
        interfaces = api_call(url)
        logger.info('interfaces: %s' % interfaces)
        return interfaces['results'][0]['ipaddr']

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if (not wd[w].is_alive()):
                    del(wd[w])
        return workers

    def run(self):
        self.rep_ip = self._replication_interface()
        logger.info('got rep_ip')
        ctx = zmq.Context()

        #fs diffs are sent via this publisher.
        rep_pub = ctx.socket(zmq.PUB)
        rep_pub.bind('tcp://%s:%d' % (self.rep_ip, self.data_port))

        #synchronization messages are received in this pull socket
        meta_pull = ctx.socket(zmq.PULL)
        meta_pull.RCVTIMEO = 500
        meta_pull.bind('tcp://%s:%d' % (self.rep_ip, self.meta_port))

        total_sleep = 0
        while True:
            if (os.getppid() != self.ppid):
                logger.info('parent exited. aborting.')
                break

            #check for any recv's coming
            try:
                self.recv_meta = meta_pull.recv_json()
                snap_id = self.recv_meta['id']
                if (self.recv_meta['msg'] == 'begin'):
                    logger.info('begin received. meta: %s' % self.recv_meta)
                    rw = Receiver(self.recv_meta, Queue())
                    self.receivers[snap_id] = rw
                    rw.start()
                    logger.info('started receiver')
                elif (self.recv_meta['msg'] == 'begin_ok'):
                    self.senders[snap_id].q.put('send')
                    logger.info('begin_ok received: %s' % snap_id)
                elif (self.recv_meta['msg'] == 'end'):
                    self.receivers[snap_id].q.put('end')
                    logger.info('end received: %s' % snap_id)
                elif (self.recv_meta['msg'] == 'end_ok'):
                    self.senders[snap_id].q.put('end')
                    logger.info('end_ok received: %s' % snap_id)
                else:
                    pass
            except zmq.error.Again:
                pass

            self._prune_workers((self.receivers, self.senders))

            if (total_sleep >= 60 and len(self.senders) < 50):
                for r in Replica.objects.filter(enabled=True):
                    rt = ReplicaTrail.objects.filter(replica=r).order_by('-state_ts')
                    now = datetime.utcnow().replace(second=0,
                                                    microsecond=0,
                                                    tzinfo=utc)
                    sw = None
                    snap_name = ('%s_replica_snap' % r.share)
                    if (len(rt) == 0):
                        snap_name = ('%s_1' % snap_name)
                        sw = Sender(r, self.rep_ip, rep_pub, Queue(),
                                    snap_name)
                    elif (rt[0].status == 'send_succeeded' and
                          (now - rt[0].state_ts).total_seconds() >
                          r.frequency):
                        snap_name = ('%s_%d' % (snap_name, rt[0].id + 1))
                        sw = Sender(r, self.rep_ip, rep_pub, Queue(),
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
    while(True):
        pass
