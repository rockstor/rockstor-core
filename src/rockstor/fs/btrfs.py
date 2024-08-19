"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
import collections
import json
import re
import time
import os
from system.osi import (
    run_command,
    create_tmp_dir,
    is_share_mounted,
    is_mounted,
    get_dev_byid_name,
    convert_to_kib,
    toggle_path_rw,
    get_device_path,
    dev_mount_point,
)
from system.exceptions import CommandException
from system.constants import MOUNT, UMOUNT, RMDIR, DEFAULT_MNT_DIR
from fs.pool_scrub import PoolScrub
from huey.contrib.djhuey import task
from django.conf import settings
import logging
from datetime import datetime
from packaging.version import Version, InvalidVersion

"""
system level helper methods to interact with the btrfs filesystem
"""

logger = logging.getLogger(__name__)

MKFS_BTRFS = "/usr/sbin/mkfs.btrfs"
BTRFS = "/usr/sbin/btrfs"
QID = "2015"
# The following model/db default setting is also used when quotas are disabled.
PQGROUP_DEFAULT = settings.MODEL_DEFS["pqgroup"]
# Potential candidate for settings.conf.in but currently only used here and
# facilitates easier user modification, ie without buildout re-config step.
# N.B. 'root/var/lib/machines' is auto created by systemd:
# https://cgit.freedesktop.org/systemd/systemd/commit/?id=113b3fc1a8061f4a24dd0db74e9a3cd0083b2251
ROOT_SUBVOL_EXCLUDE = [
    "root",
    "@",
    "@/root",
    "tmp",
    "@/tmp",
    "var",
    "@/var",
    "boot/grub2/i386-pc",
    "@/boot/grub2/i386-pc",
    "boot/grub2/x86_64-efi",
    "@/boot/grub2/x86_64-efi",
    "boot/grub2/arm64-efi",
    "@/boot/grub2/arm64-efi",
    "srv",
    "@/srv",
    "usr/local",
    "@/usr/local",
    "opt",
    "@/opt",
    "root/var/lib/machines",
    "@/.snapshots",
    ".snapshots",
]
# Note in the above we have a non-symmetrical exclusions entry of '@/.snapshots
# this is to help distinguish our .snapshots from snapper's rollback subvol.

# Create subvolume blacklist to avoid name clash with default ROOT pool.
# Used in addition to ROOT_SUBVOL_EXCLUDE. From 5.0.9-0 we no longer auto-import
# the system (ROOT) pool.
CREATE_SUBVOL_EXCLUDE = ["home", "@/home"]

# System-wide subvolume exclude list.
SUBVOL_EXCLUDE = [".beeshome", "@/.beeshome"]

# tuple subclass for devices from a btrfs view.
Dev = collections.namedtuple("Dev", "temp_name is_byid devid size allocated")
# Named Tuple for Device Pool Info.
DevPoolInfo = collections.namedtuple("DevPoolInfo", "devid size allocated uuid label")
# Named Tuple for btrfs device usage info.
DevUsageInfo = collections.namedtuple("DevUsageInfo", "temp_name size allocated")
# Named Tuple for default_subvol info: id (string) path (string) boot_to_snap (boolean)
DefaultSubvol = collections.namedtuple("DefaultSubvol", "id path boot_to_snap")
# Named Tuple for balance status: active (boolean) internal (boolean) status (dict)
BalanceStatusAll = collections.namedtuple("BalanceStatusAll", "active internal status")
# Named Tuple to define raid profile limits and data/metadata
btrfs_profile = collections.namedtuple(
    "btrfs_profile",
    "min_dev_count max_dev_missing data_raid metadata_raid data_copies data_parity",
)
# List of Rockstor btrfs raid profiles indexed by their name.
# I.e. PROFILE[raid_level].min_dev_count
# N.B. Mixed profiles indicated by "-" i.e. DATA-METADATA
# https://btrfs.readthedocs.io/en/latest/Kernel-by-version.html#jan-2020
# RAID1C34 along with incompatible flag added in kernel 5.5.
# https://btrfs.readthedocs.io/en/latest/Kernel-by-version.html#nov-2021 kernel 5.15
# enabled running raid0 and 10 with a minimum of 1 & 2 devices respectively.
# https://btrfs.readthedocs.io/en/latest/mkfs.btrfs.html
# "It's recommended to use specific profiles ..."
# The following are Rockstor's specifics:
PROFILE = {
    # Fail through profile to account catch unknown raid levels/combinations.
    # We specify a min dev count of 4 to account for any raid level,
    # and likewise play safe by allowing for no missing devices.
    "unknown": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=0,
        data_raid="unknown",
        metadata_raid="unknown",
        data_copies=1,
        data_parity=0,
    ),
    # non redundant profiles!
    "single": btrfs_profile(
        min_dev_count=1,
        max_dev_missing=0,
        data_raid="single",
        metadata_raid="single",
        data_copies=1,
        data_parity=0,
    ),
    "single-dup": btrfs_profile(
        min_dev_count=1,
        max_dev_missing=0,
        data_raid="single",
        metadata_raid="dup",
        data_copies=1,
        data_parity=0,
    ),
    "raid0": btrfs_profile(
        min_dev_count=2,
        max_dev_missing=0,
        data_raid="raid0",
        metadata_raid="raid0",
        data_copies=1,
        data_parity=0,
    ),
    # Mirrored profiles:
    "raid1": btrfs_profile(
        min_dev_count=2,
        max_dev_missing=1,
        data_raid="raid1",
        metadata_raid="raid1",
        data_copies=2,
        data_parity=0,
    ),
    "raid1c3": btrfs_profile(
        min_dev_count=3,
        max_dev_missing=2,
        data_raid="raid1c3",
        metadata_raid="raid1c3",
        data_copies=3,
        data_parity=0,
    ),
    "raid1c4": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=3,
        data_raid="raid1c4",
        metadata_raid="raid1c4",
        data_copies=4,
        data_parity=0,
    ),
    "raid10": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=1,
        data_raid="raid10",
        metadata_raid="raid10",
        data_copies=2,
        data_parity=0,
    ),
    # Parity raid levels (recommended min_dev_count is 3 & 4 respectively)
    "raid5": btrfs_profile(
        min_dev_count=2,
        max_dev_missing=1,
        data_raid="raid5",
        metadata_raid="raid5",
        data_copies=1,
        data_parity=1,
    ),
    "raid6": btrfs_profile(
        min_dev_count=3,
        max_dev_missing=2,
        data_raid="raid6",
        metadata_raid="raid6",
        data_copies=1,
        data_parity=2,
    ),
    # ------- MIXED PROFILES DATA-METADATA (max 10 chars) -------
    # Mixed Mirrored profiles:
    "raid1-1c3": btrfs_profile(
        min_dev_count=3,
        max_dev_missing=1,
        data_raid="raid1",
        metadata_raid="raid1c3",
        data_copies=2,
        data_parity=0,
    ),
    "raid1-1c4": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=1,
        data_raid="raid1",
        metadata_raid="raid1c4",
        data_copies=2,
        data_parity=0,
    ),
    "raid10-1c3": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=1,
        data_raid="raid10",
        metadata_raid="raid1c3",
        data_copies=2,
        data_parity=0,
    ),
    "raid10-1c4": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=1,
        data_raid="raid10",
        metadata_raid="raid1c4",
        data_copies=2,
        data_parity=0,
    ),
    # Parity data - Mirrored metadata
    "raid5-1": btrfs_profile(
        min_dev_count=2,
        max_dev_missing=1,
        data_raid="raid5",
        metadata_raid="raid1",
        data_copies=1,
        data_parity=1,
    ),
    "raid5-1c3": btrfs_profile(
        min_dev_count=3,
        max_dev_missing=1,
        data_raid="raid5",
        metadata_raid="raid1c3",
        data_copies=1,
        data_parity=1,
    ),
    "raid6-1c3": btrfs_profile(
        min_dev_count=3,
        max_dev_missing=2,
        data_raid="raid6",
        metadata_raid="raid1c3",
        data_copies=1,
        data_parity=2,
    ),
    "raid6-1c4": btrfs_profile(
        min_dev_count=4,
        max_dev_missing=2,
        data_raid="raid6",
        metadata_raid="raid1c4",
        data_copies=1,
        data_parity=2,
    ),
}


def add_pool(pool, disks):
    """
    Makes a btrfs pool (filesystem) of name 'pool' using the by-id disk names
    provided, then attempts to enable quotas for this pool.
    :param pool: Pool object.
    :param disks: list of by-id disk names without paths to make the pool from.
    :return o, err, rc from last command executed.
    """
    disks_fp = [get_device_path(d) for d in disks]
    draid = PROFILE[pool.raid].data_raid
    mraid = PROFILE[pool.raid].metadata_raid
    cmd = [MKFS_BTRFS, "-f", "-d", draid, "-m", mraid, "-L", pool.name]
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
                "non-zero code ({}) returned by enable_quota() while "
                "enabling quota on a newly created pool : pool name = {}, "
                "output: {}, error: {}.".format(rc2, pool.name, out2, err2)
            )
            logger.error(e_msg)
            return out2, err2, rc2
    else:
        logger.error(
            "Unknown state in add_pool() - non-zero code ({}) "
            "returned by {} with output: {} and error: {}.".format(rc, cmd, out, err)
        )
    return out, err, rc


def dev_stats_zero(target):
    """
    Simple and fast wrapper around 'btrfs device stats -c target'
    Intended as a quick boolean pool health check, ie do any devs have errors?
    The command used requires a mounted pool (vol) and does not appear to wake
    drive from a standby state.
    Bit 6 (64 decimal) of return code is set when non zero errors are found.
    :param target: Pool mount point or device name with path
    :return: True if zero errors are reported, False otherwise.
    """
    cmd = [BTRFS, "device", "stats", "-c", target]
    o, e, rc = run_command(cmd, throw=False)
    # logger.debug('out = {} err = {} rc = {}'.format(o, e, rc))
    if rc & 64:  # bitwise AND for Bit 6
        return False
    return True


