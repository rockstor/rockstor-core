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
import zmq
import os
import re
import time
from storageadmin.models import (NetworkInterface, Appliance)
from smart_manager.models import (ReplicaTrail, ReplicaShare, Replica)
from django.conf import settings
from new_sender import NewSender
from new_receiver import NewReceiver
from django.utils.timezone import utc
import logging
from django.db import DatabaseError
from util import ReplicationMixin
import json
from cli import APIWrapper


class ReplicaScheduler(ReplicationMixin, Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.senders = {}
        self.receivers = {}
        self.data_port = settings.REPLICA_DATA_PORT
        self.meta_port = settings.REPLICA_META_PORT
        self.MAX_ATTEMPTS = settings.MAX_REPLICA_SEND_ATTEMPTS
        self.recv_meta = None
        self.uuid = None
        self.base_url = 'https://localhost/api'
        self.rep_ip = None
        self.uuid = None
        self.trail_prune_interval = 3600 #seconds
        self.prune_time = int(time.time()) - (self.trail_prune_interval + 1)
        self.raw = None
        super(ReplicaScheduler, self).__init__()

    def _prune_workers(self, workers):
        for wd in workers:
            for w in wd.keys():
                if (wd[w].exitcode is not None):
                    del(wd[w])
                    self.logger.debug('deleted worker: %s' % w)
        return workers

    def _get_receiver_ip(self, replica):
        if (replica.replication_ip is not None):
            return replica.replication_ip
        try:
            appliance = Appliance.objects.get(uuid=replica.appliance)
            return appliance.ip
        except Exception, e:
            msg = ('Failed to get receiver ip. Is the receiver '
                   'appliance added?. Exception: %s' % e.__str__())
            self.logger.error(msg)
            raise Exception(msg)

    def _process_send(self, replica):
        receiver_ip = self._get_receiver_ip(replica)
        rt = ReplicaTrail.objects.filter(replica=replica).order_by('-id')
        sw = None
        snap_name = '%s_%d_replication' % (replica.share, replica.id)
        if (len(rt) == 0):
            snap_name = '%s_1' % snap_name
        else:
            snap_name = '%s_%d' % (snap_name, rt[0].id + 1)
        snap_id = ('%s_%s' %
                   (self.uuid, snap_name))
        if (len(rt) == 0):
            self.logger.debug('new sender for snap: %s' % snap_id)
            sw = NewSender(replica, snap_name, snap_id, self.logger)
        elif (rt[0].status == 'succeeded'):
            self.logger.debug('incremental sender for snap: %s' % snap_id)
            sw = NewSender(replica, snap_name, snap_id, self.logger, rt[0])
        elif (rt[0].status == 'pending'):
            prev_snap_id = ('%s_%s' % (self.uuid, rt[0].snap_name))
            if (prev_snap_id in self.senders):
                return self.logger.debug('send process ongoing for snap: '
                                         '%s. Not starting a new one.' % prev_snap_id)
            self.logger.debug('%s not found in senders. Previous '
                              'sender must have Aborted. Marking '
                              'it as failed' % prev_snap_id)
            msg = ('Sender process Aborted. See logs for '
                   'more information')
            data = {'status': 'failed',
                    'error': msg, }
            return self.update_replica_status(rt[0].id, data)
        elif (rt[0].status == 'failed'):
            snap_name = rt[0].snap_name
            #  if num_failed attempts > 10, disable the replica
            num_tries = 0
            for rto in rt:
                if (rto.status != 'failed' or
                    num_tries >= self.MAX_ATTEMPTS or
                    rto.end_ts < replica.ts):
                    break
                num_tries = num_tries + 1
            if (num_tries >= self.MAX_ATTEMPTS):
                self.logger.info('Maximum attempts(%d) reached '
                                 'for snap: %s. Disabling the '
                                 'replica.' %
                                 (self.MAX_ATTEMPTS, snap_id))
                return self.disable_replica(replica.id)

            self.logger.info('previous backup failed for snap: '
                             '%s. Starting a new one. Attempt '
                             '%d/%d.' % (snap_id, num_tries,
                                         self.MAX_ATTEMPTS))
            prev_rt = None
            for rto in rt:
                if (rto.status == 'succeeded'):
                    prev_rt = rto
                    break
            sw = NewSender(replica, snap_name, snap_id, self.logger, prev_rt)
        else:
            return self.logger.error('unknown replica trail status: %s. '
                                     'ignoring snap: %s' %
                                     (rt[0].status, snap_id))
        self.senders[snap_id] = sw
        sw.daemon = True #to kill all senders in case scheduler dies.
        sw.start()
        return snap_id

    def run(self):
        self.logger = self.get_logger()
        self.law = APIWrapper()
        try:
            if (NetworkInterface.objects.filter(itype='replication').exists()):
                self.rep_ip = NetworkInterface.objects.filter(itype='replication')[0].ipaddr
            else:
                self.rep_ip = NetworkInterface.objects.get(itype='management').ipaddr
        except NetworkInterface.DoesNotExist:
            msg = ('Failed to get replication interface. If you have only one'
                   ' network interface, assign management role to it and '
                   'replication service will use it. In addition, you can '
                   'assign a dedicated replication role to another interface.'
                   ' Aborting for now. Exception: %s' % e.__str__())
            return self.logger.error(msg)

        try:
            self.uuid = Appliance.objects.get(current_appliance=True).uuid
        except Exception, e:
            msg = ('Failed to get uuid of current appliance. Aborting. '
                   'Exception: %s' % e.__str__())
            return self.logger.error(msg)

        ctx = zmq.Context()
        frontend = ctx.socket(zmq.ROUTER)
        frontend.set_hwm(10)
        frontend.bind('tcp://%s:5555' % self.rep_ip)

        backend = ctx.socket(zmq.ROUTER)
        backend.bind('ipc:///tmp/foobar.ipc')

        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)
        self.clients = {}

        while True:
            if (os.getppid() != self.ppid):
                self.logger.error('Parent exited. Aborting.')
                ctx.destroy()
                break

            for snap_id in self.senders.keys():
                if (self.senders[snap_id].exitcode is not None):
                    del self.senders[snap_id]
                    self.logger.debug('removed sender: %s' % snap_id)
            self.logger.debug('Active senders = %s' % self.senders.keys())

            term_msgs = ('btrfs-send-init-error', 'btrfs-send-unexpected-termination-error',
                         'btrfs-send-nonzero-termination-error', 'btrfs-send-stream-finished',)
            while True:
                #This loop may still continue even if replication service
                #is terminated, as long as data is coming in.
                socks = dict(poller.poll(timeout=25000)) #poll for 10 seconds
                if (frontend in socks and socks[frontend] == zmq.POLLIN):
                    address, command, msg = frontend.recv_multipart()
                    self.logger.debug('command = %s.' % command)
                    if (address not in self.clients):
                        self.clients[address] = 1
                    else:
                        self.clients[address] += 1

                    if (self.clients[address] % 100 == 0):
                        self.logger.debug('Processed %d messages from %s' %
                                          (self.clients[address], address))
                    if (msg == 'shall I begin sending?'):
                        self.logger.debug('initial greeting from %s' % address)
                        #Start a new receiver and send the appropriate response
                        try:
                            nr = NewReceiver(address, 'test', self.logger)
                            nr.daemon = True
                            nr.start()
                            self.logger.debug('New receiver started for %s' % address)
                            continue
                        except Exception, e:
                            self.logger.debug('Exception while starting the '
                                              'new receiver for %s: %s'
                                              % (address, e.__str__()))
                            reply_msg = 'receiver-init-error'
                            frontend.send_multipart([address, command, 'receiver-init-error'])
                    else:
                        #do we hit hwm? is the dealer still connected?
                        backend.send_multipart([address, command, msg])

                    # if (msg in term_msgs):
                    #     self.logger.debug('terminal message(%s) from %s' % (msg, address))
                    #     reply_msg = 'ok, goodbye'
                    #     del self.clients[address]
                    # frontend.send_multipart([address, command, reply_msg])


                elif (backend in socks and socks[backend] == zmq.POLLIN):
                    address, command, msg = backend.recv_multipart()
                    self.logger.debug('Received backend msg: %s from: %s' % (msg, address))
                    if (re.match('new_send-', address) is not None):
                        rid = int(address.split('new_send-')[1])
                        try:
                            replica = Replica.objects.get(id=rid, enabled=True)
                            snap_id = self._process_send(replica)
                            # ns = NewSender(replica, snap_name, self.logger, rid)
                            # self.senders[rid] = ns
                            # ns.daemon = True
                            # ns.start()
                            msg = b'SUCCESS'
                        except Exception, e:
                            msg = (b'FAILED. Exception: %s' % e.__str__())
                        finally:
                            backend.send_multipart([address, command, msg])
                    elif (address in self.clients):
                        if (command == 'receiver-ready'):
                            backend.send_multipart([address, b'ACK'])
                            #a new receiver has started. reply to the sender that must be waiting
                        self.logger.debug('address: %s' % address)
                        frontend.send_multipart([address, '', msg])

                else:
                    #poller came out empty after timeout. break to do other things
                    self.logger.debug('nothing received')
                    break

def main():
    rs = ReplicaScheduler()
    rs.start()
    rs.join()
