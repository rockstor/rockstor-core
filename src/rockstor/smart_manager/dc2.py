from gevent import monkey
monkey.patch_all()
import gevent
import psutil
from socketio import socketio_manage
from socketio.server import SocketIOServer
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin
from smart_manager.models import CPUMetric
from datetime import datetime
from django.utils.timezone import utc

import os
import logging
logger = logging.getLogger(__name__)

cpu_stats = []


class DashboardNamespace(BaseNamespace, BroadcastMixin):
    send_cpu = False

    def recv_connect(self):
        self.emit('sm_data', {})

    def recv_disconnect(self):
        self.disconnect(silent=True)

    def on_sendcpu(self, msg):
        self.send_cpu = True

        def sendcpu():
            while (self.send_cpu):
                global cpu_stats
                self.emit('sm_data', {'key': 'cpu_data', 'data': cpu_stats})
                gevent.sleep(1)
        self.spawn(sendcpu)

    def on_stopcpu(self, msg):
        self.send_cpu = False


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'
        if (path == 'db2'):
            path = 'index.html'

        if path.startswith('static/') or path == 'index.html':
            try:
                data = open(path).read()
            except Exception:
                return not_found(start_response)

            if path.endswith(".js"):
                content_type = "text/javascript"
            elif path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".swf"):
                content_type = "application/x-shockwave-flash"
            else:
                content_type = "text/html"

            start_response('200 OK', [('Content-Type', content_type)])
            return [data]

        if path.startswith("socket.io"):
            socketio_manage(environ, {'/dashboard': DashboardNamespace})
        else:
            return not_found(start_response)


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not Found</h1>']


def get_cpu_stats():
    global cpu_stats
    while True:
        cpu_stats = []
        vals = psutil.cpu_times_percent(percpu=True)
        ts = datetime.utcnow().replace(tzinfo=utc)
        for i in range(len(vals)):
            name = 'cpu%d' % i
            v = vals[i]
            #cm = CPUMetric(name=name, umode=v.user, umode_nice=v.nice,
            #               smode=v.system, idle=v.idle, ts=ts)
            #cm.save()
            str_time = ts.strftime('2015-07-26T20:07:13Z')
            cpu_stats.append({'name': name, 'umode': v.user,
                              'umode_nice': v.nice, 'smode': v.system,
                              'idle': v.idle, 'ts': str_time, })
            #cpu_stats.append({'name': name, 'umode': cm.umode,
            #                  'umode_nice': cm.umode_nice, 'smode': cm.smode,
            #                  'idle': cm.idle, 'ts': str_time, })
        gevent.sleep(1)


def main():
    gevent.spawn(get_cpu_stats)
    logger.debug('Listening on port http://0.0.0.0:8080 and on port 10843 (flash policy server)')
    SocketIOServer(('0.0.0.0', 8080), Application(),
                   resource="socket.io", policy_server=True,
                   policy_listener=('0.0.0.0', 10843)).serve_forever()
