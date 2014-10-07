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

"""
system level helper methods to interact with the filesystem
"""

import re
import time
import os

from system.osi import (run_command, create_tmp_dir, is_share_mounted,
                        is_mounted)
from system.exceptions import (CommandException, NonBTRFSRootException)


MKFS_BTRFS = '/sbin/mkfs.btrfs'
BTRFS = '/sbin/btrfs'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
DD = '/bin/dd'
DEFAULT_MNT_DIR = '/mnt2/'
DF = '/bin/df'
BTRFS_DEBUG_TREE = '/sbin/btrfs-debug-tree'
RMDIR = '/bin/rmdir'
SFDISK = '/sbin/sfdisk'


class Disk():

    def __init__(self, name, size, free, parted=False, uuid=None):
        self.name = name
        self.size = size
        self.free = free
        self.parted = parted
        self.btrfs_uuid = uuid

    def __repr__(self):
        return {'name': self.name,
                'size': self.size,
                'free': self.free,
                'parted': self.parted,
                'btrfs_uuid': self.btrfs_uuid, }


def add_pool(name, data_raid, meta_raid, disks):
    """
    pool is a btrfs filesystem.
    """
    disks_fp = ['/dev/' + d for d in disks]
    cmd = [MKFS_BTRFS, '-f', '-d', data_raid, '-m', meta_raid, '-L', name]
    cmd.extend(disks_fp)
    out, err, rc = run_command(cmd)
    enable_quota(name, disks_fp[0])
    return out, err, rc


def resize_pool(pool_name, device, dev_list, add=True):
    device = '/dev/' + device
    dev_list = ['/dev/' + d for d in dev_list]
    root_mnt_pt = mount_root(pool_name, device)
    resize_flag = 'add'
    if (not add):
        resize_flag = 'delete'
    resize_cmd = [BTRFS, 'device', resize_flag, ' '.join(dev_list),
                  root_mnt_pt]
    out, err, rc = run_command(resize_cmd)
    return out, err, rc


def btrfs_wipe_disk(disk):
    dd_cmd = [DD, 'if=/dev/zero', 'of=%s' % disk, 'bs=1024', 'count=100']
    return run_command(dd_cmd)


def remove_pool(name):
    """
    just remove from database? mark it deleted? may be give a purge option that
    will do some dd type thing to the disks?

    for now -- just wipe out the pool. this is possible by dd'ing first 100KB
    of each disk in the pool.

    @todo: when btrfs return values are fixed, revisit. filesystem show for now
    returns success even if pool doesn't exist.
    """
    cmd = [BTRFS, 'filesystem', 'show', name]
    out, err, rc = run_command(cmd)
    for line in out:
        if (re.search('/dev/sd', line) is not None):
            disk = line.split()[-1]
            out, err, rc = btrfs_wipe_disk(disk)
    #last command results -- not particularly useful
    return out, err, rc


def mount_root(pool_name, device):
    root_pool_mnt = DEFAULT_MNT_DIR + pool_name
    if (is_share_mounted(pool_name)):
        return root_pool_mnt
    create_tmp_dir(root_pool_mnt)
    mnt_cmd = [MOUNT, '-t', 'btrfs', device, root_pool_mnt]
    run_command(mnt_cmd)
    return root_pool_mnt


def umount_root(root_pool_mnt):
    if (is_mounted(root_pool_mnt)):
        run_command([UMOUNT, '-l', root_pool_mnt])
        for i in range(10):
            if (not is_mounted(root_pool_mnt)):
                return run_command([RMDIR, root_pool_mnt])
            time.sleep(1)
        run_command([UMOUNT, '-f', root_pool_mnt])
    if (os.path.exists(root_pool_mnt)):
        return run_command([RMDIR, root_pool_mnt])
    return True


def add_share(pool_name, pool_device, share_name):
    """
    share is a subvolume in btrfs.
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    sub_vol_cmd = [BTRFS, 'subvolume', 'create', subvol_mnt_pt]
    run_command(sub_vol_cmd)


def mount_share(share_name, pool_device, mnt_pt):
    pool_device = '/dev/' + pool_device
    subvol_str = 'subvol=%s' % share_name
    create_tmp_dir(mnt_pt)
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, pool_device, mnt_pt]
    return run_command(mnt_cmd)


def subvol_list_helper(mnt_pt):
    """
    temporary solution until btrfs is fixed. wait upto 30 secs :(
    """
    num_tries = 0
    while (True):
        try:
            return run_command([BTRFS, 'subvolume', 'list', mnt_pt])
        except CommandException, ce:
            if (ce.rc != 19):
                #rc == 19 is due to the slow kernel cleanup thread. It should
                #eventually succeed.
                raise ce
            time.sleep(1)
            num_tries = num_tries + 1
            if (num_tries > 30):
                raise ce


def snapshot_list(mnt_pt):
    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-s', mnt_pt])
    snaps = []
    for s in o:
        snaps.append(s.split()[-1])
    return snaps


def share_id(pool_name, pool_device, share_name):
    """
    returns the subvolume id, becomes the share's uuid.
    @todo: this should be part of add_share -- btrfs create should atomically
    return the id
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    out, err, rc = subvol_list_helper(root_pool_mnt)
    subvol_id = None
    for line in out:
        if (re.search(share_name + '$', line) is not None):
            subvol_id = line.split()[1]
            break
    if (subvol_id is not None):
        return subvol_id
    raise Exception('subvolume id for share: %s not found.' % share_name)


def remove_share(pool_name, pool_device, share_name):
    """
    umount share if its mounted.
    mount root pool
    btrfs subvolume delete root_mnt/vol_name
    umount root pool
    """
    if (is_share_mounted(share_name)):
        mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, share_name))
        umount_root(mnt_pt)
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    delete_cmd = [BTRFS, 'subvolume', 'delete', subvol_mnt_pt]
    run_command(delete_cmd)


