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
logger = logging.getLogger(__name__)
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
                    logger.debug('deleted worker: %s' % w)
        return workers

    def _prune_senders(self):
        for s in self.senders.keys():
            ecode = self.senders[s].exitcode
            if (ecode is not None):
                del self.senders[s]
                logger.debug('Sender(%s) exited. exitcode: %s' % (s, ecode))
        if (len(self.senders) > 0):
            logger.debug('Active Senders: %s' % self.senders.keys())

    def _get_receiver_ip(self, replica):
        if (replica.replication_ip is not None):
            return replica.replication_ip
        try:
            appliance = Appliance.objects.get(uuid=replica.appliance)
            return appliance.ip
        except Exception, e:
            msg = ('Failed to get receiver ip. Is the receiver '
                   'appliance added?. Exception: %s' % e.__str__())
            logger.error(msg)
            raise Exception(msg)

    def _process_send(self, replica):
        sender_key = ('%s_%s' % (self.uuid, replica.id))
        if (sender_key in self.senders):
            #If the sender exited but hasn't been removed from the dict,
            #remove and proceed.
            ecode = self.senders[sender_key].exitcode
            if (ecode is not None):
                del self.senders[sender_key]
                logger.debug('Sender(%s) exited. exitcode: %s. Forcing '
                             'removal.' % (sender_key, ecode))
            else:
                raise Exception('There is live sender for(%s). Will not start '
                                'a new one.' % sender_key)

        receiver_ip = self._get_receiver_ip(replica)
        rt_qs = ReplicaTrail.objects.filter(replica=replica).order_by('-id')
        last_rt = rt_qs[0] if (len(rt_qs) > 0) else None
        if (last_rt is None):
            logger.debug('Starting a new Sender(%s).' % sender_key)
            self.senders[sender_key] = NewSender(self.uuid, receiver_ip, replica)
        elif (last_rt.status == 'succeeded'):
            logger.debug('Starting a new Sender(%s)' % sender_key)
            self.senders[sender_key] = NewSender(self.uuid, receiver_ip, replica, last_rt)
        elif (last_rt.status == 'pending'):
            msg = ('Replica trail shows a pending Sender(%s), but it is not '
                   'alive. Marking it as failed. Will not start a new one.' % sender_key)
            logger.error(msg)
            data = {'status': 'failed',
                    'error': msg, }
            self.update_replica_status(last_rt.id, data)
            raise Exception(msg)
        elif (last_rt.status == 'failed'):
            #  if num_failed attempts > 10, disable the replica
            num_tries = 0
            for rto in rt_qs:
                if (rto.status != 'failed' or
                    num_tries >= self.MAX_ATTEMPTS or
                    rto.end_ts < replica.ts):
                    break
                num_tries = num_tries + 1
            if (num_tries >= self.MAX_ATTEMPTS):
                msg = ('Maximum attempts(%d) reached for Sender(%s). A new one '
                       'will not be started and the Replica task will be '
                       'disabled.' % (self.MAX_ATTEMPTS, sender_key))
                logger.error(msg)
                self.disable_replica(replica.id)
                raise Exception(msg)

            msg = ('previous backup failed for Sender(%s). Starting a new '
                   'one. Attempt %d/%d.' %
                   (sender_key, num_tries, self.MAX_ATTEMPTS))
            logger.debug(msg)
            last_success_rt = ReplicaTrail.objects.filter(replica=replica, status='succeeded').latest('id')
            if (last_success_rt is None):
                raise Exception('Failed to find the last successful '
                                'ReplicaTrail for the Sender(%s). ' % sender_key)
            self.senders[sender_key] = NewSender(self.uuid, receiver_ip, replica, last_success_rt)
        else:
            msg = ('Unexpected ReplicaTrail status(%s) for Sender(%s). '
                   'Will not start a new one.' % (last_rt.status, sender_key))
            raise Exception(msg)

        self.senders[sender_key].daemon = True #to kill all senders in case scheduler dies.
        self.senders[sender_key].start()

    def run(self):
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
            return logger.error(msg)

        try:
            self.uuid = Appliance.objects.get(current_appliance=True).uuid
        except Exception, e:
            msg = ('Failed to get uuid of current appliance. Aborting. '
                   'Exception: %s' % e.__str__())
            return logger.error(msg)

        ctx = zmq.Context()
        frontend = ctx.socket(zmq.ROUTER)
        frontend.set_hwm(10)
        frontend.bind('tcp://%s:5555' % self.rep_ip)

        backend = ctx.socket(zmq.ROUTER)
        backend.bind('ipc://%s' % settings.REPLICATION.get('ipc_socket'))

        poller = zmq.Poller()
        poller.register(frontend, zmq.POLLIN)
        poller.register(backend, zmq.POLLIN)
        self.clients = {}

        iterations = 10 #
        poll_interval = 6000 # 6 seconds
        msg_count = 0
        while True:
            #This loop may still continue even if replication service
            #is terminated, as long as data is coming in.
            socks = dict(poller.poll(timeout=poll_interval))
            if (frontend in socks and socks[frontend] == zmq.POLLIN):
                address, command, msg = frontend.recv_multipart()
                if (address not in self.clients):
                    self.clients[address] = 1
                else:
                    self.clients[address] += 1

                if (self.clients[address] % 1000 == 0):
                    logger.debug('Processed %d messages from %s' %
                                 (self.clients[address], address))
                if (command == 'sender-ready'):
                    logger.debug('initial greeting from %s' % address)
                    #Start a new receiver and send the appropriate response
                    try:
                        nr = NewReceiver(address, msg)
                        nr.daemon = True
                        nr.start()
                        logger.debug('New receiver started for %s' % address)
                        continue
                    except Exception, e:
                        logger.debug('Exception while starting the '
                                     'new receiver for %s: %s'
                                     % (address, e.__str__()))
                        reply_msg = 'receiver-init-error'
                        frontend.send_multipart([address, command, 'receiver-init-error'])
                else:
                    #do we hit hwm? is the dealer still connected?
                    backend.send_multipart([address, command, msg])


            elif (backend in socks and socks[backend] == zmq.POLLIN):
                address, command, msg = backend.recv_multipart()
                if (command == 'new-send'):
                    rid = int(msg)
                    logger.debug('new-send request received for %d' % rid)
                    rcommand = 'ERROR'
                    try:
                        replica = Replica.objects.get(id=rid)
                        if (replica.enabled):
                            self._process_send(replica)
                            msg = ('A new Sender started successfully for '
                                   'Replication Task(%d).' % rid)
                            rcommand = 'SUCCESS'
                        else:
                            msg = ('Failed to start a new Sender for Replication '
                                   'Task(%d) because it is disabled.' % rid)
                    except Exception, e:
                        msg = ('Failed to start a new Sender for Replication '
                               'Task(%d). Exception: %s' % (rid, e.__str__()))
                        logger.error(msg)
                    finally:
                        backend.send_multipart([address, rcommand, str(msg)])
                elif (address in self.clients):
                    if (command in ('receiver-ready', 'receiver-error', 'btrfs-recv-finished')):
                        logger.debug('Identitiy: %s command: %s' % (address, command))
                        backend.send_multipart([address, b'ACK', ''])
                        #a new receiver has started. reply to the sender that must be waiting
                    frontend.send_multipart([address, command, msg])

            else:
                iterations -= 1
                if (iterations == 0):
                    iterations = 10
                    self._prune_senders()

                    if (os.getppid() != self.ppid):
                        logger.error('Parent exited. Aborting.')
                        ctx.destroy()
                        #do some cleanup of senders before quitting?
                        break



def main():
    rs = ReplicaScheduler()
    rs.start()
    rs.join()
