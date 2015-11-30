from gevent import monkey
monkey.patch_all()

import psutil
import re
import gevent
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

from django.conf import settings
from system.osi import (uptime, kernel_info)
from datetime import (datetime, timedelta)
from django.utils.timezone import utc
from storageadmin.models import Disk
from smart_manager.models import Service
from system.services import service_status
from cli.api_wrapper import APIWrapper
from system.pkg_mgmt import update_check
import logging
logger = logging.getLogger(__name__)


class DisksWidgetNamespace(BaseNamespace, BroadcastMixin):
    switch = False

    def recv_connect(self):
        self.switch = True
        self.spawn(self.send_top_disks)

    def recv_disconnect(self):
        logger.debug('disks namespace disconnected')
        self.switch = False
        self.disconnect()

    def send_top_disks(self):

        def disk_stats(prev_stats):
            # invoke body of disk_stats with empty cur_stats
            stats_file_path = '/proc/diskstats'
            cur_stats = {}
            interval = 1
            disks = [d.name for d in Disk.objects.all()]
            with open(stats_file_path) as stats_file:
                for line in stats_file.readlines():
                    fields = line.split()
                    if (fields[2] not in disks):
                        continue
                    cur_stats[fields[2]] = fields[3:]
            for disk in cur_stats.keys():
                if (disk in prev_stats):
                    prev = prev_stats[disk]
                    cur = cur_stats[disk]
                    data = []
                    for i in range(0, len(prev)):
                        if (i == 8):
                            avg_ios = (float(cur[i]) + float(prev[i]))/2
                            data.append(avg_ios)
                            continue
                        datum = None
                        if (cur[i] < prev[i]):
                            datum = float(cur[i])/interval
                        else:
                            datum = (float(cur[i]) - float(prev[i]))/interval
                        data.append(datum)
                    self.emit('diskWidget:top_disks', {
                        'key': 'diskWidget:top_disks', 'data': [{
                            'name': disk,
                            'reads_completed': data[0],
                            'reads_merged': data[1],
                            'sectors_read': data[2],
                            'ms_reading': data[3],
                            'writes_completed': data[4],
                            'writes_merged': data[5],
                            'sectors_written': data[6],
                            'ms_writing': data[7],
                            'ios_progress': data[8],
                            'ms_ios': data[9],
                            'weighted_ios': data[10],
                            'ts': str(datetime.utcnow().replace(tzinfo=utc))
                        }]
                    })
            return cur_stats

        def get_stats():
            cur_disk_stats = {}
            while self.switch:
                cur_disk_stats = disk_stats(cur_disk_stats)
                gevent.sleep(1)
        # Kick things off
        get_stats()


class CPUWidgetNamespace(BaseNamespace, BroadcastMixin):
    send_cpu = False

    def recv_connect(self):
        # Switch for emitting cpu data
        self.send_cpu = True
        self.spawn(self.send_cpu_data)

    def recv_disconnect(self):
        logger.debug('disconnect received')
        self.send_cpu = False
        self.disconnect()

    def send_cpu_data(self):
        while self.send_cpu:
            cpu_stats = {}
            cpu_stats['results'] = []
            vals = psutil.cpu_times_percent(percpu=True)
            ts = datetime.utcnow().replace(tzinfo=utc)
            for i, val in enumerate(vals):
                name = 'cpu%d' % i
                cpu_stats['results'].append({
                    'name': name, 'umode': val.user,
                    'umode_nice': val.nice, 'smode': val.system,
                    'idle': val.idle, 'ts': str(ts)
                })
            self.emit('cpuWidget:cpudata', {
                'key': 'cpuWidget:cpudata', 'data': cpu_stats
            })
            gevent.sleep(1)


class NetworkWidgetNamespace(BaseNamespace, BroadcastMixin):
    send = False

    def recv_connect(self):
        logger.debug('network stats connected')
        self.send = True
        self.spawn(self.network_stats)

    def recv_disconnect(self):
        logger.debug('network stats disconnected')
        self.send = False
        self.disconnect()

    def network_stats(self):
        from storageadmin.models import NetworkInterface

        def retrieve_network_stats(prev_stats):
            interfaces = [i.name for i in NetworkInterface.objects.all()]
            interval = 1
            cur_stats = {}
            with open('/proc/net/dev') as sfo:
                sfo.readline()
                sfo.readline()
                for l in sfo.readlines():
                    fields = l.split()
                    if (fields[0][:-1] not in interfaces):
                        continue
                    cur_stats[fields[0][:-1]] = fields[1:]
            ts = datetime.utcnow().replace(tzinfo=utc)
            if (isinstance(prev_stats, dict)):
                results = []
                for interface in cur_stats.keys():
                    if (interface in prev_stats):
                        data = map(lambda x, y: float(x)/interval if x < y else
                                   (float(x) - float(y))/interval,
                                   cur_stats[interface], prev_stats[interface])
                        results.append({
                            'device': interface, 'kb_rx': data[0],
                            'packets_rx': data[1], 'errs_rx': data[2],
                            'drop_rx': data[3], 'fifo_rx': data[4],
                            'frame': data[5], 'compressed_rx': data[6],
                            'multicast_rx': data[7], 'kb_tx': data[8],
                            'packets_tx': data[9], 'errs_tx': data[10],
                            'drop_tx': data[11], 'fifo_tx': data[12],
                            'colls': data[13], 'carrier': data[14],
                            'compressed_tx': data[15], 'ts': str(ts)
                        })
                self.emit('networkWidget:network', {
                    'key': 'networkWidget:network', 'data': {'results': results}
                })
            return cur_stats

        def send_network_stats():
            cur_stats = {}
            while self.send:
                cur_stats = retrieve_network_stats(cur_stats)
                gevent.sleep(1)
        send_network_stats()


