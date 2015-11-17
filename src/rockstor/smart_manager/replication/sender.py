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
from django.conf import settings
from contextlib import contextmanager
from django.utils.timezone import utc
from util import ReplicationMixin
from fs.btrfs import get_oldest_snap
from storageadmin.models import Appliance
import json

BTRFS = '/sbin/btrfs'
logger = logging.getLogger(__name__)


class Sender(ReplicationMixin, Process):

    def __init__(self, replica, sender_ip, snap_name, smeta_port,
                 sdata_port, rmeta_port, uuid, snap_id, rt=None):
        self.replica = replica
        self.receiver_ip = self._get_receiver_ip(self.replica)
        self.smeta_port = smeta_port
        self.sdata_port = sdata_port
        self.rmeta_port = rmeta_port
        self.sender_ip = sender_ip
        self.snap_name = snap_name
        self.uuid = uuid
        self.rt = rt
        self.rt2 = None
        self.rt2_id = None
        self.num_retain_snaps = 5
        self.ppid = os.getpid()
        self.snap_id = str(snap_id)  # must be ascii for zmq
        self.meta_begin = {'id': self.snap_id,
                           'msg': 'begin',
                           'pool': self.replica.dpool,
                           'share': self.replica.share,
                           'snap': self.snap_name,
                           'ip': self.sender_ip,
                           'data_port': self.sdata_port,
                           'meta_port': self.smeta_port,
                           'incremental': self.rt is not None,
                           'uuid': self.uuid, }
        self.meta_end = {'id': self.snap_id,
                         'msg': 'end', }
        self.kb_sent = 0
        self.ctx = zmq.Context()
        super(Sender, self).__init__()

    def _get_receiver_ip(self, replica):
        try:
            appliance = Appliance.objects.get(uuid=replica.appliance)
            return appliance.ip
        except Exception, e:
            logger.exception(e)
            msg = ('Failed to get receiver ip. Is the receiver '
                   'appliance added?')
            raise Exception(msg)

    @contextmanager
    def _clean_exit_handler(self, msg):
        try:
            yield
        except Exception, e:
            logger.error('%s. Exception: %s' % (msg, e.__str__()))
            self._sys_exit(3)

    def _sys_exit(self, code, linger=60000):
        self.ctx.destroy(linger=linger)
        sys.exit(code)

    @contextmanager
    def _update_trail_and_quit(self, msg):
        try:
            yield
        except Exception, e:
            logger.error('%s. Exception: %s' % (msg, e.__str__()))
            try:
                data = {'status': 'failed',
                        'error': msg, }
                self.update_replica_status(self.rt2_id, data)
            except Exception, e:
                logger.error('Exception occured in cleanup handler: %s' % e.__str__())
            finally:
                self._sys_exit(3)

    def _process_q(self):
        ack = self.meta_sub.recv_string()
        ack = json.loads(ack[len('meta-%s' % self.snap_id):])
        logger.debug('ack received by sender: %s' % ack)
        if (ack['msg'] == 'send_more'):
            #  excess credit messages from receiver at that end
            return self._process_q()

        if (ack['msg'] == 'error'):
            error = 'Error on Receiver: %s' % ack['error']
            with self._update_trail_and_quit(error):
                raise Exception(error)
        return ack

    def _delete_old_snaps(self, share_path):
        oldest_snap = get_oldest_snap(share_path, self.num_retain_snaps)
        if (oldest_snap is not None):
            msg = ('Failed to delete snapshot: %s. Aborting.' %
                   oldest_snap)
            with self._clean_exit_handler(msg):
                self.delete_snapshot(self.replica.share, oldest_snap)
                return self._delete_old_snaps(share_path)

    def run(self):
        msg = ('Failed to subscribe to the main scheduler')
        with self._clean_exit_handler(msg):
            self.meta_sub = self.ctx.socket(zmq.SUB)
            self.meta_sub.connect('tcp://%s:%d' % (self.sender_ip, self.sdata_port))
            self.meta_sub.RCVTIMEO = 600000 #10 minutes
            substr = 'meta-%s' % self.snap_id
            self.meta_sub.setsockopt_string(zmq.SUBSCRIBE, substr.decode('ascii'))

        msg = ('Failed to connect to receiver(%s) on meta port'
               '(%d) for snap_name: %s. Aborting.' %
               (self.receiver_ip, self.rmeta_port, self.snap_name))
        with self._clean_exit_handler(msg):
            meta_push = self.ctx.socket(zmq.PUSH)
            meta_push.connect('tcp://%s:%d' % (self.receiver_ip,
                                               self.rmeta_port))

        msg = ('Failed to connect to main scheduler')
        with self._clean_exit_handler(msg):
            self.data_push = self.ctx.socket(zmq.PUSH)
            self.data_push.connect('tcp://%s:%d' % (self.sender_ip, settings.REPLICA_SINK_PORT))

        #  1. create a new replica trail if it's the very first time
        # or if the last one succeeded
        msg = ('Failed to create local replica trail for snap_name:'
               ' %s. Aborting.' % self.snap_name)
        with self._clean_exit_handler(msg):
            self.rt2 = self.create_replica_trail(self.replica.id,
                                                 self.snap_name)
            self.rt2_id = self.rt2['id']

        #  2. create a snapshot only if it's not already from a previous
        #  failed attempt.
        msg = ('Failed to create snapshot: %s. Aborting.' % self.snap_name)
        with self._clean_exit_handler(msg):
            self.create_snapshot(self.replica.share, self.snap_name)

        #  let the receiver know that following diff is coming
        msg = ('Failed to send initial metadata communication to the '
               'receiver(%s), most likely due to a network error. Aborting.'
               % self.receiver_ip)
        with self._update_trail_and_quit(msg):
            meta_push.send_json(self.meta_begin)

        msg = ('Timeout occured while waiting for OK '
               'from the receiver(%s) to start sending data. Aborting.'
               % self.receiver_ip)
        with self._update_trail_and_quit(msg):
            ack = self._process_q()
            if (ack['msg'] == 'snap_exists'):
                data = {'status': 'succeeded',
                        'error': 'snapshot already exists on the receiver', }
                msg = ('Failed to update replica status for snap_name: %s. '
                       'Aborting.' % self.snap_name)
                with self._clean_exit_handler(msg):
                    self.update_replica_status(self.rt2_id, data)
                    self._sys_exit(0)

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
            sp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            fcntl.fcntl(sp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        except Exception, e:
            msg = ('Failed to start the low level btrfs send '
                   'command(%s). Aborting. Exception: ' % (cmd, e.__str__()))
            logger.error(msg)
            with self._update_trail_and_quit(msg):
                self.data_push.send('%sEND_FAIL' % self.snap_id)
            self._sys_exit(3)

        alive = True
        credit = settings.DEFAULT_SEND_CREDIT
        check_credit = True
        while alive:
            if (check_credit is True and credit < 1):
                #This does not seem reliable. @todo: redo.
                ack = self.meta_sub.recv_string()
                ack = json.loads(ack[len('meta-%s' % self.snap_id):])
                if (ack['msg'] == 'send_more'):
                    credit = ack['credit']
                    logger.debug('send process alive for %s. %d KB sent.' %
                                 (self.snap_id, int(self.kb_sent/1024)))
                else:
                    logger.error('unexpected message received: %s' % ack)
            try:
                if (sp.poll() is not None):
                    logger.debug('send process finished for %s. rc: %d. '
                                 'stderr: %s' % (self.snap_id,
                                                 sp.returncode,
                                                 sp.stderr.read()))
                    alive = False
                fs_data = sp.stdout.read()
            except IOError:
                continue
            except Exception, e:
                msg = ('Exception occured while reading low level btrfs '
                       'send data for %s. Aborting.' % self.snap_id)
                if (alive):
                    sp.terminate()
                with self._update_trail_and_quit(msg):
                    self.data_push.send('%sEND_FAIL' % self.snap_id)
                    raise e

            msg = ('Failed to send fsdata to the receiver for %s. Aborting.' %
                   (self.snap_id))
            with self._update_trail_and_quit(msg):
                self.data_push.send('%s%s' % (self.snap_id, fs_data))
                self.kb_sent = self.kb_sent + len(fs_data)
                credit = credit - 1

                if (not alive):
                    check_credit = False
                    if (sp.returncode != 0):
                        self.data_push.send('%sEND_FAIL' % self.snap_id)
                    else:
                        self.data_push.send('%sEND_SUCCESS' % self.snap_id)

            if (os.getppid() != self.ppid):
                logger.error('Scheduler exited. Sender for %s cannot go on. '
                             'Aborting.' % self.snap_id)
                self._sys_exit(3)

        msg = ('Timeout occured while waiting for final '
               'send confirmation from the receiver(%s) for %s. Aborting.'
               % (self.receiver_ip, self.snap_id))
        with self._update_trail_and_quit(msg):
            ack = self._process_q()
            self.data_push.send('%sACK_SUCCESS' % self.snap_id)

        data = {'status': 'succeeded',
                'kb_sent': self.kb_sent / 1024, }
        if (ack['msg'] == 'receive_error'):
            msg = ('Receiver(%s) returned a processing error for '
                   ' %s. Check it for more information.'
                   % (self.receiver_ip, self.snap_id))
            data['status'] = 'failed'
            data['error'] = msg
        else:
            share_path = ('%s%s/.snapshots/%s' %
                          (settings.MNT_PT, self.replica.pool,
                           self.replica.share))
            self._delete_old_snaps(share_path)

        msg = ('Failed to update final replica status for %s'
               '. Aborting.' % self.snap_id)
        with self._clean_exit_handler(msg):
            self.update_replica_status(self.rt2_id, data)
        self._sys_exit(0)
