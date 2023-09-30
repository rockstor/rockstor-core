"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import os
import re
import shutil
import stat
from tempfile import mkstemp
from typing import Tuple, List

from django.conf import settings

from system.constants import SYSTEMCTL
from system.osi import run_command
from system.ssh import is_sftp_running

SUPERCTL_BIN = "{}.venv/bin/supervisorctl".format(settings.ROOT_DIR)
SUPERVISORD_CONF = "{}etc/supervisord.conf".format(settings.ROOT_DIR)
SSSD_FILE = "/etc/sssd/sssd.conf"
NET = "/usr/bin/net"
WBINFO = "/usr/bin/wbinfo"
REALM = "/usr/sbin/realm"


def init_service_op(service_name, command, throw=True):
    """Run systemctl commands

    Wrapper for run_command calling systemctl, hardwired filter on service_name
    and will raise Exception on failed match. Enables run_command exceptions
    by default.
    https://www.freedesktop.org/software/systemd/man/systemctl.html for rc return codes.
    0 = unit is active, 3 = unit is not active, 4 = no such unit
    :param str service_name:
    :param str command:
    :param bool throw:
    :return: out err rc
    """
    # TODO: Consider speed-up by removing hardwired 'native' check and replacing by
    #  rc == 4 check for system unknown (not-installed) services ("no such unit").
    #  We could also do with a lean Boolean wrapper i.e. service_status_boolean()
    #  to be used in for example model properties etc, where we need only a boolean.
    supported_services = (
        "nfs-server",
        "nmb",
        "smb",
        "sshd",
        "ypbind",
        "rpcbind",
        "ntpd",
        "snmpd",
        "docker",
        "smartd",
        "shellinaboxd",
        "sssd",
        "nut-server",
        "rockstor-bootstrap",
        "rockstor",
        "systemd-shutdownd",
    )
    if service_name not in supported_services:
        raise Exception("unknown service: {}".format(service_name))

    arg_list = [SYSTEMCTL, command, service_name]
    if command == "status":
        arg_list.append("--lines=0")

    return run_command(arg_list, throw=throw)


def is_systemd_service_active(service_name):
    """Returns boolean for active status of a systemd service

    Uses init_service_op() to return a boolean for the status of a systemd service.
    Use service_status() to get status information for a Rockstor service.
    :param str service_name: name of the systemd service
    :return: True if the service is active
    :rtype: bool
    """
    _, _, rc = init_service_op(service_name=service_name, command="status", throw=False)
    if rc == 0:
        return True
    else:
        return False


def systemctl(service_name, switch):
    arg_list = [SYSTEMCTL, switch, service_name]
    if switch == "status":
        arg_list.append("--lines=0")

    return run_command(arg_list, log=True)


def set_autostart(service, switch):
    """
    Configure autostart setting for supervisord managed services eg:-
    nginx, gunicorn, smart_manager daemon, replication daemon, data-collector,
    and ztask-daemon. Works by rewriting autostart lines in  SUPERVISORD_CONF
    http://supervisord.org/
    :param service:
    :param switch:
    :return:
    """
    switch_map = {"start": "true", "stop": "false"}
    if switch not in switch_map:
        return
    switch = switch_map[switch]
    fo, npath = mkstemp()
    with open(SUPERVISORD_CONF) as sfo, open(npath, "w") as tfo:
        start = False
        stop = False
        for line in sfo.readlines():
            if re.match("\[program:{}\]".format(service), line) is not None:
                start = True
            elif start is True and len(line.strip()) == 0:
                stop = True

            if start is True and stop is False:
                if re.match("autostart", line) is not None:
                    tfo.write("autostart={}\n".format(switch))
                else:
                    tfo.write(line)
            else:
                tfo.write(line)
    shutil.move(npath, SUPERVISORD_CONF)


def superctl(
    service: str, switch: str, throw: bool = True
) -> Tuple[List[str], List[str], int]:
    out, err, rc = run_command([SUPERCTL_BIN, switch, service], throw=throw)
    set_autostart(service, switch)
    if switch == "status":
        status = out[0].split()[1]
        if status != "RUNNING":
            rc = 1
    return out, err, rc


