"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

# @todo: Let's deprecate gevent in favor of django channels and we won't need
# monkey patching and flake8 exceptions.
from gevent import monkey

from fs.btrfs import degraded_pools_found

monkey.patch_all()

import psutil  # noqa E402
import re  # noqa E402
import json  # noqa E402
import gevent  # noqa E402
import socketio  # noqa E402
from gevent import pywsgi  # noqa E402
from geventwebsocket.handler import WebSocketHandler  # noqa E402

from gevent.subprocess import Popen, PIPE  # noqa E402
from os import path  # noqa E402
from sys import getsizeof  # noqa E402
from glob import glob  # noqa E402

from system.pinmanager import (
    has_pincard,
    username_to_uid,  # noqa E402
    email_notification_enabled,
    reset_random_pins,
    generate_otp,
)

from django.conf import settings  # noqa E402
from system.osi import uptime, kernel_info, get_byid_name_map  # noqa E402
from datetime import datetime, timedelta  # noqa E402
import time  # noqa E402
from django.utils.timezone import utc  # noqa E402
from storageadmin.models import Disk, Pool  # noqa E402
from smart_manager.models import Service  # noqa E402
from system.services import service_status  # noqa E402
from cli.api_wrapper import APIWrapper  # noqa E402
from system.pkg_mgmt import rockstor_pkg_update_check, pkg_update_check  # noqa E402
import distro
import logging  # noqa E402

logger = logging.getLogger(__name__)


class RockstorIO(socketio.Namespace):
    "RockstorIO socketio.NameSpace SubClass"

    def __init__(self, *args, **kwargs):

        super(RockstorIO, self).__init__(*args, **kwargs)
        self.threads = {}

    def cleanup(self, sid):

        if sid in self.threads:
            gevent.killall(self.threads[sid])
            del self.threads[sid]

    def spawn(self, func, sid, *args, **kwargs):

        thread = gevent.spawn(func, *args, **kwargs)
        if sid in self.threads:
            self.threads[sid].append(thread)
        else:
            self.threads[sid] = [thread]


class PincardManagerNamespace(RockstorIO):
    def on_connect(self, sid, environ):

        self.aw = APIWrapper()
        self.emit(
            "pincardwelcome",
            {
                "key": "pincardManager:pincardwelcome",
                "data": "Welcome to Rockstor PincardManager",
            },
        )

    def on_disconnect(self, sid):

        self.pins_user_uname = None
        self.pins_user_uid = None
        self.pins_check = None
        self.pass_reset_time = None
        self.otp = "none"
        self.cleanup(sid)

    def on_generatepincard(self, sid, uid):
        def create_pincard(uid):

            try:
                url = "pincardmanager/create/%s" % uid
                new_pincard = self.aw.api_call(
                    url, data=None, calltype="post", save_error=False
                )
                self.emit(
                    "newpincard",
                    {"key": "pincardManager:newpincard", "data": new_pincard},
                )
            except Exception as e:
                logger.error(
                    "Failed to create Pincard with exception: %s" % e.__str__()
                )

        self.spawn(create_pincard, sid, uid)

    def on_haspincard(self, sid, user):
        def check_has_pincard(user):

            pins = []
            otp = False
            self.pins_check = []
            self.otp = "none"
            # Convert from username to uid and if user exist check for
            # pincardManager We don't tell to frontend if a user exists or not
            # to avoid exposure to security flaws/brute forcing etc
            uid = username_to_uid(user)
            user_exist = True if uid is not None else False
            user_has_pincard = False
            # If user exists we check if has a pincard
            if user_exist:
                user_has_pincard = has_pincard(uid)
            # If user is root / uid 0 we check also if email notifications are
            # enabled If not user won't be able to reset password with pincard
            if uid == 0:
                user_has_pincard = (
                    user_has_pincard and email_notification_enabled()
                )  # noqa E501

            if user_has_pincard:
                self.pins_user_uname = user
                self.pins_user_uid = uid
                pins = reset_random_pins(uid)
                for pin in pins:
                    self.pins_check.append(pin["pin_number"])

                # Set current time, user will have max 3 min to reset password
                self.pass_reset_time = datetime.now()

                if uid == 0:
                    self.otp = generate_otp(user)
                    otp = True

            self.emit(
                "haspincard",
                {
                    "key": "pincardManager:haspincard",
                    "has_pincard": user_has_pincard,
                    "pins_check": pins,
                    "otp": otp,
                },
            )

        self.spawn(check_has_pincard, sid, user)

    def on_passreset(self, sid, pinlist, otp="none"):
        def password_reset(pinlist, otp):

            reset_status = False
            reset_response = None

            # On pass reset first we check for otp If not required none = none,
            # otherwhise sent val has to match stored one
            if otp == self.otp:

                # If otp is ok we check for elapsed time to be < 3 mins
                elapsed_time = (
                    datetime.now() - self.pass_reset_time
                ).total_seconds()  # noqa E501
                if elapsed_time < 180:

                    # If received pins equal expected pins, check for values
                    # via reset_password func
                    if all(int(key) in self.pins_check for key in pinlist):
                        data = {"uid": self.pins_user_uid, "pinlist": pinlist}
                        url = "pincardmanager/reset/%s" % self.pins_user_uname
                        headers = {"content-type": "application/json"}
                        reset_data = self.aw.api_call(
                            url,
                            data=data,
                            calltype="post",
                            headers=headers,
                            save_error=False,
                        )
                        reset_response = reset_data["response"]
                        reset_status = reset_data["status"]
                    else:
                        reset_response = (
                            "Received pins set differs from "
                            "expected one. Password reset "
                            "denied"
                        )
                else:
                    reset_response = (
                        "Pincard 3 minutes reset time has "
                        "expired. Password reset denied"
                    )
            else:
                reset_response = "Sent OTP doesn't match. Password reset denied"

            self.emit(
                "passresetresponse",
                {
                    "key": "pincardManager:passresetresponse",
                    "response": reset_response,
                    "status": reset_status,
                },
            )

        self.spawn(password_reset, sid, pinlist, otp)


