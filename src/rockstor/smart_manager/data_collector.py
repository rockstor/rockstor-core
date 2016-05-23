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

from gevent import monkey
monkey.patch_all()

import psutil
import re
import json
import gevent
from socketio.server import SocketIOServer
from socketio import socketio_manage
from socketio.namespace import BaseNamespace
from socketio.mixins import BroadcastMixin

from gevent.subprocess import Popen, PIPE
from os import path
from sys import getsizeof
from glob import glob

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


class LogManagerNamespace(BaseNamespace, BroadcastMixin):

    def initialize(self):

        #Livereader subprocess append with self so accessible by all funcs
        self.livereader_process = None
        #Live reading switch to kill/stop tail -f process
        self.livereading = False
        #Set common vars used both for log reading and downloading
        self.system_logs = '/var/log/'
        self.rockstor_logs = '%svar/log/' % settings.ROOT_DIR
        self.samba_subd_logs = '%ssamba/' % self.system_logs
        self.nginx_subd_logs = '%snginx/' % self.system_logs

        self.readers = {'cat' : {'command' : '/usr/bin/cat', 'args' : '-n'},
               'tail200' : {'command' : '/usr/bin/tail', 'args' : '-n 200'},
               'tail30' : {'command' : '/usr/bin/tail', 'args' : '-n 30'},
               'tailf' : {'command' : '/usr/bin/tail', 'args' : '-f'}
        }
        
        self.logs = {'rockstor' : {'logfile' : 'rockstor.log', 'logdir' : self.rockstor_logs},
            'dmesg' : {'logfile' : 'dmesg', 'logdir' : self.system_logs},
            'nmbd' : {'logfile' : 'log.nmbd', 'logdir' : self.samba_subd_logs, 'rotatingdir' : 'old/'},
            'smbd' : {'logfile' : 'log.smbd', 'logdir' : self.samba_subd_logs, 'rotatingdir' : 'old/'},
            'winbindd' : {'logfile' : 'log.winbindd', 'logdir' : self.samba_subd_logs, 'rotatingdir' : 'old/',
                          'excluded' : ['dc-connect', 'idmap', 'locator']},
            'nginx' : {'logfile' : 'access.log', 'logdir' : self.nginx_subd_logs},
            'nginx_stdout' : {'logfile' : 'supervisord_nginx_stdout.log', 'logdir' : self.rockstor_logs},
            'nginx_stderr' : {'logfile' : 'supervisord_nginx_stderr.log', 'logdir' : self.rockstor_logs},
            'gunicorn' : {'logfile' : 'gunicorn.log', 'logdir' : self.rockstor_logs},
            'gunicorn_stdout' : {'logfile' : 'supervisord_gunicorn_stdout.log', 'logdir' : self.rockstor_logs},
            'gunicorn_stderr' : {'logfile' : 'supervisord_gunicorn_stderr.log', 'logdir' : self.rockstor_logs},
            'supervisord' : {'logfile' : 'supervisord.log', 'logdir' : self.rockstor_logs},
            'yum' : {'logfile' : 'yum.log', 'logdir' : self.system_logs},
        }
        
        self.tar_utility = ['/usr/bin/tar', 'czf']

    def recv_connect(self):

        #On first connection emit a welcome just to have a recv_connect func
        self.emit("logManager:logwelcome", {
            "key": "logManager:logwelcome", "data": "Welcome to Rockstor LogManager"
        })
        gevent.spawn(self.find_rotating_logs)

    def recv_disconnect(self):

        self.disconnect()
        #Func to secure tail -f reader
        #If browser close/crash/accidentally ends while a tail -f running,
        #this ensures running process to get stopped
        gevent.spawn(self.kill_live_reading)
    
    def build_log_path(self, selectedlog):
        
        return '%s%s' % (self.logs[selectedlog]['logdir'],self.logs[selectedlog]['logfile'])
    
    def kill_live_reading(self):

        #When user close modal log reader check livereading switch and livereader_process
        #Immediately set livereading switch to False and stop emitting to frontend
        #If livereader_process is None we were reading logs with cat, tail -n 200 or tail -n 30
        #Otherwise it was changed to a subprocess by tail -f, so we kill it and set back to None
        #to avoid other readers trying killing nothing
        self.livereading = False
        if self.livereader_process is not None:
            self.livereader_process.kill()
            self.livereader_process = None
            
        #Emit current state only for checking purpose, no funcs handle on frontend
        self.emit('logManager:logskilltailf', {
            'key' : 'logManager:logskilltailf', 'data': {
            'status' : self.livereading
            }
        })    
    
    def find_rotating_logs(self):
        
        #First build our rotated logs list, removing current log and
        #eventually excluded logs file
        #Collect logs key because iterating directly over dict doesn't let update it
        log_keys = sorted(list(self.logs.keys()))
        rotated_logs_list = []
        
        for log_key in log_keys:
            log = self.logs[log_key]['logdir']
            if ('rotatingdir' in self.logs[log_key]):
                log += self.logs[log_key]['rotatingdir']
            log += '%s*' % self.logs[log_key]['logfile']
            rotated_logs = sorted(glob(log), reverse=True)
            starting_log = self.build_log_path(log_key)
            #When looking for rotated logs we ask logname* and we get current log to, so we remove it
            if starting_log in rotated_logs:
                rotated_logs.remove(starting_log)
            if ('excluded' in self.logs[log_key]):
                rotated_logs = list(set(rotated_logs)-{l for e in self.logs[log_key]['excluded'] for l in rotated_logs if e in l})
            
            #For every list of rotated logs - grouped by current log -
            #Append each rotated log to self.logs dict and make it available for log reading/downloading
            #Build a rotated log list to be sent to client for frontend updates
            for current_rotated in rotated_logs:
                rotated_logfile, rotated_logdir = path.basename(current_rotated), ('%s/' % path.dirname(current_rotated))
                rotated_key = rotated_logfile.replace(self.logs[log_key]['logfile'], log_key)
                self.logs.update({rotated_key : {'logfile' : rotated_logfile, 'logdir' : rotated_logdir}})
                rotated_logs_list.append({'log' : rotated_key, 'logfamily' : log_key})
        
        self.emit('logManager:rotatedlogs', {'key': 'logManager:rotatedlogs', 'data': {'rotated_logs_list' : rotated_logs_list}})
        
    def on_livereading(self, action):

        gevent.spawn(self.kill_live_reading)

    def on_downloadlogs(self, logs_queued, recipient):

        def logs_downloader(logs_queued, recipient):
            #Build tar command with tar command and logs sent by client
            archive_path = '%ssrc/rockstor/logs/' % settings.ROOT_DIR
            archive_file = 'requested_logs.tgz'
            
            #If log download requested by Log Reader serve a personalized tgz file with log file name
            if (recipient == 'reader_response'):
                archive_file = '%s.tgz' % logs_queued[0]
            archive_path += archive_file
            download_command = []
            download_command.extend(self.tar_utility)
            download_command.append(archive_path)

            #Get every log location via logs dictionary
            for log in logs_queued:
                download_command.append(self.build_log_path(log))
            
            #Build download archive
            download_process = Popen(download_command, bufsize=1, stdout=PIPE)
            download_result = download_process.communicate()[0]

            #Return ready state for logs archive download specifying recipient (logManager or LogDownloader)
            self.emit('logManager:logsdownload', {
                'key': 'logManager:logsdownload', 'data': {
                'archive_name' : '/logs/%s' % archive_file,
                'recipient' : recipient
                }
            })
        
        gevent.spawn(logs_downloader, logs_queued, recipient)

    def on_readlog(self, reader, logfile):

        logs_loader = {'slow' : {'lines' : 200, 'sleep' : 0.50},
                   'fast' : {'lines' : 1, 'sleep' : 0.05},
        }

        def valid_log(logfile):
            #If file exist and size greater than 0 return true
            #else false and avoid processing
            if path.exists(logfile):
                return (path.getsize(logfile) > 0)
            else:
                return False
                
        def build_reader_command(reader):

            command = []
            command.append(self.readers[reader]['command'])
            #If our reader has opt args we add them to popen command
            if ('args' in self.readers[reader]):
                command.append(self.readers[reader]['args'])
            #Queue log file to popen command
            command.append(log_path)
            return command
            
        def static_reader(reader, log_path):
            if (valid_log(log_path)):#Log file exist and greater than 0, perform data collecting

                #Build reader command
                read_command = build_reader_command(reader)

                #Define popen process and once completed split stdout by lines
                reader_process = Popen(read_command, bufsize=1, stdout=PIPE)
                log_content = reader_process.communicate()[0]
                log_contentsize = getsizeof(log_content)
                log_content = log_content.splitlines(True)
                
                #Starting from content num of lines decide if serve it 1 line/time or in 200 lines chunks
                reader_type = 'fast' if (len(log_content) <= 200) else 'slow'
                chunk_size = logs_loader[reader_type]['lines']
                reader_sleep = logs_loader[reader_type]['sleep']
                log_content_chunks = [log_content[x:x+chunk_size] for x in xrange(0, len(log_content), chunk_size)]
                total_rows = len(log_content)

            else:#Log file missing or size 0, gently inform user
            
                #Log not exist or empty so we send fake values
                #for rows, chunks, etc to uniform data on existing functions
                #and avoid client side extra checks
                log_content = 'Selected log file is empty or doesn\'t exist'
                log_content = log_content.splitlines(True)
                total_rows = 1
                log_contentsize = getsizeof(log_content)
                log_content_chunks = []
                log_content_chunks.append(log_content)
                reader_sleep = 0
            
            #Serve each chunk with emit and sleep before next one to avoid client side browser overload
            current_rows = 0
            
            for data_chunks in log_content_chunks:
                chunk_content = ''.join(data_chunks)
                current_rows += len(data_chunks)
                self.emit('logManager:logcontent', {
                    'key': 'logManager:logcontent', 'data': {
                    'current_rows' : current_rows,
                    'total_rows' : total_rows,
                    'chunk_content' : chunk_content,
                    'content_size' : log_contentsize
                    }
                })
                gevent.sleep(reader_sleep)
        
        def live_reader(log_path):

            #Switch live reader state to True
            self.livereading = True
            
            #Build reader command from readers dict
            read_command = build_reader_command('tailf')

            self.livereader_process = Popen(read_command, bufsize=1, stdout=PIPE)
            while self.livereading:
                live_out = self.livereader_process.stdout.readline()
                self.emit('logManager:logcontent', {
                    'key': 'logManager:logcontent', 'data': {
                    'current_rows' : 1,
                    'total_rows' : 1,
                    'chunk_content' : live_out,
                    'content_size' : 1
                    }
                })

        log_path = self.build_log_path(logfile)

        if (reader == 'tailf'):
            gevent.spawn(live_reader, log_path)
        else:
            gevent.spawn(static_reader, reader, log_path)
        
    def on_getfilesize(self, logfile):

        def file_size(logfile):
            file_size = path.getsize(self.build_log_path(logfile))
            self.emit('logManager:logsize', {'key': 'logManager:logsize', 'data': file_size})
        
        gevent.spawn(file_size, logfile)

