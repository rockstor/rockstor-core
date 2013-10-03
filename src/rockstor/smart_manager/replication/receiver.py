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
from django.conf import settings

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
        super(Receiver, self).__init__()

    def run(self):
        ctx = zmq.Context()
        try:
            recv_sub = ctx.socket(zmq.SUB)
            recv_sub.connect('tcp://%s:%d' % (self.meta['ip'], self.data_port))
            recv_sub.RCVTIMEO = 100
            recv_sub.setsockopt(zmq.SUBSCRIBE, str(self.meta['id']))
        except Exception, e:
            logger.info('could not subscribe for fsdata for meta: %s' %
                        self.meta)
            logger.exception(e)
            sys.exit(3)

        try:
            meta_push = ctx.socket(zmq.PUSH)
            meta_push.connect('tcp://%s:%d' % (self.meta['ip'],
                                               self.meta_port))
        except Exception, e:
            logger.info('could not connect to target(%s:%d)' %
                        (self.meta['ip'], self.meta_port))
            logger.exception(e)
            sys.exit(3)

        sub_vol = ('%s%s' % (settings.MNT_PT, self.meta['pool']))
        cmd = [BTRFS, 'receive', sub_vol]
        ack = {'msg': 'begin_ok',
               'id': self.meta['id'],}
        meta_push.send_json(ack)
        rp = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while True:
            try:
                recv_data = recv_sub.recv()
                recv_data = recv_data[len(self.meta['id']):]
                if (recv_data == 'END_SUCCESS'):
                    logger.info('sentinel received. breaking')
                    break
                elif (recv_data == 'END_FAIL'):
                    logger.info('END_FAIL received. terminating')
                    rp.terminate()
                    sys.exit(3)
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
        logger.info('rc: %d out: %s err: %s' % (rp.returncode, out, err))
        ack = {'msg': 'receive_ok',
               'id': self.meta['id'],}
        if (rp.returncode != 0):
            ack['msg'] = 'receive_error'
        meta_push.send_json(ack)