def service_status(service_name, config=None):
    """
    Service status of either systemd or supervisord managed services.
    Hardwired to identify controlling system by service name and uses one of
    systemctl, init_service_op, or superctl to assess status accordingly.
    Note some sanity checks for some services.
    :param service_name:
    :param config:
    :return: out, err, rc
    """
    if service_name == "nis" or service_name == "nfs":
        out, err, rc = init_service_op("rpcbind", "status", throw=False)
        if rc != 0:
            return out, err, rc
        if service_name == "nis":
            return init_service_op("ypbind", "status", throw=False)
        else:
            return init_service_op("nfs-server", "status", throw=False)
    elif service_name == "ldap":
        o, e, rc = init_service_op("sssd", "status", throw=False)
        # initial check on sssd status: 0 = OK 3 = stopped 4 = no such unit
        # TODO In the following we only check config on already running sssd service!
        #  but with more modern instances, running is dependant on configuration.
        if rc != 0:
            return o, e, rc
        # check for service configuration
        if config is None:
            return o, e, 1
        # sssd is also used for the Active Directory service, so we need to
        # check if the configured LDAP domain is defined in its config file
        with open(SSSD_FILE) as sfo:
            for line in sfo.readlines():
                if (
                    re.search("domains = ", line) and re.search(config["server"], line)
                ) is not None:
                    return o, e, rc
            return o, e, 1
    elif service_name == "sftp":
        # Delegate sshd's sftp subsystem status check to system.ssh.py call.
        return is_sftp_running(return_boolean=False)
    elif service_name in ("replication", "data-collector", "ztask-daemon"):
        return superctl(service_name, "status", throw=False)
    elif service_name == "smb":
        out, err, rc = run_command(
            [SYSTEMCTL, "--lines=0", "status", "smb"], throw=False
        )
        if rc != 0:
            return out, err, rc
        return run_command([SYSTEMCTL, "--lines=0", "status", "nmb"], throw=False)
    elif service_name == "nut":
        # Establish if nut is running by lowest common denominator nut-monitor
        # In netclient mode it is all that is required, however we don't then
        # reflect the state of the other services of nut-server and nut-driver.
        return run_command(
            [SYSTEMCTL, "--lines=0", "status", "nut-monitor"], throw=False
        )
    elif service_name == "active-directory":
        if config is not None:
            active_directory_rc = 1
            o, e, rc = run_command(
                [
                    REALM,
                    "list",
                    "--name-only",
                ]
            )
            if config["domain"] in o:
                active_directory_rc = 0
            return "", "", active_directory_rc
        # bootstrap switch subsystem interprets -1 as ON so returning 1 instead
        return "", "", 1

    return init_service_op(service_name, "status", throw=False)


def update_nginx(ip, port):
    port = int(port)
    conf = "{}/etc/nginx/nginx.conf".format(settings.ROOT_DIR)
    fo, npath = mkstemp()
    with open(conf) as ifo, open(npath, "w") as tfo:
        http_server = False
        lines = ifo.readlines()
        for i in range(len(lines)):
            if (
                re.search("server {", lines[i]) is not None
                and re.search("listen.*80 default_server", lines[i + 1]) is not None
            ):
                # found legacy http server section. don't rewrite it.
                http_server = True
            if (
                not http_server
                and re.search("listen.*default_server", lines[i]) is not None
            ):
                substr = "listen {} ssl default_server".format(port)
                if ip is not None:
                    substr = "listen {}:{} ssl default_server".format(ip, port)
                lines[i] = re.sub(r"listen.* default_server", substr, lines[i])
            if not http_server:
                tfo.write(lines[i])
            if http_server is True and lines[i].strip() == "}":
                http_server = False
    shutil.move(npath, conf)
    run_command([SYSTEMCTL, "restart", "nginx"])


def define_avahi_service(service_name, share_names=None):
    """
    First define parameters to be written to the static service
    file and then organizes writing them to file using subfunctions.
    :param service_name: name of the avahi service. Will be used as
    the name of the service file.
    :param share_names: list of the names of the shares to advertise
    :return:
    """
    dest_file = "/etc/avahi/services/{}.service".format(service_name)

    # Define parameters
    avahi_service = []
    if service_name == "timemachine":
        txt_records = ["sys=waMa=0,adVF=0x100"]
        for s in range(len(share_names)):
            txt_records.append("dk{}=adVN={},adVF=0x82".format(s, share_names[s]))
        avahi_service.append({"type": "_smb._tcp", "port": "445"})
        avahi_service.append({"type": "_adisk._tcp", "txt-record": txt_records})

    # Write to file
    fh, npath = mkstemp()
    with open(npath, "w") as tfo:
        write_avahi_headers(tfo)
        for s in avahi_service:
            write_avahi_service(tfo, **s)
        write_avahi_footer(tfo)
    # Set file to rw- r-- r-- (644) via stat constants.
    os.chmod(npath, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
    shutil.move(npath, dest_file)


def write_avahi_headers(tfo):
    """
    Simply write the headers for an avahi static service file.
    :param tfo:
    :return:
    """
    tfo.write("<?xml version=\"1.0\" standalone='no'?>\n")
    tfo.write('<!DOCTYPE service-group SYSTEM "avahi-service.dtd">\n')
    tfo.write("<service-group>\n")
    tfo.write(' <name replace-wildcards="yes">%h</name>\n')


def write_avahi_footer(tfo):
    """
    Simply write the footer for an avahi static service file.
    :param tfo:
    :return:
    """
    tfo.write("</service-group>\n")


def write_avahi_service(tfo, **kwargs):
    """
    Writes the full <service> section of an avahi static service file.
    Each kwarg must follow the key: value syntax that will be used
    as key: value for the given xml key.
    When the same xml key needs to be used with multiple values, one
    must use a list of values for this given key.
    :param tfo:
    :param kwargs:
    :return:
    """
    tfo.write(" <service>\n")
    for k, v in kwargs.items():
        if isinstance(v, list):
            for v2 in v:
                tfo.write("   <{}>{}</{}>\n".format(k, v2, k))
        else:
            tfo.write("   <{}>{}</{}>\n".format(k, v, k))
    tfo.write(" </service>\n")
