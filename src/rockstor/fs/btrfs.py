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
import time
import os
import shutil
from system.osi import run_command, create_tmp_dir, is_share_mounted, \
    is_mounted, get_dev_byid_name, convert_to_kib, toggle_path_rw, \
    get_device_path
from system.exceptions import (CommandException)
from pool_scrub import PoolScrub
from django_ztask.decorators import task
from django.conf import settings
import logging

"""
system level helper methods to interact with the btrfs filesystem
"""

logger = logging.getLogger(__name__)

MKFS_BTRFS = '/sbin/mkfs.btrfs'
BTRFS = '/sbin/btrfs'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
CHATTR = '/usr/bin/chattr'
DEFAULT_MNT_DIR = '/mnt2/'
RMDIR = '/bin/rmdir'
QID = '2015'
# The following model/db default setting is also used when quotas are disabled.
PQGROUP_DEFAULT = settings.MODEL_DEFS['pqgroup']


def add_pool(pool, disks):
    """
    Makes a btrfs pool (filesystem) of name 'pool' using the by-id disk names
    provided, then attempts to enables quotas for this pool.
    :param pool: name of pool to create.
    :param disks: list of by-id disk names without paths to make the pool from.
    :return o, err, rc from last command executed.
    """
    disks_fp = [get_device_path(d) for d in disks]
    draid = mraid = pool.raid
    if pool.raid == 'single':
        mraid = 'dup'
    cmd = [MKFS_BTRFS, '-f', '-d', draid, '-m', mraid, '-L', pool.name]
    cmd.extend(disks_fp)
    # Run the create pool command, any exceptions are logged and raised by
    # run_command as a CommandException.
    out, err, rc = run_command(cmd, log=True)
    # Note that given our cmd (mkfs.btrfs) is executed with the default
    # run_command flag of throw=True then program execution is stopped in the
    # event of rc != 0 so the following clause is redundant but offers an
    # additional level of isolation.
    # Only execute enable_quota on above btrfs command having an rc=0
    if rc == 0:
        out2, err2, rc2 = enable_quota(pool)
        if rc2 != 0:
            e_msg = (
                'non-zero code (%d) returned by enable_quota() while '
                'enabling quota on a newly created pool : pool name = %s, '
                'output: %s, error: %s.' % (rc2, pool.name, out2, err2))
            logger.error(e_msg)
            return out2, err2, rc2
    else:
        logger.error('Unknown state in add_pool() - non-zero code (%d) '
                     'returned by %s with output: %s and error: %s.'
                     % (rc, cmd, out, err))
    return out, err, rc


def get_pool_info(disk):
    """
    Extracts any pool information by running btrfs fi show <disk> and collates
    the results by 'Label', 'uuid', and a list of disk names. The disks names
    found are translated to the by-id type (/dev/disk/by-id)so that their
    counterparts in the db's Disk.name field can be found.
    N.B. devices without serial may have no by-id counterpart.
    Used by CommandView()._refresh_pool_state() and
    DiskDetailView()._btrfs_disk_import
    :param disk: by-id disk name without path
    :return: a dictionary with keys of 'disks', 'label', and 'uuid';
    disks keys a list of devices, while label and uuid keys are for strings.
    """
    dpath = get_device_path(disk)
    cmd = [BTRFS, 'fi', 'show', dpath]
    o, e, rc = run_command(cmd)
    pool_info = {'disks': [], }
    for l in o:
        if (re.match('Label', l) is not None):
            fields = l.split()
            pool_info['uuid'] = fields[3]
            label = fields[1].strip("'")
            if label == 'none':
                # fs has no label, set label = uuid.
                label = pool_info['uuid']
                run_command([BTRFS, 'fi', 'label', dpath, label])
            pool_info['label'] = label
        elif (re.match('\tdevid', l) is not None):
            # We have a line starting wth <tab>devid, extract the dev name.
            # Previously this would have been sda and used as is but we need
            # it's by-id references as that is the new format for Disks.name.
            # Original sda extraction:
            # pool_info['disks'].append(l.split()[-1].split('/')[-1])
            # Updated '/dev/sda' extraction to save on a split we no longer
            # need and use this 'now' name to get our by-id name with path
            # removed. This is required as that is how device names are stored
            # in the db Disk.name so that we can locate a drive and update it's
            # pool field reference.
            dev_byid, is_byid = get_dev_byid_name(l.split()[-1], True)
            pool_info['disks'].append(dev_byid)
    return pool_info


def pool_raid(mnt_pt):
    # TODO: propose name change to get_pool_raid_levels(mnt_pt)
    o, e, rc = run_command([BTRFS, 'fi', 'df', mnt_pt])
    # data, system, metadata, globalreserve
    raid_d = {}
    for l in o:
        fields = l.split()
        if (len(fields) > 1):
            block = fields[0][:-1].lower()
            raid = fields[1][:-1].lower()
            if block not in raid_d:
                raid_d[block] = raid
    if (raid_d['metadata'] == 'single'):
        raid_d['data'] = raid_d['metadata']
    return raid_d


def cur_devices(mnt_pt):
    """
    When given a btrfs mount point a list containing the full path of all
    devices is generated by wrapping the btrfs fi show <mnt_pt> command and
    parsing the devid line.
    Used by resize_pool() to ascertain membership status of a device in a pool
    :param mnt_pt: btrfs mount point
    :return: list containing the current reported devices associated with a
    btrfs mount point in by-id (with full path) format.
    """
    dev_list_byid = []
    o, e, rc = run_command([BTRFS, 'fi', 'show', mnt_pt])
    for l in o:
        l = l.strip()
        if (re.match('devid ', l) is not None):
            # The following extracts the devices from the above command output,
            # ie /dev/sda type names, but these are transient and we use their
            # by-id type counterparts in the db and our logging hence the
            # call to convert the 'now' names to by-id type names.
            # N.B. As opposed to get_pool_info we want to preserve the path as
            # our caller expects this full path format.
            dev_byid, is_byid = get_dev_byid_name(l.split()[-1])
            dev_list_byid.append(dev_byid)
    return dev_list_byid


