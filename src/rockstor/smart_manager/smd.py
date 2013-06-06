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
from multiprocessing.connection import Listener
from django.utils.timezone import utc
from procfs import ProcRetreiver
from services import ServiceMonitor
from stap import Stap
import models
from django.conf import settings

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

def process_tap_queue(q):
    while (not q.empty()):
        m = q.get()
        m.save()


def main():

    proc_q = Queue()
    service_q = Queue()
    tap_q = Queue()

    pr = ProcRetreiver(proc_q)
    pr.daemon = True
    pr.start()
    service_mon = ServiceMonitor(service_q)
    service_mon.daemon = True
    service_mon.start()
    stap_proc = Stap(tap_q, settings.TAP_SERVER)
    stap_proc.daemon = True
    stap_proc.start()

    while (True):
        process_model_queue(proc_q)
        process_model_queue(service_q)
        process_model_queue(tap_q)
