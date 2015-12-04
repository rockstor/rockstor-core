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
import fcntl
from django.conf import settings
from contextlib import contextmanager
from django.utils.timezone import utc
from util import ReplicationMixin
from fs.btrfs import get_oldest_snap
from storageadmin.models import Appliance
import json
from cli import APIWrapper
from django import db

BTRFS = '/sbin/btrfs'


class NewSender(ReplicationMixin, Process):

    def __init__(self, replica, snap_name, snap_id, logger, rt=None):
        self.replica = replica
        self.snap_name = snap_name
        self.snap_id = snap_id
        self.logger = logger
        self.rt = rt
        self.rt2 = None
        self.rt2_id = None
        self.rid = replica.id
        self.sp = None
        self.ctx = zmq.Context()
        self.msg = ''
        self.update_trail = False
        self.kb_sent = 0
        self.ppid = os.getpid()
        self.num_retain_snaps = 5
        for alias, info in db.connections.databases.items():
            db.close_connection()

        super(NewSender, self).__init__()


    @contextmanager
    def _clean_exit_handler(self):
        try:
            yield
        except Exception, e:
            self.logger.error('%s. Exception: %s' % (self.msg, e.__str__()))
            if (self.update_trail):
                try:
                    data = {'status': 'failed',
                            'error': self.msg, }
                    self.update_replica_status(self.rt2_id, data)
                except Exception, e:
                    self.logger.error('Exception occured while updating replica status: %s' % e.__str__())
            self._sys_exit(3)

    def _sys_exit(self, code):
        if (self.sp is not None and
            self.sp.poll() is None):
            self.sp.terminate()

        self.logger.debug('calling ctx.destroy for snap_id-%d' % self.rid)
        self.ctx.destroy(linger=0)
        self.logger.debug('context destroyed for snap_id-%d' % self.rid)
        sys.exit(code)

    @contextmanager
    #but we don't always quit?
    def _update_trail_and_quit(self):
        try:
            yield
        except Exception, e:
            self.logger.error('%s. Exception: %s' % (self.msg, e.__str__()))
            try:
                data = {'status': 'failed',
                        'error': self.msg, }
                self.update_replica_status(self.rt2_id, data)
            except Exception, e:
                self.logger.error('Exception occured in cleanup handler: %s' % e.__str__())
            finally:
                self._sys_exit(3)

    def _init_greeting(self):
        self.send_req = self.ctx.socket(zmq.REQ)
        self.send_req.setsockopt_string(zmq.IDENTITY, u'snap_id-%d' % self.rid)
        self.send_req.connect('tcp://192.168.56.102:5555')
        self.send_req.send(b"shall I begin sending?")
        self.logger.debug('Initial greeting sent from snap_id-%d' % self.rid)
        self.poll.register(self.send_req, zmq.POLLIN)

    def _req_rep_helper(self, msg):
        self.send_req.send(b'%s' % msg)
        socks = dict(self.poll.poll(25000))
        if (socks.get(self.send_req) == zmq.POLLIN):
            reply = self.send_req.recv()
            return reply
        else:
            self.logger.debug('no reply from the server...')

    def _delete_old_snaps(self, share_path):
        oldest_snap = get_oldest_snap(share_path, self.num_retain_snaps)
        if (oldest_snap is not None):
            self.msg = ('Failed to delete snapshot: %s. Aborting.' %
                        oldest_snap)
            if (self.delete_snapshot(self.replica.share, oldest_snap, self.logger)):
                return self._delete_old_snaps(share_path)

    def run(self):

        self.msg = ('Top level exception in sender: snap_id-%d' % self.rid)
        with self._clean_exit_handler():
            self.logger.debug('sender run for snap_id-%d' % self.rid)
            self.law = APIWrapper()
            self.logger.debug('apiwrapper initialized for snap_id-%d' % self.rid)
            self.poll = zmq.Poller()
            self.logger.debug('poll initialized for snap_id-%d' % self.rid)
            self._init_greeting()

            self.logger.debug('before initial greeting for snap_id-%d' % self.rid)
            retries_left = 10
            while (True):
                socks = dict(self.poll.poll(3000))
                if (socks.get(self.send_req) == zmq.POLLIN):
                    reply = self.send_req.recv()
                    self.logger.debug('reply from receiver for snap_id-%d: %s' % (self.rid, reply))
                    if (reply == 'yes, please send'):
                        self.logger.debug('ok, receiver is ready for snap_id-%d' % self.rid)
                        break
                    else:
                        self.logger.debug('unexpected reply from receiver for snap_id-%d: %s' % (self.rid, reply))
                else:
                    self.logger.debug('no response from receiver for snap_id-%d. will retry' % self.rid)
                    self.send_req.setsockopt(zmq.LINGER, 0)
                    self.send_req.close()
                    self.poll.unregister(self.send_req)
                    retries_left -= 1
                    if (retries_left == 0):
                        self.logger.error('snap_id-%d Retried a few times. Receiver is unreachable. Quiting' % self.rid)
                        self._sys_exit(3)
                    self.logger.debug('reconnecting and resending for snap_id-%d' % self.rid)
                    self._init_greeting()
                    self.logger.debug('Initial greeting resent for snap_id-%d' % self.rid)

            #  1. create a new replica trail if it's the very first time
            # or if the last one succeeded
            self.msg = ('Failed to create local replica trail for snap_name:'
                        ' %s. Aborting.' % self.snap_name)
            self.rt2 = self.create_replica_trail(self.replica.id,
                                                 self.snap_name)
            self.rt2_id = self.rt2['id']

            #  2. create a snapshot only if it's not already from a previous
            #  failed attempt.
            self.msg = ('Failed to create snapshot: %s. Aborting.' % self.snap_name)
            self.create_snapshot(self.replica.share, self.snap_name, self.logger)

            snap_path = ('%s%s/.snapshots/%s/%s' %
                         (settings.MNT_PT, self.replica.pool, self.replica.share,
                          self.snap_name))
            cmd = [BTRFS, 'send', snap_path]
            if (self.rt is not None):
                prev_snap = ('%s%s/.snapshots/%s/%s' %
                             (settings.MNT_PT, self.replica.pool,
                              self.replica.share, self.rt.snap_name))
                self.logger.info('Sending incremental replica between %s -- %s' %
                                 (prev_snap, snap_path))
                cmd = [BTRFS, 'send', '-p', prev_snap, snap_path]
            else:
                self.logger.info('Sending full replica: %s' % snap_path)

            try:
                self.sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                fcntl.fcntl(self.sp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            except Exception, e:
                self.msg = ('Failed to start the low level btrfs send '
                            'command(%s). Aborting. Exception: ' % (cmd, e.__str__()))
                self.logger.error(msg)
                self.update_trail = True
                self._req_rep_helper('btrfs-send-init-error')
                self._sys_exit(3)

            alive = True
            while (alive):
                try:
                    if (self.sp.poll() is not None):
                        self.logger.debug('send process finished for %s. rc: %d. '
                                          'stderr: %s' % (self.snap_id,
                                                          self.sp.returncode,
                                                          self.sp.stderr.read()))
                        alive = False
                    fs_data = self.sp.stdout.read()
                except IOError:
                    continue
                except Exception, e:
                    self.msg = ('Exception occured while reading low level btrfs '
                                'send data for %s. Aborting.' % self.snap_id)
                    if (alive):
                        self.sp.terminate()
                    self.update_trail = True
                    self._req_rep_helper('btrfs-send-unexpected-termination-error')
                    self._sys_exit(3)

                self.msg = ('Failed to send fsdata to the receiver for %s. Aborting.' %
                            (self.snap_id))
                self.update_trail = True
                self._req_rep_helper(fs_data)
                self.kb_sent = self.kb_sent + len(fs_data)

                if (not alive):
                    if (self.sp.returncode != 0):
                        self._req_rep_helper('btrfs-send-nonzero-termination-error')
                    else:
                        self._req_rep_helper('btrfs-send-stream-finished')

                if (os.getppid() != self.ppid):
                    self.logger.error('Scheduler exited. Sender for %s cannot go on. '
                                      'Aborting.' % self.snap_id)
                    self._sys_exit(3)

            share_path = ('%s%s/.snapshots/%s' %
                          (settings.MNT_PT, self.replica.pool,
                           self.replica.share))
            self.msg = ('Failed to delete old snapshots')
            self._delete_old_snaps(share_path)

            data = {'status': 'succeeded',
                    'kb_sent': self.kb_sent / 1024, }
            self.msg = ('Failed to update final replica status for %s'
                        '. Aborting.' % self.snap_id)
            self.update_replica_status(self.rt2_id, data)
            self._sys_exit(0)


            # num_chunks = 0;
            # #this is what the first btrfs-send data transfer chunk will be
            # self.send_req.send(b'ok thanks')

            # while (True):
            #     socks = dict(self.poll.poll(25000))
            #     if (socks.get(self.send_req) == zmq.POLLIN):
            #         reply = self.send_req.recv()
            #         if (reply == 'ok, goodbye'):
            #             self.logger.debug('Send successful for snap_id-%d. Quiting' % self.rid)
            #             break
            #         if (num_chunks % 1000 == 0):
            #             self.logger.debug('Total chunks sent from snap_id-%d: %d' % (self.rid, num_chunks))
            #         if (num_chunks > 5000):
            #             self.logger.debug('no more data. final goodbye from snap_id-%d' % self.rid)
            #             self.send_req.send(b'goodbye')
            #         else:
            #             d = 's' * 1000
            #             self.send_req.send(b'%s' % d)
            #         num_chunks += 1

            #     else:
            #         self.logger.debug('no reply from server. retrying')