def resize_pool(pool, dev_list_byid, add=True):
    """
    Acts on a given pool and list of device names by generating and then
    executing the appropriate:-
    "btrfs <device list> add(default)/delete root_mnt_pt(pool)"
    command, or returning None if a disk member sanity check fails ie if
    all the supplied devices are either not already a member of the pool
    (when adding) or are already members of the pool (when deleting).
    If any device in the supplied dev_list fails this test then no command is
    executed and None is returned.
    :param pool: btrfs pool name
    :param dev_list_byid: list of devices to add/delete in by-id (without
        path).
    :param add: when true (default) or not specified then attempt to add
        dev_list devices to pool, or when specified as True attempt to delete
        dev_list devices from pool.
    :return: Tuple of results from run_command(generated command) or None if
        the device member/pool sanity check fails.
    """
    dev_list_byid = [get_device_path(d) for d in dev_list_byid]
    root_mnt_pt = mount_root(pool)
    cur_dev = cur_devices(root_mnt_pt)
    resize_flag = 'add'
    if (not add):
        resize_flag = 'delete'
    resize_cmd = [BTRFS, 'device', resize_flag, ]
    # Until we verify that all devices are or are not already members of the
    # given pools depending on if we are adding (default) or removing
    # (add=False) those devices we set our resize flag to false.
    resize = False
    for d in dev_list_byid:
        if (((resize_flag == 'add' and (d not in cur_dev)) or
                (resize_flag == 'delete' and (d in cur_dev)))):
            resize = True  # Basic disk member of pool sanity check passed.
            resize_cmd.append(d)
    if (not resize):
        return None
    resize_cmd.append(root_mnt_pt)
    return run_command(resize_cmd)


def mount_root(pool):
    """
    Mounts a given pool at the default mount root (usually /mnt2/) using the
    pool.name as the final path entry. Ie pool.name = test-pool will be mounted
    at /mnt2/test-pool. Any mount options held in pool.mnt_options will be
    added to the mount command via the -o option as will a compress =
    pool.compression entry.
    N.B. Initially the mount target is defined by /dev/disk/by-label/pool.name,
    if this fails then an attempt to mount by each member of
    /dev/disk/by-id/pool.disk_set.all() but only if there are any members.
    If this second method also fails then an exception is raised, currently all
    but the last failed mount by device name is logged. If no disk members were
    reported by pool.disk_set.count() a separate Exception is raised.
    :param pool: pool object
    :return: either the relevant mount point or an Exception which either
    indicates 'no disks in pool' or 'Unknown Reason'
    """
    root_pool_mnt = DEFAULT_MNT_DIR + pool.name
    if pool.is_mounted:
        return root_pool_mnt
    # Creates a directory to act as the mount point.
    create_tmp_dir(root_pool_mnt)
    toggle_path_rw(root_pool_mnt, rw=False)
    mnt_device = '/dev/disk/by-label/%s' % pool.name
    mnt_cmd = [MOUNT, mnt_device, root_pool_mnt, ]
    mnt_options = ''
    if (pool.mnt_options is not None):
        mnt_options = pool.mnt_options
    if (pool.compression is not None):
        if (re.search('compress', mnt_options) is None):
            mnt_options = ('%s,compress=%s' % (mnt_options, pool.compression))
    # Prior to a mount by label attempt we call btrfs device scan on all
    # members of our pool. This call ensures btrfs has up-to-date info on
    # the relevant devices and avoids the potential overkill of a system wide
    # call such as is performed in the rockstor-bootstrap service on boot.
    # Disk.target_name ensures we observe any redirect roles.
    device_scan([dev.target_name for dev in pool.disk_set.attached()])
    if (os.path.exists(mnt_device)):
        if (len(mnt_options) > 0):
            mnt_cmd.extend(['-o', mnt_options])
        run_command(mnt_cmd)
        return root_pool_mnt
    # If we cannot mount by-label, let's try mounting by device; one by one
    # until we get our first success. All devices known to our pool object
    # have already been scanned prior to our mount by label attempt above.
    if (pool.disk_set.count() < 1):
        raise Exception('Cannot mount Pool(%s) as it has no disks in it.'
                        % pool.name)
    last_device = pool.disk_set.attached().last()
    logger.info('Mount by label (%s) failed.' % mnt_device)
    for device in pool.disk_set.attached():
        mnt_device = get_device_path(device.target_name)
        logger.info('Attempting mount by device (%s).' % mnt_device)
        if (os.path.exists(mnt_device)):
            mnt_cmd = [MOUNT, mnt_device, root_pool_mnt, ]
            if (len(mnt_options) > 0):
                mnt_cmd.extend(['-o', mnt_options])
            try:
                run_command(mnt_cmd)
                return root_pool_mnt
            except Exception as e:
                if (device.name == last_device.name):
                    # exhausted mounting using all devices in the pool
                    raise e
                logger.error('Error mounting: %s. '
                             'Will try using another device.' % mnt_cmd)
                logger.exception(e)
        else:
            logger.error('Device (%s) was not found' % mnt_device)
    raise Exception('Failed to mount Pool(%s) due to an unknown reason. '
                    'Command used %s' % (pool.name, mnt_cmd))


