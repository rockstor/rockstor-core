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

import logging
logger = logging.getLogger(__name__)

class NewSender(ReplicationMixin, Process):

    def __init__(self, uuid, receiver_ip, replica, snap_name, snap_id, rt=None):
        self.uuid = uuid
        self.receiver_ip = receiver_ip
        self.receiver_port = 5555
        self.replica = replica
        self.snap_name = snap_name
        self.snap_id = snap_id
        self.rt = rt
        self.rt2 = None
        self.rt2_id = None
        self.rid = replica.id
        self.identity = u'%s-%s' % (self.uuid, self.rid)
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
            logger.error('%s. Exception: %s' % (self.msg, e.__str__()))
            if (self.update_trail):
                try:
                    data = {'status': 'failed',
                            'error': self.msg, }
                    self.update_replica_status(self.rt2_id, data)
                except Exception, e:
                    logger.error('Exception occured while updating replica status: %s' % e.__str__())
            self._sys_exit(3)

    def _sys_exit(self, code):
        if (self.sp is not None and
            self.sp.poll() is None):
            self.sp.terminate()
        self.ctx.destroy(linger=0)
        sys.exit(code)

    @contextmanager
    #but we don't always quit?
    def _update_trail_and_quit(self):
        try:
            yield
        except Exception, e:
            logger.error('%s. Exception: %s' % (self.msg, e.__str__()))
            try:
                data = {'status': 'failed',
                        'error': self.msg, }
                self.update_replica_status(self.rt2_id, data)
            except Exception, e:
                logger.error('Exception occured in cleanup handler: %s' % e.__str__())
            finally:
                self._sys_exit(3)

    def _init_greeting(self):
        self.send_req = self.ctx.socket(zmq.DEALER)
        self.send_req.setsockopt_string(zmq.IDENTITY, self.identity)
        self.send_req.connect('tcp://%s:%d' % (self.receiver_ip, self.receiver_port))
        msg = { 'pool': self.replica.dpool,
                'share': self.replica.share,
                'snap': self.snap_name,
                'incremental': self.rt is not None,
                'uuid': self.uuid, }
        msg_str = json.dumps(msg)
        self.send_req.send_multipart(['sender-ready', b'%s' % msg_str])
        logger.debug('Initial greeting sent from %s' % self.identity)
        self.poll.register(self.send_req, zmq.POLLIN)

    def _req_rep_helper(self, command, msg=''):
        self.send_req.send_multipart([command, b'%s' % msg])
        socks = dict(self.poll.poll(25000))
        if (socks.get(self.send_req) == zmq.POLLIN):
            return self.send_req.recv()
        logger.debug('no reply from the server(%s:%d) for %s' %
                     (self.receiver_ip, self.receiver_port, self.identity))

    def _delete_old_snaps(self, share_path):
        oldest_snap = get_oldest_snap(share_path, self.num_retain_snaps)
        if (oldest_snap is not None):
            self.msg = ('Failed to delete snapshot: %s. Aborting.' %
                        oldest_snap)
            if (self.delete_snapshot(self.replica.share, oldest_snap)):
                return self._delete_old_snaps(share_path)

    def run(self):

        self.msg = ('Top level exception in sender: %s' % self.identity)
        with self._clean_exit_handler():
            self.law = APIWrapper()
            self.poll = zmq.Poller()
            self._init_greeting()

            retries_left = 10
            while (True):
                socks = dict(self.poll.poll(3000))
                if (socks.get(self.send_req) == zmq.POLLIN):
                    command, reply = self.send_req.recv_multipart()
                    logger.debug('reply from receiver for %s' % self.identity)
                    if (command == 'receiver-ready'):
                        logger.debug('%s received for %s. Proceeding to send fsdata.' % (command, self.identity))
                        break
                    else:
                        if (command == 'receiver-error'):
                            self.msg = ('%s received for %s. extended reply: %s .Aborting.' %
                                        (command, self.identity, reply))
                        else:
                            self.msg = ('unexpected reply(%s) for %s. extended reply: %s. Aborting' %
                                        (command, self.identity, reply))
                        raise Exception(self.msg)
                else:
                    logger.debug('no response from receiver for %s. will retry' % self.identity)
                    self.send_req.setsockopt(zmq.LINGER, 0)
                    self.send_req.close()
                    self.poll.unregister(self.send_req)
                    retries_left -= 1
                    if (retries_left == 0):
                        logger.error('%s Retried a few times. Receiver is unreachable. Quiting' % self.identity)
                        self._sys_exit(3)
                    logger.debug('reconnecting for %s' % self.identity)
                    self._init_greeting()
                    logger.debug('Initial greeting resent for %s' % self.identity)

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
            self.create_snapshot(self.replica.share, self.snap_name)

            snap_path = ('%s%s/.snapshots/%s/%s' %
                         (settings.MNT_PT, self.replica.pool, self.replica.share,
                          self.snap_name))
            cmd = [BTRFS, 'send', snap_path]
            if (self.rt is not None):
                prev_snap = ('%s%s/.snapshots/%s/%s' %
                             (settings.MNT_PT, self.replica.pool,
                              self.replica.share, self.rt.snap_name))
                logger.info('Sending incremental replica between %s -- %s' %
                            (prev_snap, snap_path))
                cmd = [BTRFS, 'send', '-p', prev_snap, snap_path]
            else:
                logger.info('Sending full replica: %s' % snap_path)

            try:
                self.sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                fcntl.fcntl(self.sp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            except Exception, e:
                self.msg = ('Failed to start the low level btrfs send '
                            'command(%s). Aborting. Exception: ' % (cmd, e.__str__()))
                logger.error(msg)
                self.update_trail = True
                self._req_rep_helper('btrfs-send-init-error')
                self._sys_exit(3)

            alive = True
            while (alive):
                try:
                    if (self.sp.poll() is not None):
                        logger.debug('send process finished for %s. rc: %d. '
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
                self._req_rep_helper('', fs_data)
                self.kb_sent = self.kb_sent + len(fs_data)

                if (not alive):
                    if (self.sp.returncode != 0):
                        self._req_rep_helper('btrfs-send-nonzero-termination-error')
                    else:
                        self._req_rep_helper('btrfs-send-stream-finished')

                if (os.getppid() != self.ppid):
                    logger.error('Scheduler exited. Sender for %s cannot go on. '
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