def get_dev_io_error_stats(target, json_format=True):
    """
    Wrapper / parser for 'btrfs device stats -c target' intended to populate
    the disk model io_error_stats property: called from within try clause.
    :param target: device with path eg: /dev/sda or /dev/disk/by-id/virtio-3333
    :param json_format: Defaults to json format but can return dict.
    :return: json or dict format of retrieved values or None if error or no
    btrfs mount.
    """
    cmd = [BTRFS, "device", "stats", "-c", get_device_path(target)]
    o, e, rc = run_command(cmd, throw=False)
    stats = {
        "write_io_errs": "0",
        "read_io_errs": "0",
        "flush_io_errs": "0",
        "corruption_errs": "0",
        "generation_errs": "0",
    }
    if rc == 0:  # we have low level confirmation of 0 errors so return dict.
        # Avoids unnecessary parsing as we already know all errors are zero.
        if not json_format:
            return stats
        return json.dumps(stats)
    if rc == 1:
        # Device not part of a mounted btrfs vol, or dev is unknown.
        return None
    for line in o:
        fields = line.split(".")
        # e.g. ['[/dev/vdb]', 'write_io_errs    0']
        if len(fields) != 2:
            continue  # Skip line as unknown and will fail following index.
        sub_fields = fields[1].split()
        # e.g. ['write_io_errs', '0']
        if sub_fields[1] == "0":  # optimization.
            continue  # We already have this in our stats template.
        stats[sub_fields[0]] = sub_fields[1]  # ie {'write_io_errs': '42'}
    if not json_format:
        return stats
    return json.dumps(stats)


def pool_missing_dev_count(label):
    """
    Parses 'btrfs fi show --raw label' to return number of missing devices.
    Extracts vol total dev count from e.g.: "\tTotal devices 3 FS bytes used 2.63GiB".
    And counts the number of lines there-after beginning "\tdevid" and not ending
    in "SING" or "sing" (for "MISSING"/"missing").

    Label is used as this is preserved in our Pool db so will work if the pool
    fails to mount, and there by allows surfacing this as a potential reason
    for the mount failure.
    :param label: Pool label.
    :return: int for number of missing devices (total - attached).
    """
    if label is None:
        return 0
    # --raw used to minimise pre-processing of irrelevant 'used' info (units).
    cmd = [BTRFS, "fi", "show", "--raw", label]
    o, e, rc = run_command(cmd)
    total_devices = 0
    attached_devids = 0
    for line in o:
        if not line:
            continue
        # Skip "Label:" line as it has no 'missing' info.
        # Skip "warning, device 8 is missing" lines as they only appear when unmounted.
        # Skip "(TAB)*** Some devices missing" we count devid lines no ending in MISSING
        if line.startswith(("Lab", "war", "\t**")):
            continue
        if line.startswith("\tTotal"):
            total_devices = int(line.split()[2])
            continue
        if not total_devices == 0:
            # Leap 15.4 default & backport kernels (not missing)
            # devid    5 size 5.00GiB used 2.12GiB path /dev/sda
            # Newer Stable Kernel Backport (e.g. 6.2.0+) add a MISSING:
            # older kernels do not have entries for missing devices.
            # devid    1 size 0 used 0 path  MISSING
            if line.startswith("\tdev") and not line.endswith(("SING", "sing")):
                attached_devids += 1
    return total_devices - attached_devids


def degraded_pools_found():
    """
    Primarily intended to indicate the existence of any degraded pools, managed
    or otherwise. Originally used by data_collector to feed real time Web-UI
    indicators. Non-managed pool coverage allows for the indication of a
    degraded mount requirement pre-import or on fresh disaster recovery
    installs.
    :return: Number of degraded pools as indicated by any line ending in
    "missing" following an associated "Label" line.
    """
    # --raw used to minimise pre-processing of irrelevant 'used' info (units).
    cmd = [BTRFS, "fi", "show", "--raw"]
    o, e, rc = run_command(cmd)
    degraded_pool_count = 0
    in_pool = False
    for line in o:
        if not in_pool and line[0:3] == "Lab":
            in_pool = True
            continue
        # Account for older and newer kernels respectively:
        if in_pool and line.lower().endswith("missing"):
            # we are in pool details and have found a missing device
            degraded_pool_count += 1
            # use in_pool switch to avoid counting this pool twice if it has
            # multiple missing as at least 1 missing dev is degraded.
            in_pool = False
        elif line == "":
            # pool listings delimited by blank lines
            in_pool = False
    return degraded_pool_count


def set_pool_label(label, dev_temp_name, root_pool=False):
    """
    Wrapper around 'btrfs fi label dev|mnt_pt' initially intended to auto label
    pools (btrfs vols) that have 'none' as label since a label is assumed.
    Could server as more general purpose once we have pool re-naming.
    :param dev_temp_name: full_dev_path
    :param label: Desired label: overridden if root_pool = True.
    :param root_pool: Boolean indicator of system root ('/') pool.
    :return: new label if successful or None if command exception.
    """
    # we override accessor and label for the system pool.
    if root_pool:
        # root_pool already mounted so we must use mount point.
        accessor = "/"
        label = settings.SYS_VOL_LABEL
    else:  # adapt to mounted or unmounted non system root pools:
        mount_point = dev_mount_point(dev_temp_name)
        if mount_point is not None:
            accessor = mount_point
        else:
            accessor = dev_temp_name
    # This requirement limits importing ro pools with no label.
    cmd = [BTRFS, "fi", "label", accessor, label]
    # Consider udevadm trigger on this device as label changed.
    try:
        logger.debug("Attempting auto pool label for ({}).".format(accessor))
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        logger.error(
            "Pool label attempt on {} to {} failed with "
            "error: {}".format(accessor, label, e.err)
        )
        return None
    return label


def get_dev_pool_info():
    """
    Variant of get_pool_info() intended for low level use where a system wide
    view is required with temp_name indexing. Used as a replacement for
    get_pool_info in _update_disk_state() and _refresh_pool_state() to allow
    for one call to acquire all pool info system wide. Pool counterpart to
    osi.py's scan_disks(). Note that there is likely much duplication within
    the returned structure but we provide fast / light lookup for each device
    member thereafter via it's own named tuple.
    :return sys_pool_info: dict indexed by temp_name with DevPoolInfo values.
    """
    cmd = [BTRFS, "fi", "show", "--raw"]
    o, e, rc = run_command(cmd)
    # Label: 'rockstor_rockstor'  uuid: be5d2c5a-cc86-4c9a-96da-0a2add43f079
    #         Total devices 1 FS bytes used 2444705792
    #         devid    1 size 14935916544 used 3825205248 path /dev/sda3
    #
    # Label: 'rock-pool'  uuid: be4814da-a054-4ffe-82e7-b40ec33e4343
    #         Total devices 5 FS bytes used 3913490432
    #         devid   17 size 5368709120 used 1073741824 path /dev/sdb
    #         devid   18 size 5368709120 used 2415919104 path /dev/sdd
    sys_pool_info = {}
    uuid = None  # Every pool has one.
    label = "none"  # What is shown when there is no label on a pool.
    devid = 0  # Real ones start at 1 so this can be a flag of sorts.
    for line in o:
        if line == "":
            continue
        fields = line.strip().split()
        if fields[0] == "Label:":  # Pool header: set uuid and label
            label = fields[1].strip("'")  # single quotes present when != none
            uuid = fields[3]
        elif fields[0] == "Total":
            continue
        elif fields[0] == "devid":
            devid = int(fields[1])
            size = int(fields[3]) / 1024  # Bytes to KB
            allocated = int(fields[5]) / 1024  # Bytes to KB
            temp_name = fields[-1]
            dp_info = DevPoolInfo(
                devid=devid, size=size, allocated=allocated, uuid=uuid, label=label
            )
            sys_pool_info[temp_name] = dp_info
    # logger.debug('get_dev_pool_info() returning {}'.format(sys_pool_info))
    return sys_pool_info


def get_pool_info(disk):
    """
    Extracts pool information by running btrfs fi show <disk> and collates
    the results in a property keyed dictionary The disks ('disks' key) names
    found are translated to the by-id type (/dev/disk/by-id) so that their
    counterparts in the db's Disk.name field can be found. No path is stored.
    N.B. devices without serial may have no by-id counterpart.
    Enforces a non 'none' label by substituting the uuid if label = none.
    Used by CommandView()._refresh_pool_state() and
    DiskDetailView()._btrfs_disk_import
    :param disk: by-id disk name without path
    :return: a dictionary with keys of 'disks', 'label', 'uuid',
    'hasMissingDev', 'fullDevCount', and 'missingDevCount'.
    'disks' keys a dict of Dev named tuples index by their by-id names, while
    'label' and 'uuid' keys are for strings. 'hasMissingDev' is Boolean and
    defaults to False. 'fullDevCount' is taken from the "Total devices" line.
    'missingDevCount' is derived from fullDevCount - attached devs count.
    """
    dpath = get_device_path(disk)
    cmd = [BTRFS, "fi", "show", "--raw", dpath]
    o, e, rc = run_command(cmd)
    # Label: 'rockstor_rockstor'  uuid: be5d2c5a-cc86-4c9a-96da-0a2add43f079
    #         Total devices 1 FS bytes used 2465906688
    #         devid    1 size 14935916544 used 5406457856 path /dev/sda3
    pool_info = {
        "disks": {},
        "hasMissingDev": False,
        "fullDevCount": 0,
        "missingDevCount": 0,
    }
    full_dev_count = 0  # Number of devices in non degraded state.
    attached_dev_count = 0  # Number of currently attached devices.
    for l in o:
        if re.match("Label", l) is not None:
            fields = l.split()
            pool_info["uuid"] = fields[3]
            pool_info["label"] = fields[1].strip("'")
        elif re.match("\tdevid", l) is not None:
            # We have a line starting with <tab>devid, extract the temp_name,
            # devid, is_byid, size, and used. Collect in a named tuple.
            # We convert name into the db Disk.name by-id format so that our
            # caller can locate a drive and update it's pool field reference.
            attached_dev_count += 1
            # Express device info line as a list of line elements.
            fields = l.split()
            temp_name = fields[-1]
            dev_byid, is_byid = get_dev_byid_name(temp_name, remove_path=True)
            devid = fields[1]
            size = int(fields[3]) / 1024  # Bytes to KB
            allocated = int(fields[5]) / 1024  # Bytes to KB
            dev_info = Dev(
                temp_name=temp_name,
                is_byid=is_byid,
                devid=devid,
                size=size,
                allocated=allocated,
            )
            pool_info["disks"][dev_byid] = dev_info
        elif re.match("\tTotal devices", l) is not None:
            fields = l.split()
            full_dev_count = int(fields[2])
        elif re.match("\t\*\*\* Some devices missing", l) is not None:
            pool_info["hasMissingDev"] = True
    pool_info["fullDevCount"] = full_dev_count
    pool_info["missingDevCount"] = full_dev_count - attached_dev_count
    # logger.debug('get_pool_info() returning {}'.format(pool_info))
    return pool_info


