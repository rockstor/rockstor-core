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
import zmq
import subprocess
from django.utils.timezone import utc
from django.conf import settings
from django import db
from contextlib import contextmanager
from util import ReplicationMixin
from fs.btrfs import (get_oldest_snap, remove_share, set_property, is_subvol)
from system.osi import run_command
from storageadmin.models import (Disk, Pool, Appliance)
from smart_manager.models import ReplicaShare
import shutil
import time
from cli import APIWrapper
import json
import logging
logger = logging.getLogger(__name__)

BTRFS = '/sbin/btrfs'


class NewReceiver(ReplicationMixin, Process):

    def __init__(self, identity, meta):
        self.identity = identity
        self.meta = json.loads(meta)
        #self.meta_port = self.meta['meta_port']
        #self.data_port = self.meta['data_port']
        self.src_share = self.meta['share']
        self.dest_pool = self.meta['pool']
        self.incremental = self.meta['incremental']
        self.snap_name = self.meta['snap']
        self.sender_id = self.meta['uuid']

        self.ppid = os.getpid()
        self.kb_received = 0
        self.rid = None
        self.rtid = None
        self.num_retain_snaps = 5
        self.ctx = zmq.Context()
        self.rp = None
        self.raw = None
        self.ack = False
        #close all db connections prior to fork.
        for alias, info in db.connections.databases.items():
            db.close_connection()
        super(NewReceiver, self).__init__()


    def _sys_exit(self, code):
        if (self.rp is not None and self.rp.returncode is None):
            try:
                self.rp.terminate()
            except Exception, e:
                logger.error('Exception while terminating the btrfs-recv process: %s' % e.__str__())
        self.ctx.destroy(linger=0)
        if (code == 0):
            logger.debug('Identity: %s. meta: %s Receive successful' % (self.identity, self.meta))
        sys.exit(code)

    @contextmanager
    def _clean_exit_handler(self):
        try:
            yield
        except Exception, e:
            logger.error('%s. Exception: %s' % (self.msg, e.__str__()))
            if (self.ack is True):
                try:
                    command = 'receiver-error'
                    self.dealer.send_multipart(['receiver-error', b'%s' % str(self.msg)])
                    socks = dict(self.poll.poll(3000))
                    if (socks.get(self.dealer) == zmq.POLLIN):
                        msg = self.dealer.recv()
                        logger.debug('Response from the broker: %s' % msg)
                    else:
                        logger.debug('No response received from the broker for: %s. Aborting' % self.identity)
                        self._sys_exit(3)
                except Exception, e:
                    msg = ('Exception while sending %s back to the broker from %s. Aborting' % (command, self.identity))
                    logger.error('%s. Exception: %s' % (msg, e.__str__()))
                    self._sys_exit(3)
            self._sys_exit(3)

    def _delete_old_snaps(self, share_name, share_path, num_retain):
        oldest_snap = get_oldest_snap(share_path, num_retain)
        if (oldest_snap is not None):
            if (self.delete_snapshot(share_name, oldest_snap)):
                return self._delete_old_snaps(share_name, share_path, num_retain)

    def _send_recv(self, command, msg=''):
        rcommand = rmsg = None
        self.dealer.send_multipart([command, msg])
        socks = dict(self.poll.poll(25000))
        if (socks.get(self.dealer) == zmq.POLLIN):
            rcommand, rmsg = self.dealer.recv_multipart()
        logger.debug('Identity: %s command: %s rcommand: %s' %
                     (self.identity, command, rcommand))
        return rcommand, rmsg

    def run(self):
        logger.debug('Starting a new receiver for meta: %s' % self.meta)
        self.msg = ('Top level exception in receiver')
        with self._clean_exit_handler():
            self.law = APIWrapper()
            self.poll = zmq.Poller()
            self.dealer = self.ctx.socket(zmq.DEALER)
            self.dealer.setsockopt_string(zmq.IDENTITY, u'%s' % self.identity)
            self.dealer.set_hwm(10)
            self.dealer.connect('ipc:///tmp/foobar.ipc')
            self.poll.register(self.dealer, zmq.POLLIN)

            self.ack = True
            self.msg = ('Failed to get the sender ip for appliance: %s' % self.sender_id)
            self.sender_ip = Appliance.objects.get(uuid=self.sender_id).ip

            sname = ('%s_%s' % (self.sender_id, self.src_share))
            snap_dir = ('%s%s/.snapshots/%s' % (settings.MNT_PT, self.dest_pool, sname))

            #delete the share, move the oldest snap to share
            self.msg = ('Failed to promote the oldest Snapshot to Share.')
            oldest_snap = get_oldest_snap(snap_dir, self.num_retain_snaps)
            if (oldest_snap is not None):
                snap_path = ('%s/%s' % (snap_dir, oldest_snap))
                share_path = ('%s%s/%s' %
                              (settings.MNT_PT, self.dest_pool,
                               sname))
                pool = Pool.objects.get(name=self.dest_pool)
                remove_share(pool, sname, '-1/-1')
                set_property(snap_path, 'ro', 'false',
                             mount=False)
                run_command(['/usr/bin/rm', '-rf', share_path],
                            throw=False)
                shutil.move(snap_path, share_path)
                self.delete_snapshot(sname, oldest_snap)

            self.msg = ('Failed to prune old Snapshots')
            self._delete_old_snaps(sname, snap_dir, self.num_retain_snaps + 1)

            self.msg = ('Failed to validate the source share(%s) on sender(uuid: %s '
                        ') Did the ip of the sender change?' %
                        (self.src_share, self.sender_id))
            self.validate_src_share(self.sender_id, self.src_share)

            if (not self.incremental):
                self.msg = ('Failed to verify/create share: %s.' % sname)
                self.create_share(sname, self.dest_pool)

                self.msg = ('Failed to create the replica metadata object '
                            'for share: %s.' % sname)
                data = {'share': sname,
                        'appliance': self.sender_ip,
                        'src_share': self.src_share, }
                self.rid = self.create_rshare(data)
            else:
                self.msg = ('Failed to retreive the replica metadata object for '
                            'share: %s.' % sname)
                self.rid = ReplicaShare.objects.get(share=sname).id

            sub_vol = ('%s%s/%s' % (settings.MNT_PT, self.dest_pool, sname))
            if (not is_subvol(sub_vol)):
                self.msg = ('Failed to create parent subvolume %s' % sub_vol)
                run_command([BTRFS, 'subvolume', 'create', sub_vol])

            self.msg = ('Failed to create snapshot directory: %s' % snap_dir)
            run_command(['mkdir', '-p', snap_dir])
            snap_fp = ('%s/%s' % (snap_dir, self.snap_name))

            #If the snapshot already exists, presumably from the previous attempt and
            #the sender tries to send the same, reply back with snap_exists and do not
            #start the btrfs-receive
            if (is_subvol(snap_fp)):
                logger.debug('Id: %s. Snapshot to be sent(%s) already exists. Not '
                             'starting a new receive process' % (self.identity, snap_fp))
                self._send_recv('snap-exists')
                self._sys_exit(0)

            self.msg = ('Failed to create Snapshot: %s' % self.snap_name)
            self.create_snapshot(sname, self.snap_name, snap_type='receiver')

            self.msg = ('Failed to create receive trail for rid: %d' % self.rid)
            data = {'snap_name': self.snap_name, }
            self.rtid = self.create_receive_trail(self.rid, data)

            cmd = [BTRFS, 'receive', snap_dir]
            self.msg = ('Failed to start the low level btrfs receive command(%s)'
                        '. Aborting.' % cmd)
            self.rp = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

            self.msg = ('Failed to send receiver-ready for identity: %s' % self.identity)
            rcommand, rmsg = self._send_recv('receiver-ready')
            if (rcommand is None):
                self._sys_exit(3)

            term_msgs = ('btrfs-send-init-error', 'btrfs-send-unexpected-termination-error',
                         'btrfs-send-nonzero-termination-error', 'btrfs-send-stream-finished',)
            num_tries = 10
            while (True):
                socks = dict(self.poll.poll(3000))
                if (socks.get(self.dealer) == zmq.POLLIN):
                    command, message = self.dealer.recv_multipart()
                    if (command in term_msgs):
                        logger.debug('Id: %s. terminal command received: %s' % (self.identity, command))
                        data['status'] = 'failed'
                        if (command == 'btrfs-send-stream-finished'):
                            data['status'] = 'succeeded'
                        else:
                            #do some cleanup?
                            if (self.rp.poll() is None):
                                self.rp.terminate()
                        msg = ('Failed to update receive trail for rtid: %d' % self.rtid)
                        self.update_receive_trail(self.rtid, data)
                        break

                    if (self.rp.poll() is None):
                        logger.debug('Id: %s. fsdata received' % self.identity)
                        self.rp.stdin.write(message)
                        self.rp.stdin.flush()
                        self.dealer.send_multipart([b'send-more', ''])
                    else:
                        out, err = self.rp.communicate()
                        out = out.split('\n')
                        err = err.split('\n')
                        logger.error('Id: %s. btrfs-recv died unexpectedly. cmd: %s out: %s. err: %s' %
                                     (self.identity, cmd, out, err))
                        msg = ('Low level system error from btrfs receive '
                               'command. cmd: %s out: %s err: %s for rtid: %s'
                               % (cmd, out, err, self.rtid))
                        data = {'status': 'failed',
                                'error': msg, }
                        self.msg = ('Failed to update receive trail for rtid: %d.' % self.rtid)
                        self.update_receive_trail(self.rtid, data)
                        self.msg = msg
                        raise Exception()
                else:
                    num_tries -= 1
                    msg = ('Id: %s. No response received from the broker. '
                           'remaining tries: %d' % (self.identity, num_tries))
                    if (num_tries == 0):
                        msg = ('%s. Terminating the receiver.' % msg)
                        logger.error(msg)
                        break
                    logger.error(msg)

            try:
                if (self.rp.poll() is None):
                    msg = ('btrfs-recv is expected to be terminated but it did not.')
                    out, err = self.rp.communicate()
                    out = out.split('\n')
                    err = err.split('\n')
                    logger.debug('Id: %s. %s. cmd = %s out: %s err: %s rc: %s' %
                                 (self.identity, msg, cmd, out, err, self.rp.returncode))
            except Exception, e:
                #Is this a fatal error?
                logger.debug('Id: %s. Exception while terminating btrfs-receive. Meta: %s. '
                             'Probably already terminated: %s' %
                             (self.identity, self.meta, e.__str__()))

            data = {'status': 'succeeded', }
            if (self.rp.returncode != 0):
                data['status'] = 'failed'

            self._send_recv('btrfs-recv-finished')

            self.msg = ('Failed to update receive trail for rtid: %d.' % self.rtid)
            self.update_receive_trail(self.rtid, data)
            self._sys_exit(0)
