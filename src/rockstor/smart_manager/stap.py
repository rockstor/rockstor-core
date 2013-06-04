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

"""
IR from systemtap

First implementation:
Have a predefined set of stap scripts (saved as script files?)
User can turn a script on to collect data and turn off to stop
"""

from multiprocessing import Process
from multiprocessing.connection import Listener
from system.osi import run_command
import models
import zmq
import os
import time
import subprocess
import fcntl
from smart_manager.agents import process_nfsd_calls
from smart_manager.models import SProbe
from django.conf import settings

STAP_RUN = '/usr/bin/staprun'

import logging
logger = logging.getLogger(__name__)

class Stap(Process):

    def __init__(self, q, address):
        self.q = q
        self.address = address
        self.ppid = os.getpid()
        super(Stap, self).__init__()

    def run(self):
        context = zmq.Context()
        pull_socket = context.socket(zmq.PULL)
        pull_socket.RCVTIMEO = 500
        pull_socket.bind('tcp://%s:%d' % self.address)
        while True:
            if (os.getppid() != self.ppid):
                break

            task = None
            try:
                task = pull_socket.recv_json()
                logger.info('received task: %s' % (repr(task)))

                #this happens when smart manager dies while running some probes
                #and restarted later to clean up
                if (task['action'] == 'stop'):
                    continue
            except:
                #will sleeping here help? or some other zmq based wakeup?
                continue

            #wait a little till the recipe instance is saved by the
            #API. non-issue most of the time.
            start_tap = False
            num_tries = 0
            while True:
                try:
                    ro = SProbe.objects.get(id=task['roid'])
                    start_tap = True
                    logger.info('start_tap is true')
                    break
                except:
                    logger.error('waiting for recipe object. num_tries = %d' %
                                 num_tries)
                    time.sleep(1)
                    num_tries = num_tries + 1
                    if (num_tries > 20):
                        break

            if (not start_tap):
                logger.error('not starting the tap')
                ro.state = 'error'
                self.q.put(ro)
                continue

            logger.info('running command')
            cmd = [STAP_RUN, task['module'],]
            rp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            fcntl.fcntl(rp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
            logger.info('started tap')
            ro.state = 'running'
            self.q.put(ro)
            probe_stopped = False
            while True:
                try:
                    part_out = rp.stdout.read()
                    self.__process_output(part_out, task['tap'], ro)
                except IOError:
                    #occurs when there's no output to read
                    pass
                finally:
                    try:
                        stop_task = pull_socket.recv_json()
                        #should we reload from db to see 'stopped' state?
                        rp.terminate()
                        probe_stopped = True
                        logger.info('received stop')
                    except:
                        pass

                if (rp.poll() is not None):
                    if (probe_stopped is not True):
                        msg = ('Probe process died. returncode: %s. '
                               'stderr: %s' % (rp.returncode, repr(rp.stderr)))
                        logger.error(msg)
                        ro = SProbe.objects.get(id=task['roid'])
                        ro.state = 'error'
                        self.q.put(ro)
                    break
                time.sleep(.5)

        pull_socket.close()
        context.term()
        logger.info('terminated context. exiting')

    def __process_output(self, part_out, tap, ro):
        if (tap == 'nfs-distrib' or tap == 'nfs-client-distrib'):
            process_nfsd_calls(self.q, part_out, ro, logger)
