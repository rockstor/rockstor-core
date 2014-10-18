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

CHKCONFIG_BIN = '/sbin/chkconfig'
AUTHCONFIG = '/usr/sbin/authconfig'
SSHD_CONFIG = '/etc/ssh/sshd_config'
SYSTEMCTL_BIN = '/usr/bin/systemctl'
SUPERCTL_BIN = ('%s/bin/supervisorctl' % settings.ROOT_DIR)
NET = '/usr/bin/net'


def init_service_op(service_name, command, throw=True):
    supported_services = ('nfs', 'smb', 'sshd', 'ypbind', 'rpcbind', 'ntpd',
                          'winbind', 'nslcd', 'netatalk')
    if (service_name not in supported_services):
        raise Exception('unknown service: %s' % service_name)

    return run_command([SYSTEMCTL_BIN, command, service_name], throw=throw)


def chkconfig(service_name, switch):
    return run_command([CHKCONFIG_BIN, service_name, switch])


def systemctl(service_name, switch):
    return run_command([SYSTEMCTL_BIN, switch, service_name])


def superctl(service, switch):
    out, err, rc = run_command([SUPERCTL_BIN, switch, service])
    if (switch == 'status'):
        status = out[0].split()[1]
        if (status != 'RUNNING'):
            rc = 1
    return out, err, rc


def service_status(service_name):
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
          service_name == 'task-scheduler' or
          service_name == 'data-collector' or
          service_name == 'service-monitor'):
        return superctl(service_name, 'status')
    elif (service_name == 'smb'):
        out, err, rc = run_command([SYSTEMCTL_BIN, 'status', 'smb'],
                                   throw=False)
        if (rc != 0):
            return out, err, rc
        return run_command([SYSTEMCTL_BIN, 'status', 'nmb'], throw=False)
    return init_service_op(service_name, 'status', throw=False)


def winbind_input(config, command):
    ac_cmd = []
    if (command == 'stop'):
        ac_cmd.extend(['--disablewinbind', '--disablewinbindauth'])
    else:
        ac_cmd.append('--smbworkgroup=%s' % config['domain'])
        ac_cmd.append('--smbsecurity=%s' % config['security'])
        if (config['security'] == 'ads'):
            ac_cmd.append('--smbrealm=%s' % config['realm'])
        if (config['security'] == 'ads' or config['security'] == 'domain'):
            ac_cmd.append('--winbindtemplateshell=%s' %
                          config['templateshell'])
        ac_cmd.append('--smbservers=%s' % config['controllers'])
        if (config['allow-offline'] is True):
            ac_cmd.append('--enablewinbindoffline')
        else:
            ac_cmd.append('--disablewinbindoffline')
        ac_cmd.extend(['--kickstart', '--enablewinbind',
                       '--winbindtemplatehomedir=/home/%%U',
                       '--enablewinbindusedefaultdomain',
                       '--enablelocauthorize',
                       '--enablepamaccess',
                       '--disablekrb5',
                       '--disablekrb5kdcdns',
                       '--disablekrb5realmdns', ])
    return ac_cmd


def join_winbind_domain(username, passwd):
    up = '%s%%%s' % (username, passwd)
    cmd = [NET, 'ads', 'join', '-U', up, '--request-timeout', '30']
    out, err, rc = run_command(cmd, throw=False,)
    if (rc != 0):
        error = ('Below error can occur due to DNS issue. Ensure '
                 'that /etc/resolv.conf on Rockstor is pointing to '
                 'the right nameserver -- stdout: %s stderr: %s'
                 % (' '.join(out), ' '.join(err)))
        raise CommandException(out, error, rc)
    return (out, err, rc)


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
    if (service == 'winbind'):
        ac_cmd.extend(winbind_input(config, command))
    elif (service == 'ldap'):
        ac_cmd.extend(ldap_input(config, command))
    else:
        return None
    return run_command(ac_cmd)


def ads_join_status(username, passwd):
    up = '%s%%%s' % (username, passwd)
    return run_command([NET, 'ads', 'status', '-U', up, '--request-timeout',
                        '60'])
