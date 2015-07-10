from gevent import monkey
monkey.patch_all()
import gevent
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

from django.conf import settings
from system.osi import (uptime, kernel_info)

import logging
logger = logging.getLogger(__name__)


class DashboardNamespace(BaseNamespace, BroadcastMixin):
    def initialize(self):
        pass


# Read more on gevent to make connections more robust
# Best practices for spawning greenlets
class SysinfoNamespace(BaseNamespace, BroadcastMixin):
    start = False
    supported_kernel = settings.SUPPORTED_KERNEL_VERSION
    kernel_func = 0

    def recv_connect(self):
        self.emit("sysinfo", {"key": "connected"})
        self.start = True
        gevent.spawn(self.send_uptime)
        self.kernel_func = gevent.spawn(self.send_kernel_info)

    def recv_disconnect(self):
        self.start = False
        self.disconnect(silent=True)

    def send_uptime(self):
        while self.start:
            if not self.start:
                break
            self.emit('uptime', {'key': uptime()})
            gevent.sleep(30)

    def send_kernel_info(self):
            try:
                self.emit('kernel_info', {'kernel_info':
                                          kernel_info(self.supported_kernel)})
                # Send information once per connection
                self.kernel_func.kill()
            except:
                # How do errors get reported to the front end?
                self.error('unsupported_kernel', 'the kernel is bad')


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
            socketio_manage(environ, {'/sysinfo': SysinfoNamespace})
            socketio_manage(environ, {'/dashboard': DashboardNamespace})


def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not found</h1>']


def main():
    logger.debug('Listening on port http://127.0.0.1:8080 and on port 10843 (flash policy server)')
    SocketIOServer(('127.0.0.1', 8001), Application(),
                            resource="socket.io", policy_server=True).serve_forever()
