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
import subprocess
import signal
import shutil
import collections
from system.osi import (run_command, create_tmp_dir, is_share_mounted,
                        is_mounted, get_virtio_disk_serial, get_disk_serial)
from system.exceptions import (CommandException, NonBTRFSRootException)
from pool_scrub import PoolScrub
from django_ztask.decorators import task
import uuid

import logging
logger = logging.getLogger(__name__)

MKFS_BTRFS = '/sbin/mkfs.btrfs'
BTRFS = '/sbin/btrfs'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
DD = '/bin/dd'
DEFAULT_MNT_DIR = '/mnt2/'
RMDIR = '/bin/rmdir'
WIPEFS = '/usr/sbin/wipefs'
QID = '2015'


Disk = collections.namedtuple('Disk',
                              'name model serial size transport vendor '
                              'hctl type fstype label btrfs_uuid parted root')


def add_pool(pool, disks):
    """
    pool is a btrfs filesystem.
    """
    disks_fp = ['/dev/' + d for d in disks]
    cmd = [MKFS_BTRFS, '-f', '-d', pool.raid, '-m', pool.raid, '-L',
           pool.name, ]
    cmd.extend(disks_fp)
    out, err, rc = run_command(cmd)
    enable_quota(pool)
    return out, err, rc


def get_pool_info(disk):
    cmd = [BTRFS, 'fi', 'show', '/dev/%s' % disk]
    o, e, rc = run_command(cmd)
    pool_info = {'disks': [],}
    for l in o:
        if (re.match('Label', l) is not None):
            fields = l.split()
            pool_info['label'] = fields[1].strip("'")
            pool_info['uuid'] = fields[3]
        elif (re.match('\tdevid', l) is not None):
            pool_info['disks'].append(l.split()[-1].split('/')[-1])
    return pool_info

def pool_raid(mnt_pt):
    o, e, rc = run_command([BTRFS, 'fi', 'df', mnt_pt])
    # data, system, metadata, globalreserve
    raid_d = {}
    for l in o:
        fields = l.split()
        if (len(fields) > 1):
            raid_d[fields[0][:-1].lower()] = fields[1][:-1].lower()
    if (raid_d['metadata'] == 'single'):
        raid_d['data'] = raid_d['metadata']
    return raid_d;

def cur_devices(mnt_pt):
    devices = []
    o, e, rc = run_command([BTRFS, 'fi', 'show', mnt_pt])
    for l in o:
        l = l.strip()
        if (re.match('devid ', l) is not None):
            devices.append(l.split()[-1])
    return devices


def resize_pool(pool, dev_list, add=True):
    dev_list = ['/dev/' + d for d in dev_list]
    root_mnt_pt = mount_root(pool)
    cur_dev = cur_devices(root_mnt_pt)
    resize_flag = 'add'
    if (not add):
        resize_flag = 'delete'
    resize_cmd = [BTRFS, 'device', resize_flag, ]
    resize = False
    for d in dev_list:
        if (((resize_flag == 'add' and (d not in cur_dev)) or
                (resize_flag == 'delete' and (d in cur_dev)))):
            resize = True
            resize_cmd.append(d)
    if (not resize):
        return
    resize_cmd.append(root_mnt_pt)
    return run_command(resize_cmd)


def mount_root(pool):
    device = pool.disk_set.first().name
    root_pool_mnt = DEFAULT_MNT_DIR + pool.name
    if (is_share_mounted(pool.name)):
        return root_pool_mnt
    create_tmp_dir(root_pool_mnt)
    mnt_device = '/dev/disk/by-label/%s' % pool.name
    if (not os.path.exists(mnt_device)):
        mnt_device = device
        if (re.match('/dev/', device) is None):
            mnt_device = ('/dev/%s' % mnt_device)
    mnt_cmd = [MOUNT, mnt_device, root_pool_mnt, ]
    mnt_options = ''
    if (pool.mnt_options is not None):
        mnt_options = pool.mnt_options
    if (pool.compression is not None):
        if (re.search('compress', mnt_options) is None):
            mnt_options = ('%s,compress=%s' % (mnt_options, pool.compression))
    if (len(mnt_options) > 0):
        mnt_cmd.extend(['-o', mnt_options])
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


