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
from datetime import (datetime, timedelta)
from multiprocessing import Queue
from django.utils.timezone import utc
from procfs import ProcRetreiver
from services import ServiceMonitor
from stap_dispatcher import Stap
import models
from django.conf import settings
from django.core.serializers import deserialize
import zmq
import logging
logger = logging.getLogger(__name__)
from smart_manager import agents


def process_model_queue(q):
    cleanup_map = {}
    max_interval = timedelta(seconds=settings.PROBE_DATA_INTERVAL)
    new_start = datetime.utcnow().replace(tzinfo=utc) - max_interval

    while (not q.empty()):
        metric = q.get()
        metric.save()
        cleanup_map[metric] = True
    for c in cleanup_map.keys():
        model = getattr(models, c.__class__.__name__)
        model.objects.filter(ts__lt=new_start).delete()

def main():

    context = zmq.Context()
    pull_socket = context.socket(zmq.PULL)
    pull_socket.RCVTIMEO = 500
    pull_socket.bind('tcp://%s:%d' % settings.SPROBE_SINK)

    proc_q = Queue()
    service_q = Queue()

    pr = ProcRetreiver(proc_q)
    pr.daemon = True
    pr.start()
    service_mon = ServiceMonitor(service_q)
    service_mon.daemon = True
    service_mon.start()
    stap_proc = Stap(settings.TAP_SERVER)
    stap_proc.start()

    while (True):
        process_model_queue(proc_q)
        process_model_queue(service_q)
        try:
            sink_data = pull_socket.recv_json()
            if (isinstance(sink_data, dict)): #worker data
                cb = getattr(agents, sink_data['cb'])
                cb(sink_data['part_out'], sink_data['rid'], logger)
            else:
                #smart probe django model
                for d in deserialize("json", sink_data):
                    d.save()
        except zmq.error.Again:
            continue
        except Exception, e:
            logger.exception('exception while processing sink data')
            continue
    #@todo: close zmq context