def get_pool_raid_levels(mnt_pt):
    o, e, rc = run_command([BTRFS, "fi", "df", mnt_pt])
    # data, system, metadata, globalreserve
    raid_d = {}
    for l in o:
        fields = l.split()
        if len(fields) > 1:
            block = fields[0][:-1].lower()
            raid = fields[1][:-1].lower()
            if block not in raid_d:
                raid_d[block] = raid
    return raid_d


def get_pool_raid_profile(raid_levels):
    """
    Abstracts raid_levels from get_pool_raid_levels(mnt_pt) to a Rockstor raid Profile.
    See PROFILES const.
    :param raid_levels: dict returned by get_pool_raid_levels()
    :return: a PROFILE index.
    """
    # dict.get returns None if key not found.
    data_raid = raid_levels.get("data")
    metadata_raid = raid_levels.get("metadata")
    raid_profile = "unknown"
    if data_raid is None or metadata_raid is None:
        return raid_profile
    if data_raid == metadata_raid:
        raid_profile = data_raid
    else:
        # Post Python >= 3.9 use removeprefix("raid")
        if metadata_raid.startswith("raid"):  # 4 characters
            raid_profile = data_raid + "-" + metadata_raid[4:]
        else:
            raid_profile = data_raid + "-" + metadata_raid
    if raid_profile not in PROFILE:
        return "unknown"
    return raid_profile


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
    o, e, rc = run_command([BTRFS, "fi", "show", mnt_pt])
    for l in o:
        l = l.strip()
        if re.match("devid ", l) is not None:
            # The following extracts the devices from the above command output,
            # ie /dev/sda type names, but these are transient and we use their
            # by-id type counterparts in the db and our logging hence the
            # call to convert the 'now' names to by-id type names.
            # N.B. As opposed to get_pool_info we want to preserve the path as
            # our caller expects this full path format.
            dev_byid, is_byid = get_dev_byid_name(l.split()[-1])
            dev_list_byid.append(dev_byid)
    return dev_list_byid


def resize_pool_cmd(pool, dev_list_byid, add=True):
    """
    Given a pool and list of device names, returns the appropriate cmd of type:
    "btrfs <device list> add(default)/delete root_mnt_pt(pool)", or returns
    None if a disk member sanity check fails: ie if all the supplied devices
    are either, not pool members (when deleting) or are already pool members
    (when adding). If any device in the supplied dev_list fails this test then
    no command is generated and None is returned.
    :param pool: btrfs pool object
    :param dev_list_byid: by-id device list to add/delete (without paths).
    :param add: when true (default) or not specified then 'device add'
        dev_list devices to pool, when specified as True 'device delete'
        dev_list devices from pool.
    :return: appropriate btrfs command, or None if member sanity checks failed.
    """
    if pool.has_missing_dev and not add:
        if dev_list_byid == []:
            dev_list_byid = ["missing"]
        else:
            # list has at least a single element
            # substiture 'missing' for any member matching 'detached-'
            dev_list_byid = [
                "missing"
                if re.match("detached-", dev) is not None
                else get_device_path(dev)
                for dev in dev_list_byid
            ]
    else:
        dev_list_byid = [get_device_path(dev) for dev in dev_list_byid]
    root_mnt_pt = mount_root(pool)
    cur_dev = cur_devices(root_mnt_pt)
    resize_flag = "add"
    if not add:
        resize_flag = "delete"
    resize_cmd = [BTRFS, "device", resize_flag]
    # Until we verify that all devices are or are not already members of the
    # given pool, depending on if we are adding (default) or removing
    # (add=False), we set our resize flag to false.
    resize = False
    # TODO: This test looks to pass if only one member passes. Revisit.
    # TODO: But we are after a fail if only one member fails.
    for d in dev_list_byid:
        if (resize_flag == "add" and (d not in cur_dev)) or (
            resize_flag == "delete" and ((d in cur_dev) or d == "missing")
        ):
            resize = True  # Basic disk member of pool sanity check passed.
            resize_cmd.append(d)
    if not resize:
        logger.debug(
            "Resize pool - member sanity check failed. "
            "Retuning None as btrfs add/delete command."
        )
        return None
    resize_cmd.append(root_mnt_pt)
    return resize_cmd