def remount(mnt_pt, mnt_options):
    if (is_mounted(mnt_pt)):
        run_command([MOUNT, '-o', 'remount,%s' % mnt_options, mnt_pt])
    return True


def is_subvol(mnt_pt):
    show_cmd = [BTRFS, 'subvolume', 'show', mnt_pt]
    o, e, rc = run_command(show_cmd, throw=False)
    if (rc == 0):
        return True
    return False


def subvol_info(mnt_pt):
    info = {}
    o, e, rc = run_command([BTRFS, 'subvolume', 'show', mnt_pt], throw=False)
    if (rc == 0):
        for i in o:
            fields = i.strip().split(':')
            if (len(fields) > 1):
                info[fields[0].strip()] = fields[1].strip()
    return info


def add_share(pool, share_name, qid):
    """
    share is a subvolume in btrfs.
    """
    root_pool_mnt = mount_root(pool)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    show_cmd = [BTRFS, 'subvolume', 'show', subvol_mnt_pt]
    o, e, rc = run_command(show_cmd, throw=False)
    if (rc == 0):
        return o, e, rc
    if (not is_subvol(subvol_mnt_pt)):
        sub_vol_cmd = [BTRFS, 'subvolume', 'create', '-i', qid, subvol_mnt_pt]
        return run_command(sub_vol_cmd)
    return True


def mount_share(share, mnt_pt):
    if (is_mounted(mnt_pt)):
        return
    mount_root(share.pool)
    pool_device = ('/dev/%s' % share.pool.disk_set.first().name)
    subvol_str = 'subvol=%s' % share.subvol_name
    create_tmp_dir(mnt_pt)
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, pool_device, mnt_pt]
    return run_command(mnt_cmd)


def mount_snap(share, snap_name, snap_mnt=None):
    pool_device = ('/dev/%s' % share.pool.disk_set.first().name)
    share_path = ('%s%s' % (DEFAULT_MNT_DIR, share.name))
    rel_snap_path = ('.snapshots/%s/%s' % (share.name, snap_name))
    snap_path = ('%s%s/%s' %
                 (DEFAULT_MNT_DIR, share.pool.name, rel_snap_path))
    if (snap_mnt is None):
        snap_mnt = ('%s/.%s' % (share_path, snap_name))
    if (is_mounted(snap_mnt)):
        return
    mount_share(share, share_path)
    if (is_subvol(snap_path)):
        create_tmp_dir(snap_mnt)
        return run_command([MOUNT, '-o', 'subvol=%s' % rel_snap_path,
                            pool_device, snap_mnt])


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
                # rc == 19 is due to the slow kernel cleanup thread. It should
                # eventually succeed.
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


def shares_info(pool):
    # return a list of share names under this mount_point.
    # useful to gather names of all shares in a pool
    try:
        mnt_pt = mount_root(pool)
    except CommandException, e:
        if (e.rc == 32):
            #mount failed, so we just assume that something has gone wrong at a
            #lower level, like a device failure. Return empty share map.
            #application state can be removed. If the low level failure is
            #recovered, state gets reconstructed anyway.
            return {}
        raise
    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-s', mnt_pt])
    snap_idmap = {}
    for l in o:
        if (re.match('ID ', l) is not None):
            fields = l.strip().split()
            snap_idmap[fields[1]] = fields[-1]

    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-p', mnt_pt])
    shares_d = {}
    share_ids = []
    for l in o:
        if (re.match('ID ', l) is None):
            continue
        fields = l.split()
        vol_id = fields[1]
        if (vol_id in snap_idmap):
            # snapshot
            # if the snapshot directory is direct child of a pool and is rw,
            # then it's a Share. (aka Rockstor Share clone).
            clone = False
            if (len(snap_idmap[vol_id].split('/')) == 1):
                o, e, rc = run_command([BTRFS, 'property', 'get',
                                        '%s/%s' % (mnt_pt, snap_idmap[vol_id])])
                for l in o:
                    if (l == 'ro=false'):
                        clone = True
            if (not clone):
                continue

        parent_id = fields[5]
        if (parent_id in share_ids):
            # subvol of subvol. add it so child subvols can also be ignored.
            share_ids.append(vol_id)
        elif (parent_id in snap_idmap):
            # snapshot/subvol of snapshot.
            # add it so child subvols can also be ignored.
            snap_idmap[vol_id] = fields[-1]
        else:
            shares_d[fields[-1]] = '0/%s' % vol_id
            share_ids.append(vol_id)
    return shares_d

