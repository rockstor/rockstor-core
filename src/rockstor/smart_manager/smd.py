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
import zmq
import time
import sys
from django.conf import settings
from django.core.serializers import deserialize
from django.core.exceptions import ObjectDoesNotExist

from procfs import ProcRetreiver
from services import ServiceMonitor
from stap_dispatcher import Stap
from scheduler.task_dispatcher import TaskDispatcher
from smart_manager import agents
from cli.rest_util import api_call
from smart_manager.models import (CPUMetric, LoadAvg, MemInfo, PoolUsage,
                                  DiskStat, ShareUsage, ServiceStatus)

import logging
logger = logging.getLogger(__name__)

def truncate_ts_data(max_records=settings.MAX_TS_RECORDS):
    """
    cleanup ts tables: CPUMetric, LoadAvg, MemInfo, PoolUsage, DiskStat and
    ShareUsage, ServiceStatus
    Discard all records older than last max_records.
    """
    ts_models = (CPUMetric, LoadAvg, MemInfo, PoolUsage, DiskStat,
                 ShareUsage, ServiceStatus)
    try:
        for m in ts_models:
            try:
                latest_id = m.objects.latest('id').id
            except ObjectDoesNotExist, e:
                msg = ('Unable to get latest id for the model: %s. Moving '
                       'on' % (m.__name__))
                logger.error(msg)
                continue
            m.objects.filter(id__lt=latest_id-max_records).delete()
    except Exception, e:
        logger.error('Unable to truncate time series data')
        logger.exception(e)
        raise e

def clean_exit(children, pull_socket=None, context=None):
    logger.error('clean exiting smd')
    if (pull_socket is not None):
        logger.error('closing pull socket')
        pull_socket.close()
        logger.error('pull socket closed')

    if (context is not None):
        logger.error('terminating zmq context')
        context.term()
        logger.error('zmq context terminated')

    for p in children:
        if (not p.is_alive()):
            logger.error('child process: %s not alive. no need to terminate' %
                         p.name)
            continue

        logger.error('terminating the child process: %s' % p.name)
        p.terminate()
        logger.error('waiting for child process: %s to exit' % p.name)
        p.join()
        logger.error('child process: %s terminated successfully' % p.name)
    logger.error('smd out!')
    sys.exit(0)

def main():
    context = zmq.Context()
    pull_socket = context.socket(zmq.PULL)
    pull_socket.RCVTIMEO = 500
    pull_socket.bind('tcp://%s:%d' % settings.SPROBE_SINK)

    #bootstrap the machine. success of quit
    url = 'https://localhost/api/commands/bootstrap'
    time.sleep(10)
    try:
        api_call(url, calltype='post')
    except Exception, e:
        logger.error('Unable to bootstrap the machine. Moving on..')
        logger.exception(e)

    try:
        truncate_ts_data()
    except Exception, e:
        e_msg = ('Unable to do the initial ts data truncation. Aborting...')
        logger.error(e_msg)
        logger.exception(e)
        clean_exit([], pull_socket, context)

    live_procs = [ProcRetreiver(), ServiceMonitor(),
                  Stap(settings.TAP_SERVER),
                  TaskDispatcher(settings.SCHEDULER),]
    for p in live_procs:
        p.start()

    num_ts_records = 0
    while (True):
        for p in live_procs:
            if (not p.is_alive()):
                msg = ('%s is dead. exitcode: %d' % (p.name, p.exitcode))
                logger.error(msg)
                clean_exit(live_procs, pull_socket, context)
        if (len(live_procs) == 0):
            logger.error('All child processes have exited. I am returning.')
            clean_exit([], pull_socket, context)

        try:
            while (True):
                sink_data = pull_socket.recv_json()
                if (isinstance(sink_data, dict)): #worker data
                    cb = getattr(agents, sink_data['cb'])
                    cb(sink_data['part_out'], sink_data['rid'], logger)
                else:
                    #smart probe, proc, service django models
                    for d in deserialize("json", sink_data):
                        num_ts_records = num_ts_records + 1
                        d.save()
        except zmq.error.Again:
            pass
        except Exception, e:
            logger.error('exception while processing sink data. Aborting...')
            logger.exception(e)
            clean_exit(live_procs, pull_socket, context)

        if (num_ts_records > (settings.MAX_TS_RECORDS * 5)):
            try:
                truncate_ts_data()
                num_ts_records = 0
            except Exception, e:
                logger.error('Error truncating time series data. Aborting...')
                logger.exception(e)
                clean_exit(live_procs, pull_socket, context)