class LogManagerNamespace(RockstorIO):

    # Livereader subprocess append with self so accessible by all funcs
    livereader_process = None
    # Live reading switch to kill/stop tail -f process
    livereading = False
    # Set common vars used both for log reading and downloading
    system_logs = "/var/log/"
    rockstor_logs = "%svar/log/" % settings.ROOT_DIR
    samba_subd_logs = "%ssamba/" % system_logs
    nginx_subd_logs = "%snginx/" % system_logs

    readers = {
        "cat": {"command": "/usr/bin/cat", "args": "-n"},
        "tail200": {"command": "/usr/bin/tail", "args": "-n 200"},
        "tail30": {"command": "/usr/bin/tail", "args": "-n 30"},
        "tailf": {"command": "/usr/bin/tail", "args": "-f"},
    }

    logs = {
        "rockstor": {"logfile": "rockstor.log", "logdir": rockstor_logs},
        "dmesg": {"logfile": "dmesg", "logdir": system_logs},
        "nmbd": {
            "logfile": "log.nmbd",
            "logdir": samba_subd_logs,
            "rotatingdir": "old/",
        },
        "smbd": {
            "logfile": "log.smbd",
            "logdir": samba_subd_logs,
            "rotatingdir": "old/",
        },
        "winbindd": {
            "logfile": "log.winbindd",
            "logdir": samba_subd_logs,
            "rotatingdir": "old/",
            "excluded": ["dc-connect", "idmap", "locator"],
        },
        "nginx": {"logfile": "access.log", "logdir": nginx_subd_logs},
        "nginx_stdout": {
            "logfile": "supervisord_nginx_stdout.log",
            "logdir": rockstor_logs,
        },
        "nginx_stderr": {
            "logfile": "supervisord_nginx_stderr.log",
            "logdir": rockstor_logs,
        },
        "gunicorn": {"logfile": "gunicorn.log", "logdir": rockstor_logs},
        "gunicorn_stdout": {
            "logfile": "supervisord_gunicorn_stdout.log",
            "logdir": rockstor_logs,
        },
        "gunicorn_stderr": {
            "logfile": "supervisord_gunicorn_stderr.log",
            "logdir": rockstor_logs,
        },
        "supervisord": {"logfile": "supervisord.log", "logdir": rockstor_logs},
        "yum": {"logfile": "yum.log", "logdir": system_logs},
    }

    tar_utility = ["/usr/bin/tar", "czf"]

    def on_connect(self, sid, environ):

        # On first connection emit a welcome just to have a recv_connect func
        self.emit(
            "logwelcome",
            {"key": "logManager:logwelcome", "data": "Welcome to Rockstor LogManager"},
        )
        self.spawn(self.find_rotating_logs, sid)

    def on_disconnect(self, sid):

        # Func to secure tail -f reader If browser close/crash/accidentally
        # ends while a tail -f running, this ensures running process to get
        # stopped
        self.spawn(self.kill_live_reading, sid)
        self.cleanup(sid)

    def build_log_path(self, selectedlog):

        return "{0}{1}".format(
            self.logs[selectedlog]["logdir"], self.logs[selectedlog]["logfile"]
        )

    def kill_live_reading(self):

        # When user close modal log reader check livereading switch and
        # livereader_process Immediately set livereading switch to False and
        # stop emitting to frontend If livereader_process is None we were
        # reading logs with cat, tail -n 200 or tail -n 30 Otherwise it was
        # changed to a subprocess by tail -f, so we kill it and set back to
        # None to avoid other readers trying killing nothing
        self.livereading = False
        if self.livereader_process is not None:
            self.livereader_process.kill()
            self.livereader_process = None

    def find_rotating_logs(self):

        # First build our rotated logs list, removing current log and
        # eventually excluded logs file Collect logs key because iterating
        # directly over dict doesn't let update it
        log_keys = sorted(list(self.logs.keys()))
        rotated_logs_list = []

        for log_key in log_keys:
            log = self.logs[log_key]["logdir"]
            if "rotatingdir" in self.logs[log_key]:
                log += self.logs[log_key]["rotatingdir"]
            log += "%s*" % self.logs[log_key]["logfile"]
            rotated_logs = sorted(glob(log), reverse=True)
            starting_log = self.build_log_path(log_key)
            # When looking for rotated logs we ask logname* and we get current
            # log to, so we remove it
            if starting_log in rotated_logs:
                rotated_logs.remove(starting_log)
            if "excluded" in self.logs[log_key]:
                rotated_logs = list(
                    set(rotated_logs)
                    - {
                        l
                        for e in self.logs[log_key]["excluded"]
                        for l in rotated_logs
                        if e in l
                    }
                )  # noqa E501

            # For every list of rotated logs - grouped by current log - Append
            # each rotated log to self.logs dict and make it available for log
            # reading/downloading Build a rotated log list to be sent to client
            # for frontend updates
            for current_rotated in rotated_logs:
                rotated_logfile = path.basename(current_rotated)
                rotated_logdir = "%s/" % path.dirname(current_rotated)
                rotated_key = rotated_logfile.replace(
                    self.logs[log_key]["logfile"], log_key
                )
                self.logs.update(
                    {
                        rotated_key: {
                            "logfile": rotated_logfile,
                            "logdir": rotated_logdir,
                        }
                    }
                )
                rotated_logs_list.append({"log": rotated_key, "logfamily": log_key})

        self.emit(
            "rotatedlogs",
            {
                "key": "logManager:rotatedlogs",
                "data": {"rotated_logs_list": rotated_logs_list},
            },
        )

    def on_livereading(self, sid, action):

        self.spawn(self.kill_live_reading, sid)

    def on_downloadlogs(self, sid, logs_queued, recipient):
        def logs_downloader(logs_queued, recipient):
            # Build tar command with tar command and logs sent by client
            archive_path = "%ssrc/rockstor/logs/" % settings.ROOT_DIR
            archive_file = "requested_logs.tgz"

            # If log download requested by Log Reader serve a personalized tgz
            # file with log file name
            if recipient == "reader_response":
                archive_file = "%s.tgz" % logs_queued[0]
            archive_path += archive_file
            download_command = []
            download_command.extend(self.tar_utility)
            download_command.append(archive_path)

            # Get every log location via logs dictionary
            for log in logs_queued:
                download_command.append(self.build_log_path(log))

            # Build download archive
            download_process = Popen(download_command, bufsize=1, stdout=PIPE)
            download_process.communicate()

            # Return ready state for logs archive download specifying recipient
            # (logManager or LogDownloader)
            self.emit(
                "logsdownload",
                {
                    "key": "logManager:logsdownload",
                    "data": {
                        "archive_name": "/logs/%s" % archive_file,
                        "recipient": recipient,
                    },
                },
            )

        self.spawn(logs_downloader, sid, logs_queued, recipient)

    def on_readlog(self, sid, reader, logfile):

        logs_loader = {
            "slow": {"lines": 200, "sleep": 0.50},
            "fast": {"lines": 1, "sleep": 0.05},
        }

        def valid_log(logfile):
            # If file exist and size greater than 0 return true
            # else false and avoid processing
            if path.exists(logfile):
                return path.getsize(logfile) > 0
            else:
                return False

        def build_reader_command(reader):

            command = []
            command.append(self.readers[reader]["command"])
            # If our reader has opt args we add them to popen command
            if "args" in self.readers[reader]:
                command.append(self.readers[reader]["args"])
            # Queue log file to popen command
            command.append(log_path)
            return command

        def static_reader(reader, log_path):
            if valid_log(log_path):
                # Log file exist and greater than 0, perform data collecting

                # Build reader command
                read_command = build_reader_command(reader)

                # Define popen process and once completed split stdout by lines
                reader_process = Popen(read_command, bufsize=1, stdout=PIPE)
                log_content = reader_process.communicate()[0]
                log_contentsize = getsizeof(log_content)
                log_content = log_content.splitlines(True)

                # Starting from content num of lines decide if serve it 1
                # line/time or in 200 lines chunks
                reader_type = "fast" if (len(log_content) <= 200) else "slow"
                chunk_size = logs_loader[reader_type]["lines"]
                reader_sleep = logs_loader[reader_type]["sleep"]
                log_content_chunks = [
                    log_content[x : x + chunk_size]
                    for x in xrange(0, len(log_content), chunk_size)
                ]  # noqa F821
                total_rows = len(log_content)

            else:  # Log file missing or size 0, gently inform user

                # Log not exist or empty so we send fake values for rows,
                # chunks, etc to uniform data on existing functions and avoid
                # client side extra checks
                log_content = "Selected log file is empty or doesn't exist"
                log_content = log_content.splitlines(True)
                total_rows = 1
                log_contentsize = getsizeof(log_content)
                log_content_chunks = []
                log_content_chunks.append(log_content)
                reader_sleep = 0

            # Serve each chunk with emit and sleep before next one to avoid
            # client side browser overload
            current_rows = 0

            for data_chunks in log_content_chunks:
                chunk_content = "".join(data_chunks)
                current_rows += len(data_chunks)
                self.emit(
                    "logcontent",
                    {
                        "key": "logManager:logcontent",
                        "data": {
                            "current_rows": current_rows,
                            "total_rows": total_rows,
                            "chunk_content": chunk_content,
                            "content_size": log_contentsize,
                        },
                    },
                )
                gevent.sleep(reader_sleep)

        def live_reader(log_path):

            # Switch live reader state to True
            self.livereading = True

            # Build reader command from readers dict
            read_command = build_reader_command("tailf")

            self.livereader_process = Popen(read_command, bufsize=1, stdout=PIPE)
            while self.livereading:
                live_out = self.livereader_process.stdout.readline()
                self.emit(
                    "logcontent",
                    {
                        "key": "logManager:logcontent",
                        "data": {
                            "current_rows": 1,
                            "total_rows": 1,
                            "chunk_content": live_out,
                            "content_size": 1,
                        },
                    },
                )

        log_path = self.build_log_path(logfile)

        if reader == "tailf":
            self.spawn(live_reader, sid, log_path)
        else:
            self.spawn(static_reader, sid, reader, log_path)

    def on_getfilesize(self, sid, logfile):
        def file_size(logfile):

            file_size = path.getsize(self.build_log_path(logfile))
            self.emit("logsize", {"key": "logManager:logsize", "data": file_size})

        self.spawn(file_size, sid, logfile)