def umount_root(root_pool_mnt):
    if (not os.path.exists(root_pool_mnt)):
        return
    try:
        o, e, rc = run_command([UMOUNT, '-l', root_pool_mnt])
    except CommandException as ce:
        if (ce.rc == 32):
            for l in ce.err:
                l = l.strip()
                if (re.search('not mounted$', l) is not None):
                    return
            raise ce
    for i in range(20):
        if (not is_mounted(root_pool_mnt)):
            toggle_path_rw(root_pool_mnt, rw=True)
            run_command([RMDIR, root_pool_mnt])
            return
        time.sleep(2)
    run_command([UMOUNT, '-f', root_pool_mnt])
    toggle_path_rw(root_pool_mnt, rw=True)
    run_command([RMDIR, root_pool_mnt])
    return


def is_subvol(mnt_pt):
    """
    Simple wrapper around "btrfs subvolume show mnt_pt"
    :param mnt_pt: mount point of subvolume to query
    :return: True if subvolume mnt_pt exists, else False
    """
    show_cmd = [BTRFS, 'subvolume', 'show', mnt_pt]
    # Throw=False on run_command to silence CommandExceptions.
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
    # TODO: Consider making mnt_pt optional as per helper_mount_share() as then
    # TODO: we could remove almost system wide many duplicates of temp mnt_pt
    # TODO: created just prior and only for this methods call.
    if (is_mounted(mnt_pt)):
        return
    mount_root(share.pool)
    pool_device = get_device_path(share.pool.disk_set.attached()
                                       .first().target_name)
    subvol_str = 'subvol=%s' % share.subvol_name
    create_tmp_dir(mnt_pt)
    toggle_path_rw(mnt_pt, rw=False)
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, pool_device, mnt_pt]
    return run_command(mnt_cmd)


def mount_snap(share, snap_name, snap_mnt=None):
    pool_device = get_device_path(share.pool.disk_set.attached()
                                       .first().target_name)
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
        except CommandException as ce:
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
    """
    Returns a dictionary of share/subvol names via passed pool mount point
    lookup and using this to run "btrfs subvol list -s mnt_point" for snapshots
    and "btrfs subvol list -p mnt_point" for all subvols including parent id.
    N.B. Child snapshots and subvolumes are ignored but writable snapshots that
    are immediate children of a pool (vol) are not ignored and regarded as
    shares in their own right (a Share 'clone' in Rockstor parlance).
    :param pool: Pool object
    :return: dictionary indexed by share/subvol names found directly under
    Pool.name. Indexed values are share/subvol qgroup ie "0/266" see
    Share.qgroup model definition.
    """
    try:
        mnt_pt = mount_root(pool)
    except CommandException as e:
        if (e.rc == 32):
            # mount failed, so we just assume that something has gone wrong at
            # a lower level, like a device failure. Return empty share map.
            # application state can be removed. If the low level failure is
            # recovered, state gets reconstructed anyway.
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
                                        '%s/%s' % (mnt_pt,
                                                   snap_idmap[vol_id])])
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
    o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-u', '-p', '-q',
                            mnt_pt])
    share_id = share_uuid = None
    for l in o:
        if (re.match('ID ', l) is not None):
            fields = l.split()
            if (fields[-1] == share_name):
                share_id = fields[1]
                share_uuid = fields[12]
    if (share_id is None):
        return {}

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
            if (snap_name is not None):
                snaps_d[snap_name] = ('0/%s' % fields[1], writable, )
                # we rely on the observation that child snaps are listed after
                # their parents, so no need to iterate through results
                # separately. Instead, we add the uuid of a snap to the list
                # and look up if it's a parent of subsequent entries.
                snap_uuids.append(fields[17])

    return snaps_d