def parse_snap_details(mnt_pt, fields):
    writable = True
    snap_name = None
    o1, e1, rc1 = run_command([BTRFS, 'property', 'get',
                               '%s/%s' % (mnt_pt, fields[-1])])
    for l1 in o1:
        if (re.match('ro=', l1) is not None):
            if (l1.split('=')[1] == 'true'):
                writable = False
            if (writable is True):
                if (len(fields[-1].split('/')) == 1):
                    # writable snapshot + direct child of pool.
                    # So we'll treat it as a share.
                    continue
            snap_name = fields[-1].split('/')[-1]
    return snap_name, writable

def snaps_info(mnt_pt, share_name):
    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-u', '-p', '-q', mnt_pt])
    share_id = share_uuid = None
    for l in o:
        if (re.match('ID ', l) is not None):
            fields = l.split()
            if (fields[-1] == share_name):
                share_id = fields[1]
                share_uuid = fields[12]
    if (share_id is None): return {}

    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-s', '-p', '-q',
                            '-u', mnt_pt])
    snaps_d = {}
    snap_uuids = []
    for l in o:
        if (re.match('ID ', l) is not None):
            fields = l.split()
            # parent uuid must be share_uuid or another snapshot's uuid
            if (fields[7] != share_id and fields[15] != share_uuid and
                fields[15] not in snap_uuids):
                continue
            snap_name, writable = parse_snap_details(mnt_pt, fields)
            snaps_d[snap_name] = ('0/%s' % fields[1], writable, )
            # we rely on the observation that child snaps are listed after their
            # parents, so no need to iterate through results separately.
            # Instead, we add the uuid of a snap to the list and look up if
            # it's a parent of subsequent entries.
            snap_uuids.append(fields[17])

    return snaps_d


def share_id(pool, share_name):
    """
    returns the subvolume id, becomes the share's uuid.
    @todo: this should be part of add_share -- btrfs create should atomically
    return the id
    """
    root_pool_mnt = mount_root(pool)
    out, err, rc = subvol_list_helper(root_pool_mnt)
    subvol_id = None
    for line in out:
        if (re.search(share_name + '$', line) is not None):
            subvol_id = line.split()[1]
            break
    if (subvol_id is not None):
        return subvol_id
    raise Exception('subvolume id for share: %s not found.' % share_name)


def remove_share(pool, share_name, pqgroup):
    """
    umount share if its mounted.
    mount root pool
    btrfs subvolume delete root_mnt/vol_name
    umount root pool
    """
    if (is_share_mounted(share_name)):
        mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, share_name))
        umount_root(mnt_pt)
    root_pool_mnt = mount_root(pool)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    if (not is_subvol(subvol_mnt_pt)):
        return
    qgroup = ('0/%s' % share_id(pool, share_name))
    delete_cmd = [BTRFS, 'subvolume', 'delete', subvol_mnt_pt]
    run_command(delete_cmd, log=True)
    qgroup_destroy(qgroup, root_pool_mnt)
    return qgroup_destroy(pqgroup, root_pool_mnt)

def remove_snap(pool, share_name, snap_name):
    root_mnt = mount_root(pool)
    snap_path = ('%s/.snapshots/%s/%s' %
                 (root_mnt, share_name, snap_name))
    if (is_mounted(snap_path)):
        umount_root(snap_path)
    if (is_subvol(snap_path)):
        qgroup = ('0/%s' % share_id(pool, snap_name))
        run_command([BTRFS, 'subvolume', 'delete', snap_path], log=True)
        return qgroup_destroy(qgroup, root_mnt)
    else:
        o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-s', root_mnt])
        for l in o:
            #just give the first match.
            if (re.match('ID.*%s$' % snap_name, l) is not None):
                snap = '%s/%s' % (root_mnt, l.split()[-1])
                return run_command([BTRFS, 'subvolume', 'delete', snap], log=True)