class DisksWidgetNamespace(RockstorIO):

    switch = False
    byid_disk_map = {}

    def on_connect(self, sid, environ):

        self.byid_disk_map = get_byid_name_map()
        self.switch = True
        self.spawn(self.send_top_disks, sid)

    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.switch = False

    def send_top_disks(self):
        def disk_stats(prev_stats):

            disks_stats = []
            # invoke body of disk_stats with empty cur_stats
            stats_file_path = "/proc/diskstats"
            cur_stats = {}
            interval = 1
            # TODO: Consider refactoring the following to use Disk.temp_name or
            # TODO: building byid_disk_map from the same. Ideally we would have
            # TODO: performance testing in place prior to this move.
            # Build a list of our db's disk names, now in by-id type format.
            disks = [d.name for d in Disk.objects.all()]
            # /proc/diskstats has lines of the following form:
            #  8      64 sde 1034 0 9136 702 0 0 0 0 0 548 702
            #  8      65 sde1 336 0 2688 223 0 0 0 0 0 223 223
            with open(stats_file_path) as stats_file:
                for line in stats_file.readlines():
                    fields = line.split()
                    # As the /proc/diskstats lines contain transient type names
                    # we need to convert those to our by-id db names.
                    byid_name = self.byid_disk_map[fields[2]]
                    if byid_name not in disks:
                        # the disk name in this line is not one in our db so
                        # ignore it and move to the next line.
                        continue
                    cur_stats[byid_name] = fields[3:]
            for disk in cur_stats.keys():
                if disk in prev_stats:
                    prev = prev_stats[disk]
                    cur = cur_stats[disk]
                    data = []
                    for i in range(0, len(prev)):
                        if i == 8:
                            avg_ios = (float(cur[i]) + float(prev[i])) / 2
                            data.append(avg_ios)
                            continue
                        datum = None
                        if cur[i] < prev[i]:
                            datum = float(cur[i]) / interval
                        else:
                            datum = (float(cur[i]) - float(prev[i])) / interval
                        data.append(datum)
                    disks_stats.append(
                        {
                            "name": disk,
                            "reads_completed": data[0],
                            "reads_merged": data[1],
                            "sectors_read": data[2],
                            "ms_reading": data[3],
                            "writes_completed": data[4],
                            "writes_merged": data[5],
                            "sectors_written": data[6],
                            "ms_writing": data[7],
                            "ios_progress": data[8],
                            "ms_ios": data[9],
                            "weighted_ios": data[10],
                            "ts": str(
                                datetime.utcnow().replace(tzinfo=utc).isoformat()
                            ),  # noqa E501
                        }
                    )

            self.emit("top_disks", {"key": "diskWidget:top_disks", "data": disks_stats})
            return cur_stats

        def get_stats():
            cur_disk_stats = {}
            while self.switch:
                cur_disk_stats = disk_stats(cur_disk_stats)
                gevent.sleep(1)

        # Kick things off
        get_stats()


