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
from contextlib import contextmanager
from util import ReplicationMixin
from fs.btrfs import (get_oldest_snap, remove_share, set_property, is_subvol)
from system.osi import run_command
from storageadmin.models import (Disk, Pool, Appliance)
from smart_manager.models import ReplicaShare
import shutil
import time
from cli import APIWrapper

BTRFS = '/sbin/btrfs'


class Receiver(ReplicationMixin, Process):

    def __init__(self, meta, logger):
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
        self.num_retain_snaps = 5
        self.ctx = zmq.Context()
        self.logger = logger
        self.rp = None
        self.raw = None
        super(Receiver, self).__init__()


    def _sys_exit(self, code, linger=60000):
        if (self.rp is not None and self.rp.returncode is None):
            try:
                self.rp.terminate()
            except Exception, e:
                self.logger.error('Exception while terminating the btrfs-recv process: %s' % e.__str__())
        self.ctx.destroy(linger=linger)
        sys.exit(code)

    @contextmanager
    def _clean_exit_handler(self, msg, ack=False):
        try:
            yield
        except Exception, e:
            self.logger.error('%s. Exception: %s' % (msg, e.__str__()))
            if (ack is True):
                try:
                    err_ack = {'msg': 'error',
                               'id': self.meta['id'],
                               'error': msg, }
                    self.meta_push.send_json(err_ack)
                    self.logger.debug('error_ack sent: %s' % err_ack)
                except Exception, e:
                    msg = ('Failed to send ack: %s to the sender for meta: '
                           '%s. Aborting' % (err_ack, self.meta))
                    self.logger.error('%s. Exception: %s' % (msg, e.__str__()))
                    self._sys_exit(3)
            self._sys_exit(3)

    def _delete_old_snaps(self, share_name, share_path, num_retain):
        oldest_snap = get_oldest_snap(share_path, num_retain)
        if (oldest_snap is not None):
            msg = ('Failed to delete snapshot: %s. Aborting.' %
                   oldest_snap)
            with self._clean_exit_handler(msg):
                if (self.delete_snapshot(share_name, oldest_snap, self.logger)):
                    return self._delete_old_snaps(share_name, share_path, num_retain)


    def run(self):
        self.law = APIWrapper()
        msg = ('Failed to get the sender ip from the uuid(%s) for meta: %s' %
               (self.meta['uuid'], self.meta))
        with self._clean_exit_handler(msg):
            self.sender_ip = Appliance.objects.get(uuid=self.meta['uuid']).ip

        msg = ('Failed to validate the source share(%s) on sender(uuid: %s '
               'ip: %s) for meta: %s. Did the ip of the sender change?' %
               (self.src_share, self.sender_id, self.sender_ip, self.meta))
        with self._clean_exit_handler(msg):
            self.validate_src_share(self.sender_id, self.src_share)

        msg = ('Failed to connect to the sender(%s) on data_port(%s). meta: '
               '%s. Aborting.' % (self.sender_ip, self.data_port, self.meta))
        with self._clean_exit_handler(msg):
            #connection does not mean we are instantly connected.
            #so no validation of that kind possible with pub sub
            #for example, if the sender ip is different from what we have
            #in the db, no error is raised here.
            recv_sub = self.ctx.socket(zmq.SUB)
            recv_sub.connect('tcp://%s:%d' % (self.sender_ip, self.data_port))
            recv_sub.RCVTIMEO = 1000 # 1 minute
            recv_sub.setsockopt_string(zmq.SUBSCRIBE, self.meta['id'].decode('ascii'))

        msg = ('Failed to connect to the sender(%s) on '
               'meta_port(%d). meta: %s. Aborting.' %
               (self.sender_ip, self.meta_port, self.meta))
        with self._clean_exit_handler(msg):
            #same comment from above applies here for push connection also.
            self.meta_push = self.ctx.socket(zmq.PUSH)
            self.meta_push.connect('tcp://%s:%d' % (self.sender_ip,
                                                    self.meta_port))

        sname = ('%s_%s' % (self.sender_id, self.src_share))
        if (not self.incremental):
            msg = ('Failed to verify/create share: %s. meta: %s. '
                   'Aborting.' % (sname, self.meta))
            with self._clean_exit_handler(msg, ack=True):
                self.create_share(sname, self.dest_pool, self.logger)

            msg = ('Failed to create the replica metadata object '
                   'for share: %s. meta: %s. Aborting.' %
                   (sname, self.meta))
            with self._clean_exit_handler(msg, ack=True):
                data = {'share': sname,
                        'appliance': self.sender_ip,
                        'src_share': self.src_share,
                        'data_port': self.data_port,
                        'meta_port': self.meta_port, }
                self.rid = self.create_rshare(data)

        else:
            msg = ('Failed to retreive the replica metadata object for '
                   'share: %s. meta: %s. Aborting.' % (sname, self.meta))
            with self._clean_exit_handler(msg):
                self.rid = ReplicaShare.objects.get(share=sname).id

        sub_vol = ('%s%s/%s' % (settings.MNT_PT, self.meta['pool'],
                                sname))
        if (not is_subvol(sub_vol)):
            msg = ('Failed to create parent subvolume %s' % sub_vol)
            with self._clean_exit_handler(msg, ack=True):
                run_command([BTRFS, 'subvolume', 'create', sub_vol])

        snap_dir = ('%s%s/.snapshots/%s' % (settings.MNT_PT, self.meta['pool'],
                                           sname))
        run_command(['mkdir', '-p', snap_dir])
        snap_fp = ('%s/%s' % (snap_dir, self.snap_name))
        with self._clean_exit_handler(msg):
            if (is_subvol(snap_fp)):
                ack = {'msg': 'snap_exists',
                       'id': self.meta['id'], }
                self.meta_push.send_json(ack)
                self.logger.debug('snap_exists ack sent: %s' % ack)
                self._sys_exit(0)

        cmd = [BTRFS, 'receive', snap_dir]
        msg = ('Failed to start the low level btrfs receive command(%s)'
               '. Aborting.' % (cmd))
        with self._clean_exit_handler(msg, ack=True):
            self.rp = subprocess.Popen(cmd, shell=False, stdin=subprocess.PIPE,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)

        msg = ('Failed to send begin_ok to the sender for meta: %s' %
               self.meta)
        with self._clean_exit_handler(msg):
            ack = {'msg': 'begin_ok',
                   'id': self.meta['id'], }
            self.meta_push.send_json(ack)
            self.logger.debug('begin_ok ack sent: %s' % ack)
        recv_timeout_counter = 0
        credit = settings.DEFAULT_SEND_CREDIT
        check_credit = True
        t0 = t0_cycle = time.time()
        recv_cycle = 0
        msg_count = 0
        while True:
            if (check_credit is True and credit < 5):
                ack = {'msg': 'send_more',
                       'id': self.meta['id'],
                       'credit': settings.DEFAULT_SEND_CREDIT, }
                self.meta_push.send_json(ack)
                self.logger.debug('send_more ack sent: %s' % ack)
                msg_count_cycle = settings.DEFAULT_SEND_CREDIT - credit
                msg_count += msg_count_cycle
                cur_t = time.time()
                total_kb = self.kb_received / 1024
                cycle_kb = recv_cycle / 1024
                total_xfer = total_kb / (cur_t - t0)
                cycle_xfer = cycle_kb / (cur_t - t0_cycle)
                total_avg_msg = self.kb_received / msg_count
                cycle_avg_msg = recv_cycle / msg_count_cycle
                self.logger.debug('%s KB received so far: %f . this cycle: %f .'
                                  'xfer rate so far: %f . this cycle: %f .'
                                  'Avg msg size(Bytes) so far: %f . this cycle: %f .' %
                                  (self.meta['id'], total_kb, cycle_kb, total_xfer, cycle_xfer,
                                   total_avg_msg, cycle_avg_msg))
                recv_cycle = 0
                t0_cycle = time.time()
                credit = credit + settings.DEFAULT_SEND_CREDIT

            try:
                recv_data = recv_sub.recv()
                recv_data = recv_data[len(self.meta['id']):]
                credit = credit - 1
                recv_timeout_counter = 0
                self.kb_received += len(recv_data)
                recv_cycle += len(recv_data)
                if (self.rtid is None):
                    msg = ('Failed to create snapshot: %s. Aborting.' %
                           self.snap_name)
                    # create a snapshot only if it's not already from a previous failed attempt
                    with self._clean_exit_handler(msg, ack=True):
                        self.create_snapshot(sname, self.snap_name,
                                             self.logger, snap_type='receiver')

                    data = {'snap_name': self.snap_name}
                    msg = ('Failed to create receive trail for rid: %d'
                           '. meta: %s' % (self.rid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        self.rtid = self.create_receive_trail(self.rid, data)

                if (recv_data == 'END_SUCCESS' or recv_data == 'END_FAIL'):
                    check_credit = False
                    data = {'kb_received': self.kb_received / 1024, }
                    self.logger.debug('END message received for %s : %s' %
                                      (self.meta['id'], recv_data))
                    if (recv_data == 'END_SUCCESS'):
                        data['status'] = 'succeeded'
                        try:
                            #delete any snapshots older than num_retain
                            self._delete_old_snaps(sname, snap_dir, self.num_retain_snaps + 1)
                        except Exception, e:
                            self.logger.error('Exception while deleting old '
                                              'snapshots: %s' % e.__str__())
                            #raising the exception would make a bigger mess.
                            #problematic past snapshots can be manually deleted.

                        #delete the share, move the oldest snap to share
                        try:
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
                                self.delete_snapshot(sname, oldest_snap, self.logger)
                        except Exception, e:
                            msg = ('Failed to promote the oldest Snapshot to Share'
                                   ' for %s' % self.meta['id'])
                            self.logger.error('%s. Exception: %s' % (msg, e.__str__()))
                    else:
                        self.logger.error('END_FAIL received for meta: %s. '
                                          'Terminating.' % self.meta)
                        if (self.rp.poll() is None):
                            self.rp.terminate()
                        data['status'] = 'failed'

                    msg = ('Failed to update receive trail for rtid: %d'
                           '. meta: %s' % (self.rtid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        self.update_receive_trail(self.rtid, data)
                    break
                if (self.rp.poll() is None):
                    self.rp.stdin.write(recv_data)
                    self.rp.stdin.flush()
                else:
                    self.logger.error('It seems the btrfs receive process died'
                                      ' unexpectedly for meta: %s' % self.meta)
                    out, err = self.rp.communicate()
                    msg = ('Low level system error from btrfs receive '
                           'command. out: %s err: %s for rtid: %s meta: %s'
                           % (out, err, self.rtid, self.meta))
                    with self._clean_exit_handler(msg, ack=True):
                        data = {'status': 'failed',
                                'error': msg, }
                        self.update_receive_trail(self.rtid, data)
            except zmq.error.Again:
                recv_timeout_counter = recv_timeout_counter + 1
                if (recv_timeout_counter > 600): #10 minutes
                    self.logger.error('Nothing received in the last 60 seconds '
                                      'from the sender(%s) for meta: %s. Aborting.'
                                      % (self.sender_ip, self.meta))
                    self._sys_exit(3)
            except Exception, e:
                msg = ('Exception occured while receiving fsdata for meta: %s.'
                       'Exception: %s' % (self.meta, e.__str__()))
                self.logger.error(msg)
                try:
                    self.rp.terminate()
                except Exception, e:
                    self.logger.error('Exception while terminating btrfs-recv '
                                      'for %s: %s' % (self.meta['id'], e.__str__()))
                    #don't raise the exception because it will create a bigger mess.

                data['status'] = 'failed'
                data['error'] = msg
                msg = ('Failed to update receive trail for rtid: %d'
                       '. meta: %s' % (self.rtid, self.meta))
                with self._clean_exit_handler(msg, ack=True):
                    self.update_receive_trail(self.rtid, data)
                self._sys_exit(3)
            finally:
                if (os.getppid() != self.ppid):
                    self.logger.error('parent exited. aborting.')
                    self._sys_exit(3)

        #rfo/stdin should be closed by now. We get here only if the sender
        #dint throw an error or if receiver did not get terminated
        try:
            out, err = self.rp.communicate()
            self.logger.debug('cmd = %s out: %s err: %s rc: %s' %
                              (cmd, out, err, self.rp.returncode))
        except Exception, e:
            self.logger.debug('Exception while terminating receive. Meta: %s. '
                              'Probably already terminated: %s' %
                              (self.meta, e.__str__()))

        ack = {'msg': 'receive_ok',
               'id': self.meta['id'], }
        data = {'status': 'succeeded', }
        if (self.rp.returncode != 0):
            ack['msg'] = 'receive_error'
            data['status'] = 'failed'

        msg = ('Failed to update receive trail for rtid: %d. meta: '
               '%s' % (self.rtid, self.meta))
        with self._clean_exit_handler(msg, ack=True):
            self.update_receive_trail(self.rtid, data)

        msg = ('Failed to send final ack to the sender for meta: %s' %
               self.meta)
        with self._clean_exit_handler(msg):
            self.meta_push.send_json(ack)
            self.logger.debug('Receive finished for %s. ack = %s' % (sname, ack))

        try:
            recv_sub.RCVTIMEO = 60000 # 1 minute
            recv_data = recv_sub.recv()
            recv_data = recv_data[len(self.meta['id']):]
        except Exception, e:
            self.logger.error('Exception while waiting for final ack from '
                              'sender for %s: %s' % (sname, e.__str__()))
            #it's ok if we don't receive the final ack, this is perhaps a
            #hacky way of waiting a while to make sure the previous send
            #made it through.

        self._sys_exit(0)