def share_id(pool, share_name):
    """
    Returns the subvolume id, becomes the share's uuid.
    @todo: this should be part of add_share -- btrfs create should atomically
    Works by iterating over the output of btrfs subvolume list, received from
    subvol_list_helper() looking for a match in share_name. If found the same
    line is parsed for the ID, example line in output:
    'ID 257 gen 13616 top level 5 path rock-ons-root'
    :param pool: a pool object.
    :param share_name: target share name to find
    :return: the id for the given share_name or an Exception stating no id
    found
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


def remove_share(pool, share_name, pqgroup, force=False):
    """
    umount share if its mounted.
    unsures given pool is mounted.
    if force flag set then first delete all share's subvolumes.
    btrfs subvolume delete root_mnt/vol_name.
    destroy shares qgroup and associated pqgroup.
    :param pool: pool object
    :param share_name: Share name as in share.name
    :param pqgroup: Pqgroup to be removed
    :param force: Flag used to also remove all subvolumes of the given share.
    """
    if (is_share_mounted(share_name)):
        mnt_pt = ('%s%s' % (DEFAULT_MNT_DIR, share_name))
        umount_root(mnt_pt)
    root_pool_mnt = mount_root(pool)
    subvol_mnt_pt = root_pool_mnt + '/' + share_name
    if (not is_subvol(subvol_mnt_pt)):
        return
    # Remove the immutable flag if set as this will block a subvol delete
    # with an 'Operation not permitted' and leave an unmounted share.
    # This flag can also break replication as we supplant the transient share.
    # The immutable flag has been seen to spontaneously appear. Upon this
    # bug being resolved we might consider promoting to force=True calls only.
    chattr_cmd = [CHATTR, '-i', subvol_mnt_pt]
    run_command(chattr_cmd, log=True)
    if (force):
        o, e, rc = run_command([BTRFS, 'subvolume', 'list', '-o',
                                subvol_mnt_pt])
        for l in o:
            if (re.match('ID ', l) is not None):
                subvol = root_pool_mnt + '/' + l.split()[-1]
                # TODO: consider recursive immutable flag removal.
                run_command([BTRFS, 'subvolume', 'delete', subvol], log=True)
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
            # just give the first match.
            if (re.match('ID.*%s$' % snap_name, l) is not None):
                snap = '%s/%s' % (root_mnt, l.split()[-1])
                return run_command([BTRFS, 'subvolume', 'delete', snap],
                                   log=True)


def add_snap_helper(orig, snap, writable):
    cmd = [BTRFS, 'subvolume', 'snapshot', orig, snap]
    if (not writable):
        cmd.insert(3, '-r')
    try:
        return run_command(cmd)
    except CommandException as ce:
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
    return add_snap_helper(orig_path, clone_path, True)


def add_snap(pool, share_name, snap_name, writable):
    """
    create a snapshot
    """
    root_pool_mnt = mount_root(pool)
    share_full_path = ('%s/%s' % (root_pool_mnt, share_name))
    snap_dir = ('%s/.snapshots/%s' % (root_pool_mnt, share_name))
    create_tmp_dir(snap_dir)
    snap_full_path = ('%s/%s' % (snap_dir, snap_name))
    return add_snap_helper(share_full_path, snap_full_path, writable)


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
    remove_share(pool, subvol_name, PQGROUP_DEFAULT)
    shutil.move(snap_fp, '%s/%s/%s' % (DEFAULT_MNT_DIR, pool.name, sname))
    create_tmp_dir(mnt_pt)
    subvol_str = 'subvol=%s' % sname
    dpath = get_device_path(pool.disk_set.attached().first().target_name)
    mnt_cmd = [MOUNT, '-t', 'btrfs', '-o', subvol_str, dpath, mnt_pt]
    run_command(mnt_cmd)


def switch_quota(pool, flag='enable'):
    root_mnt_pt = mount_root(pool)
    cmd = [BTRFS, 'quota', flag, root_mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        # Avoid failure when attempting an enable/disable quota change if
        # our pool (vol) is ro: by catching this specific CommandException:
        emsg = "ERROR: quota command failed: Read-only file system"
        if e.err[0] == emsg:
            logger.error('Failed to {} quotas on pool ({}). To resolve '
                         'run "btrfs quota {} {}".'.format(flag, pool.name,
                                                           flag, root_mnt_pt))
            return e.out, e.err, e.rc
        # otherwise we raise an exception as normal.
        raise e
    return o, e, rc


def enable_quota(pool):
    return switch_quota(pool)


def disable_quota(pool_name):
    return switch_quota(pool_name, flag='disable')


def are_quotas_enabled(mnt_pt):
    """
    Simple wrapper around 'btrfs qgroup show -f --raw mnt_pt' intended
    as a fast determiner of True / False status of quotas enabled
    :param mnt_pt: Mount point of btrfs filesystem
    :return: True on rc = 0 False otherwise.
    """
    o, e, rc = run_command([BTRFS, 'qgroup', 'show', '-f', '--raw', mnt_pt])
    if rc == 0:
        return True
    return False


def qgroup_exists(mnt_pt, qgroup):
    """
    Simple wrapper around 'btrfs qgroup show --raw mnt_pt' intended to
    establish if a specific qgroup exists on a btrfs filesystem.
    :param mnt_pt: btrfs filesystem mount point, usually the pool.
    :param qgroup: qgroup of the form 2015/n (intended for use with pqgroup)
    :return: True is given qgroup exists in command output, False otherwise.
    """
    o, e, rc = run_command([BTRFS, 'qgroup', 'show', '--raw', mnt_pt])
    # example output:
    # 'qgroupid         rfer         excl '
    # '-------         ----         ---- '
    # '0/5             16384        16384 '
    # ...
    # '2015/12             0            0 '
    if rc == 0 and len(o) > 2:
        # index from 2 to miss header lines and -1 to skip end blank line = []
        qgroup_list = [line.split()[0] for line in o[2:-1]]
        # eg from rockstor_rockstor pool we get:
        # qgroup_list=['0/5', '0/257', '0/258', '0/260', '2015/1', '2015/2']
        if qgroup in qgroup_list:
            return True
    return False


def qgroup_id(pool, share_name):
    sid = share_id(pool, share_name)
    return '0/' + sid


def qgroup_max(mnt_pt):
    """
    Parses the output of "btrfs qgroup show mnt_pt" to find the highest qgroup
    matching QID/* if non is found then 0 will be returned.
    Quotas not enabled is flagged by a -1 return value.
    :param mnt_pt: A given btrfs mount point.
    :return: -1 if quotas not enabled, else highest 2015/* qgroup found or 0
    """
    try:
        o, e, rc = run_command([BTRFS, 'qgroup', 'show', mnt_pt], log=True)
    except CommandException as e:
        # disabled quotas will result in o = [''], rc = 1 and e[0] =
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info('Mount Point: {} has Quotas disabled, skipping qgroup '
                        'show.'.format(mnt_pt))
            # and return our default res
            return -1
        # otherwise we raise an exception as normal.
        raise
    # if no exception was raised find the max 2015/qgroup
    res = 0
    for l in o:
        if (re.match('%s/' % QID, l) is not None):
            cid = int(l.split()[0].split('/')[1])
            if (cid > res):
                res = cid
    return res


def qgroup_create(pool, qgroup=PQGROUP_DEFAULT):
    """
    When passed only a pool an attempt will be made to ascertain if quotas is
    enabled, if not '-1/-1' is returned as a flag to indicate this state.
    If quotas are enabled then the highest available quota of the form
    2015/n is selected and created, if possible (Read-only caveat).
    If passed both a pool and a specific qgroup an attempt is made, given the
    same behaviour as above, to create this specific group: this scenario is
    primarily used to re-establish prior existing qgroups post quota disable,
    share manipulation, quota enable cycling.
    :param pool: A pool object.
    :param qgroup: native qgroup of the form 2015/n
    :return: -1/-1 on quotas disabled or Read-only fs encountered, otherwise
    it will return the successfully created native quota, ie 2015/n.
    """
    # mount pool
    mnt_pt = mount_root(pool)
    max_native_qgroup = qgroup_max(mnt_pt)
    if max_native_qgroup == -1:
        # We have received a quotas disabled flag so will be unable to create
        # a new quota group. So return our db default which can in turn flag
        # an auto updated of pqgroup upon next refresh-share-state.
        return PQGROUP_DEFAULT
    if qgroup != PQGROUP_DEFAULT:
        qid = qgroup
    else:
        qid = ('%s/%d' % (QID, max_native_qgroup + 1))
    try:
        out, err, rc = run_command([BTRFS, 'qgroup', 'create', qid, mnt_pt],
                                   log=True)
    except CommandException as e:
        # ro mount options will result in o= [''], rc = 1 and e[0] =
        emsg = 'ERROR: unable to create quota group: Read-only file system'
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info('Pool: {} is Read-only, skipping qgroup '
                        'create.'.format(pool.name))
            # We now return PQGROUP_DEFAULT because our proposed next
            # available pqgroup can't be assigned anyway (Read-only file
            # system). This in turn avoids populating share db pqgroup with
            # non existent pqgroups and further flags for retires via the
            # existing quota disabled management system.
            return PQGROUP_DEFAULT
        # raise an exception as usual otherwise
        raise
    return qid


def qgroup_destroy(qid, mnt_pt):
    cmd = [BTRFS, 'qgroup', 'show', mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        # we may have quotas disabled so catch and deal.
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        if e.err[0] == emsg:
            # we have quotas disabled so can't destroy any anyway so skip
            # and deal by returning False so our caller moves on.
            return False
        # otherwise we raise an exception as normal
        raise e
    for l in o:
        if (re.match(qid, l) is not None and l.split()[0] == qid):
            return run_command([BTRFS, 'qgroup', 'destroy', qid, mnt_pt],
                               log=True)
    return False


def qgroup_is_assigned(qid, pqid, mnt_pt):
    # Returns true if the given qgroup qid is already assigned to pqid for the
    # path(mnt_pt)
    cmd = [BTRFS, 'qgroup', 'show', '-pc', mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        # we may have quotas disabled so catch and deal.
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        if e.err[0] == emsg:
            # No deed to scan output as nothing to see with quotas disabled.
            # And since no quota capability can be enacted we return True
            # to avoid our caller trying any further with quotas.
            return True
        # otherwise we raise an exception as normal
        raise e
    for l in o:
        fields = l.split()
        if (len(fields) > 3 and
                fields[0] == qid and
                fields[3] == pqid):
            return True
    return False


def share_pqgroup_assign(pqgroup, share):
    """
    Convenience wrapper to qgroup_assign() for use with a share object where
    we wish to assign / reassign it's current db held qgroup to a passed
    pqgroup.
    :param pqgroup: pqgroup to use as parent.
    :param share: share object
    :return: qgroup_assign() result.
    """
    mnt_pt = '{}/{}'.format(settings.MNT_PT, share.pool.name)
    return qgroup_assign(share.qgroup, pqgroup, mnt_pt)


def qgroup_assign(qid, pqid, mnt_pt):
    """
    Wrapper for 'BTRFS, qgroup, assign, qid, pqid, mnt_pt'
    :param qid: qgroup to assign as child of pqgroup
    :param pqid: pqgroup to use as parent
    :param mnt_pt: btrfs filesystem mountpoint (usually the associated pool)
    """
    if (qgroup_is_assigned(qid, pqid, mnt_pt)):
        return True

    # since btrfs-progs 4.2, qgroup assign succeeds but throws a warning:
    # "WARNING: # quotas may be inconsistent, rescan needed" and returns with
    # exit code 1.
    try:
        run_command([BTRFS, 'qgroup', 'assign', qid, pqid, mnt_pt], log=True)
    except CommandException as e:
        emsg = 'ERROR: unable to assign quota group: Read-only file system'
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info('Read-only fs ({}), skipping qgroup assign: '
                        'child ({}), parent ({}).'.format(mnt_pt, qid, pqid))
            return e.out, e.err, e.rc
        wmsg = 'WARNING: quotas may be inconsistent, rescan needed'
        if e.err[0] == wmsg:
            # schedule a rescan if one is not currently running.
            dmsg = ('Quota inconsistency while assigning %s. Rescan scheduled.'
                    % qid)
            try:
                run_command([BTRFS, 'quota', 'rescan', mnt_pt])
                return logger.debug(dmsg)
            except CommandException as e2:
                emsg = 'ERROR: quota rescan failed: Operation now in progress'
                if e2.err[0] == emsg:
                    return logger.debug('%s.. Another rescan already in '
                                        'progress.' % dmsg)
                logger.exception(e2)
                raise e2
        logger.exception(e)
        raise e


def update_quota(pool, qgroup, size_bytes):
    # TODO: consider changing qgroup to pqgroup if we are only used this way.
    root_pool_mnt = mount_root(pool)
    # Until btrfs adds better support for qgroup limits. We'll not set limits.
    # It looks like we'll see the fixes in 4.2 and final ones by 4.3.
    # Update: Further quota improvements look to be landing in 4.15.
    # cmd = [BTRFS, 'qgroup', 'limit', str(size_bytes), qgroup, root_pool_mnt]
    cmd = [BTRFS, 'qgroup', 'limit', 'none', qgroup, root_pool_mnt]
    # Set defaults in case our run_command fails to assign them.
    out = err = ['']
    rc = 0
    if qgroup == PQGROUP_DEFAULT:
        # We have a 'quotas disabled' or 'Read-only' qgroup value flag,
        # log and return blank.
        logger.info('Pool: {} ignoring '
                    'update_quota on {}'.format(pool.name, qgroup))
        return out, err, rc
    try:
        out, err, rc = run_command(cmd, log=True)
    except CommandException as e:
        # ro mount options will result in o= [''], rc = 1 and e[0] =
        emsg = 'ERROR: unable to limit requested quota group: ' \
               'Read-only file system'
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info('Pool: {} is Read-only, skipping qgroup '
                        'limit.'.format(pool.name))
            return out, err, rc
        # quotas disabled results in o = [''], rc = 1 and e[0] =
        emsg2 = 'ERROR: unable to limit requested quota group: ' \
                'Invalid argument'
        # quotas disabled is not a fatal failure but here we key from what
        # is a non specific error: 'Invalid argument'.
        # TODO: improve this clause as currently too broad.
        # TODO: we could for example use if qgroup_max(mnt) == -1
        if e.err[0] == emsg2:
            logger.info('Pool: {} has encountered a qgroup limit issue, '
                        'skipping qgroup limit. Disabled quotas can cause '
                        'this error'.format(pool.name))
            return out, err, rc
        emsg3 = 'ERROR: unable to limit requested quota group: ' \
                'No such file or directory'
        if e.err[0] == emsg3:
            logger.info('Pool: {} is missing expected '
                        'qgroup {}'.format(pool.name, qgroup))
            logger.info('Previously disabled quotas can cause this issue')
            return out, err, rc
        # raise an exception as usual otherwise
        raise
    return out, err, rc


def volume_usage(pool, volume_id, pvolume_id=None):
    """
    New function to collect volumes rusage and eusage instead of share_usage
    plus parent rusage and eusage (2015/* qgroup)
    N.B. this function has 2 personalities.
    When called with 2 parameters (pool, volume_id) it returns 2 values.
    But with 3 parameters (pool, volume_id, pvolume_id) it returns 4 values if
    the last parameter is != None.
    :param pool: Pool object
    :param volume_id: qgroupid eg '0/261'
    :param pvolume_id: qgroupid eg '2015/4'
    :return: list of len 2 (when pvolume_id=None) or 4 elements. The first 2
    pertain to the qgroupid=volume_id the second 2, if present, are for the
    qgroupid=pvolume_id. I.e [rfer, excl, rfer, excl]
    """
    # Obtain path to share in pool, this preserved because
    # granting pool exists
    root_pool_mnt = mount_root(pool)
    cmd = [BTRFS, 'subvolume', 'list', root_pool_mnt]
    out, err, rc = run_command(cmd, log=True)
    short_id = volume_id.split('/')[1]
    volume_dir = ''

    for line in out:
        fields = line.split()
        if (len(fields) > 0 and short_id in fields[1]):
            volume_dir = root_pool_mnt + '/' + fields[8]
            break
    """
    Rockstor volume/subvolume hierarchy is not standard
    and Snapshots actually not always under Share but on Pool,
    so btrf sub list -o deprecated because won't always return
    expected data; volumes (shares & snapshots) sizes got via qgroups.
    Rockstor structure has default share qgroup 0/* becoming child of
    2015/* new qgroup and share snapshots 0/*+1 qgroups assigned to new
    Rockstor 2015/*.
    Original 0/* qgroup returns current share content size,
    2015/* qgroup returns 'real' share size considering snapshots sizes too
    Note: 2015/* rfer and excl sizes are always equal so to compute
    current real size we can indistinctly use one of them.
    """
    cmd = [BTRFS, 'qgroup', 'show', volume_dir]
    out, err, rc = run_command(cmd, log=True, throw=False)
    volume_id_sizes = [0, 0]
    pvolume_id_sizes = [0, 0]
    for line in out:
        fields = line.split()
        # We may index up to [2] fields (3 values) so ensure they exist.
        if (len(fields) > 2 and '/' in fields[0]):
            qgroup = fields[0]
            if (qgroup == volume_id):
                rusage = convert_to_kib(fields[1])
                eusage = convert_to_kib(fields[2])
                volume_id_sizes = [rusage, eusage]
            if (pvolume_id is not None and qgroup == pvolume_id):
                pqgroup_rusage = convert_to_kib(fields[1])
                pqgroup_eusage = convert_to_kib(fields[2])
                pvolume_id_sizes = [pqgroup_rusage, pqgroup_eusage]
    if pvolume_id is None:
        return volume_id_sizes
    return volume_id_sizes + pvolume_id_sizes


def shares_usage(pool, share_map, snap_map):
    # TODO: currently unused, is this to be deprecated
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
            r_usage = convert_to_kib(fields[-2])
            e_usage = convert_to_kib(fields[-1])
            usage_map[combined_map[fields[0]]] = (r_usage, e_usage)
    return usage_map


def pool_usage(mnt_pt):
    """Return used space of the storage pool mounted at mnt_pt.

    Used space is considered to be:
    - All space currently used by data;
    - All space currently allocated for metadata and system data.
    """
    cmd = [BTRFS, 'fi', 'usage', '-b', mnt_pt]
    out, err, rc = run_command(cmd)

    used = 0
    for line in out:
        fields = re.split('\W+', line)
        if line.startswith('Data'):
            used += int(fields[5])
        elif re.search('Size', line):
            used += int(fields[3])

    return used / 1024


def usage_bound(disk_sizes, num_devices, raid_level):
    """Return the total amount of storage possible within this pool's set
    of disks, in bytes.

    Algorithm adapted from Hugo Mills' implementation at:
    http://carfax.org.uk/btrfs-usage/js/btrfs-usage.js
    """
    # Determine RAID parameters
    data_ratio = 1
    stripes = 1
    parity = 0

    # Number of chunks to write at a time: as many as possible within the
    # number of stripes
    chunks = num_devices

    if raid_level == 'single':
        chunks = 1
    elif raid_level == 'raid0':
        stripes = 2
    elif raid_level == 'raid1':
        data_ratio = 2
        chunks = 2
    elif raid_level == 'raid10':
        data_ratio = 2
        stripes = max(2, int(num_devices / 2))
    elif raid_level == 'raid5':
        parity = 1
    elif raid_level == 'raid6':
        parity = 2

    # Round down so that we have an exact number of duplicate copies
    chunks -= chunks % data_ratio

    # Check for feasibility at the lower end
    if num_devices < data_ratio * (stripes + parity):
        return 0

    # Compute the trivial bound
    bound = int(sum(disk_sizes) / chunks)

    # For each partition point q, compute B_q (the test predicate) and
    # modify the trivial bound if it passes.
    bounding_q = -1
    for q in range(chunks - 1):
        slice = sum(disk_sizes[q + 1:])
        b = int(slice / (chunks - q - 1))
        if disk_sizes[q] >= b and b < bound:
            bound = b
            bounding_q = q

    # The bound is the number of allocations we can make in total. If we
    # have no bounding_q, then we have hit the trivial bound, and exhausted
    # all space, so we can return immediately.
    if bounding_q == -1:
        return bound * ((chunks / data_ratio) - parity)

    # If we have a bounding_q, then all the devices past q are full, and
    # we can remove them. The devices up to q have been used in every one
    # of the allocations, so we can just reduce them by bound.
    disk_sizes = [size - bound for index, size in enumerate(disk_sizes)
                  if index <= bounding_q]

    new_bound = usage_bound(disk_sizes, bounding_q + 1, raid_level)

    return bound * ((chunks / data_ratio) - parity) + new_bound


def scrub_start(pool, force=False):
    mnt_pt = mount_root(pool)
    p = PoolScrub(mnt_pt, force)
    p.start()
    return p.pid


def scrub_status(pool):
    """
    Returns the raw statistics per-device (-R option) of the ongoing or last
    known btrfs scrub. Works by parsing the output of the following command:
    btrfs scrub status -R <mount-point>
    :param pool: pool object
    :return: dictionary indexed via 'status' and if a finished or halted, or
    cancelld scrub is indicated then the duration of that scrub is added as
    value to added index 'duration'. In all 'status' cases bar 'unknown',
    data_bytes_scrubbed is passed as value to index 'kb_scrubbed' and all
    other -R invoked details are returned as key value pairs.
    """
    stats = {'status': 'unknown', }
    mnt_pt = mount_root(pool)
    out, err, rc = run_command([BTRFS, 'scrub', 'status', '-R', mnt_pt])
    if err != [''] and len(err) > 0:
        if err[0] == "WARNING: failed to read status: Connection reset by " \
                     "peer":
            stats['status'] = 'conn-reset'
            return stats
    if len(out) > 1:
        if re.search('interrupted', out[1]) is not None:
            stats['status'] = 'halted'
            # extract the duration from towards the end of the first line eg:
            # "... 2017, interrupted after 00:00:09, not running"
            dfields = out[1].split()[-3].strip(',').split(':')
            stats['duration'] = ((int(dfields[0]) * 60 * 60) +
                                 (int(dfields[1]) * 60) + int(dfields[2]))
        elif re.search('running', out[1]) is not None:
            stats['status'] = 'running'
        elif re.search('finished', out[1]) is not None:
            stats['status'] = 'finished'
            # extract the duration from the end of the first line eg:
            # "... 2017 and finished after 00:00:16"
            dfields = out[1].split()[-1].split(':')
            stats['duration'] = ((int(dfields[0]) * 60 * 60) +
                                 (int(dfields[1]) * 60) + int(dfields[2]))
        elif re.search('aborted', out[1]) is not None:
            stats['status'] = 'cancelled'
            # extract the duration from the end of the first line eg:
            # "... 2017 and was aborted after 00:04:56"
            # TODO: we have code duplication here re finished clause above.
            dfields = out[1].split()[-1].split(':')
            stats['duration'] = ((int(dfields[0]) * 60 * 60) +
                                 (int(dfields[1]) * 60) + int(dfields[2]))
        else:
            return stats
    else:  # we have an unknown status as out is 0 or 1 lines long.
        return stats
    for l in out[2:-1]:
        fields = l.strip().split(': ')
        if fields[0] == 'data_bytes_scrubbed':
            stats['kb_scrubbed'] = int(fields[1]) / 1024
        else:
            stats[fields[0]] = int(fields[1])
    return stats


@task()
def start_balance(mnt_pt, force=False, convert=None):
    cmd = ['btrfs', 'balance', 'start', mnt_pt]
    # With no filters we also get a warning that block some balances due to
    # expected long execution time, in this case "--full-balance" is required.
    if force:
        cmd.insert(3, '-f')
    if convert is not None:
        cmd.insert(3, '-dconvert=%s' % convert)
        # Override metadata on single pools to be dup, as per btrfs default.
        if convert == 'single':
            convert = 'dup'
        cmd.insert(3, '-mconvert=%s' % convert)
    else:
        # As we are running with no convert filters a warning and 10 second
        # countdown with ^C prompt will result unless we use "--full-balance".
        # This warning is now present in the Web-UI "Start a new balance"
        # button tooltip.
        cmd.insert(3, '--full-balance')
    logger.debug('Balance command ({}).'.format(cmd))
    run_command(cmd)


def balance_status(pool):
    """
    Wrapper around btrfs balance status pool_mount_point to extract info about
    the current status of a balance.
    :param pool: pool object to query
    :return: dictionary containing parsed info about the balance status,
    ie indexed by 'status' and 'percent_done'.
    """
    stats = {'status': 'unknown', }
    # The balance status of an umounted pool is undetermined / unknown, ie it
    # could still be mid balance: our balance status command requires a
    # relevant active mount path.
    # Note that if we silently fail through the mount confirmation then our
    # balance status will reflect the system pool balance status.
    try:
        mnt_pt = mount_root(pool)
    except Exception as e:
        logger.error('Exception while refreshing balance status for Pool({}). '
                     'Returning "unknown": {}'.format(pool.name, e.__str__()))
        return stats
    out, err, rc = run_command([BTRFS, 'balance', 'status', mnt_pt],
                               throw=False)
    if (len(out) > 0):
        if (re.match('Balance', out[0]) is not None):
            if (re.search('cancel requested', out[0]) is not None):
                stats['status'] = 'cancelling'
            elif (re.search('pause requested', out[0]) is not None):
                stats['status'] = 'pausing'
            elif (re.search('paused', out[0]) is not None):
                stats['status'] = 'paused'
            else:
                stats['status'] = 'running'
            # make sure we have a second line before parsing it.
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


def device_scan(dev_byid_list=['all']):
    """
    When called with no parameters a 'btrfs device scan' is executed, ie a
    system wide scan of all /dev block devices to update their btrfs status.
    Otherwise the list of devices is iterated and a 'btrfs device scan dev'
    is executed for each item in the passed list. Detached device names and
    path names that don't exist are ignored.
    :param dev_byid_list: list of byid device names (without paths) to perform
    a 'btrfs device scan' on. If not supplied then a single element list
    ['all'] is substituted and this flags a system wide scan request.
    :return: (out, err, rc) of the first rc !=0 run or the last rc = 0 run.
    """
    out = err = ['']
    # default to successful return code unless we find otherwise.
    rc = 0
    if len(dev_byid_list) > 0:
        if dev_byid_list[0] == 'all':
            return run_command([BTRFS, 'device', 'scan'])
        for dev_byid in dev_byid_list:
            if re.match('detached-', dev_byid) is not None:
                # Skip detached devices as we know they don't exist.
                # Potential log point for early detached device discovery.
                continue
            dev_byid_withpath = get_device_path(dev_byid)
            if os.path.exists(dev_byid_withpath):  # only scan existing devices
                # using throw=False, to process the rc != 0 logic
                # afterwards. Without throw=False, when rc != 0, exception is
                # raised and the following if statement will never get
                # executed.
                out, err, rc = run_command(
                    [BTRFS, 'device', 'scan', dev_byid_withpath], throw=False)
                if rc != 0:
                    # Return on first non zero return code.
                    # Note that a drive specific device scan on a non btrfs
                    # device returns 'Invalid argument'!! and rc=1.
                    return out, err, rc
    return out, err, rc


def btrfs_uuid(disk):
    """return uuid of a btrfs filesystem"""
    o, e, rc = run_command(
        [BTRFS, 'filesystem', 'show', get_device_path(disk)])
    return o[0].split()[3]


def set_property(mnt_pt, name, val, mount=True):
    if (mount is not True or is_mounted(mnt_pt)):
        cmd = [BTRFS, 'property', 'set', mnt_pt, name, val]
        return run_command(cmd)


def get_snap(subvol_path, oldest=False, num_retain=None, regex=None,
             test_mode=False):
    """
    If the supplied path is a directory, it's last element after delimiter (/)
    it taken and used as the share name. A subvol list is then generated via
    "btrfs subvol list -o subvol_path" command.
    :param subvol_path:
    :param oldest:
    :param num_retain:
    :param regex:
    :param test_mode:
    :return:
    """
    if (not os.path.isdir(subvol_path)) and not test_mode:
        return None
    share_name = subvol_path.split('/')[-1]
    cmd = [BTRFS, 'subvol', 'list', '-o', subvol_path]
    o, e, rc = run_command(cmd)
    snaps = {}
    for l in o:
        fields = l.split()
        if (len(fields) > 0):
            snap_fields = fields[-1].split('/')
            if (len(snap_fields) != 3 or snap_fields[1] != share_name):
                # not the Share we are interested in.
                continue
            if (regex is not None and
                    re.search(regex, snap_fields[2]) is None):
                # regex not in the name
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
    return get_snap(subvol_path, oldest=True, num_retain=num_retain,
                    regex=regex)


def get_lastest_snap(subvol_path, regex=None):
    return get_snap(subvol_path, regex=regex)
