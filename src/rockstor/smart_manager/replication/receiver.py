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
import os
import sys
import logging
import zmq
import subprocess
import fcntl
import json
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from util import (create_share, update_receive_trail, create_snapshot,
                  create_rshare)

BTRFS = '/sbin/btrfs'
logger = logging.getLogger(__name__)

class Receiver(Process):
    baseurl = 'https://localhost/api/'

    def __init__(self, meta, q):
        self.meta = meta
        self.meta_port = settings.REPLICA_META_PORT
        self.data_port = settings.REPLICA_DATA_PORT
        self.q = q
        self.ppid = os.getpid()
        self.kb_received = 0
        super(Receiver, self).__init__()

    def _clean_exit(self, msg, exception):
        logger.error(msg)
        logger.exception(exception)
        sys.exit(3)

    def run(self):
        ctx = zmq.Context()
        try:
            recv_sub = ctx.socket(zmq.SUB)
            recv_sub.connect('tcp://%s:%d' % (self.meta['ip'], self.data_port))
            recv_sub.RCVTIMEO = 100
            recv_sub.setsockopt(zmq.SUBSCRIBE, str(self.meta['id']))
        except Exception, e:
            msg = ('Failed to connect to the sender(%s) on '
                   'data_port(%s). meta: %s. Aborting.'
                   % (self.meta['ip'], self.data_port, self.meta))
            self._clean_exit(msg, e)

        try:
            meta_push = ctx.socket(zmq.PUSH)
            meta_push.connect('tcp://%s:%d' % (self.meta['ip'],
                                               self.meta_port))
        except Exception, e:
            msg = ('Failed to connect to the sender(%s) on '
                   'meta_port(%d). meta: %s. Aborting.' %
                   (self.meta['ip'], self.meta_port, self.meta))
            self._clean_exit(msg, e)

        #@todo: use appliance uuid instead?
        sname = ('%s-%s' % (self.meta['ip'], self.meta['share']))
        try:
            create_share(sname, self.meta['pool'], logger)
        except Exception, e:
            msg = ('Failed to verify/create share: %s. meta: %s' %
                   (sname, self.meta))
            self._clean_exit(msg, e)

        try:
            data = {'share': sname,
                    'appliance': self.meta['ip'],
                    'src_share': self.meta['share'],
                    'data_port': self.data_port,
                    'meta_port': self.meta_port,}
            self.rid = create_rshare(data, logger)
        except Exception, e:
            msg = ('Failed to create the replica metadata object for '
                   'share: %s. meta: %s' % (sname, self.meta))
            self._clean_exit(msg, e)

        sub_vol = ('%s%s/%s' % (settings.MNT_PT, self.meta['pool'],
                                sname))
        cmd = [BTRFS, 'receive', sub_vol]
        rp = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.debug('Btrfs receive started for snap: %s' % sub_vol)
        #@todo: do basic rp check
        ack = {'msg': 'begin_ok',
               'id': self.meta['id'],}
        meta_push.send_json(ack)
        logger.debug('begin_ok sent for meta: %s' % self.meta)
        rtrail_created = False
        while True:
            try:
                recv_data = recv_sub.recv()
                recv_data = recv_data[len(self.meta['id']):]
                self.kb_received = self.kb_received + len(recv_data)
                if (not rtrail_created):
                    data = {'snap_name': self.meta['snap']}
                    update_receive_trail(self.rid, data, logger,
                                         calltype='post')
                    rtrail_created = True
                ts = datetime.utcnow().replace(tzinfo=utc)
                if (recv_data == 'END_SUCCESS'):
                    logger.debug('END_SUCCESS received for meta: %s' %
                                 self.meta)
                    rtid =
                    data = {'kb_received': self.kb_received,
                            'receive_succeeded': ts,}
                    update_receive_trail(rtid, data, logger)
                    break
                elif (recv_data == 'END_FAIL'):
                    logger.info('END_FAIL received. terminating')
                    data = {'kb_received': self.kb_received,
                            'receive_failed': ts,}
                    update_receive_trail(rtid, data, logger)
                    rp.terminate()
                    break
                rp.stdin.write(recv_data)
                rp.stdin.flush()
            except zmq.error.Again:
                pass
            except Exception, e:
                logger.info('exception occured while receiving fsdata')
                logger.exception(e)
                rp.terminate()
                sys.exit(3)
            finally:
                if (os.getppid() != self.ppid):
                    logger.info('parent exited. aborting.')
                    break
        #rfo/stdin should be closed by now
        out, err = rp.communicate()
        logger.debug('rc: %d out: %s err: %s' % (rp.returncode, out, err))
        ack = {'msg': 'receive_ok',
               'id': self.meta['id'],}
        if (rp.returncode != 0):
            ack['msg'] = 'receive_error'
            update_receive_trail(logger)
        else:
            ts = datetime.utcnow().replace(tzinfo=utc)
            try:
                create_snapshot(share, snap_name, logger)
            except Exception, e:
                msg = ('Failed to create snapshot: %s. Aborting.' %
                       snap_name)
                self._clean_exit(msg, e)

            data = {'snapshot_created': ts,}
            update_receive_trail(rtid, data, logger)

        meta_push.send_json(ack)