class CPUWidgetNamespace(RockstorIO):

    send_cpu = False

    def on_connect(self, sid, environ):

        # Switch for emitting cpu data
        self.send_cpu = True
        self.spawn(self.send_cpu_data, sid)

    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.send_cpu = False

    def send_cpu_data(self):

        while self.send_cpu:
            cpu_stats = {}
            cpu_stats["results"] = []
            vals = psutil.cpu_times_percent(percpu=True)
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
            for i, val in enumerate(vals):
                name = "cpu%d" % i
                cpu_stats["results"].append(
                    {
                        "name": name,
                        "umode": val.user,
                        "umode_nice": val.nice,
                        "smode": val.system,
                        "idle": val.idle,
                        "ts": str(ts),
                    }
                )
            self.emit("cpudata", {"key": "cpuWidget:cpudata", "data": cpu_stats})
            gevent.sleep(1)


class NetworkWidgetNamespace(RockstorIO):

    send = False

    def on_connect(self, sid, environ):

        self.send = True
        self.spawn(self.network_stats, sid)

    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.send = False

    def network_stats(self):

        from storageadmin.models import NetworkDevice

        def retrieve_network_stats(prev_stats):

            interfaces = [i.name for i in NetworkDevice.objects.all()]
            interval = 1
            cur_stats = {}
            with open("/proc/net/dev") as sfo:
                sfo.readline()
                sfo.readline()
                for l in sfo.readlines():
                    fields = l.split()
                    if fields[0][:-1] not in interfaces:
                        continue
                    cur_stats[fields[0][:-1]] = fields[1:]
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
            if isinstance(prev_stats, dict):
                results = []
                for interface in cur_stats.keys():
                    if interface in prev_stats:
                        data = map(
                            lambda x, y: float(x) / interval
                            if x < y
                            else (float(x) - float(y)) / interval,
                            cur_stats[interface],
                            prev_stats[interface],
                        )
                        results.append(
                            {
                                "device": interface,
                                "kb_rx": data[0],
                                "packets_rx": data[1],
                                "errs_rx": data[2],
                                "drop_rx": data[3],
                                "fifo_rx": data[4],
                                "frame": data[5],
                                "compressed_rx": data[6],
                                "multicast_rx": data[7],
                                "kb_tx": data[8],
                                "packets_tx": data[9],
                                "errs_tx": data[10],
                                "drop_tx": data[11],
                                "fifo_tx": data[12],
                                "colls": data[13],
                                "carrier": data[14],
                                "compressed_tx": data[15],
                                "ts": str(ts),
                            }
                        )
                if len(results) > 0:
                    self.emit(
                        "network",
                        {"key": "networkWidget:network", "data": {"results": results}},
                    )
            return cur_stats

        def send_network_stats():

            cur_stats = {}
            while self.send:
                cur_stats = retrieve_network_stats(cur_stats)
                gevent.sleep(1)

        send_network_stats()


