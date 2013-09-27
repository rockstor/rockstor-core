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

import time
import os
from multiprocessing import Process
from models import (Service, ServiceStatus)
from system.services import service_status
import logging
logger = logging.getLogger(__name__)

class ServiceMonitor(Process):

    def __init__(self, q):
        self.q = q
        self.ppid = os.getpid()
        self.interval = 10 #seconds
        super(ServiceMonitor, self).__init__()

    def run(self):
        try:
            while (True):
                if (os.getppid() != self.ppid):
                    msg = ('Parent process(smd) exited. I am exiting too.')
                    return logger.error(msg)

                if (self.q.qsize() < 1000):
                    for s in Service.objects.all():
                        sso = ServiceStatus(service=s, status=False)
                        try:
                            out, err, rc = service_status(s.name)
                            if (rc == 0):
                                sso.status = True
                        except Exception, e:
                            msg = ('Exception while getting status of '
                                   'service: %s' % s.name)
                            logger.error(msg)
                            logger.exception(e)
                        finally:
                            self.q.put(sso)
                time.sleep(self.interval)
        except Exception, e:
            msg = ('unhandled exception in %s. Exiting' % self.name)
            logger.error(msg)
            logger.exception(e)
            raise e