class DisksWidgetNamespace(BaseNamespace, BroadcastMixin):
    switch = False

    def recv_connect(self):
        self.switch = True
        self.spawn(self.send_top_disks)

    def recv_disconnect(self):
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
                            'ts': str(datetime.utcnow().replace(tzinfo=utc).isoformat())
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
        self.send_cpu = False
        self.disconnect()

    def send_cpu_data(self):
        while self.send_cpu:
            cpu_stats = {}
            cpu_stats['results'] = []
            vals = psutil.cpu_times_percent(percpu=True)
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
            for i, val in enumerate(vals):
                name = 'cpu%d' % i
                cpu_stats['results'].append({
                    'name': name, 'umode': val.user,
                    'umode_nice': val.nice, 'smode': val.system,
                    'idle': val.idle, 'ts': str(ts)
                })
                logger.debug('Time is %s' % ts)
            self.emit('cpuWidget:cpudata', {
                'key': 'cpuWidget:cpudata', 'data': cpu_stats
            })
            gevent.sleep(1)


class NetworkWidgetNamespace(BaseNamespace, BroadcastMixin):
    send = False

    def recv_connect(self):
        self.send = True
        self.spawn(self.network_stats)

    def recv_disconnect(self):
        self.send = False
        self.disconnect()

    def network_stats(self):
        from storageadmin.models import NetworkDevice

        def retrieve_network_stats(prev_stats):
            interfaces = [i.name for i in NetworkDevice.objects.all()]
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
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
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
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
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

    def recv_connect(self):
        self.emit('services:connected', {
            'key': 'services:connected', 'data': 'connected'
        })
        self.spawn(self.send_service_statuses)

    def recv_disconnect(self):
        self.disconnect()

    def send_service_statuses(self):
        while True:
            data = {}
            for service in Service.objects.all():
                config = None
                if (service.config is not None):
                    try:
                        config = json.loads(service.config)
                    except Exception, e:
                        logger.error('Exception while loading config of '
                                     'Service(%s): %s' %
                                     (service.name, e.__str__()))
                data[service.name] = {}
                output, error, return_code = service_status(service.name, config=config)
                data[service.name]['running'] = return_code

            self.emit('services:get_services', {
                'data': data, 'key': 'services:get_services'
            })
            gevent.sleep(15)


