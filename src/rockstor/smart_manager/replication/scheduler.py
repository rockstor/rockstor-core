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
from smart_manager.models import (ReplicaTrail, ReplicaShare, Replica)
from django.conf import settings
from sender import Sender
from receiver import Receiver
from django.utils.timezone import utc
from cli.rest_util import api_call
import logging
logger = logging.getLogger(__name__)
from django.db import DatabaseError
from util import (update_replica_status, disable_replica, prune_receive_trail,
                  get_replicas, get_replica_trail, prune_replica_trail)


class ReplicaScheduler(Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.senders = {}
        self.receivers = {}
        self.data_port = settings.REPLICA_DATA_PORT
        self.meta_port = settings.REPLICA_META_PORT
        self.MAX_ATTEMPTS = settings.MAX_REPLICA_SEND_ATTEMPTS
        self.recv_meta = None
        self.pubq = Queue()
        self.uuid = None
        self.prune_time = int(time.time())
        super(ReplicaScheduler, self).__init__()

    def _my_uuid(self):
        url = 'https://localhost/api/appliances/1'
        ad = api_call(url, save_error=False)
        return ad['uuid']

    def _replication_interface(self):
        url = 'https://localhost/api/network'
        interfaces = api_call(url, save_error=False)
        mgmt_iface = [x for x in interfaces['results']
                      if x['itype'] == 'management'][0]
        return mgmt_iface['ipaddr']

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if (wd[w].exitcode is not None):
                    del(wd[w])
        return workers

    def run(self):
        while True:
            try:
                self.rep_ip = self._replication_interface()
                self.uuid = self._my_uuid()
                break
            except:
                msg = ('Failed to get replication interface or uuid. '
                       'Aborting.')
                return logger.error(msg)

        ctx = zmq.Context()
        #  fs diffs are sent via this publisher.
        rep_pub = ctx.socket(zmq.PUB)
        rep_pub.bind('tcp://%s:%d' % (self.rep_ip, self.data_port))

        #  synchronization messages are received in this pull socket
        meta_pull = ctx.socket(zmq.PULL)
        meta_pull.RCVTIMEO = 100
        meta_pull.bind('tcp://%s:%d' % (self.rep_ip, self.meta_port))

        total_sleep = 0
        while True:
            if (os.getppid() != self.ppid):
                logger.error('Parent exited. Aborting.')
                break

            while(not self.pubq.empty()):
                msg = self.pubq.get()
                rep_pub.send(msg)

            #  check for any recv's coming
            num_msgs = 0
            while (num_msgs < 1000):
                try:
                    self.recv_meta = meta_pull.recv_json()
                    num_msgs = num_msgs + 1
                    snap_id = self.recv_meta['id']
                    if (self.recv_meta['msg'] == 'begin'):
                        rw = Receiver(self.recv_meta)
                        self.receivers[snap_id] = rw
                        rw.start()
                    elif (snap_id not in self.senders):
                        logger.error('Unknown snap_id(%s) received. Ignoring'
                                     % snap_id)
                    else:
                        self.senders[snap_id].q.put(self.recv_meta)
                except zmq.error.Again:
                    break

            self._prune_workers((self.receivers, self.senders))

            if (int(time.time()) - self.prune_time > 3600):
                self.prune_time = int(time.time())
                for rs in ReplicaShare.objects.all():
                    prune_receive_trail(rs.id, logger)
                for r in Replica.objects.all():
                    prune_replica_trail(r.id, logger)

            if (total_sleep >= 60 and len(self.senders) < 50):

                try:
                    for r in get_replicas(logger):
                        rt = get_replica_trail(r.id, logger)
                        now = datetime.utcnow().replace(second=0,
                                                        microsecond=0,
                                                        tzinfo=utc)
                        sw = None
                        snap_name = 'replication'
                        rt2 = ReplicaTrail.objects.filter().order_by('-id')
                        if (len(rt2) != 0):
                            snap_name = ('%s_%d' % (snap_name, rt2[0].id + 1))
                        else:
                            snap_name = ('%s_1' % snap_name)
                        snap_id = ('%s_%s_%s_%s' %
                                   (self.uuid, r.pool, r.share, snap_name))
                        if (len(rt) == 0):
                            logger.debug('new sender for snap: %s' % snap_id)
                            sw = Sender(r, self.rep_ip, self.pubq, Queue(),
                                        snap_name, self.meta_port,
                                        self.data_port, r.meta_port, self.uuid,
                                        snap_id)
                        elif (rt[0].status == 'succeeded'):
                            if (((now - rt[0].end_ts).total_seconds() >
                                 (r.frequency * 60))):
                                logger.debug('incremental sender for snap: %s'
                                             % snap_id)
                                sw = Sender(r, self.rep_ip, self.pubq, Queue(),
                                            snap_name, self.meta_port,
                                            self.data_port, r.meta_port,
                                            self.uuid, snap_id, rt[0])
                            else:
                                continue
                        elif (rt[0].status == 'pending'):
                            prev_snap_id = ('%s_%s_%s_%s' % (self.uuid,
                                            r.pool, r.share, rt[0].snap_name))
                            if (prev_snap_id in self.senders):
                                logger.debug('send process ongoing for snap: '
                                             '%s' % snap_id)
                                continue
                            logger.debug('%s not found in senders. Previous '
                                         'sender must have Aborted. Marking '
                                         'it as failed' % prev_snap_id)
                            msg = ('Sender process Aborted. See logs for '
                                   'more information')
                            data = {'status': 'failed',
                                    'end_ts': now,
                                    'error': msg,
                                    'send_failed': now, }
                            update_replica_status(rt[0].id, data, logger)
                            continue
                        elif (rt[0].status == 'failed'):
                            snap_name = rt[0].snap_name
                            #  if num_failed attempts > 10, disable the replica
                            num_tries = 0
                            for rto in rt:
                                if (rto.status != 'failed' or
                                    num_tries >= self.MAX_ATTEMPTS or
                                    rto.end_ts < r.ts):
                                    break
                                num_tries = num_tries + 1
                            if (num_tries >= self.MAX_ATTEMPTS):
                                logger.info('Maximum attempts(%d) reached '
                                            'for snap: %s. Disabling the '
                                            'replica.' %
                                            (self.MAX_ATTEMPTS, snap_id))
                                disable_replica(r.id, logger)
                                continue
                            logger.info('previous backup failed for snap: '
                                        '%s. Starting a new one. Attempt '
                                        '%d/%d.' % (snap_id, num_tries,
                                                    self.MAX_ATTEMPTS))
                            prev_rt = None
                            for rto in rt:
                                if (rto.status == 'succeeded'):
                                    prev_rt = rto
                                    break
                            sw = Sender(r, self.rep_ip, self.pubq, Queue(),
                                        snap_name, self.meta_port,
                                        self.data_port, r.meta_port,
                                        self.uuid, snap_id, prev_rt)
                        else:
                            logger.error('unknown replica trail status: %s. '
                                         'ignoring snap: %s' %
                                         (rt[0].status, snap_id))
                            continue
                        self.senders[snap_id] = sw
                        sw.daemon = True
                        sw.start()
                    total_sleep = 0
                except DatabaseError, e:
                    e_msg = ('Error getting the list of enabled replica '
                             'tasks. Moving on')
                    logger.error(e_msg)
                    logger.exception(e)

            time.sleep(1)
            total_sleep = total_sleep + 1


def main():
    logger.debug('starting replica scheduler')
    rs = ReplicaScheduler()
    rs.start()
    logger.debug('Started Replica Scheduler')
    rs.join()
