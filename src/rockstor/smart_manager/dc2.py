from gevent import monkey
monkey.patch_all()

import gevent
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

from django.conf import settings
from system.osi import (uptime, kernel_info)

import psutil
from datetime import datetime
from django.utils.timezone import utc

from smart_manager.models import CPUMetric

from system.services import service_status
import logging
logger = logging.getLogger(__name__)


class WidgetNamespace(BaseNamespace, BroadcastMixin):
    send_cpu = False

    def recv_connect(self):
        logger.debug("Widget namespace connected")
        self.emit('widgets:connected', {
            'key': 'widgets:connected', 'data': 'connected'
        })
        # Switch for emitting cpu data
        self.send_cpu = True
        self.spawn(self.send_cpu_data)

    def recv_disconnect(self):
        logger.debug('disconnect received')
        self.send_cpu = False
        self.disconnect()

    def send_cpu_data(self):
        while self.send_cpu:
            cpu_stats = []
            vals = psutil.cpu_times_percent(percpu=True)
            ts = datetime.utcnow().replace(tzinfo=utc)
            for i, val in enumerate(vals):
                name = 'cpu%d' % i
                cm = CPUMetric(name=name, umode=val.user, umode_nice=val.nice,
                               smode=val.system, idle=val.idle, ts=ts)
                str_time = ts.strftime('%Y-%m-%dT%H:%M:%SZ')
                cpu_stats.append({'name': name, 'umode': val.user,
                                  'umode_nice': val.nice, 'smode': val.system,
                                  'idle': val.idle, 'ts': str_time, })
                cpu_stats.append({'name': name, 'umode': cm.umode,
                                  'umode_nice': cm.umode_nice, 'smode': cm.smode,
                                  'idle': cm.idle, 'ts': str_time })

            self.emit('widgets:cpudata', {
                'key': 'widgets:cpudata', 'data': cpu_stats
            })
            gevent.sleep(1)


class ServicesNamespace(BaseNamespace, BroadcastMixin):

    # Called before the recv_connect function
    def initialize(self):
        logger.debug('Services have been initialized')

    def recv_connect(self):
        logger.debug("Services has connected")
        self.emit('services:connected', {
            'key': 'services:connected', 'data': 'connected'
        })
        self.spawn(self.send_service_statuses)

    def recv_disconnect(self):
        logger.debug("Services have disconnected")
        self.disconnect()

    def send_service_statuses(self):
        # Iterate through the collection and assign the values accordingly
        services = ('nfs', 'smb', 'ntpd', 'winbind', 'netatalk',
                    'snmpd', 'docker', 'smartd', 'replication',
                    'nis', 'ldap', 'sftp', 'data-collector', 'smartd',
                    'service-monitor', 'docker', 'task-scheduler')
        while True:
            data = {}
            for service in services:
                data[service] = {}
                output, error, return_code = service_status(service)
                if (return_code == 0):
                    data[service]['running'] = return_code
                else:
                    data[service]['running'] = return_code

            self.emit('services:get_services', {
                'data': data, 'key': 'services:get_services'
            })
            gevent.sleep(5)


class SysinfoNamespace(BaseNamespace, BroadcastMixin):
    start = False
    supported_kernel = settings.SUPPORTED_KERNEL_VERSION

    # Called before the connection is established
    def initialize(self):
        logger.debug("Sysinfo has been initialized")

    # This function is run once on every connection
    def recv_connect(self):
        logger.debug("Sysinfo has connected")
        self.emit("sysinfo:sysinfo", {
            "key": "sysinfo:connected", "data": "connected"
        })
        self.start = True
        gevent.spawn(self.send_uptime)
        gevent.spawn(self.send_kernel_info)
        gevent.spawn(self.update_rockons)
        gevent.spawn(self.send_utcnow)

    # Run on every disconnect
    def recv_disconnect(self):
        logger.debug("Sysinfo has disconnected")
        self.start = False
        self.disconnect()

    def send_uptime(self):
        # Seems redundant
        while self.start:
            self.emit('sysinfo:uptime', {
                'data': uptime(), 'key': 'sysinfo:uptime'
            })
            gevent.sleep(30)

    def send_kernel_info(self):
            try:
                self.emit('sysinfo:kernel_info', {
                    'data': kernel_info(self.supported_kernel),
                    'key': 'sysinfo:kernel_info'
                })
            except Exception as e:
                logger.debug('kernel error')
                # Emit an event to the front end to capture error report
                self.emit('sysinfo:kernel_error', {
                    'data': str(e),
                    'key': 'sysinfo:kernel_error'
                })
                self.error('unsupported_kernel', str(e))

    def send_utcnow(self):
        while True:
            self.emit('sysinfo:utcnow', {
                'data': str(datetime.utcnow().replace(tzinfo=utc)),
                'key': 'sysinfo:utcnow'
            })
            gevent.sleep(1)

    def update_rockons(self):
        from cli.rest_util import api_call
        try:
            url = 'https://localhost/api/rockons/update'
            api_call(url, data=None, calltype='post', save_error=False)
            logger.debug('Updated Rock-on metadata')
        except Exception, e:
            logger.debug('failed to update Rock-on metadata. low-level '
                         'exception: %s' % e.__str__())


class Application(object):
    def __init__(self):
        self.buffer = []

    def __call__(self, environ, start_response):
        path = environ['PATH_INFO'].strip('/') or 'index.html'

        if path.startswith('/static') or path == 'index.html':
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
            socketio_manage(environ, {'/services': ServicesNamespace,
                                      '/sysinfo': SysinfoNamespace,
                                      '/widgets': WidgetNamespace})


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not found</h1>']


def main():
    logger.debug('Listening on port http://127.0.0.1:8080 and on port 10843 (flash policy server)')
    SocketIOServer(('127.0.0.1', 8001), Application(),
            resource="socket.io", policy_server=True).serve_forever()