def remove_snap(pool_name, pool_device, share_name, snap_name):
    full_name = ('%s/%s' % (share_name, snap_name))
    if (is_share_mounted(full_name)):
        umount_root('%s%s' % (DEFAULT_MNT_DIR, full_name))
    root_pool_mnt = mount_root(pool_name, pool_device)
    subvol_mnt_pt = ('%s/%s_%s' % (root_pool_mnt, share_name, snap_name))
    return run_command([BTRFS, 'subvolume', 'delete', subvol_mnt_pt])


def add_snap(pool_name, pool_device, share_name, snap_name,
             share_prepend=True):
    """
    create a snapshot
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    share_full_path = root_pool_mnt + '/' + share_name
    snap_full_path = ('%s/%s' % (root_pool_mnt, snap_name))
    if (share_prepend is True):
        snap_full_path = ('%s/%s_%s' % (root_pool_mnt, share_name, snap_name))
    #snapshot -r for replication. snapshots must be readonly for btrfs
    #send/recv to work.
    snap_cmd = [BTRFS, 'subvolume', 'snapshot', '-r', share_full_path,
                snap_full_path]
    try:
        run_command(snap_cmd)
    except CommandException, ce:
        if (ce.rc != 19):
            #rc == 19 is due to the slow kernel cleanup thread. snapshot gets
            #created just fine. lookup is delayed arbitrarily.
            raise ce


def rollback_snap(snap_name, sname, subvol_name, pool_name, pool_device):
    """
    1. umount the share
    2. mount the snap as the share
    3. remove the share
    """
    mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, sname))
    if (is_share_mounted(sname)):
        umount_root(mnt_pt)
    mount_share(snap_name, pool_device, mnt_pt)
    remove_share(pool_name, pool_device, subvol_name)


def switch_quota(pool_name, device, flag='enable'):
    root_mnt_pt = mount_root(pool_name, device)
    cmd = [BTRFS, 'quota', flag, root_mnt_pt]
    return run_command(cmd)


def enable_quota(pool_name, device):
    return switch_quota(pool_name, device)


def disable_quota(pool_name, device):
    return switch_quota(pool_name, device, flag='disable')


def update_quota(pool_name, pool_device, qgroup, size_bytes):
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    cmd = [BTRFS, 'qgroup', 'limit', str(size_bytes), qgroup, root_pool_mnt]
    return run_command(cmd)


def share_usage(pool_name, pool_device, share_id):
    """
    for now, exclusive byte count
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    cmd = [BTRFS, 'qgroup', 'show', root_pool_mnt]
    out, err, rc = run_command(cmd)
    usage = None
    for line in out:
        fields = line.split()
        if (fields[0] == share_id):
            usage = int(fields[-2]) / 1024 # usage in KB
            break
    if (usage is None):
        raise Exception('usage cannot be determined for share_id: %s' %
                        share_id)
    return usage


def shares_usage(pool_name, pool_device, share_map, snap_map):
    #don't mount the pool if at least one share in the map is mounted.
    usage_map = {}
    mnt_pt = None
    for s in share_map.keys():
        if (is_share_mounted(share_map[s])):
            mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, share_map[s]))
            break
    if (mnt_pt is None):
        mnt_pt = mount_root(pool_name, '/dev/' + pool_device)
    cmd = [BTRFS, 'qgroup', 'show', mnt_pt]
    out, err, rc = run_command(cmd)
    combined_map = dict(share_map, **snap_map)
    for line in out:
        fields = line.split()
        if (len(fields) > 0 and fields[0] in combined_map):
            r_usage = int(fields[-2]) / 1024 # referenced usage in KB
            e_usage = int(fields[-1]) / 1024 # exclusive usage in KB
            usage_map[combined_map[fields[0]]] = (r_usage, e_usage)
    return usage_map