def add_snap_helper(orig, snap, readonly=False):
    cmd = [BTRFS, 'subvolume', 'snapshot', orig, snap]
    if (readonly):
        cmd.insert(3, '-r')
    try:
        return run_command(cmd)
    except CommandException, ce:
        if (ce.rc != 19):
            # rc == 19 is due to the slow kernel cleanup thread. snapshot gets
            # created just fine. lookup is delayed arbitrarily.
            raise ce


def add_clone(pool, share, clone, snapshot=None):
    """
    clones either a share or a snapshot
    """
    pool_mnt = mount_root(pool)
    orig_path = pool_mnt
    if (snapshot is not None):
        orig_path = ('%s/.snapshots/%s/%s' %
                     (orig_path, share, snapshot))
    else:
        orig_path = ('%s/%s' % (orig_path, share))
    clone_path = ('%s/%s' % (pool_mnt, clone))
    return add_snap_helper(orig_path, clone_path)


def add_snap(pool, share_name, snap_name, readonly=False):
    """
    create a snapshot
    """
    root_pool_mnt = mount_root(pool)
    share_full_path = ('%s/%s' % (root_pool_mnt, share_name))
    snap_dir = ('%s/.snapshots/%s' % (root_pool_mnt, share_name))
    create_tmp_dir(snap_dir)
    snap_full_path = ('%s/%s' % (snap_dir, snap_name))
    return add_snap_helper(share_full_path, snap_full_path, readonly)


def rollback_snap(snap_name, sname, subvol_name, pool):
    """
    1. validate destination snapshot and umount the share
    2. remove the share
    3. move the snapshot to share location and mount it.
    """
    mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, sname))
    snap_fp = ('%s/%s/.snapshots/%s/%s' % (DEFAULT_MNT_DIR, pool.name, sname,
                                           snap_name))
    if (not is_subvol(snap_fp)):
        raise Exception('Snapshot(%s) does not exist. Rollback is not '
                        'possible' % snap_fp)
    mount_root(pool)
    if (is_share_mounted(sname)):
        umount_root(mnt_pt)
    remove_share(pool, subvol_name, '-1/-1')
    shutil.move(snap_fp, '%s/%s/%s' % (DEFAULT_MNT_DIR, pool.name, sname))
    create_tmp_dir(mnt_pt)
    subvol_str = 'subvol=%s' % sname
    dpath = '/dev/%s' % pool.disk_set.first().name
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, dpath, mnt_pt]
    run_command(mnt_cmd)


def switch_quota(pool, flag='enable'):
    root_mnt_pt = mount_root(pool)
    cmd = [BTRFS, 'quota', flag, root_mnt_pt]
    return run_command(cmd)


def enable_quota(pool):
    return switch_quota(pool)


def disable_quota(pool_name):
    return switch_quota(pool_name, flag='disable')


def qgroup_id(pool, share_name):
    sid = share_id(pool, share_name)
    return '0/' + sid

def qgroup_max(mnt_pt):
    o, e, rc = run_command([BTRFS, 'qgroup', 'show', mnt_pt], log=True)
    res = 0
    for l in o:
        if (re.match('%s/' % QID, l) is not None):
            cid = int(l.split()[0].split('/')[1])
            if (cid > res):
                res = cid
    return res

def qgroup_create(pool):
    # mount pool
    mnt_pt = mount_root(pool)
    qid = ('%s/%d' % (QID, qgroup_max(mnt_pt) + 1))
    o, e, rc = run_command([BTRFS, 'qgroup', 'create', qid, mnt_pt], log=True)
    return qid


def qgroup_destroy(qid, mnt_pt):
    o, e, rc = run_command([BTRFS, 'qgroup', 'show', mnt_pt])
    for l in o:
        if (re.match(qid, l) is not None and
            l.split()[0] == qid):
            return run_command([BTRFS, 'qgroup', 'destroy', qid, mnt_pt], log=True)
    return False