class SysinfoNamespace(BaseNamespace, BroadcastMixin):
    start = False
    supported_kernel = settings.SUPPORTED_KERNEL_VERSION

    # Called before the connection is established
    def initialize(self):
        self.aw = APIWrapper()

    # This function is run once on every connection
    def recv_connect(self):
        self.emit("sysinfo:sysinfo", {
            "key": "sysinfo:connected", "data": "connected"
        })
        self.start = True
        gevent.spawn(self.update_storage_state)
        gevent.spawn(self.update_check)
        gevent.spawn(self.update_rockons)
        gevent.spawn(self.send_uptime)
        gevent.spawn(self.send_kernel_info)
        gevent.spawn(self.prune_logs)

    # Run on every disconnect
    def recv_disconnect(self):
        self.start = False
        self.disconnect()

    def send_uptime(self):
        # Seems redundant
        while self.start:
            self.emit('sysinfo:uptime', {
                'data': uptime(), 'key': 'sysinfo:uptime'
            })
            gevent.sleep(60)

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

    def update_rockons(self):
        try:
            self.aw.api_call('rockons/update', data=None, calltype='post', save_error=False)
        except Exception, e:
            logger.error('failed to update Rock-on metadata. low-level '
                         'exception: %s' % e.__str__())

    def update_storage_state(self):
        #update storage state once a minute as long as
        #there is a client connected.
        while self.start:
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
                except Exception, e:
                    logger.error('%s. exception: %s' % (r['error'], e.__str__()))
            gevent.sleep(60)

    def update_check(self):
        uinfo = update_check()
        self.emit('sysinfo:software-update', {
            'data': uinfo,
            'key': 'sysinfo:software-update'
        })

    def prune_logs(self):
        while self.start:
            self.aw.api_call('sm/tasks/log/prune', data=None, calltype='post', save_error=False)
            gevent.sleep(3600)

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
                                      '/logmanager': LogManagerNamespace,
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
