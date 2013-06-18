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
import os
import subprocess
import shutil
import socket

from exceptions import CommandException

MKDIR = '/bin/mkdir'
RMDIR = '/bin/rmdir'
CHMOD = '/bin/chmod'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
EXPORTFS = '/usr/sbin/exportfs'
RESTART = '/sbin/restart'
EXPORT_DIR = '/export/'
SMB_CONFIG = '/etc/samba/smb.conf'
SERVICE = '/sbin/service'
HOSTID = '/usr/bin/hostid'


import logging
logger = logging.getLogger(__name__)

class Disk():

    def __init__(self, name, size, free, parted=False):
        self.name = name
        self.size = size
        self.free = free
        self.parted = parted

    def __repr__(self):
        return {'name': self.name,
                'size': self.size,
                'free': self.free,
                'parted': self.parted, }

def scan_disks(min_size):
    """
    min_size is in KB, so it is also number of blocks. Discard any disk with
    num_blocks < min_size
    """
    disks = {}
    with open('/proc/partitions') as pfo:
        for line in pfo.readlines():
            disk_fields = line.split()
            if (len(disk_fields) != 4):
                continue
            if (re.match('sd[a-z]+$|xvd[a-z]+$', disk_fields[3]) is not None):
                name = disk_fields[3]
                num_blocks = int(disk_fields[2]) # each block is 1KB
                if (num_blocks < min_size):
                    continue
                disk = Disk(name=name, size=num_blocks, free=num_blocks)
                disks[name] = disk.__repr__()
            elif (re.match('sd[a-z]+[0-9]+$|xvd[a-z]+[0-9]+$', disk_fields[3])
                  is not None):
                name = disk_fields[3][0:3]
                if (name in disks):
                    del(disks[name])
        return disks

def run_command(cmd, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE):
    p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr)
    out, err = p.communicate()
    out = out.split('\n')
    err = err.split('\n')
    rc = p.returncode
    if (rc != 0):
        raise CommandException(out, err, rc)
    return (out, err, rc)

def sys_info():
    sys_info = {}
    sys_info['hostname'] = socket.gethostname()
    with open('/proc/uptime') as ufo:
        sys_info['uptime'] = ufo.readline().split()[0]
    with open('/proc/meminfo') as mfo:
        sys_info['memory'] = mfo.readline().split()[1]
    with open('/proc/loadavg') as lfo:
        sys_info['load'] = lfo.readline().strip()
    with open('/proc/cpuinfo') as cfo:
        sys_info['processors'] = 0
        for line in cfo.readlines():
            if (re.search('processor', line)):
                sys_info['processors'] = sys_info['processors'] + 1
    return sys_info

def create_tmp_dir(dirname):
    return run_command([MKDIR, '-p', dirname])

def rm_tmp_dir(dirname):
    return run_command([RMDIR, dirname])

def nfs4_mount_setup(mnt_pt):
    """
    nfs4 without any authentication, for now.
    create /export/share_name with 777, where share_name is the last dentry in
    the mnt_pt.
    mount --bind mnt_pt /export/share_name
    """
    share_name = mnt_pt.split('/')[-1]
    export_dir = EXPORT_DIR + share_name
    if (not os.path.ismount(export_dir)):
        run_command([MKDIR, '-p', export_dir])
        run_command([CHMOD, '-R', '777', export_dir])
        return run_command([MOUNT, '--bind', mnt_pt, export_dir])
    return True

def nfs4_mount_teardown(mnt_pt):
    """
    reverse of setup. cleanup when there are no more exports
    """
    share_name = mnt_pt.split('/')[-1]
    export_dir = EXPORT_DIR + share_name
    if (os.path.exists(export_dir)):
        if (os.path.ismount(export_dir)):
            run_command([UMOUNT, export_dir])
        return run_command([RMDIR, export_dir])
    return True

def refresh_nfs_exports(exports):
    """
    input format:

    [{'mount_point': '/mnt2/share1',
     'clients': [{'client_str': 'www.example.com',
                  'option_list' 'rw,insecure,'},]},]

    if 'clients' is an empty list, then unmount and cleanup.
    """
    logger.debug('refreshing exports: %s' % exports)
    with open('/etc/exports', 'w') as efo:
        for e in exports:
            if (len(e['clients']) == 0):
                nfs4_mount_teardown(e['mount_point'])
                continue

            nfs4_mount_setup(e['mount_point'])
            client_str = ''
            for c in e['clients']:
                client_str = ('%s%s(%s) ' % (client_str, c['client_str'],
                                             c['option_list']))
            export_str = ('%s %s\n' % (e['mount_point'], client_str))
            efo.write(export_str)
    return run_command([EXPORTFS, '-ra'])

def refresh_smb_config(exports, clean_config):
    shutil.copyfile(clean_config, SMB_CONFIG)
    with open(SMB_CONFIG, 'a') as sfo:
        for e in exports:
            sfo.write('[%s]\n' % e.share.name)
            sfo.write('    comment = %s\n' % e.comment)
            sfo.write('    path = %s\n' % e.path)
            sfo.write('    browsable = %s\n' % e.browsable)
            sfo.write('    read only = %s\n' % e.read_only)
            sfo.write('    create mask = %s\n' % e.create_mask)
    return True

def restart_samba():
    """
    call whenever config is updated
    """
    smbd_cmd = [SERVICE, 'smb', 'restart']
    return run_command(smbd_cmd)

def hostid():
    """
    return the hostid of the machine
    """
    return run_command([HOSTID])