class MemoryWidgetNamespace(RockstorIO):

    switch = False

    def on_connect(self, sid, environ):

        self.switch = True
        self.spawn(self.send_meminfo_data, sid)

    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.switch = False

    def send_meminfo_data(self):

        while self.switch:
            stats_file = "/proc/meminfo"
            (
                total,
                free,
                buffers,
                cached,
                swap_total,
                swap_free,
                active,
                inactive,
                dirty,
            ) = (None,) * 9
            with open(stats_file) as sfo:
                for l in sfo.readlines():
                    if re.match("MemTotal:", l) is not None:
                        total = int(l.split()[1])
                    elif re.match("MemFree:", l) is not None:
                        free = int(l.split()[1])
                    elif re.match("Buffers:", l) is not None:
                        buffers = int(l.split()[1])
                    elif re.match("Cached:", l) is not None:
                        cached = int(l.split()[1])
                    elif re.match("SwapTotal:", l) is not None:
                        swap_total = int(l.split()[1])
                    elif re.match("SwapFree:", l) is not None:
                        swap_free = int(l.split()[1])
                    elif re.match("Active:", l) is not None:
                        active = int(l.split()[1])
                    elif re.match("Inactive:", l) is not None:
                        inactive = int(l.split()[1])
                    elif re.match("Dirty:", l) is not None:
                        dirty = int(l.split()[1])
                        break  # no need to look at lines after dirty.
            ts = datetime.utcnow().replace(tzinfo=utc).isoformat()
            self.emit(
                "memory",
                {
                    "key": "memoryWidget:memory",
                    "data": {
                        "results": [
                            {
                                "total": total,
                                "free": free,
                                "buffers": buffers,
                                "cached": cached,
                                "swap_total": swap_total,
                                "swap_free": swap_free,
                                "active": active,
                                "inactive": inactive,
                                "dirty": dirty,
                                "ts": str(ts),
                            }
                        ]
                    },
                },
            )
            gevent.sleep(1)


