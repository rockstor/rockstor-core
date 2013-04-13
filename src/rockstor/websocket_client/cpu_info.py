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

from socketIO_client import SocketIO
import random
import requests
import json
import time
from django.conf import settings

import logging


def on_response(*args):
    pass

def main():
    logging.basicConfig(filename=settings.WEBSOCKET_CLIENT['logfile'],
                        level=logging.DEBUG)
    logging.debug('Started logging')
    num_samples = 120;
    socketIO = SocketIO('localhost', settings.NGINX_WEBSOCKET_PORT, secure=True)
    max_ts = None
    prev_cpu_data = [];
    # TODO handle multiple cpus
    for i in range(num_samples):
        prev_cpu_data.append({u'umode': 0, u'umode_nice': 0, u'smode': 0, u'idle': 0, u'ts': None})

    while True:
        # read from db
        auth_params = {'apikey': 'adminapikey'}

        # Get cpu metrics
        r = requests.get('https://localhost/api/sm/cpumetric/?format=json', verify=False, params = auth_params)
        cpu_data = r.json()
        tmp = []
        # find max timestamp
        if (len(cpu_data) < num_samples):
            for i in range(num_samples - len(cpu_data)):
                tmp.append({u'umode': 0, u'umode_nice': 0, u'smode': 0, u'idle': 0, u'ts': None})
            tmp.extend(cpu_data)
            cpu_data = tmp

        cpu_util = [];
        for i in range(num_samples):
            cpu_util.append({
                'umode': cpu_data[i][u'umode'] - prev_cpu_data[i][u'umode'],
                'umode_nice': cpu_data[i][u'umode_nice'] - prev_cpu_data[i][u'umode_nice'],
                'smode': cpu_data[i][u'smode'] - prev_cpu_data[i][u'smode'],
                'idle': cpu_data[i][u'idle'] - prev_cpu_data[i][u'idle']
                })


        # send to websocket
        new_cpu_data = False
        if cpu_data[num_samples-1][u'ts'] != prev_cpu_data[num_samples-1][u'ts']:
            new_cpu_data = True
        prev_cpu_data = cpu_data

        msg = {}
        if new_cpu_data:
            msg['cpu_util'] = cpu_util

        # Get loadavg metrics
        r = requests.get('https://localhost/api/sm/loadavg/?format=json', verify=False, params = auth_params)
        load_data = r.json()
        msg['load_avg'] = load_data

        if (r.status_code != 200):
            socketIO.emit('sm_data_update', {'msg': json.dumps(msg)}, on_response)
        else:
            logging.debug('invalid CPU data - JSON data invalid')

        # Sleep before getting the next set of data
        time.sleep(5)
