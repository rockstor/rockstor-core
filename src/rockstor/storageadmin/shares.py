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

import subprocess
import re

class Share():

    def __init__(self, name, vol_id, pool, size):
        self.name = name
        self.vol_id = vol_id
        self.pool = pool
        self.size = size

def mount_pool(pool):
    pool_mnt = "/tmp/btrfs-" + pool.name
    proc = subprocess.Popen(["/bin/mkdir", "-p", pool_mnt],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    proc = subprocess.Popen(["/bin/mount", "-t", "btrfs", pool.disks[0],
                             pool_mnt], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)
    output, error = proc.communicate()
    return pool_mnt

def umount_pool(pool):
    pool_mnt = "/tmp/btrfs-" + pool.name
    proc = subprocess.Popen(["/bin/umount", pool_mnt], stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False)
    output, error = proc.communicate()

def create_share(pool, name):
    pool_mnt = mount_pool(pool)
    #create subvolume
    sub_vol = pool_mnt + '/' + name
    proc = subprocess.Popen(["/sbin/btrfs", "subvolume", "create", sub_vol],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    proc = subprocess.Popen(["/sbin/btrfs", "subvolume", "list", pool_mnt],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    output = output.split('\n')
    vol_id = -1
    for line in output:
        if (re.match(".*" + name + "$", line) is not None):
            vol_id = line.split()[1]
    share = Share(name, vol_id, pool, 0)
    umount_pool(pool)
    return share

def list_shares(pool):
    pool_mnt = mount_pool(pool)
    proc = subprocess.Popen(["/sbin/btrfs", "subvolume", "list", pool_mnt],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    output = output.split('\n')
    shares = []
    for line in output:
        elems = line.split()
        if (len(elems) != 7): continue
        shares.append(Share(elems[-1], elems[1], pool, 0))
    umount_pool(pool)
    return shares

def delete_share(pool, name):
    pool_mnt = mount_pool(pool)
    sub_vol = pool_mnt + '/' + name
    proc = subprocess.Popen(["/sbin/btrfs", "subvolume", "delete", sub_vol],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    umount_pool(pool)