def qgroup_is_assigned(qid, pqid, mnt_pt):
    # Returns true if the given qgroup qid is already assigned to pqid for the
    # path(mnt_pt)
    o, e, rc = run_command([BTRFS, 'qgroup', 'show', '-pc', mnt_pt])
    for l in o:
        fields = l.split()
        if (len(fields) > 3 and
            fields[0] == qid and
            fields[3] == pqid):
            return True
    return False

def qgroup_assign(qid, pqid, mnt_pt):
    if (qgroup_is_assigned(qid, pqid, mnt_pt)):
        return True

    # in btrfs-progs 4.2, qgroup assign succeeds but throws a warning:
    # "WARNING: # quotas may be inconsistent, rescan needed" and returns with
    # exit code 1.
    try:
        run_command([BTRFS, 'qgroup', 'assign', qid, pqid, mnt_pt],
                    log=True)
    except CommandException, e:
        wmsg = 'WARNING: quotas may be inconsistent, rescan needed'
        if (e.rc == 1 and e.out[0] == wmsg):
            if (qgroup_is_assigned(qid, pqid, mnt_pt)):
                return True
        raise e


def update_quota(pool, qgroup, size_bytes):
    root_pool_mnt = mount_root(pool)
    # Until btrfs adds better support for qgroup limits. We'll not set limits.
    # It looks like we'll see the fixes in 4.2 and final ones by 4.3.
    # cmd = [BTRFS, 'qgroup', 'limit', str(size_bytes), qgroup, root_pool_mnt]
    cmd = [BTRFS, 'qgroup', 'limit', 'none', qgroup, root_pool_mnt]
    return run_command(cmd, log=True)


def convert_to_KiB(size):
    SMAP = {
        'KiB': 1,
        'MiB': 1024,
        'GiB': 1024 * 1024,
        'TiB': 1024 * 1024 * 1024,
        'PiB': 1024 * 1024 * 1024 * 1024, }
    suffix = size[-3:]
    num = size[:-3]
    if (suffix not in SMAP):
        if (size[-1] == 'B'):
            return 0
        raise Exception('Unknown suffix(%s) while converting to KiB' % suffix)
    return int(float(num) * SMAP[suffix])


def share_usage(pool, share_id):
    """
    for now, exclusive byte count
    """
    root_pool_mnt = mount_root(pool)
    cmd = [BTRFS, 'qgroup', 'show', root_pool_mnt]
    out, err, rc = run_command(cmd, log=True)
    rusage = eusage = None
    for line in out:
        fields = line.split()
        if (fields[0] == share_id):
            rusage = convert_to_KiB(fields[-2])
            eusage = convert_to_KiB(fields[-2])
            break
    if (rusage is None or eusage is None):
        raise Exception('usage cannot be determined for share_id: %s' %
                        share_id)
    return (rusage, eusage)


def shares_usage(pool, share_map, snap_map):
    # don't mount the pool if at least one share in the map is mounted.
    usage_map = {}
    mnt_pt = None
    for s in share_map.keys():
        if (is_share_mounted(share_map[s])):
            mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, share_map[s]))
            break
    if (mnt_pt is None):
        mnt_pt = mount_root(pool)
    cmd = [BTRFS, 'qgroup', 'show', mnt_pt]
    out, err, rc = run_command(cmd, log=True)
    combined_map = dict(share_map, **snap_map)
    for line in out:
        fields = line.split()
        if (len(fields) > 0 and fields[0] in combined_map):
            r_usage = convert_to_KiB(fields[-2])
            e_usage = convert_to_KiB(fields[-1])
            usage_map[combined_map[fields[0]]] = (r_usage, e_usage)
    return usage_map


