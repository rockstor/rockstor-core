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

from system.osi import (run_command, create_tmp_dir, rm_tmp_dir)


MKFS_BTRFS = '/sbin/mkfs.btrfs'
BTRFS = '/sbin/btrfs'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
DD = '/bin/dd'
SYNC = '/bin/sync'
DEFAULT_MNT_DIR = '/mnt2/'
DF = '/bin/df'

def add_pool(name, data_raid, meta_raid, disks):
    """
    pool is a btrfs filesystem.
    """
    disks_fp = ['/dev/' + d for d in disks]
    cmd = [MKFS_BTRFS, '-d', data_raid, '-m', meta_raid, '-L', name]
    cmd.extend(disks_fp)
    out, err, rc = run_command(cmd)
    enable_quota(name, disks_fp[0])
    return out, err, rc

def pool_usage(pool_name, device):
    device = '/dev/' + device
    root_mnt_pt = mount_root(pool_name, device)
    usage_cmd = [BTRFS, 'filesystem', 'df', root_mnt_pt]
    out, err, rc = run_command(usage_cmd)
    umount_root(root_mnt_pt)
    return out, err, rc

def pool_usage2(pool_name, device):
    device = ('/dev/%s' % device)
    root_mnt_pt = mount_root(pool_name, device)
    usage_cmd = [DF, '-k', '-P', root_mnt_pt]
    out, err, rc = run_command(usage_cmd)
    umount_root(root_mnt_pt)
    return out[1]

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
    umount_root(root_mnt_pt)
    return out, err, rc

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
            dd_cmd = [DD, 'if=/dev/zero', 'of=%s' % disk, 'bs=1024',
                      'count=100']
            out, err, rc = run_command(dd_cmd)
    #last command results -- not particularly useful
    return out, err, rc

def mount_root(pool_name, device):
    root_pool_mnt = DEFAULT_MNT_DIR + pool_name
    create_tmp_dir(root_pool_mnt)
    mnt_cmd = [MOUNT, '-t', 'btrfs', device, root_pool_mnt]
    run_command(mnt_cmd)
    return root_pool_mnt

def umount_root(root_pool_mnt):
    umount_cmd = [UMOUNT, '-l', root_pool_mnt]
    run_command(umount_cmd)
    rm_tmp_dir(root_pool_mnt)

def add_share(pool_name, pool_device, share_name):
    """
    share is a subvolume in btrfs.
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    sub_vol_cmd = [BTRFS, 'subvolume', 'create', subvol_mnt_pt]
    run_command(sub_vol_cmd)
    run_command(SYNC)
    umount_root(root_pool_mnt)

def mount_share(share_name, pool_device, mnt_pt):
    pool_device = '/dev/' + pool_device
    subvol_str = 'subvol=%s' % share_name
    create_tmp_dir(mnt_pt)
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, pool_device, mnt_pt]
    return run_command(mnt_cmd)

def is_share_mounted(sname):
    mnt_pt = DEFAULT_MNT_DIR + sname
    with open ('/proc/mounts') as pfo:
        for line in pfo.readlines():
            if (re.search(' ' + mnt_pt + ' ', line) is not None):
                return True
    return False

def share_id(pool_name, pool_device, share_name):
    """
    returns the subvolume id, becomes the share's uuid.
    @todo: this should be part of add_share -- btrfs create should atomically
    return the id
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    cmd = [BTRFS, 'subvolume', 'list', root_pool_mnt]
    out, err, rc = run_command(cmd)
    subvol_id = None
    for line in out:
        if (re.search(share_name + '$', line) is not None):
            subvol_id = line.split()[1]
            break
    run_command(SYNC)
    umount_root(root_pool_mnt)
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
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    delete_cmd = [BTRFS, 'subvolume', 'delete', subvol_mnt_pt]
    run_command(delete_cmd)
    umount_root(root_pool_mnt)

def add_snap(pool_name, pool_device, share_name, snap_name):
    """
    create a snapshot
    """
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    share_full_path = root_pool_mnt + '/' + share_name
    snap_full_path = root_pool_mnt + '/' + snap_name
    snap_cmd = [BTRFS, 'subvolume', 'snapshot', share_full_path,
                snap_full_path]
    run_command(snap_cmd)
    umount_root(root_pool_mnt)

def remove_snap(pool_name, pool_device, snap_name):
    """
    remove a snapshot. same as removing a share
    """
    return remove_share(pool_name, pool_device, snap_name)

def switch_quota(pool_name, device, flag='enable'):
    root_mnt_pt = mount_root(pool_name, device)
    cmd = [BTRFS, 'quota', flag, root_mnt_pt]
    out, err, rc = run_command(cmd)
    #@hack -- umount without sync failes.
    run_command(SYNC)
    umount_root(root_mnt_pt)
    return out, err, rc

def enable_quota(pool_name, device):
    return switch_quota(pool_name, device)

def disable_quota(pool_name, device):
    return switch_quota(pool_name, device, flag='disable')

def update_quota(pool_name, pool_device, qgroup, size_bytes):
    pool_device = '/dev/' + pool_device
    root_pool_mnt = mount_root(pool_name, pool_device)
    cmd = [BTRFS, 'qgroup', 'limit', size_bytes, qgroup, root_pool_mnt]
    out, err, rc = run_command(cmd)
    run_command(SYNC)
    umount_root(root_pool_mnt)
    return out, err, rc

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
            usage = fields[-1]
            break
    run_command(SYNC)
    umount_root(root_pool_mnt)
    if (usage is None):
        raise Exception('usage cannot be determined for share_id: %s' %
                        share_id)
    return usage
