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
import zmq
import time
import subprocess
import fcntl

from django.conf import settings
from smart_manager.models import SProbe
from smart_manager.agents import cb_map
import logging
logger = logging.getLogger(__name__)

STAP_RUN = '/usr/bin/staprun'

class StapWorker(Process):

    def __init__(self, task):
        self.task = task
        self.ppid = os.getpid()
        super(StapWorker, self).__init__()

    def run(self):

        self.ctx = zmq.Context()
        self.sink_socket = self.ctx.socket(zmq.PUSH)
        self.sink_socket.connect('tcp://%s:%d' % settings.SPROBE_SINK)
        logger.info('running command')
        cmd = [STAP_RUN, self.task['module'],]
        rp = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
        fcntl.fcntl(rp.stdout.fileno(), fcntl.F_SETFL, os.O_NONBLOCK)
        logger.info('started tap')
        probe_stopped = False
        sink_data = {'cb': cb_map[self.task['tap']],
                     'rid': self.task['roid'],}
        while True:
            try:
                sink_data['part_out'] = rp.stdout.read()
                self.sink_socket.send_json(sink_data)
            except IOError:
                #occurs when there's no output to read
                pass
            finally:
                if (not self.task['queue'].empty()):
                    #stop or pause received.
                    msg = self.task['queue'].get()
                    #@todo: handle pause.
                    rp.terminate()
                    probe_stopped = True
                    logger.info('received stop')
                    break

            if (rp.poll() is not None):
                if (probe_stopped is not True):
                    msg = ('Probe process died. returncode: %s. '
                           'stderr: %s' % (rp.returncode, repr(rp.stderr)))
                    logger.error(msg)
                break
            time.sleep(.5)