def pool_usage(mnt_pt):
    # @todo: remove temporary raid5/6 custom logic once fi usage
    # supports raid5/6.
    cmd = [BTRFS, 'fi', 'usage', '-b', mnt_pt]
    total = 0
    inuse = 0
    free = 0
    data_ratio = 1
    raid56 = False
    parity = 1
    disks = set()
    out, err, rc = run_command(cmd)
    for e in err:
        e = e.strip()
        if (re.match('WARNING: RAID56', e) is not None):
            raid56 = True

    for o in out:
        o = o.strip()
        if (raid56 is True and re.match('/dev/', o) is not None):
            disks.add(o.split()[0])
        elif (raid56 is True and re.match('Data,RAID', o) is not None):
            if (o[5:10] == 'RAID6'):
                parity = 2
        elif (re.match('Device size:', o) is not None):
            total = int(o.split()[2]) / 1024
        elif (re.match('Used:', o) is not None):
            inuse = int(o.split()[1]) / 1024
        elif (re.match('Free ', o) is not None):
            free = int(o.split()[2]) / 1024
        elif (re.match('Data ratio:', o) is not None):
            data_ratio = float(o.split()[2])
            if (data_ratio < 0.01):
                data_ratio = 0.01
    if (raid56 is True):
        num_disks = len(disks)
        if (num_disks > 0):
            per_disk = total / num_disks
            total = (num_disks - parity) * per_disk
    else:
        total = total / data_ratio
        inuse = inuse / data_ratio
    free = total - inuse
    return (total, inuse, free)


def scrub_start(pool, force=False):
    mnt_pt = mount_root(pool)
    p = PoolScrub(mnt_pt)
    p.start()
    return p.pid


def scrub_status(pool):
    stats = {'status': 'unknown', }
    mnt_pt = mount_root(pool)
    out, err, rc = run_command([BTRFS, 'scrub', 'status', '-R', mnt_pt])
    if (len(out) > 1):
        if (re.search('running', out[1]) is not None):
            stats['status'] = 'running'
        elif (re.search('finished', out[1]) is not None):
            stats['status'] = 'finished'
            dfields = out[1].split()[-1].split(':')
            stats['duration'] = ((int(dfields[0]) * 60 * 60) +
                                 (int(dfields[1]) * 60) + int(dfields[2]))
        else:
            return stats
    else:
        return stats
    for l in out[2:-1]:
        fields = l.strip().split(': ')
        if (fields[0] == 'data_bytes_scrubbed'):
            stats['kb_scrubbed'] = int(fields[1]) / 1024
        else:
            stats[fields[0]] = int(fields[1])
    return stats


@task()
def start_balance(mnt_pt, force=False, convert=None):
    cmd = ['btrfs', 'balance', 'start', mnt_pt]
    if (force):
        cmd.insert(3, '-f')
    if (convert is not None):
        cmd.insert(3, '-dconvert=%s' % convert)
        cmd.insert(3, '-mconvert=%s' % convert)
    run_command(cmd)


def balance_status(pool):
    stats = {'status': 'unknown', }
    mnt_pt = mount_root(pool)
    out, err, rc = run_command([BTRFS, 'balance', 'status', mnt_pt],
                               throw=False)
    if (len(out) > 0):
        if (re.match('Balance', out[0]) is not None):
            stats['status'] = 'running'
            if ((len(out) > 1 and
                    re.search('chunks balanced', out[1]) is not None)):
                percent_left = out[1].split()[-2][:-1]
                try:
                    percent_left = int(percent_left)
                    stats['percent_done'] = 100 - percent_left
                except:
                    pass
        elif (re.match('No balance', out[0]) is not None):
            stats['status'] = 'finished'
            stats['percent_done'] = 100
    return stats


def device_scan():
    return run_command([BTRFS, 'device', 'scan'])


def btrfs_uuid(disk):
    """return uuid of a btrfs filesystem"""
    o, e, rc = run_command([BTRFS, 'filesystem', 'show', '/dev/%s' % disk])
    return o[0].split()[3]


def btrfs_label(disk):
    o, e, rc = run_command([BTRFS, 'filesystem', 'label', '/dev/%s' % disk])
    return o[0]


def btrfs_importable(disk):
    o, e, rc = run_command([BTRFS, 'check', '/dev/%s' % disk], throw=False)
    if (rc == 0):
        return True
    return False


