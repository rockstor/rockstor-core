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

import re
from django.conf import settings
from osi import run_command
from exceptions import CommandException
import shutil
from tempfile import mkstemp
import os
from shutil import move

CHKCONFIG_BIN = '/sbin/chkconfig'
AUTHCONFIG = '/usr/sbin/authconfig'
SSHD_CONFIG = '/etc/ssh/sshd_config'
SYSTEMCTL_BIN = '/usr/bin/systemctl'
SUPERCTL_BIN = ('%s/bin/supervisorctl' % settings.ROOT_DIR)
SUPERVISORD_CONF = ('%s/etc/supervisord.conf' % settings.ROOT_DIR)
NET = '/usr/bin/net'
AFP_CONFIG = '/etc/netatalk/afp.conf'


def init_service_op(service_name, command, throw=True):
    """
    Wrapper for run_command calling systemctl, hardwired filter on service_name
    and will raise Exception on failed match. Enables run_command exceptions
    by default.
    :param service_name:
    :param command:
    :param throw:
    :return: out err rc
    """
    supported_services = ('nfs', 'smb', 'sshd', 'ypbind', 'rpcbind', 'ntpd',
                          'nslcd', 'netatalk', 'snmpd', 'docker',
                          'smartd', 'nut-server')
    if (service_name not in supported_services):
        raise Exception('unknown service: %s' % service_name)

    return run_command([SYSTEMCTL_BIN, command, service_name], throw=throw)


def chkconfig(service_name, switch):
    return run_command([CHKCONFIG_BIN, service_name, switch])


def systemctl(service_name, switch):
    return run_command([SYSTEMCTL_BIN, switch, service_name])


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
    switch_map = {'start': 'true',
                  'stop': 'false'}
    if (switch not in switch_map):
        return
    switch = switch_map[switch]
    fo, npath = mkstemp()
    with open(SUPERVISORD_CONF) as sfo, open(npath, 'w') as tfo:
        start = False
        stop = False
        for line in sfo.readlines():
            if (re.match('\[program:%s\]' % service, line) is not None):
                start = True
            elif (start is True and len(line.strip()) == 0):
                stop = True

            if (start is True and stop is False):
                if (re.match('autostart', line) is not None):
                    tfo.write('autostart=%s\n' % switch)
                else:
                    tfo.write(line)
            else:
                tfo.write(line)
    move(npath, SUPERVISORD_CONF)


def superctl(service, switch):
    out, err, rc = run_command([SUPERCTL_BIN, switch, service])
    set_autostart(service, switch)
    if (switch == 'status'):
        status = out[0].split()[1]
        if (status != 'RUNNING'):
            rc = 1
    return out, err, rc


def service_status(service_name, config=None):
    """
    Service status of either systemd or supervisord managed services.
    Hardwired to identify controlling system by service name and uses one of
    systemctrl, init_service_op, or superctl to assess status accordingly.
    Note some sanity checks for some services.
    :param service_name:
    :return:
    """
    if (service_name == 'nis' or service_name == 'nfs'):
        out, err, rc = init_service_op('rpcbind', 'status', throw=False)
        if (rc != 0):
            return out, err, rc
        if (service_name == 'nis'):
            return init_service_op('ypbind', 'status', throw=False)
        else:
            return init_service_op('nfs', 'status', throw=False)
    elif (service_name == 'ldap'):
        return init_service_op('nslcd', 'status', throw=False)
    elif (service_name == 'sftp'):
        out, err, rc = init_service_op('sshd', 'status', throw=False)
        if (rc != 0):
            return out, err, rc
        with open(SSHD_CONFIG) as sfo:
            for line in sfo.readlines():
                if (re.match("Subsystem\tsftp\tinternal-sftp", line) is not
                        None):
                    return out, err, rc
            return out, err, -1
    elif (service_name == 'replication' or
          service_name == 'data-collector'):
        return superctl(service_name, 'status')
    elif (service_name == 'smb'):
        out, err, rc = run_command([SYSTEMCTL_BIN, 'status', 'smb'],
                                   throw=False)
        if (rc != 0):
            return out, err, rc
        return run_command([SYSTEMCTL_BIN, 'status', 'nmb'], throw=False)
    elif (service_name == 'nut'):
        # Establish if nut is running by lowest common denominator nut-monitor
        # In netclient mode it is all that is required, however we don't then
        # reflect the state of the other services of nut-server and nut-driver.
        return run_command([SYSTEMCTL_BIN, 'status', 'nut-monitor'],
                           throw=False)
    elif (service_name == 'active-directory'):
        if (config is not None):
            REALM = '/usr/sbin/realm'
            o, e, rc = run_command([REALM, 'list', '--name-only'])
            for l in o:
                if (l == config['domain']):
                    return '', '', 0
        return '', '', -1

    return init_service_op(service_name, 'status', throw=False)


def ldap_input(config, command):
    ac_cmd = []
    if (command == 'stop'):
        ac_cmd.extend(['--disableldap', '--disableldapauth'])
    else:
        ac_cmd.extend(['--enableldap', '--enableldapauth'])
        ac_cmd.append('--ldapserver=%s' % config['server'])
        ac_cmd.append('--ldapbasedn=%s' % config['basedn'])
        if (config['enabletls'] is True):
            ac_cmd.append('--enableldaptls')
            ac_cmd.append('--ldaploadcacert=%s' % config['cert'])
    return ac_cmd


def toggle_auth_service(service, command, config=None):
    ac_cmd = [AUTHCONFIG, '--update', ]
    if (service == 'ldap'):
        ac_cmd.extend(ldap_input(config, command))
    else:
        return None
    return run_command(ac_cmd)


def rockstor_afp_config(fo, afpl):
    fo.write(';####BEGIN: Rockstor AFP CONFIG####\n')
    for c in afpl:
        vol_size = int(c.vol_size() / 1024)
        fo.write('[%s]\n' % c.description)
        fo.write('  path = %s\n' % c.path)
        fo.write('  time machine = %s\n' % c.time_machine)
        fo.write('  vol size limit = %d\n\n' % vol_size)
    fo.write(';####END: Rockstor AFP CONFIG####\n')


def refresh_afp_config(afpl):
    fo, npath = mkstemp()
    with open(AFP_CONFIG) as afo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in afo.readlines():
            if (re.match(';####BEGIN: Rockstor AFP CONFIG####', line)
                    is not None):
                rockstor_section = True
                rockstor_afp_config(tfo, afpl)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_afp_config(tfo, afpl)
    shutil.move(npath, AFP_CONFIG)
    os.chmod(AFP_CONFIG, 0644)
