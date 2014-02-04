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
from util import (create_share, create_receive_trail, update_receive_trail,
                  create_snapshot, create_rshare, rshare_id)

BTRFS = '/sbin/btrfs'
logger = logging.getLogger(__name__)

class Receiver(Process):

    def __init__(self, meta, q):
        self.meta = meta
        self.meta_port = self.meta['meta_port']
        self.data_port = self.meta['data_port']
        self.sender_ip = self.meta['ip']
        self.src_share = self.meta['share']
        self.dest_pool = self.meta['pool']
        self.incremental = self.meta['incremental']
        self.snap_name = self.meta['snap']
        self.q = q
        self.ppid = os.getpid()
        self.kb_received = 0
        self.rid = None
        self.rtid = None
        super(Receiver, self).__init__()

    def _clean_exit(self, msg, exception):
        logger.error(msg)
        logger.exception(exception)
        sys.exit(3)

    def run(self):
        ctx = zmq.Context()
        try:
            recv_sub = ctx.socket(zmq.SUB)
            recv_sub.connect('tcp://%s:%d' % (self.sender_ip, self.data_port))
            recv_sub.RCVTIMEO = 100
            recv_sub.setsockopt(zmq.SUBSCRIBE, str(self.meta['id']))
        except Exception, e:
            msg = ('Failed to connect to the sender(%s) on '
                   'data_port(%s). meta: %s. Aborting.'
                   % (self.sender_ip, self.data_port, self.meta))
            self._clean_exit(msg, e)

        try:
            meta_push = ctx.socket(zmq.PUSH)
            meta_push.connect('tcp://%s:%d' % (self.sender_ip,
                                               self.meta_port))
        except Exception, e:
            msg = ('Failed to connect to the sender(%s) on '
                   'meta_port(%d). meta: %s. Aborting.' %
                   (self.sender_ip, self.meta_port, self.meta))
            self._clean_exit(msg, e)

        #@todo: use appliance uuid instead?
        sname = ('%s-%s' % (self.src_share, self.sender_ip))
        if (not self.incremental):
            try:
                create_share(sname, self.dest_pool, logger)
            except Exception, e:
                msg = ('Failed to verify/create share: %s. meta: %s. '
                       'Aborting.' % (sname, self.meta))
                self._clean_exit(msg, e)

            try:
                data = {'share': sname,
                        'appliance': self.sender_ip,
                        'src_share': self.src_share,
                        'data_port': self.data_port,
                        'meta_port': self.meta_port,}
                self.rid = create_rshare(data, logger)
            except Exception, e:
                msg = ('Failed to create the replica metadata object '
                       'for share: %s. meta: %s. Aborting.' %
                       (sname, self.meta))
                self._clean_exit(msg, e)
        else:
            try:
                self.rid = rshare_id(sname, logger)
            except Exception, e:
                msg = ('Failed to retreive the replica metadata object for '
                       'share: %s. meta: %s. Aboring.' % (sname, self.meta))
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
        while True:
            try:
                recv_data = recv_sub.recv()
                recv_data = recv_data[len(self.meta['id']):]
                self.kb_received = self.kb_received + len(recv_data)
                if (self.rtid is None):
                    try:
                        create_snapshot(sname, self.snap_name, logger,
                                        snap_type='receiver')
                    except Exception, e:
                        msg = ('Failed to create snapshot: %s. Aborting.' %
                               self.snap_name)
                        self._clean_exit(msg, e)

                    data = {'snap_name': self.snap_name}
                    try:
                        self.rtid = create_receive_trail(self.rid, data,
                                                         logger)
                    except Exception, e:
                        msg = ('Failed to create receive trail for rid: %d'
                               '. meta: %s' % (self.rid, self.meta))
                        self._clean_exit(msg, e)

                if (recv_data == 'END_SUCCESS' or recv_data == 'END_FAIL'):
                    ts = datetime.utcnow().replace(tzinfo=utc)
                    data = {'kb_received': self.kb_received,}
                    if (recv_data == 'END_SUCCESS'):
                        logger.debug('END_SUCCESS received for meta: %s' %
                                     self.meta)
                        data['receive_succeeded'] = ts
                    else:
                        logger.error('END_FAIL received for meta: %s. '
                                     'Terminating.' % self.meta)
                        rp.terminate()
                        data['receive_failed'] = ts
                        data['status'] = 'failed'
                    try:
                        update_receive_trail(self.rtid, data, logger)
                    except Exception, e:
                        msg = ('Failed to update receive trail for rtid: %d'
                               '. meta: %s' % (self.rtid, self.meta))
                        self._clean_exit(msg, e)
                    break
                rp.stdin.write(recv_data)
                rp.stdin.flush()
            except zmq.error.Again:
                pass
            except Exception, e:
                msg = ('Exception occured while receiving fsdata')
                logger.error(msg)
                logger.exception(e)
                rp.terminate()
                data['receive_failed'] = datetime.utcnow().replace(tzinfo=utc)
                data['status'] = 'failed'
                data['error'] = msg
                try:
                    update_receive_trail(self.rtid, data, logger)
                except Exception, e:
                    msg = ('Failed to update receive trail for rtid: %d'
                               '. meta: %s' % (self.rtid, self.meta))
                    self._clean_exit(msg, e)
                sys.exit(3)
            finally:
                if (os.getppid() != self.ppid):
                    logger.error('parent exited. aborting.')
                    sys.exit(3)

        #rfo/stdin should be closed by now. We get here only if the sender
        #dint throw an error or if receiver did not get terminated
        out, err = rp.communicate()
        logger.debug('rc: %d out: %s err: %s' % (rp.returncode, out, err))
        ack = {'msg': 'receive_ok',
               'id': self.meta['id'],}
        data = {'status': 'succeeded',
                'end_ts': datetime.utcnow().replace(tzinfo=utc),}
        if (rp.returncode != 0):
            ack['msg'] = 'receive_error'
            data['status'] = 'failed'

        try:
            update_receive_trail(self.rtid, data, logger)
        except Exception, e:
            msg = ('Failed to update receive trail for rtid: %d. meta: '
                   '%s' % (self.rtid, self.meta))
            self._clean_exit(msg, e)

        meta_push.send_json(ack)