def root_disk():
    """
    Returns the drive device name where / mount point is found.
    Works by parsing /proc/mounts. Eg if the root entry was as follows:
    /dev/sdc3 / btrfs rw,noatime,ssd,space_cache,subvolid=258,subvol=/root 0 0
    the returned value is sdc
    The assumption is that the partition number will be a single character.
    """
    with open('/proc/mounts') as fo:
        for line in fo.readlines():
            fields = line.split()
            if (fields[1] == '/' and
                    (fields[2] == 'ext4' or fields[2] == 'btrfs')):
                disk = os.path.realpath(fields[0])
                return disk[5:-1]
    msg = ('root filesystem is not BTRFS. During Rockstor installation, '
           'you must select BTRFS instead of LVM and other options for '
           'root filesystem. Please re-install Rockstor properly.')
    raise NonBTRFSRootException(msg)


def scan_disks(min_size):
    root = root_disk()
    cmd = ['/usr/bin/lsblk', '-P', '-o',
           'NAME,MODEL,SERIAL,SIZE,TRAN,VENDOR,HCTL,TYPE,FSTYPE,LABEL,UUID']
    o, e, rc = run_command(cmd)
    dnames = {}
    disks = []
    serials = []
    root_serial = root_model = root_transport = root_vendor = root_hctl = None
    # to use udevadm to retrieve serial number rather than lsblk, make this True
    always_use_udev_serial = False
    device_names_seen = []
    for l in o:
        if (re.match('NAME', l) is None):
            continue
        dmap = {}
        cur_name = ''
        cur_val = ''
        name_iter = True
        val_iter = False
        sl = l.strip()
        i = 0
        while i < len(sl):
            if (name_iter and sl[i] == '=' and sl[i + 1] == '"'):
                name_iter = False
                val_iter = True
                i = i + 2
            elif (val_iter and sl[i] == '"' and
                    (i == (len(sl) - 1) or sl[i + 1] == ' ')):
                val_iter = False
                name_iter = True
                i = i + 2
                dmap[cur_name.strip()] = cur_val.strip()
                cur_name = ''
                cur_val = ''
            elif (name_iter):
                cur_name = cur_name + sl[i]
                i = i + 1
            elif (val_iter):
                cur_val = cur_val + sl[i]
                i = i + 1
            else:
                raise Exception('Failed to parse lsblk output: %s' % sl)
        # md devices, such as mdadmin software raid and some hardware raid block
        # devices show up in lsblk's output multiple times with identical info.
        # Given we only need one copy of this info we remove duplicate device
        # name entries, also offers more sane output to views/disk.py where name
        # will be used as the index
        if (dmap['NAME'] in device_names_seen):
            continue
        device_names_seen.append(dmap['NAME'])
        # We are not interested in CD / DVD rom devices so skip to next device
        if (dmap['TYPE'] == 'rom'):
            continue
        if (dmap['NAME'] == root):
            # Based on our root variable we are looking at the system drive.
            # Given lsblk doesn't return serial, model, transport, vendor, hctl
            # when displaying partitions we grab and stash them while we are
            # looking at the root drive directly.
            # N.B. assumption is lsblk first displays devices then partitions,
            # this is the observed behaviour so far.
            root_serial = dmap['SERIAL']
            root_model = dmap['MODEL']
            root_transport = dmap['TRAN']
            root_vendor = dmap['VENDOR']
            root_hctl = dmap['HCTL']
        if (dmap['TYPE'] == 'part'):
            for dname in dnames.keys():
                if (re.match(dname, dmap['NAME']) is not None):
                    dnames[dname][11] = True
        if (((dmap['NAME'] != root and dmap['TYPE'] != 'part') or
                (dmap['TYPE'] == 'part' and dmap['FSTYPE'] == 'btrfs'))):
            dmap['parted'] = False  # part = False by default
            dmap['root'] = False
            if (dmap['TYPE'] == 'part' and dmap['FSTYPE'] == 'btrfs'):
                # btrfs partition for root (rockstor_rockstor) pool
                if (re.match(root, dmap['NAME']) is not None):
                    # now add the properties we stashed when looking at the root
                    # drive rather than the root partition we see here.
                    dmap['SERIAL'] = root_serial
                    dmap['root'] = True
                    dmap['MODEL'] = root_model
                    dmap['TRAN'] = root_transport
                    dmap['VENDOR'] = root_vendor
                    dmap['HCTL'] = root_hctl
                else:
                    # ignore btrfs partitions that are not for rootfs.
                    continue
            # convert size into KB
            size_str = dmap['SIZE']
            if (size_str[-1] == 'G'):
                dmap['SIZE'] = int(float(size_str[:-1]) * 1024 * 1024)
            elif (size_str[-1] == 'T'):
                dmap['SIZE'] = int(float(size_str[:-1]) * 1024 * 1024 * 1024)
            else:
                continue
            if (dmap['SIZE'] < min_size):
                continue
            if (dmap['SERIAL'] == '' or always_use_udev_serial):
                # lsblk fails to retrieve SERIAL from VirtIO drives and some
                # sdcard devices so try specialized function.
                # dmap['SERIAL'] = get_virtio_disk_serial(dmap['NAME'])
                dmap['SERIAL'] = get_disk_serial(dmap['NAME'], None)
            if (dmap['SERIAL'] == '' or (dmap['SERIAL'] in serials)):
                # No serial number still or its a repeat.
                # Overwrite drive serial entry in db with 'fake-serial-' + uuid4
                # see disk/disks_table.jst for a use of this flag mechanism.
                # Previously we did dmap['SERIAL'] = dmap['NAME'] which is less
                # robust as it can itself produce duplicate serial numbers in db
                dmap['SERIAL'] = 'fake-serial-' + str(uuid.uuid4())
                # 12 chars (fake-serial-) + 36 chars (uuid4) = 48 chars
            serials.append(dmap['SERIAL'])
            for k in dmap.keys():
                if (dmap[k] == ''):
                    dmap[k] = None
            dnames[dmap['NAME']] = [dmap['NAME'], dmap['MODEL'],
                                    dmap['SERIAL'], dmap['SIZE'],
                                    dmap['TRAN'], dmap['VENDOR'],
                                    dmap['HCTL'], dmap['TYPE'],
                                    dmap['FSTYPE'], dmap['LABEL'],
                                    dmap['UUID'], dmap['parted'],
                                    dmap['root'], ]
    for d in dnames.keys():
        disks.append(Disk(*dnames[d]))
    return disks