def mount_root(pool):
    """
    Mounts a given pool at the default mount root (usually /mnt2/) using the
    pool.name as the final path entry. Ie pool.name = test-pool will be mounted
    at /mnt2/test-pool. Any mount options held in pool.mnt_options will be
    added to the mount command via the -o option as will a compress =
    pool.compression entry.
    If the pool concerned has root.role == "root" (i.e. it's the system pool), there are
    2 possible mount variants; depending on default_subvol().boot_to_snap:
    Boot to snap True: add "subvol=/@" and mount as per normal data pools at /mnt2/ROOT
    Boot to snap False: use the existing fstab managed mount at "/", ie no /mnt2/ROOT.
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
    root_pool_mnt = pool.mnt_pt
    if pool.is_mounted:
        return root_pool_mnt
    # Creates a directory to act as the mount point.
    create_tmp_dir(root_pool_mnt)
    toggle_path_rw(root_pool_mnt, rw=False)
    mnt_device = "/dev/disk/by-label/{}".format(pool.name)
    mnt_cmd = [MOUNT, mnt_device, root_pool_mnt]
    mnt_options = ""
    if pool.mnt_options is not None:
        mnt_options = pool.mnt_options
    if pool.compression is not None:
        if re.search("compress", mnt_options) is None:
            mnt_options = "{},compress={}".format(mnt_options, pool.compression)
    if pool.role == "root" and root_pool_mnt != "/":  # boot-to-snap - See pool model
        mnt_options = "{},subvol=/@".format(mnt_options)
    # Prior to a mount by label attempt we call btrfs device scan on all
    # members of our pool. This call ensures btrfs has up-to-date info on
    # the relevant devices and avoids the potential overkill of a system wide
    # call such as is performed in the rockstor-bootstrap service on boot.
    # Disk.target_name ensures we observe any redirect roles.
    device_scan([dev.target_name for dev in pool.disk_set.attached()])
    if os.path.exists(mnt_device):
        if len(mnt_options) > 0:
            mnt_cmd.extend(["-o", mnt_options])
        run_command(mnt_cmd)
        return root_pool_mnt
    # If we cannot mount by-label, let's try mounting by device; one by one
    # until we get our first success. All devices known to our pool object
    # have already been scanned prior to our mount by label attempt above.
    if pool.disk_set.count() < 1:
        raise Exception(
            "Cannot mount Pool({}) as it has no disks in it.".format(pool.name)
        )
    last_device = pool.disk_set.attached().last()
    logger.info("Mount by label ({}) failed.".format(mnt_device))
    for device in pool.disk_set.attached():
        mnt_device = get_device_path(device.target_name)
        logger.info("Attempting mount by device ({}).".format(mnt_device))
        if os.path.exists(mnt_device):
            mnt_cmd = [MOUNT, mnt_device, root_pool_mnt]
            if len(mnt_options) > 0:
                mnt_cmd.extend(["-o", mnt_options])
            try:
                run_command(mnt_cmd)
                return root_pool_mnt
            except Exception as e:
                if device.name == last_device.name:
                    # exhausted mounting using all devices in the pool
                    raise e
                logger.error(
                    "Error mounting: {}. "
                    "Will try using another device.".format(mnt_cmd)
                )
                logger.exception(e)
        else:
            logger.error("Device ({}) was not found".format(mnt_device))
    raise Exception(
        "Failed to mount Pool({}) due to an unknown reason. "
        "Command used {}".format(pool.name, mnt_cmd)
    )


def umount_root(root_pool_mnt):
    if not os.path.exists(root_pool_mnt):
        return
    try:
        o, e, rc = run_command([UMOUNT, "-l", root_pool_mnt])
    except CommandException as ce:
        if ce.rc == 32:
            for l in ce.err:
                l = l.strip()
                if re.search("not mounted\.$", l) is not None:
                    return
            raise ce
    for i in range(20):
        if not is_mounted(root_pool_mnt):
            toggle_path_rw(root_pool_mnt, rw=True)
            run_command([RMDIR, root_pool_mnt])
            return
        time.sleep(2)
    run_command([UMOUNT, "-f", root_pool_mnt])
    toggle_path_rw(root_pool_mnt, rw=True)
    run_command([RMDIR, root_pool_mnt])
    return


def is_subvol(mnt_pt):
    """
    Simple wrapper around "btrfs subvolume show mnt_pt"
    :param mnt_pt: mount point of subvolume to query
    :return: True if subvolume mnt_pt exists, else False
    """
    show_cmd = [BTRFS, "subvolume", "show", mnt_pt]
    # Throw=False on run_command to silence CommandExceptions.
    o, e, rc = run_command(show_cmd, throw=False)
    if rc == 0:
        return True
    return False


def subvol_info(mnt_pt):
    info = {}
    o, e, rc = run_command([BTRFS, "subvolume", "show", mnt_pt], throw=False)
    if rc == 0:
        for i in o:
            fields = i.strip().split(":")
            if len(fields) > 1:
                info[fields[0].strip()] = fields[1].strip()
    return info


def add_share(pool, share_name, qid):
    """
    Wrapper for 'btrfs subvol create' pool_mnt/share_name that will contextually also
    include a Rockstor native qgroup option, e.g. '-i 2015/6', if our -1/-1 flag value
    for quotas disabled is not found.
    A Rockstor 'share' is a btrfs 'subvolume'.
    :param pool: pool object
    :param share_name: string for proposed share (btrfs subvol) name.
    :return run_command(generated_command) or True if given pool subvol already exists.
    """
    root_pool_mnt = mount_root(pool)
    subvol_mnt_pt = root_pool_mnt + "/" + share_name
    # Ensure our root_pool_mnt is not immutable, see: remove_share()
    toggle_path_rw(root_pool_mnt, rw=True)
    if not is_subvol(subvol_mnt_pt):
        if qid == PQGROUP_DEFAULT:  # Quotas disabled
            sub_vol_cmd = [BTRFS, "subvolume", "create", subvol_mnt_pt]
        else:
            sub_vol_cmd = [BTRFS, "subvolume", "create", "-i", qid, subvol_mnt_pt]
        return run_command(sub_vol_cmd)
    return True


def mount_share(share, mnt_pt):
    # TODO: Consider making mnt_pt optional as per helper_mount_share() as then
    # TODO: we could remove almost system wide many duplicates of temp mnt_pt
    # TODO: created just prior and only for this methods call.
    if is_mounted(mnt_pt):
        return
    mount_root(share.pool)
    pool_device = get_device_path(share.pool.disk_set.attached().first().target_name)
    qgroup = share.qgroup
    # share.qgroup = "0/subvolid" use for subvol reference as more
    # flexible than "subvol=share.subvol_name" (prior method).
    subvol_str = "subvolid={}".format(qgroup[2:])
    create_tmp_dir(mnt_pt)
    toggle_path_rw(mnt_pt, rw=False)
    mnt_cmd = [MOUNT, "-t", "btrfs", "-o", subvol_str, pool_device, mnt_pt]
    return run_command(mnt_cmd)


def mount_snap(share, snap_name, snap_qgroup, snap_mnt=None):
    pool_device = get_device_path(share.pool.disk_set.attached().first().target_name)
    share_path = share.mnt_pt
    rel_snap_path = ".snapshots/{}/{}".format(share.name, snap_name)
    snap_path = "{}/{}".format(share.pool.mnt_pt, rel_snap_path).replace("//", "/")
    if snap_mnt is None:
        snap_mnt = "{}/.{}".format(share_path, snap_name)
    if is_mounted(snap_mnt):
        return
    mount_share(share, share_path)
    if is_subvol(snap_path):
        create_tmp_dir(snap_mnt)
        # snap_qgroup = "0/subvolid" use for subvol reference as more
        # flexible than "subvol=rel_snap_path" (prior method).
        subvol_str = "subvolid={}".format(snap_qgroup[2:])
        return run_command([MOUNT, "-o", subvol_str, pool_device, snap_mnt], log=True)


def default_subvol():
    """
    Returns the default vol/subvol id, path, and boot_to_snap boolean for /, used by
    system-rollback/boot-to-snapshot.
    If not set this ID = 5 i.e. the top level of the volume.
    Works by parsing the output from 'btrfs subvol get-default /':
    not set (default):
    ID 5 (FS_TREE)
    no system rollback enabled:
    ID 257 gen 5796 top level 5 path @
    or another example of the same:
    ID 256 gen 2858 top level 5 path @
    root configured for snapshots/rollback (default before any rollbacks):
    ID 268 gen 2345 top level 267 path @/.snapshots/1/snapshot
    and after having rolled back this can look like the following:
    ID 456 gen 24246 top level 258 path @/.snapshots/117/snapshot
    """
    cmd = [BTRFS, "subvolume", "get-default", "/"]
    out, e, rc = run_command(cmd, throw=False)
    if rc == 0 and len(out) > 0:
        # we have no run error and at least one line of output
        line_list = out[0].split()
        return DefaultSubvol(
            id=line_list[1],
            path=line_list[-1],  # N.B. can return ("5", "FS_TREE")
            boot_to_snap=(line_list[-1] != "@" and line_list[-1] != "(FS_TREE)"),
        )
    logger.exception(e)
    raise e


def snapshot_idmap(pool_mnt_pt):
    """
    Executes 'btrfs subvol list -s pool_mnt_pt' and parses the result. Returns
    a map/dictionary with snapshot id as key and it's path (relative to
    pool_mnt_pt) as value, ie with the 'home' subvol having a snapshot:
    'ID 286 gen 43444 cgen 43444 top le [...] path .snapshots/home/home-snap-1'
    we return = {'286': '.snapshots/home/home-snap-1'}
    :param pool_mnt_pt: Pool (vol) mount point.
    :return: Dict of relative snapshot paths indexed by their subvol id.
    """
    out, e, rc = run_command([BTRFS, "subvolume", "list", "-s", pool_mnt_pt])
    snap_idmap = {}
    for line in out:
        if re.match("ID ", line) is not None:
            fields = line.strip().split()
            snap_idmap[fields[1]] = fields[-1].replace("@/", "", 1)
    return snap_idmap


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
        pool_mnt_pt = mount_root(pool)
    except CommandException as e:
        if e.rc == 32:
            # mount failed, so we just assume that something has gone wrong at
            # a lower level, like a device failure. Return empty share map.
            # application state can be removed. If the low level failure is
            # recovered, state gets reconstructed anyway.
            return {}
        raise
    snap_idmap = snapshot_idmap(pool_mnt_pt)
    default_id = default_subvol().id
    o, e, rc = run_command([BTRFS, "subvolume", "list", "-p", pool_mnt_pt])
    shares_d = {}
    share_ids = []
    for l in o:
        if re.match("ID ", l) is None:
            continue
        fields = l.split()
        if fields[-1] in SUBVOL_EXCLUDE:
            logger.debug(
                "Skipping system-wide excluded subvol: name=({}).".format(fields[-1])
            )
            continue
        # Exclude root fs (in subvol) to avoid dependence on subvol name to
        # root fs top level dir name collision for normal operation.
        # And to expose root fs components that are themselves a subvol of
        # the root fs subvol ie @ with subvol @/home as they are inherently
        # more appropriate than the entire root fs anyway.
        # temp
        if pool.role == "root":
            # Vol/subvol auto mounted if no subvol/subvolid options are used.
            # Skipped to surface it's subvols as we only surface one layer.
            # Relevant to system rollback by booting from snapshots.
            if fields[-1] in ROOT_SUBVOL_EXCLUDE or fields[1] == default_id:
                logger.debug("Skipping excluded subvol: name=({}).".format(fields[-1]))
                continue
        vol_id = fields[1]
        if vol_id in snap_idmap:
            # snapshot so check if is_clone:
            s_name, writable, is_clone = parse_snap_details(
                pool_mnt_pt, snap_idmap[vol_id]
            )
            if not is_clone:
                continue
        parent_id = fields[5]
        if parent_id in share_ids:
            # subvol of subvol. add it so child subvols can also be ignored.
            share_ids.append(vol_id)
        elif parent_id in snap_idmap and not parent_id == default_id:
            # Boot to snapshot root pools are themselves a snapshot.
            # snapshot/subvol of snapshot.
            # add it so child subvols can also be ignored.
            snap_idmap[vol_id] = fields[-1].replace("@/", "", 1)
        else:
            # Found subvol of pool or excluded subvol-  storing for return.
            # Non snapper root rollback config:
            # ID 257 gen 5351 parent 5 top level 5 path @
            # ID 296 gen 5338 parent 257 top level 257 path home
            # When root is a snapper root rollback config we have:
            # ID 257 gen 33 parent 5 top level 5 path @
            # ID 264 gen 216 parent 257 top level 257 path @/home
            # We have assumed the prior behaviour and as we mount the root pool
            # vol/subvol via it's label we have /mnt2/ROOT not /mnt2/@.
            # Remove '@/' from rel path if found ie '@/home' to 'home' as then
            # pool+relative path works.
            shares_d[fields[-1].replace("@/", "", 1)] = "0/{}".format(vol_id)
            share_ids.append(vol_id)
    return shares_d


def parse_snap_details(pool_mnt_pt, snap_rel_path):
    """
    Returns a snapshot,s name or None if that snap is deemed to be a clone.
    Clone (is_clone) = writable snapshot + direct child of pool_mnt_pt.
    All calls also return writable, and is_clone booleans.
    :param pool_mnt_pt:  Pool (vol) mount point, ie: settings.MNT_PT/pool.name
    :param snap_rel_path: Relative snapshot path .
    :return: snap_name (None if clone), writable (Boolean), is_clone (Boolean)
    Note: is_clone is redundant but serves as a convenience boolean.
    """
    if pool_mnt_pt == "/":
        full_snap_path = pool_mnt_pt + snap_rel_path
    else:
        full_snap_path = pool_mnt_pt + "/" + snap_rel_path
    writable = not get_property(full_snap_path, "ro")
    snap_name = None
    is_clone = False
    if writable and (len(snap_rel_path.split("/")) == 1):
        # writable snapshot + direct child of pool = Rockstor clone.
        is_clone = True  # (leaving snap_name = None as not a snap but a clone)
    else:
        snap_name = snap_rel_path.split("/")[-1]
    return snap_name, writable, is_clone


def snaps_info(pool_mnt_pt, share_name):
    """
    Generates a dictionary of Rockstor relevant on-pool snapshots which do not
    include clones. See parse_snap_details() for clone definition.
    Works by analysing the varying output of differently optioned btrfs subvol
    commands and parse_snap_details() to extract the snap name (from rel path)
    and
    :param pool_mnt_pt: Pool (vol) mount point, ie: settings.MNT_PT/pool.name
    :param share_name: share/snap.name
    :return: dict indexed by snap name with tuple values of:
    (qgroup, writable) where qgroup = 0/subvolid and writable = Boolean.
    """
    # -p = show parent ID, -u = uuid of subvol, -q = parent uuid of subvol
    o, e, rc = run_command([BTRFS, "subvolume", "list", "-u", "-p", "-q", pool_mnt_pt])
    subvol_id = share_uuid = None
    for l in o:
        if re.match("ID ", l) is not None:
            fields = l.split()
            if fields[-1].replace("@/", "", 1) == share_name:
                subvol_id = fields[1]
                share_uuid = fields[12]
    if subvol_id is None:
        return {}
    # addition options to above subvol list: -s = only show snapshot subvols
    o, e, rc = run_command(
        [BTRFS, "subvolume", "list", "-s", "-p", "-q", "-u", pool_mnt_pt]
    )
    snaps_d = {}
    snap_uuids = []
    for l in o:
        if re.match("ID ", l) is not None:
            fields = l.split()
            # parent uuid must be share_uuid or another snapshot's uuid
            if (
                fields[7] != subvol_id
                and fields[15] != share_uuid
                and fields[15] not in snap_uuids
            ):
                continue
            # Strip @/ prior to calling parse_snap_details, see:
            # snapshot_idmap() for same.
            stripped_path = fields[-1].replace("@/", "", 1)
            snap_name, writable, is_clone = parse_snap_details(
                pool_mnt_pt, stripped_path
            )
            # Redundant second clause - defence against 'None' dict index.
            if not is_clone and snap_name is not None:
                snaps_d[snap_name] = ("0/{}".format(fields[1]), writable)
                # we rely on the observation that child snaps are listed after
                # their parents, so no need to iterate through results
                # separately. Instead, we add the uuid of a snap to the list
                # and look up if it's a parent of subsequent entries.
                snap_uuids.append(fields[17])
    return snaps_d


def share_id(pool, share_name):
    """
    Returns the subvolume id: becomes the share's / snapshots's qgroup.
    @todo: this should be part of add_share -- btrfs create should atomically
    Works by iterating over the output of btrfs subvolume list, received from
    subvol_list_helper() looking for a match in share_name. If found the same
    line is parsed for the ID, example line in above command output:
    'ID 257 gen 13616 top level 5 path rock-ons-root'
    consequent subvol_id return value:
    '257'
    :param pool: a pool object.
    :param share_name: target share name to find
    :return: the id for the given share_name or an Exception stating no id
    found
    """
    root_pool_mnt = mount_root(pool)
    # Note: Previous sole remaining user of subvol_list_helper() - removed.
    out, err, rc = run_command([BTRFS, "subvolume", "list", root_pool_mnt])
    subvol_id = None
    for line in out:
        if re.search(share_name + "$", line) is not None:
            subvol_id = line.split()[1]
            break
    if subvol_id is not None:
        return subvol_id
    raise Exception("subvolume id for share: {} not found.".format(share_name))


def remove_share(pool, share_name, pqgroup, force=False):
    """
    umount share if it's mounted.
    ensures given pool is mounted.
    if force flag set then first delete all share's subvolumes.
    btrfs subvolume delete root_mnt/vol_name.
    destroy shares qgroup and associated pqgroup.
    :param pool: pool object
    :param share_name: Share name as in share.name
    :param pqgroup: Pqgroup to be removed
    :param force: Flag used to also remove all subvolumes of the given share.
    """
    if is_share_mounted(share_name):
        # N.B. we only unmount rockstor managed share points.
        mnt_pt = "{}{}".format(DEFAULT_MNT_DIR, share_name)
        umount_root(mnt_pt)
    root_pool_mnt = mount_root(pool)
    subvol_mnt_pt = root_pool_mnt + "/" + share_name
    if not is_subvol(subvol_mnt_pt):
        return
    # Remove the immutable flag if set as this will block a subvol delete
    # with an 'Operation not permitted' and leave an unmounted share.
    # This flag can also break replication as we supplant the transient share.
    # The immutable flag has been seen to spontaneously appear. Upon this
    # bug being resolved we might consider promoting to force=True calls only.
    # TODO: Consider also using the following command to allow delete of the
    # initial (anomalous) temp replication snap as share; but this also blindly
    # circumvents ro 'protection' for any other share!
    # set_property(subvol_mnt_pt, 'ro', 'false', mount=False)
    toggle_path_rw(subvol_mnt_pt, rw=True)
    if force:
        o, e, rc = run_command([BTRFS, "subvolume", "list", "-o", subvol_mnt_pt])
        for l in o:
            if re.match("ID ", l) is not None:
                subvol = root_pool_mnt + "/" + l.split()[-1]
                # TODO: consider recursive immutable flag removal.
                run_command([BTRFS, "subvolume", "delete", subvol], log=True)
    qgroup = "0/{}".format(share_id(pool, share_name))
    delete_cmd = [BTRFS, "subvolume", "delete", subvol_mnt_pt]
    run_command(delete_cmd, log=True)
    qgroup_destroy(qgroup, root_pool_mnt)
    return qgroup_destroy(pqgroup, root_pool_mnt)


def remove_snap(pool, share_name, snap_name, snap_qgroup):
    root_mnt = mount_root(pool)
    snap_path = "{}/.snapshots/{}/{}".format(root_mnt, share_name, snap_name)
    if is_mounted(snap_path):
        umount_root(snap_path)
    if is_subvol(snap_path):
        run_command([BTRFS, "subvolume", "delete", snap_path], log=True)
        return qgroup_destroy(snap_qgroup, root_mnt)
    else:
        # TODO: Consider using snapshot_idmap() for dict of id -> snap-path
        o, e, rc = run_command([BTRFS, "subvolume", "list", "-s", root_mnt])
        for l in o:
            # just give the first match.
            if re.match("ID.*{}$".format(snap_name), l) is not None:
                snap = "{}/{}".format(root_mnt, l.split()[-1])
                return run_command([BTRFS, "subvolume", "delete", snap], log=True)


def add_snap_helper(orig, snap, writable):
    cmd = [BTRFS, "subvolume", "snapshot", orig, snap]
    if not writable:
        cmd.insert(3, "-r")
    # TODO: Consider removing hopefully now redundant rc = 19 exception clause.
    try:
        return run_command(cmd)
    except CommandException as ce:
        if ce.rc != 19:
            # rc == 19 is due to the slow kernel cleanup thread. snapshot gets
            # created just fine. lookup is delayed arbitrarily.
            raise ce


def add_clone(pool, share, clone, snapshot=None):
    """
    clones either a share or a snapshot
    """
    pool_mnt = mount_root(pool)
    orig_path = pool_mnt
    if snapshot is not None:
        orig_path = "{}/.snapshots/{}/{}".format(orig_path, share, snapshot)
    else:
        orig_path = "{}/{}".format(orig_path, share)
    clone_path = "{}/{}".format(pool_mnt, clone)
    return add_snap_helper(orig_path, clone_path, True)


def add_snap(share, snap_name, writable):
    """
    create a snapshot
    """
    share_full_path = share.mnt_pt
    snap_dir = "{}/.snapshots/{}".format(share.pool.mnt_pt, share.subvol_name).replace(
        "//", "/"
    )
    create_tmp_dir(snap_dir)
    snap_full_path = "{}/{}".format(snap_dir, snap_name)
    return add_snap_helper(share_full_path, snap_full_path, writable)


def switch_quota(pool, flag="enable"):
    root_mnt_pt = mount_root(pool)
    cmd = [BTRFS, "quota", flag, root_mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        # Avoid failure when attempting an enable/disable quota change if
        # our pool (vol) is ro: by catching this specific CommandException:
        emsg = "ERROR: quota command failed: Read-only file system"
        if e.err[0] == emsg:
            logger.error(
                "Failed to {} quotas on pool ({}). To resolve "
                'run "btrfs quota {} {}".'.format(flag, pool.name, flag, root_mnt_pt)
            )
            return e.out, e.err, e.rc
        # otherwise we raise an exception as normal.
        raise e
    return o, e, rc


def enable_quota(pool):
    return switch_quota(pool)


def disable_quota(pool):
    return switch_quota(pool, flag="disable")


def rescan_quotas(pool):
    root_mnt_pt = mount_root(pool)
    cmd = [BTRFS, "quota", "rescan", root_mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=True)
    except CommandException as e:
        # Catch breaking exception on Read-only filesystem, log and move on.
        emsg = "ERROR: quota rescan failed: Read-only file system"
        if e.err[0] == emsg:
            logger.info(
                "Pool: ({}) is Read-only, skipping quota rescan.".format(pool.name)
            )
            return e.out, e.err, e.rc
        # Catch breaking exception for non fatal 'already running' state.
        emsg2 = "ERROR: quota rescan failed: Operation now in progress"
        if e.err[0] == emsg2:
            logger.info(
                "Pool ({}) has quota rescan in progress, skipping "
                "rescan request.".format(pool.name)
            )
            return e.out, e.err, e.rc
        # otherwise we raise an exception as normal.
        raise e
    return o, e, rc


def are_quotas_enabled(mnt_pt):
    """
    Simple wrapper around 'btrfs qgroup show -f --raw mnt_pt' intended
    as a fast determiner of True / False status of quotas enabled
    :param mnt_pt: Mount point of btrfs filesystem
    :return: True on rc = 0 and (err = '' or err = rescan recommended warning),
    False otherwise.
    """
    o, e, rc = run_command([BTRFS, "qgroup", "show", "-f", "--raw", mnt_pt])
    if rc == 0 and (
        e[0] == "" or e[0] == "WARNING: qgroup data inconsistent, rescan recommended"
    ):
        return True
    # Note on above e[0] clauses:
    # Catch rare but observed rc == 0 when quotas disabled, e.g.:
    # btrfs qgroup show -f --raw /mnt2/rock-pool
    # WARNING: quota disabled, qgroup data may be out of date
    # qgroupid         rfer         excl
    # --------         ----         ----
    # 0/5                 0            0
    #
    # echo $?
    # 0
    # We are called in a try except block: caller assumes False on Exception.
    return False


def qgroup_exists(mnt_pt, qgroup):
    """
    Simple wrapper around 'btrfs qgroup show --raw mnt_pt' intended to
    establish if a specific qgroup exists on a btrfs filesystem.
    :param mnt_pt: btrfs filesystem mount point, usually the pool.
    :param qgroup: qgroup of the form 2015/n (intended for use with pqgroup)
    :return: True is given qgroup exists in command output, False otherwise.
    """
    o, e, rc = run_command([BTRFS, "qgroup", "show", "--raw", mnt_pt])
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
    return "0/" + sid


def qgroup_max(mnt_pt):
    """
    Parses the output of "btrfs qgroup show mnt_pt" to find the highest qgroup
    matching QID/* if non is found then 0 will be returned.
    Quotas not enabled is flagged by a -1 return value.
    :param mnt_pt: A given btrfs mount point.
    :return: -1 if quotas not enabled, else highest 2015/* qgroup found or 0
    """
    try:
        o, e, rc = run_command([BTRFS, "qgroup", "show", mnt_pt], log=False)
    except CommandException as e:
        # disabled quotas can result in o = [''], rc = 1 and e[0] =
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info(
                "Mount Point: {} has Quotas disabled, skipping qgroup "
                "show.".format(mnt_pt)
            )
            # and return our default res
            return -1
        # confused/indeterminate quota state:
        emsg2 = "ERROR: cannot find the qgroup"
        # this is non fatal so treat as disabled and advise. Avoids blocking imports.
        # Also check second line for same, as first line can be taken by the following:
        # "WARNING: qgroup data inconsistent, rescan recommended"
        if (re.match(emsg2, e.err[0]) is not None) or (
            len(e.err) > 1 and re.match(emsg2, e.err[1]) is not None
        ):
            logger.info(
                "Mount Point: {} has indeterminate quota status, skipping "
                "qgroup show.\nTry 'btrfs quota disable {}'.".format(mnt_pt, mnt_pt)
            )
            return -1
        # otherwise we raise an exception as normal.
        raise
    # Catch quota disabled WARNING (no associated Exception) and info log.
    if e[0] == "WARNING: quota disabled, qgroup data may be out of date":
        logger.info(
            "Mount Point: {} has Quotas disabled WARNING, skipping "
            "qgroup show.".format(mnt_pt)
        )
        # and return our default res
        return -1
    # if no exception, and no caught WARNING, find the max 2015/qgroup
    res = 0
    for l in o:
        if re.match("{}/".format(QID), l) is not None:
            cid = int(l.split()[0].split("/")[1])
            if cid > res:
                res = cid
    return res


def qgroup_create(pool, qgroup=PQGROUP_DEFAULT):
    """
    When passed only a pool an attempt will be made to ascertain if quotas are
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
        qid = "{}/{}".format(QID, max_native_qgroup + 1)
    try:
        out, err, rc = run_command([BTRFS, "qgroup", "create", qid, mnt_pt], log=False)
    except CommandException as e:
        # ro mount options will result in o= [''], rc = 1 and e[0] =
        emsg = "ERROR: unable to create quota group: Read-only file system"
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info(
                "Pool: {} is Read-only, skipping qgroup create.".format(pool.name)
            )
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
    cmd = [BTRFS, "qgroup", "show", mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=False)
    except CommandException as e:
        # we may have quotas disabled so catch and deal.
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        if e.err[0] == emsg:
            # we have quotas disabled so can't destroy any anyway so skip
            # and deal by returning False so our caller moves on.
            return False
        # Also catch missing qgroup and log suggestion as per in qgroup_max()
        # confused/indeterminate quota state:
        emsg2 = "ERROR: cannot find the qgroup"
        # this is non fatal so treat as disabled and advise. Avoids blocking imports.
        # Also check second line for same, as first line can be taken by the following:
        # "WARNING: qgroup data inconsistent, rescan recommended"
        if (re.match(emsg2, e.err[0]) is not None) or (
            len(e.err) > 1 and re.match(emsg2, e.err[1]) is not None
        ):
            logger.info(
                "Mount Point: {} has indeterminate quota status, skipping "
                "qgroup show.\nTry 'btrfs quota disable {}'.".format(mnt_pt, mnt_pt)
            )
            return False
        # otherwise we raise an exception as normal
        raise e
    for l in o:
        if re.match(qid, l) is not None and l.split()[0] == qid:
            return run_command([BTRFS, "qgroup", "destroy", qid, mnt_pt], log=True)
    return False


def qgroup_is_assigned(qid: str, pqid: str, mnt_pt: str) -> bool:
    """
    Returns true if quota group qid is assigned to parent quota group pqid,
    for the Pool mount point mnt_pt. Parses "BTRFS qgroup show -pc mnt_pt"
    @param qid: quota group id, i.e. "0/268"
    @param pqid: parent quota group id, i.e. "2015/2"
    @param mnt_pt: Mount point on Pool of interest
    @return: qid is assigned to pqid for given pool
    """
    cmd = [BTRFS, "qgroup", "show", "-pc", mnt_pt]
    try:
        o, e, rc = run_command(cmd, log=False)
    except CommandException as e:
        emsg = "ERROR: can't list qgroups: quotas not enabled"
        if e.err[0] == emsg:
            # No need to scan output as nothing to see with quotas disabled.
            # And since no quota capability can be enacted we return True
            # to avoid our caller trying any further with quotas.
            return True
        # otherwise we raise an exception as normal
        raise e
    #   [0]       [1]       [2]       [3]   [4]   [5]
    # Qgroupid Referenced Exclusive Parent Child Path
    for line in o:
        fields = line.split()
        if len(fields) <= 3:
            continue
        qgroupid: str = fields[0]
        parent: str = fields[3]
        if qgroupid == qid and pqid in parent.split(","):
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
    return qgroup_assign(share.qgroup, pqgroup, share.pool.mnt_pt)


def qgroup_assign(qid, pqid, mnt_pt):
    """
    Wrapper for 'BTRFS, qgroup, assign, qid, pqid, mnt_pt'
    :param qid: qgroup to assign as child of pqgroup
    :param pqid: pqgroup to use as parent
    :param mnt_pt: btrfs filesystem mountpoint (usually the associated pool)
    """
    if qgroup_is_assigned(qid, pqid, mnt_pt):
        return True

    # since btrfs-progs 4.2, qgroup assign succeeds but throws a warning:
    # "WARNING: # quotas may be inconsistent, rescan needed" and returns with
    # exit code 1.
    try:
        run_command([BTRFS, "qgroup", "assign", qid, pqid, mnt_pt], log=False)
    except CommandException as e:
        emsg = "ERROR: unable to assign quota group: Read-only file system"
        # this is non-fatal, so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info(
                "Read-only fs ({}), skipping qgroup assign: "
                "child ({}), parent ({}).".format(mnt_pt, qid, pqid)
            )
            return e.out, e.err, e.rc
        # Under some indeterminate quota states the following error occurs:
        emsg2 = "ERROR: unable to assign quota group: Invalid argument"
        # This can results in a failed import if not caught and given quotas
        # are non critical we catch and error log rather than hard failing.
        # TODO: This is a broad error message and it's inclusion should be
        # TODO: re-assessed after major btrfs version increases: post quotas
        # TODO: considered more stable.
        if e.err[0] == emsg2:
            logger.error(
                '"{}" received on fs ({}), skipping qgroup assign: '
                "child ({}), parent ({}). This may be related to an "
                "undetermined quota state.".format(emsg2, mnt_pt, qid, pqid)
            )
            return e.out, e.err, e.rc
        # N.B. we catch known errors and log to avoid blocking share imports.
        # Newer btrfs schedules its own quota rescans and with serialized quote changes
        # these can overlap, so we catch, log, and move on to avoid blocking imports.
        rescan_sched_out = "Quota data changed, rescan scheduled"
        rescan_sched_err = "ERROR: quota rescan failed: Operation now in progress"
        if e.err[0] == rescan_sched_err:
            self_rescan_error = "--- WARNING: auto quota rescan overlap \n({})".format(
                rescan_sched_err
            )
            return logger.info(rescan_sched_out + "\n" + self_rescan_error)
        wmsg = "WARNING: quotas may be inconsistent, rescan needed"
        if e.err[0] == wmsg:
            # schedule a rescan if one is not currently running.
            dmsg = "Quota inconsistency while assigning {}. Rescan scheduled.".format(
                qid
            )
            try:
                run_command([BTRFS, "quota", "rescan", mnt_pt])
                return logger.debug(dmsg)
            except CommandException as e2:
                emsg = "ERROR: quota rescan failed: Operation now in progress"
                if e2.err[0] == emsg:
                    return logger.debug(
                        "{}.. Another rescan already in progress.".format(dmsg)
                    )
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
    cmd = [BTRFS, "qgroup", "limit", "none", qgroup, root_pool_mnt]
    # Set defaults in case our run_command fails to assign them.
    out = err = [""]
    rc = 0
    if qgroup == PQGROUP_DEFAULT:
        # We have a 'quotas disabled' or 'Read-only' qgroup value flag,
        # log and return blank.
        logger.info("Pool: {} ignoring update_quota on {}".format(pool.name, qgroup))
        return out, err, rc
    try:
        out, err, rc = run_command(cmd, log=False)
    except CommandException as e:
        # ro mount options will result in o= [''], rc = 1 and e[0] =
        emsg = "ERROR: unable to limit requested quota group: Read-only file system"
        # this is non fatal so we catch this specific error and info log it.
        if e.err[0] == emsg:
            logger.info(
                "Pool: {} is Read-only, skipping qgroup limit.".format(pool.name)
            )
            return out, err, rc
        # quotas disabled results in o = [''], rc = 1 and e[0] =
        emsg2 = "ERROR: unable to limit requested quota group: Invalid argument"
        # quotas disabled is not a fatal failure but here we key from what
        # is a non specific error: 'Invalid argument'.
        # TODO: improve this clause as currently too broad.
        # TODO: we could for example use if qgroup_max(mnt) == -1
        if e.err[0] == emsg2:
            logger.info(
                "Pool: {} has encountered a qgroup limit issue, "
                "skipping qgroup limit. Disabled quotas can cause "
                "this error".format(pool.name)
            )
            return out, err, rc
        emsg3 = (
            "ERROR: unable to limit requested quota group: No such file or directory"
        )
        if e.err[0] == emsg3:
            logger.info(
                "Pool: {} is missing expected qgroup {}".format(pool.name, qgroup)
            )
            logger.info("Previously disabled quotas can cause this issue")
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
    cmd = [BTRFS, "subvolume", "list", root_pool_mnt]
    out, err, rc = run_command(cmd, log=True)
    short_id = volume_id.split("/")[1]
    volume_dir = ""
    # Examine all pool subvols until we find an ID match in column 1, then normalise
    # it's full path by replacing (fast) leading @/ and double "//" with "/".
    for line in out:
        fields = line.split()
        if len(fields) > 0 and short_id in fields[1]:
            volume_dir = (
                root_pool_mnt + "/" + fields[-1].replace("@/", "", 1)
            ).replace("//", "/")
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
    # Here we depend on fail through throw=False if quotas are disabled/indeterminate
    cmd = [BTRFS, "qgroup", "show", volume_dir]
    out, err, rc = run_command(cmd, log=False, throw=False)
    volume_id_sizes = [0, 0]
    pvolume_id_sizes = [0, 0]
    for line in out:
        fields = line.split()
        # We may index up to [2] fields (3 values) so ensure they exist.
        if len(fields) > 2 and "/" in fields[0]:
            qgroup = fields[0]
            if qgroup == volume_id:
                rusage = convert_to_kib(fields[1])
                eusage = convert_to_kib(fields[2])
                volume_id_sizes = [rusage, eusage]
            if pvolume_id is not None and qgroup == pvolume_id:
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
        if is_share_mounted(share_map[s]):
            mnt_pt = "{}{}".format(DEFAULT_MNT_DIR, share_map[s])
            break
    if mnt_pt is None:
        mnt_pt = mount_root(pool)
    cmd = [BTRFS, "qgroup", "show", mnt_pt]
    out, err, rc = run_command(cmd, log=True)
    combined_map = dict(share_map, **snap_map)
    for line in out:
        fields = line.split()
        if len(fields) > 0 and fields[0] in combined_map:
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
    cmd = [BTRFS, "fi", "usage", "-b", mnt_pt]
    out, err, rc = run_command(cmd)

    used = 0
    for line in out:
        fields = re.split("\W+", line)
        if line.startswith("Data"):
            used += int(fields[5])
        elif re.search("Size", line):
            used += int(fields[3])

    return used / 1024


def usage_bound(disk_sizes, num_devices, raid_level):
    """Return the total amount of storage possible within this pool's set
    of disks, in bytes.

    Algorithm adapted from Hugo Mills' implementation previously at:
    http://carfax.org.uk/btrfs-usage/js/btrfs-usage.js
    and replaced by the elm generated: https://carfax.org.uk/btrfs-usage/elm.js
    """
    # Determine RAID parameters
    data_copies = PROFILE[raid_level].data_copies
    data_parity = PROFILE[raid_level].data_parity

    # TODO: As stripes/chunks depend on pool geometry we cannot use PROFILE.
    #  Once we are Python 3 compatible, re-assess our size calculation in light of
    #  https://github.com/knorrie/python-btrfs i.e.:
    #  btrfs-space-calculator
    stripes = 1
    # Number of chunks to write at a time: as many as possible within the
    # number of stripes
    chunks = num_devices

    if raid_level.startswith(("unknown", "single")):
        chunks = 1
    # We have no mixed raid levels with raid0, but in case we encounter them:
    elif raid_level.startswith("raid0"):
        stripes = 2
    # Take care not to match raid10 before its time:
    elif raid_level == "raid1" or raid_level.startswith("raid1-"):
        chunks = 2
    elif raid_level.startswith("raid10"):
        stripes = max(2, int(num_devices / 2))

    # Round down so that we have an exact number of duplicate copies
    chunks -= chunks % data_copies

    # Check for feasibility at the lower end
    if num_devices < data_copies * (stripes + data_parity):
        return 0

    # Compute the trivial bound
    bound = int(sum(disk_sizes) / chunks)

    # For each partition point q, compute B_q (the test predicate) and
    # modify the trivial bound if it passes.
    bounding_q = -1
    for q in range(chunks - 1):
        slice_value = sum(disk_sizes[q + 1 :])
        b = int(slice_value / (chunks - q - 1))
        if disk_sizes[q] >= b and b < bound:
            bound = b
            bounding_q = q

    # The bound is the number of allocations we can make in total. If we
    # have no bounding_q, then we have hit the trivial bound, and exhausted
    # all space, so we can return immediately.
    if bounding_q == -1:
        return bound * ((chunks / data_copies) - data_parity)

    # If we have a bounding_q, then all the devices past q are full, and
    # we can remove them. The devices up to q have been used in every one
    # of the allocations, so we can just reduce them by bound.
    disk_sizes = [
        size - bound for index, size in enumerate(disk_sizes) if index <= bounding_q
    ]

    new_bound = usage_bound(disk_sizes, bounding_q + 1, raid_level)

    return bound * ((chunks / data_copies) - data_parity) + new_bound


def scrub_start(pool, force=False):
    mnt_pt = mount_root(pool)
    p = PoolScrub(mnt_pt, force)
    p.start()
    return p.pid


def btrfsprogs_legacy() -> bool:
    """
    Returns True if "btrfs version" considered legacy: i.e. < "v5.1.2".
    Example output of "btrfs version" is "btrfs-progs v6.5.1".
    v4.12 (Leap 15.2), v4.19.1 (Leap 15.3), v5.14 (Leap 15.4 & 15.5),
    v6.5.1 (Leap 15.6), v6.9.2 TW or Backports (July 2024).
    For assumed version string schema:
    https://packaging.python.org/en/latest/specifications/version-specifiers/#version-scheme
    :return: Legacy status.
    """
    legacy_version = Version("v5.1.2")
    installed_version = Version("v6.7.8")  # Place-holder flag value
    out, err, rc = run_command([BTRFS, "version"])
    try:
        installed_version = Version(out[0].split()[1])
    except Exception as e:
        logger.exception(e)
        if not e.__class__ == InvalidVersion:
            raise e
    if installed_version < legacy_version:
        return True
    return False


def scrub_status_extra(mnt_pt):
    """
    Non legacy btrfs-progs returns (in default non -R form) time_left, ETA, and rate
    during a scrub operation (status = "running").
    Otherwise, only rate is available.
    Collect and return these extra statistics (where available).
    :param mnt_pt: pool mount point
    :return: dictionary indexed by 'time_left', 'ETA', 'rate': where available.
    from non legacy btrfs-progs versions.
    """
    stats = {}
    out2, err2, rc2 = run_command([BTRFS, "scrub", "status", mnt_pt])
    if re.search("running", out2[2]) is not None:
        # time_left
        fields2 = out2[4].split()[-1].split(":")
        stats["time_left"] = (
            (int(fields2[0]) * 60 * 60) + (int(fields2[1]) * 60) + int(fields2[2])
        )
        # eta
        fields3 = out2[5].strip().split(": ")
        dateFormat = "%a %b %d %H:%M:%S %Y"
        stats["eta"] = datetime.strptime(fields3[1].strip(), dateFormat)
        # rate
        fields4 = out2[8].strip().split(": ")
        stats["rate"] = fields4[1].strip()
    else:  # status not running:
        fields5 = out2[5].strip().split(": ")
        stats["rate"] = fields5[1].strip()
    return stats


def scrub_status(pool, legacy=False):
    """
    Wrapper for scrub_status_raw(), and if (status not conn-reset or unknown) and
    btrfsprogs_legacy() False, add scrub_status_extra() to the results.
    :param pool: pool object
    :param legacy: btrfsprogs_legacy()
    :return: dictionary indexed by scrub 'status' and various statistics.
    """
    mnt_pt = mount_root(pool)
    stats_raw = scrub_status_raw(mnt_pt, legacy)
    if (
        legacy  # legacy btrfs has no extra eta etc info
        or stats_raw["status"] == "conn-reset"
        or stats_raw["status"] == "unknown"
    ):
        return stats_raw
    stats_extra = scrub_status_extra(mnt_pt)
    total_status = stats_raw.copy()
    total_status.update(stats_extra)
    return total_status


def scrub_status_raw(mnt_pt, legacy=False):
    """
    Returns the raw statistics per-device (-R option) of the ongoing or last
    known btrfs scrub. Works by parsing the output of the following command:
    btrfs scrub status -R <mount-point>
    :param mnt_pt: pool mount point.
    :param legacy: Boolean indicating legacy btrfs-progs: see btrfsprogs_legacy().
    :return: dictionary indexed via 'status' and if a finished or halted, or
    cancelled scrub is indicated then the duration of that scrub is added as
    value to added index 'duration'. In all 'status' cases bar 'unknown',
    data_bytes_scrubbed is passed as value to index 'kb_scrubbed' and all
    other -R invoked details are returned as key value pairs.
    """
    stats = {"status": "unknown"}
    # Based on version of btrfs progs, set the offset to parse properly
    if legacy:
        statOffset = 1
        durOffset = 1
        fieldOffset = 2
        haltOffset = -3
    else:
        statOffset = 2
        durOffset = 3
        fieldOffset = 4
        haltOffset = -1
    out, err, rc = run_command([BTRFS, "scrub", "status", "-R", mnt_pt])
    if err != [""] and len(err) > 0:
        if err[0] == "WARNING: failed to read status: Connection reset by peer":
            stats["status"] = "conn-reset"
            return stats
    if len(out) > 1:
        if re.search("interrupted", out[statOffset]) is not None:
            stats["status"] = "halted"
            # extract the duration from towards the end of the first line eg:
            # "... 2017, interrupted after 00:00:09, not running"
            dfields = out[durOffset].split()[haltOffset].strip(",").split(":")
            stats["duration"] = (
                (int(dfields[0]) * 60 * 60) + (int(dfields[1]) * 60) + int(dfields[2])
            )
        elif re.search("running", out[statOffset]) is not None:
            stats["status"] = "running"
        elif re.search("finished", out[statOffset]) is not None:
            stats["status"] = "finished"
            # extract the duration from the end of the first line eg:
            # "... 2017 and finished after 00:00:16"
            dfields = out[durOffset].split()[-1].split(":")
            stats["duration"] = (
                (int(dfields[0]) * 60 * 60) + (int(dfields[1]) * 60) + int(dfields[2])
            )
        elif re.search("aborted", out[statOffset]) is not None:
            stats["status"] = "cancelled"
            # extract the duration from the end of the first line eg:
            # "... 2017 and was aborted after 00:04:56"
            # TODO: we have code duplication here re finished clause above.
            dfields = out[durOffset].split()[-1].split(":")
            stats["duration"] = (
                (int(dfields[0]) * 60 * 60) + (int(dfields[1]) * 60) + int(dfields[2])
            )
        else:
            return stats
    else:  # we have an unknown status as out is 0 or 1 lines long.
        return stats
    for line in out[fieldOffset:-1]:
        fields = line.strip().split(": ")
        if fields[0] == "data_bytes_scrubbed":
            stats["kb_scrubbed"] = int(fields[1]) / 1024
        else:
            stats[fields[0]] = int(fields[1])
    return stats


@task()
def start_resize_pool(cmd):
    """
    Note for device add, which is almost instantaneous, we are currently called
    via the huey async bypass function (start_resize_pool.call_local()) which
    bypasses our @task() decorator and we are then called directly.
    See: https://huey.readthedocs.io/en/latest/guide.html#tips-and-tricks

    https://www.untangled.dev/2020/07/01/huey-minimal-task-queue-django/
    "... avoid passing a Django model instance or queryset as parameter."
    "Instead pass the object id, which is an int..."
    and retrieve the Django object a-fresh in the task function.
    :param cmd: btrfs dev add/delete command in run_command() format (ie list).
    """
    logger.debug("Resize pool command ({}).".format(cmd))
    # N.B. in some instances, such as live disk removal, an attempt to remove missing:
    # btrfs device delete missing /mnt2/pool-label
    # results in rc=1, out=[""], and err=
    # ["ERROR: error removing device 'missing': no missing devices found to remove", '']
    # return advice, in this case, to improve usability. Customised exception message is
    # presented in Pool details page - Balances tab, Errors or Notes column.
    try:
        run_command(cmd, log=True)
    except CommandException as e:
        emsg = (
            "ERROR: error removing device 'missing': no missing devices found to remove"
        )
        if e.err[0] == emsg:
            msg = (
                "Missing Device removal failed, ensure degraded,rw mount options are used "
                "(a reboot may be required)."
            )
            logger.error(msg)
            raise Exception(
                "{} Command was ({}). Command Exception was ({}).".format(
                    msg, " ".join(cmd), emsg
                )
            )
        raise e


def balance_pool_cmd(mnt_pt, force=False, convert=None):
    cmd = ["btrfs", "balance", "start", mnt_pt]
    # With no filters we also get a warning that block some balances due to
    # expected long execution time, in this case "--full-balance" is required.
    if force:
        cmd.insert(3, "-f")
    if convert is not None:
        cmd.insert(3, "-dconvert={}".format(PROFILE[convert].data_raid))
        cmd.insert(3, "-mconvert={}".format(PROFILE[convert].metadata_raid))
    else:
        # As we are running with no convert filters a warning and 10 second
        # countdown with ^C prompt will result unless we use "--full-balance".
        # This warning is now present in the Web-UI "Start a new balance"
        # button tooltip.
        cmd.insert(3, "--full-balance")
    logger.debug("Balance command ({}).".format(cmd))
    return cmd


@task()
def start_balance(cmd):
    """
    Simple named wrapper to run balance command via Huey with logging and possible
    exception filtering in case we need to improve error messaging.
    See: start_resize_pool as counterpart wrapper.

    https://www.untangled.dev/2020/07/01/huey-minimal-task-queue-django/
    "... avoid passing a Django model instance or queryset as parameter."
    "Instead pass the object id, which is an int..."
    and retrieve the Django object a-fresh in the task function.
    :param cmd: btrfs dev add/delete command in run_command() format (ie list).
    :param cmd:
    :return:
    """
    logger.debug("Balance pool command ({}).".format(cmd))
    try:
        run_command(cmd)
    except CommandException as e:
        # We may need additional exception filtering/altering here.
        raise e


def balance_status(pool):
    """
    Wrapper around btrfs balance status pool_mount_point to extract info about
    the current status of a balance.
    :param pool: pool object to query
    :return: dictionary containing parsed info about the balance status,
    ie indexed by 'status' and 'percent_done'.
    """
    stats = {"status": "unknown"}
    # The balance status of an umounted pool is undetermined / unknown, ie it
    # could still be mid balance: our balance status command requires a
    # relevant active mount path.
    # Note that if we silently fail through the mount confirmation then our
    # balance status will reflect the system pool balance status.
    try:
        mnt_pt = mount_root(pool)
    except Exception as e:
        logger.error(
            "Exception while refreshing balance status for Pool({}). "
            'Returning "unknown": {}'.format(pool.name, e.__str__())
        )
        return stats
    out, err, rc = run_command([BTRFS, "balance", "status", mnt_pt], throw=False)
    if len(out) > 0:
        if re.match("Balance", out[0]) is not None:
            if re.search("cancel requested", out[0]) is not None:
                stats["status"] = "cancelling"
            elif re.search("pause requested", out[0]) is not None:
                stats["status"] = "pausing"
            elif re.search("paused", out[0]) is not None:
                stats["status"] = "paused"
            else:
                stats["status"] = "running"
            # make sure we have a second line before parsing it.
            if len(out) > 1 and re.search("chunks balanced", out[1]) is not None:
                percent_left = out[1].split()[-2][:-1]
                try:
                    percent_left = int(percent_left)
                    stats["percent_done"] = 100 - percent_left
                except:
                    pass
        elif re.match("No balance", out[0]) is not None:
            stats["status"] = "finished"
            stats["percent_done"] = 100
    return stats


def get_devid_usage(mnt_pt):
    """
    Extracts device usage information for a given mount point; includes
    detached devices where devid is preserved but device name is replaced by
    'missing': where there can be multiple 'missing' entries.
    Wraps 'btrfs device usage -b mnt_pt'.
    Used by _update_disk_state() to retrieve detached disk size/allocated info.
    :return: btrfs devid indexed dict with DevUsageInfo values
    """
    ALLOCATION_TYPES = ["Data", "Metadata", "System"]
    devid_usage_info = {}
    cmd = [BTRFS, "device", "usage", "-b", mnt_pt]
    o, e, rc = run_command(cmd)
    devid = None  # None allows for fast comparison for flag use.
    temp_name = "missing"
    size = 0
    allocated = 0
    for line in o:
        if line == "":
            continue
        fields = line.replace(",", " ").split()
        if fields[1] == "slack:":
            continue  # We are not interested currently so skip for speed.
        if fields[1] == "ID:":  # New device section: set devid index
            devid = int(fields[2])
            temp_name = fields[0]
        elif fields[1] == "size:":
            size = int(fields[2]) / 1024  # Bytes to KB
        elif fields[0] in ALLOCATION_TYPES:
            allocated += int(fields[2]) / 1024  # Bytes to KB
        elif fields[0] == "Unallocated:":
            # End of a legitimate device entry so record our tally so far:
            devid_usage_info[devid] = DevUsageInfo(
                temp_name=temp_name, size=size, allocated=allocated
            )
            allocated = 0  # Reset our per device tally prior to next entry.
    # logger.debug('get_devid_usage() returning {}.'.format(devid_usage_info))
    return devid_usage_info


def balance_status_internal(pool):
    """
    As internal balance events, such as are initiated by btrfs dev remove, are
    not reported by 'btrfs balance status', we have to devise our own system;
    at least until these events, which can last hours, are surfaced otherwise.
    Here we parse the output of 'btrfs dev usage -b mnt_pt' and look for a
    negative unallocated value. This negative value progressively approaches
    zero where upon the task is complete and the associated device disappears:
    having had all of it's data removed.
    Note that when more than one disk is removed btrfs internally does one at
    a time so we need only find a single instance irrespective.

    Until we get a better option this function serves a minimal subset of the
    functions provided for regular balances by balance_status(pool) but for
    'internal' balances (our name) that are auto initiated on disk removal.
    A future enhancement could be to ascertain partial percent done, which may
    be viable by resourcing get_devid_usage(); but since a device size can be
    zero, for a detached device, and allocated approaches zero while negative
    unallocated does the same this may be tricky as we have no start state
    datum: leaving only a whole pool analysis - indicated disks but then the
    serial nature of removal hampers this approach.
    :param pool: Pool db object.
    :return: dictionary containing parsed info about the balance status,
    ie indexed by 'status' and 'percent_done'.
    """
    stats = {"status": "unknown"}
    try:
        mnt_pt = mount_root(pool)
    except Exception as e:
        logger.error(
            "Exception while refreshing internal balance status for"
            "Pool({}). Returning "
            '"unknown": {}'.format(pool.name, e.__str__())
        )
        return stats
    cmd = [BTRFS, "dev", "usage", "-b", mnt_pt]
    o, err, rc = run_command(cmd, throw=False)
    unallocated = None
    for line in o:
        if line == "":
            continue
        fields = line.replace(",", " ").split()
        if fields[0] == "Unallocated:":
            unallocated = int(fields[1])
            if unallocated < 0:
                stats["status"] = "running"
                break
    if unallocated is not None and unallocated >= 0:
        # We have no 'tell' so report a finished balance as there is no
        # evidence of one happening.
        stats["status"] = "finished"
        stats["percent_done"] = 100
    return stats


def balance_status_all(pool):
    """
    Wrapper/meta caller of balance_status() and balance_status_internal().
    If the former reports no live balance the latter is checked.
    Used to inform the caller of the current or last know status as reported
    by a call to 'btfs balance status' (balance_status()) or an implied
    internal balance as repoted by balance_status_internal().
    For status dict see called functions.
    param pool: Pool db object.
    :return: named tupil: active:boolean, internal:boolean, status:dict
    """
    active = False
    internal = False
    status = balance_status(pool)
    if status["status"] in ["unknown", "finished"]:
        # Try internal balance detection as we don't have regular balance in-flight.
        status_internal = balance_status_internal(pool)
        if status_internal["status"] not in ["unknown", "finished"]:
            internal = active = True
            status = status_internal
    else:
        active = True
    logger.debug(
        "Balance active: ({}), Internal: ({}), Live Status: ({})".format(
            active, internal, status
        )
    )
    return BalanceStatusAll(active=active, internal=internal, status=status)


def device_scan(dev_byid_list=["all"]):
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
    out = err = [""]
    # default to successful return code unless we find otherwise.
    rc = 0
    if len(dev_byid_list) > 0:
        if dev_byid_list[0] == "all":
            return run_command([BTRFS, "device", "scan"])
        for dev_byid in dev_byid_list:
            if re.match("detached-", dev_byid) is not None:
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
                    [BTRFS, "device", "scan", dev_byid_withpath], throw=False
                )
                if rc != 0:
                    # Return on first non zero return code.
                    # Note that a drive specific device scan on a non btrfs
                    # device returns 'Invalid argument'!! and rc=1.
                    return out, err, rc
    return out, err, rc


def btrfs_uuid(disk):
    """return uuid of a btrfs filesystem"""
    o, e, rc = run_command([BTRFS, "filesystem", "show", get_device_path(disk)])
    return o[0].split()[3]


def set_property(mnt_pt, name, val, mount=True):
    if mount is not True or is_mounted(mnt_pt):
        cmd = [BTRFS, "property", "set", mnt_pt, name, val]
        return run_command(cmd)


def get_property(mnt_pt, prop_name=None):
    """
    Convenience wrapper around 'btrfs property get prop_name mnt_pt'.
    :param mnt_pt: Vol(pool)/subvol(share/snap) mount point.
    :return: if called with no prop_name specified then a dict of available
    properties. But if called with a single property then the value and type
    appropriate for that property ie:
    string for label (in presented in properties),
    string for compression ie: zlib (if presented in properties), lzo, zstd,
    and Boolean for prop_name='ro'
    If prop_name specified but not found then None is returned.
    N.B. compression property for subvol only, vol/pool uses mount option.
    """
    KNOWN_PROPERTIES = ["ro", "compression", "label"]
    # TODO: Consider using -t as a form of typesetting on our mnt_pt:
    cmd = [BTRFS, "property", "get", mnt_pt]
    if prop_name is not None:
        cmd.append(prop_name)
    o, e, rc = run_command(cmd)
    properties = {}
    for line in o:
        fields = line.split("=")
        if fields[0] in KNOWN_PROPERTIES:
            properties[fields[0]] = fields[-1]
    # Switch the ro property, if found, from string to Boolean.
    if "ro" in properties:
        if properties["ro"] == "true":
            properties["ro"] = True
        else:
            properties["ro"] = False
    if prop_name is None:
        return properties
    if prop_name in properties:
        return properties[prop_name]
    # We have been asked for a property we haven't found.
    return None


def get_snap(subvol_path, oldest=False, num_retain=None, regex=None, test_mode=False):
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
    share_name = subvol_path.split("/")[-1]
    # Note on future modifications re following command:
    # -o shows only subvolumes below specified path but may be deprecated soon:
    # https://www.mail-archive.com/linux-btrfs@vger.kernel.org/msg75514.html
    cmd = [BTRFS, "subvol", "list", "-o", subvol_path]
    o, e, rc = run_command(cmd)
    snaps = {}
    for l in o:
        fields = l.split()
        if len(fields) > 0:
            snap_fields = fields[-1].split("/")
            if len(snap_fields) != 3 or snap_fields[1] != share_name:
                # not the Share we are interested in.
                continue
            if regex is not None and re.search(regex, snap_fields[2]) is None:
                # regex not in the name
                continue
            snaps[int(fields[1])] = snap_fields[2]
    snap_ids = sorted(snaps.keys())
    if oldest:
        if len(snap_ids) > num_retain:
            return snaps[snap_ids[0]]
    elif len(snap_ids) > 0:
        return snaps[snap_ids[-1]]
    return None


def get_oldest_snap(subvol_path, num_retain, regex=None):
    return get_snap(subvol_path, oldest=True, num_retain=num_retain, regex=regex)


def get_lastest_snap(subvol_path, regex=None):
    return get_snap(subvol_path, regex=regex)
