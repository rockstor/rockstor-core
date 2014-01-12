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
from shutil import move
import subprocess

from django.conf import settings
from osi import run_command
from exceptions import CommandException

SERVICE_BIN = '/sbin/service'
CHKCONFIG_BIN = '/sbin/chkconfig'
AUTHCONFIG = '/usr/sbin/authconfig'
SSHD_CONFIG = '/etc/ssh/sshd_config'
SYSTEMCTL_BIN = '/usr/bin/systemctl'
SUPERCTL_BIN = ('%s/bin/supervisorctl' % settings.ROOT_DIR)
NET = '/usr/bin/net'

def init_service_op(service_name, command, throw=True):
    supported_services = ('nfs', 'smb', 'sshd', 'ypbind', 'rpcbind', 'ntpd',
                          'winbind', 'nslcd',)
    if (service_name not in supported_services):
        raise Exception('unknown service: %s' % service_name)

    cmd = [SERVICE_BIN, service_name, command]
    out, err, rc = run_command(cmd, throw=throw)
    return out, err, rc

def chkconfig(service_name, switch):
    return run_command([CHKCONFIG_BIN, service_name, switch])

def systemctl(service_name, switch):
    return run_command([SYSTEMCTL_BIN, switch, service_name])

def superctl(service, switch):
    service = 'rd'
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
    elif (service_name == 'replication'):
        return superctl(service_name, 'status')
    elif (service_name == 'smb'):
        run_command([SYSTEMCTL_BIN, 'status', 'smb'])
        return run_command([SYSTEMCTL_BIN, 'status', 'nmb'])
    return init_service_op(service_name, 'status', throw=False)

def winbind_input(config, command):
    ac_cmd = []
    if (command == 'stop'):
        ac_cmd.extend(['--disablewinbind','--disablewinbindauth'])
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
                       '--disablekrb5realmdns',])
    return ac_cmd

def join_winbind_domain(username, passwd):
    up = '%s%%%s' % (username, passwd)
    cmd = [NET, 'ads', 'join', '-U', up, '--request-timeout', '30']
    out, err, rc = run_command(cmd, throw=False,)
    if (rc != 0):
        error = None
        for e in out + err:
            if (re.search('AD: Operations error', e) is not None):
                error = ('Below error can occur due to DNS issue. Ensure '
                         'that /etc/resolv.conf on Rockstor is pointing to '
                         'the right DNS server -- stdout: %s stderr: %s'
                         % (' '.join(out), ' '.join(err)))
                break
        if (error is None):
            error = ('Below error may be helpful for further '
                     'troubleshooting -- stdout: %s stderr: %s'
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
    ac_cmd = [AUTHCONFIG, '--update',]
    if (service == 'winbind'):
        ac_cmd.extend(winbind_input(config, command))
    elif (service == 'ldap'):
        ac_cmd.extend(ldap_input(config, command))
    else:
        return None
    return run_command(ac_cmd)

def toggle_sftp_service(switch=True):
    written = False
    sftp_str = ("Subsystem\tsftp\tinternal-sftp\n")
    with open(SSHD_CONFIG) as sfo:
        with open('/tmp/sshd_config', 'w') as tfo:
            for line in sfo.readlines():
                if (re.match('Subsystem', line) is not None):
                    if (switch == True):
                        tfo.write(sftp_str)
                        written = True
                else:
                    tfo.write(line)
            if (switch is True and written is False):
                tfo.write(sftp_str)
    move('/tmp/sshd_config', '/etc/ssh/sshd_config')
    return init_service_op('sshd', 'reload')

def ads_joined():
    return run_command([NET, 'ads', 'testjoin'])
