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
from cli.rest_util import api_call
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
            recv_sub.connect('tcp://%s:%d' % (self.meta['ip'],
                                              self.data_port))
            recv_sub.RCVTIMEO = 500
            #recv_sub.setsockopt(zmq.SUBSCRIBE, str(self.meta['id']))
            recv_sub.setsockopt(zmq.SUBSCRIBE, '')
            logger.info('subscribed for fsdata for meta: %s' % self.meta)
        except Exception, e:
            logger.info('could not subscribe for fsdata for meta: %s' %
                        self.meta)
            logger.exception(e)
            sys.exit(3)

        try:
            meta_push = ctx.socket(zmq.PUSH)
            meta_push.connect('tcp://%s:%d' % (self.meta['ip'],
                                               self.meta_port))
            logger.info('connected to pull socket for meta: %s' % self.meta)
        except Exception, e:
            logger.info('could not connect to target(%s:%d)' %
                        (self.meta['ip'], self.meta_port))
            logger.exception(e)
            sys.exit(3)

        sub_vol = ('%s%s/%s' % (settings.MNT_PT, self.meta['pool'],
                                self.meta['share']))
        cmd = [BTRFS, 'recv', sub_vol]
        with open('/tmp/btrfs-recv', 'w') as rfo:
            ack = {'msg': 'begin_ok',
                   'id': self.meta['id'],}
            meta_push.send_json(ack)
            logger.info('ack sent: %s' % ack)
            rp = subprocess.Popen(cmd, shell=False, stdin=rfo,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            logger.info('btrfs recv started')
            more_data = True
            while True:
                try:
                    recv_data = recv_sub.recv()
                    #recv_data = recv_data[len(self.meta['id']):]
                    rfo.write(recv_data)
                    logger.info('fsdata received. meta: %s' % self.meta)
                except zmq.error.Again:
                    if (not more_data):
                        logger.info('no more data to receive from '
                                    'publisher. meta: %s' % self.meta)
                        break
                except Exception, e:
                    logger.info('exception occured while receiving fsdata')
                    logger.exception(e)
                    rp.terminate()
                    sys.exit(3)
                finally:
                    logger.info('in finally')
                    if (not self.q.empty()):
                        msg = self.q.get()
                        logger.info('end(%s) received. meta: %s' %
                                    (msg, self.meta))
                        ack = {'msg': 'end_ok',
                               'id': self.meta['id'],}
                        meta_push.send_json(ack)
                        logger.info('ack sent: %s' % ack)
                        more_data = False
        #rfo/stdin should be closed by now
        rp.communicate()

