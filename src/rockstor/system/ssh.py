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
from tempfile import mkstemp

from services import systemctl
from fs.btrfs import (mount_share, is_share_mounted)
from system.osi import run_command

SSHD_CONFIG = '/etc/ssh/sshd_config'
MKDIR = '/bin/mkdir'
MOUNT = '/bin/mount'

def update_sftp_config(input_list):
    """
    input list is a list of dictionaries. sample dictionary:
    {'user': 'rocky',
     'dir': '/mnt3/shareX',}

    """
    fo, npath = mkstemp()
    with open(SSHD_CONFIG) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            if (re.match('####BEGIN: Rockstor SFTP CONFIG####', line) is not
                None):
                tfo.write(line)
                for entry in input_list:
                    tfo.write('Match User %s\n' % entry['user'])
                    tfo.write('\tChrootDirectory %s\n' % entry['dir'])
                    tfo.write('\tForceCommand internal-sftp\n\n')
                tfo.write('####END: Rockstor SFTP CONFIG####\n')
                break
            else:
                tfo.write(line)
    move(npath, SSHD_CONFIG)
    return systemctl('sshd', 'reload')

def sftp_mount_map(mnt_prefix):
    mnt_map = {}
    with open('/proc/mounts') as pfo:
        for line in pfo.readlines():
            if (re.search(' ' + mnt_prefix, line) is not None):
                fields = line.split()
                sname = fields[2].split('/')[-1]
                editable = fields[5][1:3]
                mnt_map[sname] = editable
    return mnt_map

def sftp_mount(share, mnt_prefix, sftp_mnt_prefix, mnt_map, editable='rw'):
    #don't mount if already mounted
    sftp_mnt_pt = ('%s%s/%s' % (sftp_mnt_prefix, share.name, share.name))
    share_mnt_pt = ('%s%s' % (mnt_prefix, share.name))
    if (share.name in mnt_map):
        cur_editable = mnt_map[share.name]
        if (cur_editable != editable):
            return run_command([MOUNT, '-o', 'remount,%s,bind' % editable,
                                share_mnt_pt, sftp_mnt_pt])
    else:
        run_command([MKDIR, '-p', sftp_mnt_pt])
        run_command([MOUNT, '--bind', share_mnt_pt, sftp_mnt_pt])
        if (editable == 'ro'):
            run_command([MOUNT, '-o', 'remount,%s,bind' % editable,
                         share_mnt_pt, sftp_mnt_pt])