class MemoryWidgetNamespace(BaseNamespace, BroadcastMixin):
    switch = False

    def recv_connect(self):
        self.switch = True
        self.spawn(self.send_meminfo_data)

    def recv_disconnect(self):
        self.switch = False
        self.disconnect()

    def send_meminfo_data(self):
        while self.switch:
            stats_file = '/proc/meminfo'
            (total, free, buffers, cached, swap_total, swap_free, active, inactive,
             dirty,) = (None,) * 9
            with open(stats_file) as sfo:
                for l in sfo.readlines():
                    if (re.match('MemTotal:', l) is not None):
                        total = int(l.split()[1])
                    elif (re.match('MemFree:', l) is not None):
                        free = int(l.split()[1])
                    elif (re.match('Buffers:', l) is not None):
                        buffers = int(l.split()[1])
                    elif (re.match('Cached:', l) is not None):
                        cached = int(l.split()[1])
                    elif (re.match('SwapTotal:', l) is not None):
                        swap_total = int(l.split()[1])
                    elif (re.match('SwapFree:', l) is not None):
                        swap_free = int(l.split()[1])
                    elif (re.match('Active:', l) is not None):
                        active = int(l.split()[1])
                    elif (re.match('Inactive:', l) is not None):
                        inactive = int(l.split()[1])
                    elif (re.match('Dirty:', l) is not None):
                        dirty = int(l.split()[1])
                        break  # no need to look at lines after dirty.
            ts = datetime.utcnow().replace(tzinfo=utc)
            self.emit('memoryWidget:memory', {
                'key': 'memoryWidget:memory', 'data': {'results': [{
                    'total': total, 'free': free, 'buffers': buffers,
                    'cached': cached, 'swap_total': swap_total,
                    'swap_free': swap_free, 'active': active,
                    'inactive': inactive, 'dirty': dirty, 'ts': str(ts)
                    }]
                }
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
        services = [s.name for s in Service.objects.all()]
        while True:
            data = {}
            for service in services:
                data[service] = {}
                output, error, return_code = service_status(service)
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
        self.aw = APIWrapper()
        logger.debug("Sysinfo has been initialized")

    # This function is run once on every connection
    def recv_connect(self):
        logger.debug("Sysinfo has connected")
        self.emit("sysinfo:sysinfo", {
            "key": "sysinfo:connected", "data": "connected"
        })
        self.start = True
        gevent.spawn(self.refresh_system)
        gevent.spawn(self.send_uptime)
        gevent.spawn(self.send_kernel_info)

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
                logger.error('Exception while gathering kernel info: %s' % e.__str__())
                # Emit an event to the front end to capture error report
                self.emit('sysinfo:kernel_error', {
                    'data': str(e),
                    'key': 'sysinfo:kernel_error'
                })
                self.error('unsupported_kernel', str(e))

    def refresh_system(self):
        cur_ts = datetime.utcnow()
        if ((cur_ts - self.environ['scan_ts']).total_seconds() < self.environ['scan_interval']):
            logger.debug('Skipping system state refresh as it was done less '
                         'than %d seconds ago.' % self.environ['scan_interval'])
            return
        self.update_storage_state()
        self.update_rockons()
        self.update_check()

    def update_rockons(self):
        try:
            self.aw.api_call('rockons/update', data=None, calltype='post', save_error=False)
            logger.debug('Updated Rock-on metadata.')
        except Exception, e:
            logger.debug('failed to update Rock-on metadata. low-level '
                         'exception: %s' % e.__str__())

    def update_storage_state(self):
        resources = [{'url': 'disks/scan',
                      'success': 'Disk state updated successfully',
                      'error': 'Failed to update disk state.'},
                     {'url': 'commands/refresh-pool-state',
                      'success': 'Pool state updated successfully',
                      'error': 'Failed to update pool state.'},
                     {'url': 'commands/refresh-share-state',
                      'success': 'Share state updated successfully',
                      'error': 'Failed to update share state.'},
                     {'url': 'commands/refresh-snapshot-state',
                      'success': 'Snapshot state updated successfully',
                      'error': 'Failed to update snapshot state.'},]
        for r in resources:
            try:
                self.aw.api_call(r['url'], data=None, calltype='post', save_error=False)
                logger.debug(r['success'])
            except Exception, e:
                logger.error('%s. exception: %s' % (r['error'], e.__str__()))

    def update_check(self):
        uinfo = update_check()
        self.emit('sysinfo:software-update', {
            'data': uinfo,
            'key': 'sysinfo:software-update'
        })
        logger.debug('sent update information %s' % repr(uinfo))

class Application(object):
    def __init__(self):
        self.buffer = []
        self.scan_interval = 300
        self.scan_ts = datetime.utcnow() - timedelta(seconds=self.scan_interval)

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
            environ['scan_ts'] = self.scan_ts
            environ['scan_interval'] = self.scan_interval
            cur_ts = datetime.utcnow()
            socketio_manage(environ, {'/services': ServicesNamespace,
                                      '/sysinfo': SysinfoNamespace,
                                      '/cpu-widget': CPUWidgetNamespace,
                                      '/memory-widget': MemoryWidgetNamespace,
                                      '/network-widget': NetworkWidgetNamespace,
                                      '/disk-widget': DisksWidgetNamespace,
            })
            if ((cur_ts - self.scan_ts).total_seconds() > self.scan_interval):
                self.scan_ts = cur_ts

def not_found(start_response):
    start_response('404 Not Found', [])
    return ['<h1>Not found</h1>']


def main():
    logger.debug('Listening on port http://127.0.0.1:8080 and on port 10843 (flash policy server)')
    SocketIOServer(('127.0.0.1', 8001), Application(),resource="socket.io",
                   policy_server=True).serve_forever()