class ServicesNamespace(RockstorIO):

    start = False

    def on_connect(self, sid, environ):

        self.emit("connected", {"key": "services:connected", "data": "connected"})
        self.start = True
        self.spawn(self.send_service_statuses, sid)

    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.start = False

    def send_service_statuses(self):

        while self.start:

            data = {}
            for service in Service.objects.all():
                config = None
                if service.config is not None:
                    try:
                        config = json.loads(service.config)
                    except Exception as e:
                        logger.error(
                            "Exception while loading config of "
                            "Service(%s): %s" % (service.name, e.__str__())
                        )
                data[service.name] = {}
                output, error, return_code = service_status(service.name, config=config)
                data[service.name]["running"] = return_code

            self.emit("get_services", {"data": data, "key": "services:get_services"})
            gevent.sleep(15)


class SysinfoNamespace(RockstorIO):

    start = False
    supported_kernel = settings.SUPPORTED_KERNEL_VERSION
    os_distro_name = settings.OS_DISTRO_NAME

    # This function is run once on every connection
    def on_connect(self, sid, environ):

        self.aw = APIWrapper()
        self.emit("connected", {"key": "sysinfo:connected", "data": "connected"})
        self.start = True
        self.spawn(self.update_storage_state, sid)
        self.spawn(self.update_check, sid)
        self.spawn(self.yum_updates, sid)
        self.spawn(self.update_rockons, sid)
        self.spawn(self.send_kernel_info, sid)
        self.spawn(self.prune_logs, sid)
        self.spawn(self.send_localtime, sid)
        self.spawn(self.send_uptime, sid)
        self.spawn(self.send_distroinfo, sid)
        self.spawn(self.shutdown_status, sid)
        self.spawn(self.pool_degraded_status, sid)
        self.spawn(self.pool_dev_stats, sid)

    # Run on every disconnect
    def on_disconnect(self, sid):

        self.cleanup(sid)
        self.start = False

    def send_uptime(self):

        while self.start:
            self.emit("uptime", {"key": "sysinfo:uptime", "data": uptime()})
            gevent.sleep(60)

    def send_distroinfo(self):
        while self.start:
            data = {"distro": self.os_distro_name, "version": distro.version()}
            self.emit("distro_info", {"key": "sysinfo:distro_info", "data": data})
            gevent.sleep(600)

    def send_localtime(self):

        while self.start:

            self.emit(
                "localtime",
                {"key": "sysinfo:localtime", "data": time.strftime("%H:%M (%z %Z)")},
            )
            gevent.sleep(40)

    def send_kernel_info(self):

        try:
            self.emit(
                "kernel_info",
                {
                    "key": "sysinfo:kernel_info",
                    "data": kernel_info(self.supported_kernel),
                },
            )
            # kernel_info() in above raises an Exception if the running
            # kernel != supported kernel and so:
        except Exception as e:
            logger.error("Exception while gathering kernel info: %s" % e.__str__())
            # Emit an event to the front end to capture error report
            self.emit("kernel_error", {"key": "sysinfo:kernel_error", "data": str(e)})
            self.error("unsupported_kernel", str(e))

    def update_rockons(self):

        try:
            self.aw.api_call(
                "rockons/update", data=None, calltype="post", save_error=False
            )
        except Exception as e:
            logger.error(
                "failed to update Rock-on metadata. low-level "
                "exception: %s" % e.__str__()
            )

    def update_storage_state(self):
        # update storage state once a minute as long as
        # there is a client connected.
        while self.start:
            resources = [
                {
                    "url": "disks/scan",
                    "success": "Disk state updated successfully",
                    "error": "Failed to update disk state.",
                },
                {
                    "url": "commands/refresh-pool-state",
                    "success": "Pool state updated successfully",
                    "error": "Failed to update pool state.",
                },
                {
                    "url": "commands/refresh-share-state",
                    "success": "Share state updated successfully",
                    "error": "Failed to update share state.",
                },
                {
                    "url": "commands/refresh-snapshot-state",
                    "success": "Snapshot state updated successfully",
                    "error": "Failed to update snapshot state.",
                },
            ]
            for r in resources:
                try:
                    self.aw.api_call(
                        r["url"], data=None, calltype="post", save_error=False
                    )
                except Exception as e:
                    logger.error("%s. exception: %s" % (r["error"], e.__str__()))
            gevent.sleep(60)

    def update_check(self):

        uinfo = rockstor_pkg_update_check()
        self.emit("software_update", {"key": "sysinfo:software_update", "data": uinfo})

    def yum_updates(self):

        while self.start:
            packages = pkg_update_check()
            data = {}
            if packages:  # Non empty lists are True.
                data["yum_updates"] = True
            else:
                data["yum_updates"] = False
            data["packages"] = packages
            self.emit("yum_updates", {"key": "sysinfo:yum_updates", "data": data})
            gevent.sleep(1800)  # 1800 seconds = 30 mins

    def on_runyum(self, sid):
        def launch_yum():

            try:
                data = {"yum_updating": False, "yum_updates": False}
                self.aw.api_call(
                    "commands/update", data=None, calltype="post", save_error=False
                )
                self.emit("yum_updates", {"key": "sysinfo:yum_updates", "data": data})
            except Exception as e:
                logger.error("Unable to perform Package Updates: %s" % e.__str__())

        self.spawn(launch_yum, sid)

    def prune_logs(self):

        while self.start:
            self.aw.api_call(
                "sm/tasks/log/prune", data=None, calltype="post", save_error=False
            )
            gevent.sleep(3600)

    def shutdown_status(self):

        while self.start:
            data = {}
            output, error, return_code = service_status("systemd-shutdownd")
            data["status"] = return_code
            if return_code == 0:
                for row in output:
                    if re.search("Status", row) is not None:
                        data["message"] = row.split(":", 1)[1]

            self.emit(
                "shutdown_status", {"key": "sysinfo:shutdown_status", "data": data}
            )

            gevent.sleep(30)

    def pool_degraded_status(self):

        # Examples of data.message:
        # "Pools found degraded: (2) unimported"
        # "Pools found degraded: (rock-pool)"
        # "Pools found degraded: (rock-pool, rock-pool-3)"
        # "Pools found degraded: (rock-pool, rock-pool-3), plus (1) unimported"
        while self.start:
            data = {"status": "OK"}
            deg_pools_count = degraded_pools_found()
            if deg_pools_count > 0:
                data["status"] = "degraded"
                data["message"] = "Pools found degraded: "
                labels = []
                for p in Pool.objects.all():
                    if p.has_missing_dev:
                        deg_pools_count -= 1
                        labels.append(p.name)
                if labels != []:
                    data["message"] += "({})".format(", ".join(labels))
                if deg_pools_count > 0:
                    # we have degraded un-managed pools, add this info
                    if labels != []:
                        data["message"] += ", plus "
                    data["message"] += "({}) unimported".format(deg_pools_count)

            self.emit(
                "pool_degraded_status",
                {"key": "sysinfo:pool_degraded_status", "data": data},
            )

            gevent.sleep(30)

    def pool_dev_stats(self):

        # Examples of data.message:
        # "Pools found with device errors: (rock-pool)"
        # "Pools found with device errors: (rock-pool, rock-pool-3)"
        # TODO: Consider blending into the existing pool_degraded_status()
        # TODO: to reduce overheads of looping through pools again.
        # TODO: The combined emitter could be called pool_health_status().
        while self.start:
            data = {"status": "OK"}
            labels = []
            for p in Pool.objects.all():
                if not p.dev_stats_ok:
                    labels.append(p.name)
            if labels != []:
                data["status"] = "errors"
                data["message"] = "Pools found with device errors: "
                data["message"] += "({})".format(", ".join(labels))

            self.emit("pool_dev_stats", {"key": "sysinfo:pool_dev_stats", "data": data})

            gevent.sleep(30)


def main():

    # Reference to new python-socket-io lib:
    # http://python-socketio.readthedocs.io/ IMPORTANT: to listen on a new
    # event always have it on_youreventname(self, sid, yourparams) IMPORTANT:
    # never use hypens (minus) on events and namespaces : open issue about this
    # on github repo
    sio_namespaces = [
        ServicesNamespace("/services"),
        SysinfoNamespace("/sysinfo"),
        CPUWidgetNamespace("/cpu_widget"),
        MemoryWidgetNamespace("/memory_widget"),
        NetworkWidgetNamespace("/network_widget"),
        DisksWidgetNamespace("/disk_widget"),
        LogManagerNamespace("/logmanager"),
        PincardManagerNamespace("/pincardmanager"),
    ]
    sio_server = socketio.Server(async_mode="gevent")
    for namespace in sio_namespaces:
        sio_server.register_namespace(namespace)
    app = socketio.Middleware(sio_server)
    logger.debug("Python-socketio listening on port http://127.0.0.1:8001")
    pywsgi.WSGIServer(("", 8001), app, handler_class=WebSocketHandler).serve_forever()
