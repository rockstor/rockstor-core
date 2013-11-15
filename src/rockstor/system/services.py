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

from osi import run_command

SERVICE_BIN = '/sbin/service'
CHKCONFIG_BIN = '/sbin/chkconfig'
AUTHCONFIG = '/usr/sbin/authconfig'
SSHD_CONFIG = '/etc/ssh/sshd_config'

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
                if (re.match('Subsystem', line) is not None):
                    return out, err, rc
            return out, err, -1
    return init_service_op(service_name, 'status', throw=False)

def winbind_input(config, command):
    ac_cmd = []
    if (command == 'stop'):
        ac_cmd.extend(['--disablewinbind','--disablewinbindauth'])
    else:
        ac_cmd.append('--smbsecurity=%s' % config['security'])
        if (config['allow-offline'] is True):
            ac_cmd.append('--enablewinbindoffline')
        ac_cmd.append('--smbservers=%s' % config['controllers'])
        ac_cmd.append('--smbworkgroup=%s' % config['domain'])
        if (config['security'] == 'ad' or config['security'] == 'domain'):
            ac_cmd.append('--winbindtemplateshell=%s' %
                          config['templateshell'])
        if (config['security'] == 'ad'):
            ac_cmd.append('--smbrealm=%s' % config['realm'])
        ac_cmd.extend(['--enablewinbind', '--enablewinbindauth'])
    return ac_cmd

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
