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
import zmq
from django.conf import settings
from django.core.serializers import serialize
from datetime import datetime
from django.utils.timezone import utc
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

class ServiceMonitor(Process):

    def __init__(self):
        self.ppid = os.getpid()
        self.interval = 1 #seconds
        super(ServiceMonitor, self).__init__()

    def _sink_put(self, sink, ro):
        #data = serialize("json", (ro,))
        #sink.send_json(data)
        ro.save()

    def run(self):
        context = zmq.Context()
        sink_socket = context.socket(zmq.PUSH)
        sink_socket.connect('tcp://%s:%d' % settings.SPROBE_SINK)
        first_loop = True
        try:
            while (True):
                if (os.getppid() != self.ppid):
                    msg = ('Parent process(smd) exited. I am exiting too.')
                    return logger.error(msg)

                ts = datetime.utcnow().replace(tzinfo=utc)
                for s in Service.objects.all():
                    sso = None
                    if (first_loop is not True):
                        try:
                            sso = ServiceStatus.objects.filter(service=s).latest('id')
                        except ObjectDoesNotExist:
                            pass

                    status = False
                    try:
                        out, err, rc = service_status(s.name)
                        if (rc == 0):
                            status = True
                    except Exception, e:
                        msg = ('Exception while getting status of '
                               'service: %s' % s.name)
                        logger.error(msg)
                        logger.exception(e)
                    finally:
                        if (sso is None or sso.status != status):
                            sso = ServiceStatus(service=s,
                                                status=status, ts=ts)
                        else:
                            sso.ts = ts
                            sso.count = sso.count + 1
                        self._sink_put(sink_socket, sso)
                        first_loop = False
                time.sleep(self.interval)
        except Exception, e:
            msg = ('unhandled exception in %s. Exiting' % self.name)
            logger.error(msg)
            logger.exception(e)
            raise e
