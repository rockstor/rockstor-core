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

STAP_RUN = '/usr/bin/staprun'

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
        pull_socket.bind('tcp://127.0.0.1:10000')
        while True:
            if (os.getppid() != self.ppid):
                break

            task = None
            try:
                task = pull_socket.recv_json()
            except:
                continue

            cmd = [STAP_RUN, task['module'], '-c', 'sleep 10']
            out, err, rc = run_command(cmd)
            model = getattr(models, task['tap_class'])
            #need to make it more generic so we can just throw a blob of data
            #at any model in here.
            if (task['tap'] == 'iostats'):
                for line in out[2:]:
                    fields = line.split()
                    m_i = model(proc_name=fields[0], num_open=fields[1],
                                num_read=fields[2], sum_read=fields[3],
                                avg_read=fields[4], num_write=fields[5],
                                sum_write=fields[6], avg_write=fields[7])
                    self.q.put(m_i)
            elif (task['tap'] == 'hello'):
                m_i = model(message=out)
                self.q.put(m_i)

        pull_socket.close()
        context.term()