def pool_usage(pool_device):
    pool_device = ('/dev/%s' % pool_device)
    cmd = [BTRFS_DEBUG_TREE, '-r', pool_device]
    out, err, rc = run_command(cmd)
    total = None
    usage = None
    for line in out:
        if (re.match('total bytes ', line) is not None):
            total = int(line.split()[2]) / 1024 # in KB
        if (re.match('bytes used ', line) is not None):
            usage = int(line.split()[2]) / 1024 # in KB
            break #usage line is right after total line.
    if (usage is None or total is None):
        raise Exception('usage not available for pool device: %s' %
                        pool_device)
    return (total, usage)


def scrub_start(pool_name, pool_device):
    mnt_pt = mount_root(pool_name, '/dev/' + pool_device)
    out, err, rc = run_command([BTRFS, 'scrub', 'start', mnt_pt])
    return int(out[0].split('(pid=')[1][:-1])


def scrub_cancel(mnt_pt):
    pass


def scrub_resume(mnt_pt):
    pass


def scrub_status(pool_name, pool_device):
    stats = {}
    mnt_pt = mount_root(pool_name, '/dev/' + pool_device)
    out, err, rc = run_command([BTRFS, 'scrub', 'status', mnt_pt])
    if (len(out) > 2):
        if (out[1].strip() == 'no stats available'):
            stats['status'] = 'running'
            return stats
        stats['duration'] = out[1].strip().split()[-2]
        fields = out[2].strip().split()
        stats['errors'] = fields[-2]
        mult_factor = 1
        if (fields[3][-2:] == 'MB'):
            mult_factor = 1024
            kb_scrubbed = fields[3][:-2]
        if (fields[3][-3:] == 'MiB'):
            mult_factor = 1024
            kb_scrubbed = fields[3][:-3]
        elif (fields[3][-2:] == 'GB'):
            mult_factor = 1024 ** 2
            kb_scrubbed = fields[3][:-2]
        elif (fields[3][-2:] == 'TB'):
            mult_factor = 1024 ** 3
            kb_scrubbed = fields[3][:-2]
        stats['kb_scrubbed'] = int(float(kb_scrubbed) * mult_factor)
        stats['status'] = 'finished'
        return stats
    return {'status': 'unknown', }


def device_scan():
    return run_command([BTRFS, 'device', 'scan'])


def btrfs_uuid(disk):
    """return uuid of a btrfs filesystem"""
    o, e, rc = run_command([BTRFS, 'filesystem', 'show', '/dev/%s' % disk])
    return o[0].split()[3]


def scan_btrfs_fs():
    o, e, rc = run_command([BTRFS, 'filesystem', 'show'])
    fs_map = {}
    cur_uuid = None
    for l in o:
        l = l.strip()
        if (re.match('Label: ', l) is not None):
            cur_uuid = l.split()[3]
        elif (re.match('devid', l) is not None):
            device = l.split()[-1].split('/')[-1]
            fs_map[device] = cur_uuid
    return fs_map


def root_disk():
    """
    returns the partition(s) used for /. Typically it's sda.
    """
    with open('/proc/mounts') as fo:
        for line in fo.readlines():
            fields = line.split()
            if (fields[1] == '/' and
                (fields[2] == 'ext4' or fields[2] == 'btrfs')):
                return fields[0][5:-1]
    msg = ('root filesystem is not BTRFS. During Rockstor installation, '
           'you must select BTRFS instead of LVM and other options for '
           'root filesystem. Please re-install Rockstor properly.')
    raise NonBTRFSRootException(msg)


def scan_disks(min_size):
    """
    min_size is in KB, so it is also number of blocks. Discard any disk with
    num_blocks < min_size
    """
    root = root_disk()
    disks = {}
    fs_map = scan_btrfs_fs()
    with open('/proc/partitions') as pfo:
        for line in pfo.readlines():
            disk_fields = line.split()
            if (len(disk_fields) != 4):
                continue
            if (re.match('sd[a-z]+$|xvd[a-z]+$', disk_fields[3]) is not None):
                name = disk_fields[3]
                #  each block is 1KB.
                num_blocks = int(disk_fields[2])
                if (num_blocks < min_size):
                    continue
                uuid = None
                if (name in fs_map):
                    uuid = fs_map[name]
                disk = Disk(name=name, size=num_blocks, free=num_blocks,
                            uuid=uuid)
                disks[name] = disk.__repr__()
            elif (re.match('sd[a-z]+[0-9]+$|xvd[a-z]+[0-9]+$', disk_fields[3])
                  is not None):
                name = disk_fields[3][0:-1]
                if (name in disks):
                    if (name == root):
                        del(disks[name])
                    else:
                        disks[name]['parted'] = True
    return disks


def wipe_disk(disk):
    """
    removes partition table on a disk by dd'ing first 512 bytes
    """
    disk = ('/dev/%s' % disk)
    run_command([DD, 'if=/dev/zero', 'of=%s' % disk, 'bs=512', 'count=1'])
    return run_command([SFDISK, '-R', disk])
