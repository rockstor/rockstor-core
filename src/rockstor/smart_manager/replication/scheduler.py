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
import zmq
import os
import time
from datetime import datetime
from storageadmin.models import (NetworkInterface, Appliance)
from smart_manager.models import (ReplicaTrail, ReplicaShare, Replica)
from django.conf import settings
from sender import Sender
from receiver import Receiver
from django.utils.timezone import utc
from cli.rest_util import api_call
import logging
logger = logging.getLogger(__name__)
from django.db import DatabaseError
from util import ReplicationMixin
import json


class ReplicaScheduler(ReplicationMixin, Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.senders = {}
        self.receivers = {}
        self.data_port = settings.REPLICA_DATA_PORT
        self.meta_port = settings.REPLICA_META_PORT
        self.MAX_ATTEMPTS = settings.MAX_REPLICA_SEND_ATTEMPTS
        self.recv_meta = None
        self.uuid = None
        self.base_url = 'https://localhost/api'
        self.rep_ip = None
        self.uuid = None
        self.trail_prune_interval = 3600 #seconds
        self.prune_time = int(time.time()) - (self.trail_prune_interval + 1)
        super(ReplicaScheduler, self).__init__()

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if (wd[w].exitcode is not None):
                    del(wd[w])
                    logger.debug('deleted worker: %s' % w)
        return workers

    def _process_send(self, replica):
        rt = ReplicaTrail.objects.filter(replica=replica).order_by('-id')
        now = datetime.utcnow().replace(second=0,
                                        microsecond=0,
                                        tzinfo=utc)
        sw = None
        snap_name = '%s_%d_replication' % (replica.share, replica.id)
        if (len(rt) == 0):
            snap_name = '%s_1' % snap_name
        else:
            snap_name = '%s_%d' % (snap_name, rt[0].id + 1)
        snap_id = ('%s_%s_%s_%s' %
                   (self.uuid, replica.pool, replica.share, snap_name))
        if (len(rt) == 0):
            logger.debug('new sender for snap: %s' % snap_id)
            sw = Sender(replica, self.rep_ip, snap_name, self.meta_port,
                        self.data_port, replica.meta_port, self.uuid, snap_id)
        elif (rt[0].status == 'succeeded'):
            logger.debug('incremental sender for snap: %s'
                         % snap_id)
            sw = Sender(replica, self.rep_ip, snap_name, self.meta_port,
                        self.data_port, replica.meta_port, self.uuid, snap_id,
                        rt[0])
        elif (rt[0].status == 'pending'):
            prev_snap_id = ('%s_%s_%s_%s' % (self.uuid,
                            replica.pool, replica.share, rt[0].snap_name))
            if (prev_snap_id in self.senders):
                return logger.debug('send process ongoing for snap: '
                                    '%s' % prev_snap_id)
            logger.debug('%s not found in senders. Previous '
                         'sender must have Aborted. Marking '
                         'it as failed' % prev_snap_id)
            msg = ('Sender process Aborted. See logs for '
                   'more information')
            data = {'status': 'failed',
                    'end_ts': now.strftime(settings.SNAP_TS_FORMAT),
                    'error': msg,
                    'send_failed': now, }
            return self.update_replica_status(rt[0].id, data)
        elif (rt[0].status == 'failed'):
            snap_name = rt[0].snap_name
            #  if num_failed attempts > 10, disable the replica
            num_tries = 0
            for rto in rt:
                if (rto.status != 'failed' or
                    num_tries >= self.MAX_ATTEMPTS or
                    rto.end_ts < replica.ts):
                    break
                num_tries = num_tries + 1
            if (num_tries >= self.MAX_ATTEMPTS):
                logger.info('Maximum attempts(%d) reached '
                            'for snap: %s. Disabling the '
                            'replica.' %
                            (self.MAX_ATTEMPTS, snap_id))
                return self.disable_replica(replica.id)

            logger.info('previous backup failed for snap: '
                        '%s. Starting a new one. Attempt '
                        '%d/%d.' % (snap_id, num_tries,
                                    self.MAX_ATTEMPTS))
            prev_rt = None
            for rto in rt:
                if (rto.status == 'succeeded'):
                    prev_rt = rto
                    break
            sw = Sender(replica, self.rep_ip, snap_name, self.meta_port,
                        self.data_port, replica.meta_port, self.uuid, snap_id,
                        prev_rt)
        else:
            return logger.error('unknown replica trail status: %s. '
                                'ignoring snap: %s' %
                                (rt[0].status, snap_id))
        self.senders[snap_id] = sw
        sw.daemon = True
        sw.start()

    def run(self):
        try:
            if (NetworkInterface.objects.filter(itype='replication').exists()):
                self.rep_ip = NetworkInterface.objects.filter(itype='replication')[0].ipaddr
            else:
                self.rep_ip = NetworkInterface.objects.filter(ipaddr__isnull=False)[0].ipaddr
        except Exception, e:
            msg = ('Failed to get replication interface. Aborting. '
                   'Exception: %s' % e.__str__())
            return logger.error(msg)

        try:
            self.uuid = Appliance.objects.get(current_appliance=True).uuid
        except Exception, e:
            msg = ('Failed to get uuid of current appliance. Aborting. '
                   'Exception: %s' % e.__str__())
            return logger.error(msg)

        ctx = zmq.Context()
        #  fs diffs are sent via this publisher.
        rep_pub = ctx.socket(zmq.PUB)
        rep_pub.bind('tcp://%s:%d' % (self.rep_ip, self.data_port))

        #  synchronization messages are received in this pull socket
        meta_pull = ctx.socket(zmq.PULL)
        meta_pull.bind('tcp://%s:%d' % (self.rep_ip, self.meta_port))

        data_sink = ctx.socket(zmq.PULL)
        data_sink.bind('tcp://%s:%d' % (self.rep_ip, settings.REPLICA_SINK_PORT))

        poller = zmq.Poller()
        poller.register(meta_pull, zmq.POLLIN)
        poller.register(data_sink, zmq.POLLIN)

        while True:
            if (os.getppid() != self.ppid):
                logger.error('Parent exited. Aborting.')
                ctx.destroy()
                break

            while True:
                #This loop may still continue even if replication service
                #is terminated, as long as data is coming in.
                socks = dict(poller.poll(timeout=10000)) #poll for 10 seconds
                if (meta_pull in socks and socks[meta_pull] == zmq.POLLIN):
                    self.recv_meta = meta_pull.recv_json()
                    msg_id = self.recv_meta.get('id', -1)
                    msg = self.recv_meta.get('msg', '')
                    if (msg == 'begin'):
                        rw = Receiver(self.recv_meta)
                        self.receivers[msg_id] = rw
                        rw.start()
                    elif (msg == 'new_send'):
                        self._prune_workers((self.receivers, self.senders))
                        try:
                            replica = Replica.objects.get(id=msg_id, enabled=True)
                            self._process_send(replica)
                        except Replica.DoesNotExist:
                            logger.error('Replication task with id(%s) does '
                                         'not exist of is not enabled.' % msg_id)
                    elif (msg_id in self.senders):
                        msg = 'meta-%s%s' % (msg_id, json.dumps(self.recv_meta))
                        rep_pub.send(str(msg))
                    else:
                        logger.error('Message(%s) cannot be processed. Ignoring'
                                     % self.recv_meta)
                elif (data_sink in socks and socks[data_sink] == zmq.POLLIN):
                    rep_pub.send(data_sink.recv())
                elif (len(socks) != 0):
                    logger.error('poller picked up something unknown: %s' % socks)
                else:
                    #poller came out empty after timeout. break to do other things
                    break

            if (int(time.time()) - self.prune_time > self.trail_prune_interval):
                #trail objects keep accumulating and may grow to be quite large.
                #so once every trail_prune_interval seconds, deleted the old ones
                #by default the prune helper methods delete records older than 7 days
                self.prune_time = int(time.time()) #reset
                for rs in ReplicaShare.objects.all():
                    self.prune_receive_trail(rs.id)
                for r in Replica.objects.all():
                    self.prune_replica_trail(r.id)

def main():
    rs = ReplicaScheduler()
    rs.start()
    logger.debug('Started Replica Scheduler')
    rs.join()
