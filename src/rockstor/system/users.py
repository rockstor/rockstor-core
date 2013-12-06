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

from exceptions import CommandException
from osi import run_command
import subprocess
import re

import logging
logger = logging.getLogger(__name__)

PW_FILE = '/etc/passwd'
GROUP_FILE = '/etc/group'
USERADD = '/usr/sbin/useradd'
USERDEL = '/usr/sbin/userdel'
PASSWD = '/usr/bin/passwd'
USERMOD = '/usr/sbin/usermod'
SMBPASSWD = '/usr/bin/smbpasswd'

def get_users(min_uid=5000, uname=None):
    users = {}
    with open(PW_FILE) as pfo:
        for l in pfo.readlines():
            fields = l.strip().split(':')
            if (int(fields[2]) < min_uid):
                continue
            if (uname is not None):
                if (uname == fields[0]):
                    return {fields[0]: fields[2:],}
            else:
                users[fields[0]] = fields[2:]
    return users

def userdel(uname):
    return run_command([USERDEL, '-r', uname])

def get_epasswd(username):
    with open('/etc/shadow') as sfo:
        for l in sfo.readlines():
            fields = l.split(':')
            if (re.match(fields[0], username) is not None):
                return fields[1]
    return None

def usermod(username, passwd):
    cmd = [PASSWD, '--stdin', username]
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    out, err = p.communicate(input=passwd)
    rc = p.returncode
    if (rc != 0):
        raise CommandException(out, err, rc)
    return (out, err, rc)

def smbpasswd(username, passwd):
    cmd = [SMBPASSWD, '-s', '-a', username]
    p = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE, stdin=subprocess.PIPE)
    pstr = ('%s\n%s\n' % (passwd, passwd))
    out, err = p.communicate(input=pstr)
    rc = p.returncode
    if (rc != 0):
        raise CommandException(out, err, rc)
    return (out, err, rc)

def update_shell(username, shell):
    return run_command([USERMOD, '-s', shell, username])

def useradd(username, uid, shell):
    return run_command([USERADD, '-s', shell, '-m', '-u', str(uid),
                        username])