def wipe_disk(disk):
    disk = ('/dev/%s' % disk)
    return run_command([WIPEFS, '-a', disk])


def blink_disk(disk, total_exec, read, sleep):
    DD_CMD = [DD, 'if=/dev/%s' % disk, 'of=/dev/null', 'bs=512',
              'conv=noerror']
    p = subprocess.Popen(DD_CMD, shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    total_elapsed_time = 0
    while (total_elapsed_time < total_exec):
        if (p.poll() is not None):
            return
        time.sleep(read)
        p.send_signal(signal.SIGSTOP)
        time.sleep(sleep)
        total_elapsed_time += read + sleep
        p.send_signal(signal.SIGCONT)
    p.terminate()


def set_property(mnt_pt, name, val, mount=True):
    if (mount is not True or is_mounted(mnt_pt)):
        cmd = [BTRFS, 'property', 'set', mnt_pt, name, val]
        return run_command(cmd)


def get_snap(subvol_path, oldest=False, num_retain=None, regex=None):
    if (not os.path.isdir(subvol_path)): return None
    share_name = subvol_path.split('/')[-1]
    cmd = [BTRFS, 'subvol', 'list', '-o', subvol_path]
    o, e, rc = run_command(cmd)
    snaps = {}
    for l in o:
        fields = l.split()
        if (len(fields) > 0):
            snap_fields = fields[-1].split('/')
            if (len(snap_fields) != 3 or
                snap_fields[1] != share_name):
                #not the Share we are interested in.
                continue
            if (regex is not None and re.search(regex, snap_fields[2]) is None):
                #regex not in the name
                continue
            snaps[int(fields[1])] = snap_fields[2]
    snap_ids = sorted(snaps.keys())
    if (oldest):
        if(len(snap_ids) > num_retain):
            return snaps[snap_ids[0]]
    elif (len(snap_ids) > 0):
        return snaps[snap_ids[-1]]
    return None


def get_oldest_snap(subvol_path, num_retain, regex=None):
    return get_snap(subvol_path, oldest=True, num_retain=num_retain, regex=regex)


def get_lastest_snap(subvol_path, regex=None):
    return get_snap(subvol_path, regex=regex)
