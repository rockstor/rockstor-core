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
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from contextlib import contextmanager
from util import (create_share, create_receive_trail, update_receive_trail,
                  create_snapshot, create_rshare, rshare_id, get_sender_ip,
                  delete_snapshot)
from cli.rest_util import set_token
from fs.btrfs import (get_oldest_snap, remove_share, set_property, is_subvol)
from system.osi import run_command
from storageadmin.models import (Disk, Pool)
import shutil


BTRFS = '/sbin/btrfs'
logger = logging.getLogger(__name__)


class Receiver(Process):

    def __init__(self, meta):
        self.meta = meta
        self.meta_port = self.meta['meta_port']
        self.data_port = self.meta['data_port']
        self.sender_ip = None
        self.src_share = self.meta['share']
        self.dest_pool = self.meta['pool']
        self.incremental = self.meta['incremental']
        self.snap_name = self.meta['snap']
        self.sender_id = self.meta['uuid']
        self.ppid = os.getpid()
        self.kb_received = 0
        self.rid = None
        self.rtid = None
        self.meta_push = None
        self.ctx = zmq.Context()
        super(Receiver, self).__init__()

    def _sys_exit(self, code, linger=10):
        self.ctx.destroy(linger=linger)
        logger.debug('zmq context destroyed. exiting with code: %d' % code)
        sys.exit(code)

    @contextmanager
    def _clean_exit_handler(self, msg, ack=False):
        try:
            yield
        except Exception, e:
            logger.error(msg)
            logger.exception(e)
            if (ack is True):
                try:
                    err_ack = {'msg': 'error',
                               'id': self.meta['id'],
                               'error': msg, }
                    self.meta_push.send_json(err_ack)
                except Exception, e:
                    msg = ('Failed to send ack: %s to the sender for meta: '
                           '%s. Aborting' % (err_ack, self.meta))
                    logger.error(msg)
                    logger.exception(e)
                    self._sys_exit(3)
            self._sys_exit(3)

    def run(self):
        set_token()
        msg = ('Failed to get the sender ip from the uuid(%s) for meta: %s' %
               (self.meta['uuid'], self.meta))
        with self._clean_exit_handler(msg):
            self.sender_ip = get_sender_ip(self.meta['uuid'], logger)
        logger.debug('sender ip: %s' % self.sender_ip)

        msg = ('Failed to connect to the sender(%s) on data_port(%s). meta: '
               '%s. Aborting.' % (self.sender_ip, self.data_port, self.meta))
        with self._clean_exit_handler(msg):
            #@todo: add validation
            recv_sub = self.ctx.socket(zmq.SUB)
            recv_sub.connect('tcp://%s:%d' % (self.sender_ip, self.data_port))
            recv_sub.RCVTIMEO = 100
            recv_sub.setsockopt(zmq.SUBSCRIBE, str(self.meta['id']))

        msg = ('Failed to connect to the sender(%s) on '
               'meta_port(%d). meta: %s. Aborting.' %
               (self.sender_ip, self.meta_port, self.meta))
        with self._clean_exit_handler(msg):
            self.meta_push = self.ctx.socket(zmq.PUSH)
            url = ('tcp://%s:%d' % (self.sender_ip, self.meta_port))
            logger.debug('meta url: %s' % url)
            self.meta_push.connect('tcp://%s:%d' % (self.sender_ip,
                                                    self.meta_port))

        sname = ('%s_%s' % (self.sender_id, self.src_share))
        if (not self.incremental):
            msg = ('Failed to verify/create share: %s. meta: %s. '
                   'Aborting.' % (sname, self.meta))
            with self._clean_exit_handler(msg, ack=True):
                create_share(sname, self.dest_pool, logger)

            msg = ('Failed to create the replica metadata object '
                   'for share: %s. meta: %s. Aborting.' %
                   (sname, self.meta))
            with self._clean_exit_handler(msg, ack=True):
                data = {'share': sname,
                        'appliance': self.sender_ip,
                        'src_share': self.src_share,
                        'data_port': self.data_port,
                        'meta_port': self.meta_port, }
                self.rid = create_rshare(data, logger)

        else:
            msg = ('Failed to retreive the replica metadata object for '
                   'share: %s. meta: %s. Aborting.' % (sname, self.meta))
            with self._clean_exit_handler(msg):
                self.rid = rshare_id(sname, logger)

        sub_vol = ('%s%s/.snapshots/%s' % (settings.MNT_PT, self.meta['pool'],
                                           sname))
        if (not is_subvol(sub_vol)):
            msg = ('Failed to create parent subvolume %s' % sub_vol)
            with self._clean_exit_handler(msg, ack=True):
                run_command([BTRFS, 'subvolume', 'create', sub_vol])

        snap_fp = ('%s/%s' % (sub_vol, self.snap_name))
        logger.info('snap_fp: %s' % snap_fp)
        msg = ('Snaphost: %s already exists.' % snap_fp)
        with self._clean_exit_handler(msg):
            if (is_subvol(snap_fp)):
                ack = {'msg': 'snap_exists',
                       'id': self.meta['id'], }
                self.meta_push.send_json(ack)
                logger.debug(msg)

        cmd = [BTRFS, 'receive', sub_vol]
        msg = ('Failed to start the low level btrfs receive command(%s)'
               '. Aborting.' % (cmd))
        with self._clean_exit_handler(msg, ack=True):
            rp = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            logger.debug('Btrfs receive started for snap: %s' % sub_vol)

        msg = ('Failed to send begin_ok to the sender for meta: %s' %
               self.meta)
        with self._clean_exit_handler(msg):
            ack = {'msg': 'begin_ok',
                   'id': self.meta['id'], }
            self.meta_push.send_json(ack)
            logger.debug('begin_ok sent for meta: %s' % self.meta)
        recv_timeout_counter = 0
        credit = 10
        check_credit = True
        while True:
            if (check_credit is True and credit == 0):
                ack = {'msg': 'send_more',
                       'id': self.meta['id'], }
                self.meta_push.send_json(ack)
                credit = 10
                logger.debug('kb received = %d' % int(self.kb_received / 1024))

            try:
                recv_data = recv_sub.recv()
                recv_data = recv_data[len(self.meta['id']):]
                credit = credit - 1
                recv_timeout_counter = 0
                self.kb_received = self.kb_received + len(recv_data)
                if (self.rtid is None):
                    msg = ('Failed to create snapshot: %s. Aborting.' %
                           self.snap_name)
                    # create a snapshot only if it's not already from a previous failed attempt
                    with self._clean_exit_handler(msg, ack=True):
                        create_snapshot(sname, self.snap_name, logger,
                                        snap_type='receiver')

                    data = {'snap_name': self.snap_name}
                    msg = ('Failed to create receive trail for rid: %d'
                           '. meta: %s' % (self.rid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        self.rtid = create_receive_trail(self.rid, data,
                                                         logger)

                if (recv_data == 'END_SUCCESS' or recv_data == 'END_FAIL'):
                    check_credit = False
                    ts = datetime.utcnow().replace(tzinfo=utc)
                    data = {'kb_received': self.kb_received / 1024, }
                    if (recv_data == 'END_SUCCESS'):
                        logger.debug('END_SUCCESS received for meta: %s' %
                                     self.meta)
                        data['receive_succeeded'] = ts
                        #delete the share, move the oldest snap to share
                        oldest_snap = get_oldest_snap(sub_vol, 3)
                        if (oldest_snap is not None):
                            snap_path = ('%s/%s' % (sub_vol, oldest_snap))
                            share_path = ('%s%s/%s' %
                                          (settings.MNT_PT, self.dest_pool,
                                           sname))
                            msg = ('Failed to promote the oldest Snapshot(%s) '
                                   'to Share(%s)' % (snap_path, share_path))
                            try:
                                pool = Pool.objects.get(name=self.dest_pool)
                                pool_device = Disk.objects.filter(
                                    pool=pool)[0].name
                                remove_share(pool, pool_device, sname)
                                set_property(snap_path, 'ro', 'false',
                                             mount=False)
                                run_command(['/usr/bin/rm', '-rf', share_path],
                                            throw=False)
                                shutil.move(snap_path, share_path)
                                set_property(share_path, 'ro', 'true',
                                             mount=False)
                                delete_snapshot(sname, oldest_snap, logger)
                            except Exception, e:
                                logger.error(msg)
                                logger.exception(msg)
                    else:
                        logger.error('END_FAIL received for meta: %s. '
                                     'Terminating.' % self.meta)
                        rp.terminate()
                        data['receive_failed'] = ts
                        data['status'] = 'failed'

                    msg = ('Failed to update receive trail for rtid: %d'
                           '. meta: %s' % (self.rtid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        update_receive_trail(self.rtid, data, logger)
                    break
                if (rp.poll() is None):
                    rp.stdin.write(recv_data)
                    rp.stdin.flush()
                else:
                    logger.error('It seems the btrfs receive process died'
                                 ' unexpectedly.')
                    out, err = rp.communicate()
                    logger.debug('btrfs receive out: %s err: %s' % (out, err))
                    msg = ('Low level system error from btrfs receive '
                           'command. out: %s err: %s for rtid: %s meta: %s'
                           % (out, err, self.rtid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        ts = datetime.utcnow().replace(tzinfo=utc)
                        data = {'receive_failed': ts,
                                'status': 'failed',
                                'error': msg, }
                        update_receive_trail(self.rtid, data, logger)
            except zmq.error.Again:
                recv_timeout_counter = recv_timeout_counter + 1
                if (recv_timeout_counter > 600):
                    logger.error('Nothing received in the last 60 seconds '
                                 'from the sender for meta: %s. Aborting.'
                                 % self.meta)
                    raise
            except Exception, e:
                msg = ('Exception occured while receiving fsdata')
                logger.error(msg)
                logger.exception(e)
                rp.terminate()
                out, err = rp.communicate()
                logger.debug('rc: %d out: %s err: %s' % (rp.returncode, out,
                                                         err))
                data['receive_failed'] = datetime.utcnow().replace(tzinfo=utc)
                data['status'] = 'failed'
                data['error'] = msg

                msg = ('Failed to update receive trail for rtid: %d'
                       '. meta: %s' % (self.rtid, self.meta))
                with self._clean_exit_handler(msg, ack=True):
                    update_receive_trail(self.rtid, data, logger)
                self._sys_exit(3)
            finally:
                if (os.getppid() != self.ppid):
                    logger.error('parent exited. aborting.')
                    self._sys_exit(3)

        #rfo/stdin should be closed by now. We get here only if the sender
        #dint throw an error or if receiver did not get terminated
        try:
            out, err = rp.communicate()
            logger.debug('rc: %d out: %s err: %s' % (rp.returncode, out, err))
        except Exception, e:
            logger.debug('Exception while terminating receive. Probably '
                         'already terminated.')
            logger.exception(e)

        ack = {'msg': 'receive_ok',
               'id': self.meta['id'], }
        data = {'status': 'succeeded',
                'end_ts': datetime.utcnow().replace(tzinfo=utc), }
        if (rp.returncode != 0):
            ack['msg'] = 'receive_error'
            data['status'] = 'failed'

        msg = ('Failed to update receive trail for rtid: %d. meta: '
               '%s' % (self.rtid, self.meta))
        with self._clean_exit_handler(msg, ack=True):
            update_receive_trail(self.rtid, data, logger)

        msg = ('Failed to send final ack to the sender for meta: %s' %
               self.meta)
        with self._clean_exit_handler(msg):
            self.meta_push.send_json(ack)
        logger.debug('final ack sent for meta: %s' % self.meta)
        self._sys_exit(0)
