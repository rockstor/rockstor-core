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

from socket import inet_ntoa
from struct import pack
from tempfile import mkstemp
import collections
import hashlib
import logging
import os
import re
import shutil
import signal
import stat
import subprocess  # TODO: consider drop in replacement of subprocess32 module
import time
import uuid

from django.conf import settings

from exceptions import CommandException, NonBTRFSRootException


logger = logging.getLogger(__name__)


CAT = '/usr/bin/cat'
CHATTR = '/usr/bin/chattr'
DD = '/usr/bin/dd'
DEFAULT_MNT_DIR = '/mnt2/'
EXPORTFS = '/usr/sbin/exportfs'
GRUBBY = '/usr/sbin/grubby'
HDPARM = '/usr/sbin/hdparm'
HOSTID = '/usr/bin/hostid'
HOSTNAMECTL = '/usr/bin/hostnamectl'
LS = '/usr/bin/ls'
LSBLK = '/usr/bin/lsblk'
MKDIR = '/usr/bin/mkdir'
MOUNT = '/usr/bin/mount'
NMCLI = '/usr/bin/nmcli'
RMDIR = '/usr/bin/rmdir'
SHUTDOWN = settings.SHUTDOWN
SYSTEMCTL_BIN = '/usr/bin/systemctl'
SYSTEMD_ESCAPE = '/usr/bin/systemd-escape'
UDEVADM = settings.UDEVADM
UMOUNT = '/usr/bin/umount'
WIPEFS = '/usr/sbin/wipefs'
RTC_WAKE_FILE = '/sys/class/rtc/rtc0/wakealarm'
RETURN_BOOLEAN = True
EXCLUDED_MOUNT_DEVS = ['sysfs', 'proc', 'devtmpfs', 'securityfs', 'tmpfs',
                       'devpts', 'cgroup', 'pstore', 'configfs', 'systemd-1',
                       'mqueue', 'debugfs', 'hugetlbfs', 'nfsd', 'sunrpc']

Disk = collections.namedtuple('Disk',
                              'name model serial size transport vendor '
                              'hctl type fstype label uuid parted root '
                              'partitions')


def inplace_replace(of, nf, regex, nl):
    with open(of) as afo, open(nf, 'w') as tfo:
        replaced = [False, ] * len(regex)
        for l in afo.readlines():
            ireplace = False
            for i in range(0, len(regex)):
                if (re.match(regex[i], l) is not None):
                    tfo.write(nl[i])
                    replaced[i] = True
                    ireplace = True
                    break
            if (not ireplace):
                tfo.write(l)
        for i in range(0, len(replaced)):
            if (not replaced[i]):
                tfo.write(nl[i])


def run_command(cmd, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE, throw=True,
                log=False, input=None):
    try:
        # We force run_command to always use en_US
        # to avoid issues on date and number formats
        # on not Anglo-Saxon systems (ex. it, es, fr, de, etc)
        fake_env = dict(os.environ)
        fake_env['LANG'] = 'en_US.UTF-8'
        cmd = map(str, cmd)
        if log:
            logger.debug('Running command: {}'.format(' '.join(cmd)))
        p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr,
                             stdin=stdin, env=fake_env)
        out, err = p.communicate(input=input)
        out = out.split('\n')
        err = err.split('\n')
        rc = p.returncode
    except Exception as e:
        raise Exception(
            'Exception while running command({}): {}'.format(cmd, e))

    if rc != 0:
        if log:
            e_msg = ('non-zero code({0}) returned by command: {1}. output: '
                     '{2} error: {3}'.format(rc, cmd, out, err))
            logger.error(e_msg)
        if throw:
            raise CommandException(cmd, out, err, rc)
    return (out, err, rc)


def scan_disks(min_size, test_mode=False):
    """
    Using lsblk we scan all attached disks and categorize them according to
    if they are partitioned, their file system, if the drive hosts our / mount
    point etc. The result of this scan is used by:-
    view/disk.py _update_disk_state
    for further analysis / categorization.
    N.B. if a device (partition or whole dev) hosts swap or is of no interest
    then it is ignored.
    :param min_size: Discount all devices below this size in KB
    :param test_mode: Used by unit tests for deterministic 'fake-serial-' mode.
    :return: List containing drives of interest
    """
    base_root_disk = root_disk()  # /dev/sda if /dev/sda3, or md126 if md126p2
    cmd = [LSBLK, '-P', '-p', '-o',
           'NAME,MODEL,SERIAL,SIZE,TRAN,VENDOR,HCTL,TYPE,FSTYPE,LABEL,UUID']
    o, e, rc = run_command(cmd)
    dnames = {}  # Working dictionary of devices.
    disks = []  # List derived from the final working dictionary of devices.
    serials_seen = []  # List tally of serials seen during this scan.
    # Stash variables to pass base info on root_disk to root device proper.
    root_serial = root_model = root_transport = root_vendor = root_hctl = None
    # flag to indicate bcache backing device found.
    bdev_flag = False
    # To use udevadm to retrieve serial number rather than lsblk, make this
    # True N.B. when lsblk returns no serial for a device then udev is used
    # anyway.
    always_use_udev_serial = False
    device_names_seen = []  # List tally of devices seen during this scan
    for line in o:
        # skip processing of all lines that don't begin with "NAME"
        if (re.match('NAME', line) is None):
            continue
        # setup our line / dev name dependant variables
        # easy read categorization flags, all False until found otherwise.
        is_root_disk = False  # base dev that / is mounted on ie system disk
        is_partition = is_btrfs = False
        dmap = {}  # to hold line info from lsblk output eg NAME: sda
        # line parser variables
        cur_name = ''
        cur_val = ''
        name_iter = True
        val_iter = False
        sl = line.strip()
        i = 0
        while i < len(sl):
            # We iterate over the line to parse it's information char by char
            # keeping track of name or value and adding the char accordingly
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
        # md devices, such as mdadmin software raid and some hardware raid
        # block devices show up in lsblk's output multiple times with identical
        # info.  Given we only need one copy of this info we remove duplicate
        # device name entries, also offers more sane output to views/disk.py
        # where name will be used as the index
        if (dmap['NAME'] in device_names_seen):
            continue
        device_names_seen.append(dmap['NAME'])
        # We are not interested in CD / DVD rom devices so skip to next device
        if (dmap['TYPE'] == 'rom'):
            continue
        # We are not interested in swap partitions or devices so skip further
        # processing and move to next device.
        # N.B. this also facilitates a simpler mechanism of classification.
        if (dmap['FSTYPE'] == 'swap'):
            continue
        # convert size into KB
        size_str = dmap['SIZE']
        if (size_str[-1] == 'G'):
            dmap['SIZE'] = int(float(size_str[:-1]) * 1024 * 1024)
        elif (size_str[-1] == 'T'):
            dmap['SIZE'] = int(float(size_str[:-1]) * 1024 * 1024 * 1024)
        else:
            # Move to next line if we don't understand the size as GB or TB
            # Note that this may cause an entry to be ignored if formatting
            # changes.
            # Previous to the explicit ignore swap clause this often caught
            # swap but if swap was in GB and above min_size then it could
            # show up when not in a partition (the previous caveat clause).
            continue
        if (dmap['SIZE'] < min_size):
            continue
        # ----- Now we are done with easy exclusions we begin classification.
        # If md device populate unused MODEL with basic member/raid summary.
        if (re.match('/dev/md', dmap['NAME']) is not None):
            # cheap way to display our member drives
            dmap['MODEL'] = get_md_members(dmap['NAME'])
        # ------------ Start more complex classification -------------
        if (dmap['NAME'] == base_root_disk):  # as returned by root_disk()
            # We are looking at the system drive that hosts, either
            # directly or as a partition, the / mount point.
            # Given lsblk doesn't return serial, model, transport, vendor, hctl
            # when displaying partitions we grab and stash them while we are
            # looking at the root drive directly, rather than the / partition.
            # N.B. assumption is lsblk first displays devices then partitions,
            # this is the observed behaviour so far.
            root_serial = dmap['SERIAL']
            root_model = dmap['MODEL']
            root_transport = dmap['TRAN']
            root_vendor = dmap['VENDOR']
            root_hctl = dmap['HCTL']
            # Set readability flag as base_dev identified.
            is_root_disk = True  # root as returned by root_disk()
            # And until we find a partition on this root disk we will label it
            # as our root, this then allows for non partitioned root devices
            # such as mdraid installs where root is directly on eg /dev/md126.
            # N.B. this assumes base devs are listed before their partitions.
            dmap['root'] = True
        # Normal partitions are of type 'part', md partitions are of type 'md'
        # normal disks are of type 'disk' md devices are of type eg 'raid1'.
        # Disk members of eg intel bios raid md devices
        # fstype='isw_raid_member' Note for future re-write; when using udevadm
        # DEVTYPE, partition and disk works for both raid and non raid
        # partitions and devices.
        # ----- Begin readability variables assignment:
        # - is this a partition, regular or md type.
        if (dmap['TYPE'] == 'part' or dmap['TYPE'] == 'md'):
            is_partition = True
        # - is filesystem of type btrfs
        if (dmap['FSTYPE'] == 'btrfs'):
            is_btrfs = True
        # End readability variables assignment

        if is_partition:
            dmap['parted'] = True
            # We don't account for partitions within partitions, but making
            # an empty dict here simplifies conditionals as always a dict then.
            dmap['partitions'] = {}
            # Search our working dictionary of already scanned devices by name
            # We are assuming base devices are listed first and if of interest
            # we have recorded it and can now back port it's partitioned
            # status.
            for dname in dnames.keys():
                if (re.match(dname, dmap['NAME']) is not None):
                    # Our device name has a base device entry of interest
                    # saved: ie we have scanned and saved sdb but looking at
                    # sdb3 now.  Given we have found a partition on an existing
                    # base dev we should update that base dev's entry in dnames
                    # to parted "True" as when recorded lsblk type on base
                    # device would have been disk or RAID1 or raid1 (for base
                    # md dev).  Change the 12th entry (0 indexed) of this
                    # device to True The 12 entry is the parted flag so we
                    # label our existing base dev entry as parted ie
                    # partitioned.
                    dnames[dname][11] = True
                    # Also take this opportunity to back port software raid
                    # info from partitions to the base device if the base
                    # device doesn't already have an fstype identifying it's
                    # raid member status. For Example:- bios raid base dev
                    # gives lsblk FSTYPE="isw_raid_member"; we already catch
                    # this directly.  Pure software mdraid base dev has lsblk
                    # FSTYPE="" but a partition on this pure software mdraid
                    # that is a member of eg md125 has
                    # FSTYPE="linux_raid_member"
                    # Add the same treatment for partitions hosting LUKS
                    # containers.
                    if dmap['FSTYPE'] == 'linux_raid_member' \
                            and (dnames[dname][8] is None):
                        # N.B. 9th item (index 8) in dname = FSTYPE We are a
                        # partition that is an mdraid raid member so backport
                        # this info to our base device ie sda1 raid member so
                        # label sda's FSTYPE entry the same as it's partition's
                        # entry if the above condition is met, ie only if the
                        # base device doesn't already have an FSTYPE entry ie
                        # None, this way we don't overwrite / loose info and we
                        # only need to have one partition identified as an
                        # mdraid member to classify the entire device (the base
                        # device) as a raid member, at least in part.
                        dnames[dname][8] = dmap['FSTYPE']
                    if dmap['FSTYPE'] == 'crypto_LUKS' \
                            and (dnames[dname][8] is None):
                        # As per mdraid we backport to the base device LUKS
                        # containers that live in partitions as the base device
                        # will have an FSTYPE="" and as per mdraid we classify
                        # the entire device as a LUKS container member even if
                        # it is only in part (ie this partition). But we only
                        # backport this information if there currently exists
                        # no FSTYPE on the base device, there by protecting
                        # against fstype information loss on the base device.
                        # Please see mdraid partition treatment for additional
                        # comments on index number used.
                        dnames[dname][8] = dmap['FSTYPE']
                        # and uuid backport
                        dnames[dname][10] = dmap['UUID']
                    # Akin to back porting a partitions FSTYPE to it's base
                    # device, as with 'linux_raid_member' above, we can do the
                    # same for btrfs if found in a partition.
                    # This is intended to facilitate the user redirection role
                    # so that the base disk can be labeled with it's partitions
                    # fstype, label (for pool updates) uuid, and size.
                    # N.B. The base device info will end up pertaining to the
                    # highest partition numbers details. Design limitation.
                    if is_btrfs and dnames[dname][8] is None:
                        # We are a btrfs partition where the base device has no
                        # fstype entry: backport: fstype, label, uuid & size.
                        # fstype backport
                        dnames[dname][8] = dmap['FSTYPE']
                        # label backport is at index 9
                        dnames[dname][9] = dmap['LABEL']
                        # and uuid backport
                        dnames[dname][10] = dmap['UUID']
                        # and size backport
                        dnames[dname][3] = dmap['SIZE']
                    # Build a dictionary of the partitions we find.
                    # Back port our current name as a partition entry in our
                    # base devices 'partitions' dictionary 14th item (index 13)
                    dnames[dname][13][dmap['NAME']] = dmap['FSTYPE']
                    # This dict is intended for use later in roles such as
                    # import / export devices or external backup drives so
                    # that the role config mechanism can offer up the known
                    # partitions found so that the eventual configured role
                    # will know which partition on the role based device to
                    # work with and it current filesystem type.
                    # Has one role per device limit but helps to keep usability
                    # and underlying disk management simpler.
        else:
            # We are not a partition so record this.
            dmap['parted'] = False
            # As we are not a partition it is assumed that we might hold a
            # partition so start an empty partition dictionary for this.
            # N.B. This assumes base devices are listed before their partitions
            dmap['partitions'] = {}
            # This dict will be populated when we find our partitions and back
            # port their names and fstype (as values).
        if ((not is_root_disk and not is_partition) or
                is_btrfs):
            # We have a non system disk that is not a partition
            # or
            # We have a device that is btrfs formatted
            # Or we may just be a non system disk without partitions.
            dmap['root'] = is_root_disk
            if is_btrfs:
                # a btrfs file system
                # Regex to identify a partition on the base_root_disk.
                # Root on 'sda3' gives base_root_disk 'sda'.
                if re.match('/dev/sd|/dev/vd', dmap['NAME']) is not None:
                    # eg 'sda' or 'vda' with >= one additional digit,
                    part_regex = base_root_disk + '\d+'
                else:
                    # md126 or nvme0n1 with 'p' + >= one additional digit eg:
                    # md126p3 or nvme0n1p4; also mmcblk0p2 for base mmcblk0.
                    part_regex = base_root_disk + 'p\d+'
                if re.match(part_regex, dmap['NAME']) is not None:
                    logger.debug('--- Inheriting base_root_disk info ---')
                    # We are assuming that a partition with a btrfs fs on is
                    # our root if it's name begins with our base system disk
                    # name. Now add the properties we stashed when looking at
                    # the base root disk rather than the root partition we see
                    # here.
                    dmap['SERIAL'] = root_serial
                    dmap['MODEL'] = root_model
                    dmap['TRAN'] = root_transport
                    dmap['VENDOR'] = root_vendor
                    dmap['HCTL'] = root_hctl
                    # As we have found root to be on a partition we can now un
                    # flag the base device as having been root prior to finding
                    # this partition on that base_root_disk N.B. Assumes base
                    # dev is listed before it's partitions The 13th item in
                    # dnames entries is root so index = 12.  Only update our
                    # base_root_disk if it exists in our scanned disks as this
                    # may be the first time we are seeing it. Search to see if
                    # we already have an entry for the the base_root_disk which
                    # may be us or our base dev if we are a partition
                    for dname in dnames.keys():
                        if dname == base_root_disk:
                            dnames[base_root_disk][12] = False
                    # And update this device as real root
                    # Note we may be looking at the base_root_disk or one of
                    # it's partitions there after.
                    dmap['root'] = True
                else:
                    # We have a non system disk btrfs filesystem.
                    # Ie we are a whole disk or a partition with btrfs on but
                    # NOT on the system disk.
                    # Most likely a current btrfs data drive or one we could
                    # import.
                    # Ignore / skip this btrfs device if it's a partition
                    if is_partition:
                        logger.debug('-- Skipping non root btrfs partition -')
                        continue
            # No more continues so the device we have is to be passed to our db
            # entry system views/disk.py ie _update_disk_state()
            # Do final tidy of data in dmap and ready for entry in dnames dict.
            # db needs unique serial so provide one where there is none found.
            # First try harder with udev if lsblk failed on serial retrieval.
            if (dmap['SERIAL'] == '' or always_use_udev_serial):
                # lsblk fails to retrieve SERIAL from VirtIO drives and some
                # sdcard devices and md devices so try specialized function.
                dmap['SERIAL'] = get_disk_serial(dmap['NAME'], dmap['TYPE'])
            # Now try specialized serial propagation methods:
            # Bcache virtual block devices get their backing devices uuid
            # We propagate the uuid for a bcache backing device to it's virtual
            # counterpart device for use as a serial number.
            # Note however that we are only interested in the 'backing device'
            # type of bcache as it has the counterpart virtual block device.
            if (dmap['FSTYPE'] == 'bcache'):
                bcache_dev_type = get_bcache_device_type(dmap['NAME'])
                if bcache_dev_type == 'bdev':
                    bdev_uuid = dmap['UUID']
                    # We set out bdev_flag to inform the next device
                    # interpretation.
                    bdev_flag = True
                elif bcache_dev_type == 'cdev':
                    # We have a bcache caching device, not a backing device.
                    # Change fstype as an indicator to _update_disk_state()
                    # role system. N.B. fstype bcachecdev is fictitious.
                    dmap['FSTYPE'] = 'bcachecdev'
            else:
                # we are a non bcache bdev but we might be the virtual device
                # if we are listed directly after a bcache bdev.
                if bdev_flag:
                    # Assumption is there is only one virtual device for each
                    # bdev and that it is listed directly after it's associated
                    # bdev. We are listed directly after a bcache bdev but
                    # could still be any device. As no cheap distinguishing
                    # properties we for now rely on device name:
                    if re.match('bcache', dmap['NAME']) is not None:
                        # We avoid overwriting any serial just in case, normal
                        # bcache virtual devices have no serial reported by
                        # lsblk but future lsblk versions may change this.
                        if dmap['SERIAL'] == '':
                            # transfer our stashed bdev uuid as a serial.
                            dmap['SERIAL'] = 'bcache-%s' % bdev_uuid
                # reset the bdev_flag as we are only interested in devices
                # listed directly after a bdev anyway.
                bdev_flag = False
            if (dmap['SERIAL'] == '' or (dmap['SERIAL'] in serials_seen)):
                # No serial number still or its a repeat. Overwrite drive
                # serial entry in dmap with fake-serial- + uuid4 See
                # disk/disks_table.jst for a use of this flag mechanism.
                # Previously we did dmap['SERIAL'] = dmap['NAME'] which is less
                # robust as it can itself produce duplicate serial numbers.
                if test_mode:
                    # required for reproducible output for repeatable tests
                    dmap['SERIAL'] = 'fake-serial-'
                else:
                    # 12 chars (fake-serial-) + 36 chars (uuid4) = 48 chars
                    dmap['SERIAL'] = 'fake-serial-' + str(uuid.uuid4())
            serials_seen.append(dmap['SERIAL'])
            # replace all dmap values of '' with None.
            for key in dmap.keys():
                if (dmap[key] == ''):
                    dmap[key] = None
            # transfer our device info as now parsed in dmap to the dnames dict
            dnames[dmap['NAME']] = [dmap['NAME'], dmap['MODEL'],
                                    dmap['SERIAL'], dmap['SIZE'],
                                    dmap['TRAN'], dmap['VENDOR'],
                                    dmap['HCTL'], dmap['TYPE'],
                                    dmap['FSTYPE'], dmap['LABEL'],
                                    dmap['UUID'], dmap['parted'],
                                    dmap['root'], dmap['partitions'], ]
    # Transfer our collected disk / dev entries of interest to the disks list.
    for d in dnames.keys():
        disks.append(Disk(*dnames[d]))
        # logger.debug('disks item = %s ', Disk(*dnames[d]))
    return disks


def uptime():
    with open('/proc/uptime') as ufo:
        # TODO: check on readline here as reads a character at a time
        # TODO: xreadlines() reads one line at a time.
        return int(float(ufo.readline().split()[0]))


def def_kernel():
    kernel = None
    o, e, rc = run_command([GRUBBY, '--default-kernel'], throw=False)
    if (len(o) > 0):
        k_fields = o[0].split('/boot/vmlinuz-')
        if (len(k_fields) == 2):
            kernel = k_fields[1]
    return kernel


def kernel_info(supported_version):
    uname = os.uname()
    if uname[2] != supported_version and os.path.isfile(GRUBBY):
        e_msg = ('You are running an unsupported kernel(%s). Some features '
                 'may not work properly.' % uname[2])
        carg = '--set-default=/boot/vmlinuz-{}'.format(supported_version)
        run_command([GRUBBY, carg])
        e_msg = ('%s Please reboot and the system will '
                 'automatically boot using the supported kernel(%s)' %
                 (e_msg, supported_version))
        raise Exception(e_msg)
    return uname[2]


def create_tmp_dir(dirname):
    # TODO: suggest name change to create_dir
    return run_command([MKDIR, '-p', dirname])


def rm_tmp_dir(dirname):
    # TODO: suggest name change to remove_dir
    return run_command([RMDIR, dirname])


def toggle_path_rw(path, rw=True):
    attr = '-i'
    if not rw:
        attr = '+i'
    return run_command([CHATTR, attr, path])


def nfs4_mount_teardown(export_pt):
    """
    reverse of setup. cleanup when there are no more exports
    """
    if (is_mounted(export_pt)):
        run_command([UMOUNT, '-l', export_pt])
        for i in range(10):
            if (not is_mounted(export_pt)):
                toggle_path_rw(export_pt, rw=True)
                return run_command([RMDIR, export_pt])
            time.sleep(1)
        run_command([UMOUNT, '-f', export_pt])
    if (os.path.exists(export_pt)):
        toggle_path_rw(export_pt, rw=True)
        run_command([RMDIR, export_pt])
    return True


def bind_mount(mnt_pt, export_pt):
    if (not is_mounted(export_pt)):
        run_command([MKDIR, '-p', export_pt])
        toggle_path_rw(export_pt, rw=False)
        return run_command([MOUNT, '--bind', mnt_pt, export_pt])
    return True


def refresh_nfs_exports(exports):
    """
    input format:

    {'export_point': [{'client_str': 'www.example.com',
                       'option_list': 'rw,insecure,'
                       'mnt_pt': mnt_pt,},],
                       ...}

    if 'clients' is an empty list, then unmount and cleanup.
    """
    fo, npath = mkstemp()
    with open(npath, 'w') as efo:
        shares = []
        for e in exports.keys():
            if (len(exports[e]) == 0):
                #  do share tear down at the end, only snaps here
                if (len(e.split('/')) == 4):
                    nfs4_mount_teardown(e)
                else:
                    shares.append(e)
                continue

            if (not is_mounted(e)):
                bind_mount(exports[e][0]['mnt_pt'], e)
            client_str = ''
            admin_host = None
            for c in exports[e]:
                run_command([EXPORTFS, '-i', '-o', c['option_list'],
                             '%s:%s' % (c['client_str'], e)])
                client_str = ('%s%s(%s) ' % (client_str, c['client_str'],
                                             c['option_list']))
                if ('admin_host' in c):
                    admin_host = c['admin_host']
            if (admin_host is not None):
                run_command([EXPORTFS, '-i', '-o', 'rw,no_root_squash',
                             '%s:%s' % (admin_host, e)])
                client_str = ('%s %s(rw,no_root_squash)' % (client_str,
                                                            admin_host))
            export_str = ('%s %s\n' % (e, client_str))
            efo.write(export_str)
        for s in shares:
            nfs4_mount_teardown(s)
    shutil.move(npath, '/etc/exports')
    return run_command([EXPORTFS, '-ra'])


def config_network_device(name, dtype='ethernet', method='auto', ipaddr=None,
                          netmask=None, autoconnect='yes', gateway=None,
                          dns_servers=None):
    # 1. delete any existing connections that are using the given device.
    show_cmd = [NMCLI, 'c', 'show']
    o, e, rc = run_command(show_cmd)
    for l in o:
        fields = l.strip().split()
        if (len(fields) > 3 and fields[-1] == name):
            # fields[-3] is the uuid of the connection
            run_command([NMCLI, 'c', 'delete', fields[-3]])
    # 2. Add a new connection
    add_cmd = [NMCLI, 'c', 'add', 'type', dtype, 'con-name', name, 'ifname',
               name]
    if (method == 'manual'):
        add_cmd.extend(['ip4', '%s/%s' % (ipaddr, netmask)])
    if (gateway is not None and len(gateway.strip()) > 0):
        add_cmd.extend(['gw4', gateway])
    run_command(add_cmd)
    # 3. modify with extra options like dns servers
    if (method == 'manual'):
        mod_cmd = [NMCLI, 'c', 'mod', name, ]
        if (dns_servers is not None and len(dns_servers.strip()) > 0):
            mod_cmd.extend(['ipv4.dns', dns_servers])
        if (autoconnect == 'no'):
            mod_cmd.extend(['connection.autoconnect', 'no'])
        if (len(mod_cmd) > 4):
            run_command(mod_cmd)
    run_command([NMCLI, 'c', 'up', name])
    # wait for the interface to be activated
    num_attempts = 0
    while True:
        state = get_net_config(name)[name].get('state', None)
        if (state != 'activated'):
            time.sleep(1)
            num_attempts += 1
        else:
            break
        if (num_attempts > 30):
            msg = ('Waited %s seconds for connection(%s) state to '
                   'be activated but it has not. Giving up. current state: %s'
                   % (num_attempts, name, state))
            raise Exception(msg)


def convert_netmask(bits):
    # convert netmask bits into ip representation
    bits = int(bits)
    mask = 0
    for i in range(32-bits, 32):
        mask |= (1 << i)
    return inet_ntoa(pack('>I', mask))


def net_config_helper(name):
    config = {}
    o, e, rc = run_command([NMCLI, '-t', 'c', 'show', name], throw=False)
    if (rc == 10):
        return config
    for l in o:
        l = l.strip()
        if ('method' in config):
            if (config['method'] == 'auto'):
                # dhcp
                if (re.match('DHCP4.OPTION.*ip_address = .+', l) is not None):
                    config['ipaddr'] = l.split('= ')[1]
                elif (re.match('DHCP4.OPTION.*:domain_name_servers = .+', l) is
                      not None):
                    config['dns_servers'] = l.split('= ')[1]
                elif (re.match('DHCP4.OPTION.*:subnet_mask = .+', l) is
                      not None):
                    config['netmask'] = l.split('= ')[1]
                elif (re.match('IP4.GATEWAY:.+', l) is not None):
                    config['gateway'] = l.split(':')[1]

            elif (config['method'] == 'manual'):
                # manual
                if (re.match('IP4.ADDRESS', l) is not None):
                    kv_split = l.split(':')
                    if (len(kv_split) > 1):
                        vsplit = kv_split[1].split('/')
                    if (len(vsplit) > 0):
                        config['ipaddr'] = vsplit[0]
                    if (len(vsplit) > 1):
                        config['netmask'] = convert_netmask(vsplit[1])
                elif (re.match('ipv4.dns:.+', l) is not None):
                    config['dns_servers'] = l.split(':')[1]
                elif (re.match('ipv4.gateway:.+', l) is not None):
                    config['gateway'] = l.split(':')[1]

            else:
                raise Exception('Unknown ipv4.method(%s). ' % config['method'])

        if (re.match('connection.interface-name:', l) is not None):
            config['name'] = l.split(':')[1]
        elif (re.match('connection.autoconnect:', l) is not None):
            config['autoconnect'] = l.split(':')[1]
        elif (re.match('ipv4.method:.+', l) is not None):
            config['method'] = l.split(':')[1]

        if (re.match('GENERAL.DEVICES:.+', l) is not None):
            config['dname'] = l.split(':')[1]
        elif (re.match('connection.type:.+', l) is not None):
            config['ctype'] = l.split(':')[1]
        elif (re.match('GENERAL.STATE:.+', l) is not None):
            config['state'] = l.split(':')[1]

    if ('dname' in config):
        o, e, rc = run_command([NMCLI, '-t', '-f', 'all', 'd', 'show',
                                config['dname'], ])
        for l in o:
            l = l.strip()
            if (re.match('GENERAL.TYPE:.+', l) is not None):
                config['dtype'] = l.split(':')[1]
            elif (re.match('GENERAL.HWADDR:.+', l) is not None):
                config['mac'] = l.split('GENERAL.HWADDR:')[1]
            elif (re.match('CAPABILITIES.SPEED:.+', l) is not None):
                config['dspeed'] = l.split(':')[1]

    return config


def get_net_config(all=False, name=None):
    if (all):
        o, e, rc = run_command([NMCLI, '-t', 'd', 'show'])
        config = {}
        for i in range(len(o)):
            if (re.match('GENERAL.DEVICE:', o[i]) is not None and
                re.match('GENERAL.TYPE:', o[i + 1]) is not None and
                    o[i + 1].strip().split(':')[1] == 'ethernet'):
                dname = o[i].strip().split(':')[1]
                mac = o[i+2].strip().split('GENERAL.HWADDR:')[1]
                name = o[i+5].strip().split('GENERAL.CONNECTION:')[1]
                config[dname] = {'dname': dname,
                                 'mac': mac,
                                 'name': name,
                                 'dtype': 'ethernet', }
        for device in config:
            config[device].update(net_config_helper(config[device]['name']))
            if (config[device]['name'] == '--'):
                config[device]['name'] = device
        return config
    return {name: net_config_helper(name), }


def update_issue(ipaddr):
    msg = ("\n\nYou can go to RockStor's webui by pointing your web browser"
           " to https://%s\n\n" % ipaddr)
    with open('/etc/issue', 'w') as ifo:
        ifo.write(msg)


def sethostname(hostname):
    return run_command([HOSTNAMECTL, 'set-hostname', hostname])


def gethostname():
    o, e, rc = run_command([HOSTNAMECTL, '--static'])
    return o[0]


def is_share_mounted(sname, mnt_prefix=DEFAULT_MNT_DIR):
    mnt_pt = mnt_prefix + sname
    return mount_status(mnt_pt, RETURN_BOOLEAN)


def is_mounted(mnt_pt):
    return mount_status(mnt_pt, RETURN_BOOLEAN)


def mount_status(mnt_pt, return_boolean=False):
    """
    Parses /proc/mounts to extract the status of a given mount point.
    Line fields are as follows:
    dev_name mount_point fstype mount_options dummy_value dummy_value
    In either mode this function typically takes around 0.05ms without GC.
    It should be kept light as it is called frequently by Pool and Share
    models via their mount_status and is_mounted properties.
    :param mnt_pt: pool (volume) or subvolume mount point (with full path).
    :param return_boolean: If set to 'True' only a boolean is returned,
    otherwise a string of current mount options, or 'unmounted', is returned.
    :return: if return_boolean then True or False depending on mount state.
    If return_boolean=False (default) then a string is returned of the current
    mount options, or 'unmounted' if no relevant /proc/mounts entry was found.
    """
    with open('/proc/mounts') as pfo:
        for each_line in pfo.readlines():
            line_fields = each_line.split()
            if len(line_fields) < 4:
                # Avoid index issues as we expect >= 4 columns.
                continue
            if line_fields[0] in EXCLUDED_MOUNT_DEVS:
                # Skip excluded/special mount devices ie sysfs, proc, etc.
                continue
            if line_fields[1] == mnt_pt:
                # We have an active mount, return according to personality.
                if return_boolean:
                    return True
                return line_fields[3]
    if return_boolean:
        return False
    return 'unmounted'


def dev_mount_point(dev_temp_name):
    """
    Parses /proc/mounts to return the first associated mount point for a given
    device temp name (ie /dev/sda).
    Note this is trivially different from mount_status() but intended initially
    for use by set_pool_label.
    :param dev_temp_name: /dev/sda3 or /dev/bcache0, or /dev/mapper/luks-...
    :return: None if note device match found or first associated mount point.
    """
    with open('/proc/mounts') as pfo:
        for each_line in pfo.readlines():
            line_fields = each_line.split()
            if len(line_fields) < 4:
                # Avoid index issues as we expect >= 4 columns.
                continue
            if line_fields[0] in EXCLUDED_MOUNT_DEVS:
                # Skip excluded/special mount devices ie sysfs, proc, etc.
                continue
            if line_fields[0] == dev_temp_name:
                logger.debug('dev_mount_point returning {}'.format(line_fields[1]))
                return line_fields[1]
    logger.debug('dev_mount_point() returning None')
    return None


def remount(mnt_pt, mnt_options):
    if (is_mounted(mnt_pt)):
        run_command([MOUNT, '-o', 'remount,%s' % mnt_options, mnt_pt])
    return True


def wipe_disk(disk_byid):
    """
    Simple run_command wrapper to execute "wipefs -a disk_byid"
    :param disk_byid: by-id type name without path as found in db Disks.name.
    :return: o, e, rc tuple returned by the run_command wrapper running the
    locally generated wipefs command.
    """
    disk_byid_withpath = get_device_path(disk_byid)
    return run_command([WIPEFS, '-a', disk_byid_withpath])


def blink_disk(disk_byid, total_exec, read, sleep):
    """
    Method to cause a drives activity light to blink by parameter defined
    timings to aid in physically locating an attached disk.
    Works by causing drive activity via a dd read to null from the disk_byid.
    N.B. Utilises subprocess and signal to run on dd on an independent thread.
    :param disk_byid: by-id type disk name without path
    :param total_exec: Total time to blink the drive light.
    :param read: Read (light on) time.
    :param sleep: light off time.
    :return: None.
    """
    dd_cmd = [DD, 'if=%s' % get_device_path(disk_byid), 'of=/dev/null',
              'bs=512', 'conv=noerror']
    p = subprocess.Popen(dd_cmd, shell=False, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    total_elapsed_time = 0
    while (total_elapsed_time < total_exec):
        if (p.poll() is not None):
            return None
        time.sleep(read)
        p.send_signal(signal.SIGSTOP)
        time.sleep(sleep)
        total_elapsed_time += read + sleep
        p.send_signal(signal.SIGCONT)
    p.terminate()


def convert_to_kib(size):
    """Attempts to convert a size string that is initially expected to have 3
    letters indicating it's units, into the equivalent KiB units.
    If no known 3 letter Unit string is identified and 'B' is found then 0 is
    returned.
    Upon no string match is found in the above process for 'size' unit then an
    exception is raised to this effect.
    :param size: String parameter to process
    :return: post processed size parameter expressed in equivalent integer
    KiB's or zero if units in size are found to 'B'
    """
    suffix_map = {
        'KiB': 1,
        'MiB': 1024,
        'GiB': 1024 * 1024,
        'TiB': 1024 * 1024 * 1024,
        'PiB': 1024 * 1024 * 1024 * 1024, }
    suffix = size[-3:]
    num = size[:-3]
    if (suffix not in suffix_map):
        if (size[-1] == 'B'):
            return 0
        raise Exception('Unknown suffix(%s) while converting to KiB' % suffix)
    return int(float(num) * suffix_map[suffix])


def root_disk():
    """
    Returns the base drive device name where / mount point is found.
    Works by parsing /proc/mounts. Eg if the root entry was as follows:
    /dev/sdc3 / btrfs rw,noatime,ssd,space_cache,subvolid=258,subvol=/root 0 0
    the returned value is sdc
    The assumption with non md devices is that the partition number will be a
    single character.
    :return: /dev/sdX type device name (with path) where root is mounted.
    """
    # TODO: Consider 'lsblk -no pkname devname' rather than parse and strip.
    # -no pkname returns blank line with /dev/mapper/luks but no partitions.
    # -n = no headings, -o specify output (pkname = Parent Kernel Name)
    with open('/proc/mounts') as fo:
        for line in fo.readlines():
            fields = line.split()
            if (fields[1] == '/' and fields[2] == 'btrfs'):
                # We have found our '/' and it's of fs type btrfs
                if (re.match('/dev/mapper/luks-', fields[0]) is not None):
                    # Our root is on a mapped open LUKS container so we need
                    # not resolve the symlink, ie /dev/dm-0, as we loose info
                    # and lsblk's name output also uses the luks-<uuid> name.
                    # So we return the name component
                    # as there are no partitions within these devices so it is
                    # it's own base device. N.B. we do not resolve to the
                    # parent device hosting the LUKS container itself.
                    return fields[0]
                # resolve symbolic links to their targets.
                disk = os.path.realpath(fields[0])
                if (re.match('/dev/md', disk) is not None):
                    # We have an Multi Device naming scheme which is a little
                    # different ie 3rd partition = md126p3 on the md126 device,
                    # or md0p3 as third partition on md0 device.  As md devs
                    # often have 1 to 3 numerical chars we search for one or
                    # more numeric characters, this assumes our dev name has no
                    # prior numerical components ie starts /dev/md but then we
                    # are here due to that match.  Find the indexes of the
                    # device name without the partition.  Search for where the
                    # numbers after "md" end.  N.B. the following will also
                    # work if root is not in a partition ie on md126 directly.
                    end = re.search('\d+', disk).end()
                    return disk[:end]
                if (re.match('/dev/nvme', disk) is not None):
                    # We have an nvme device. These have the following naming
                    # conventions.
                    # Base device examples: nvme0n1 or nvme1n1
                    # First partition on the first device would be nvme0n1p1
                    # The first number after 'nvme' is the device number.
                    # Partitions are indicated by the p# combination ie 'p1'.
                    # We need to also account for a root install on the base
                    # device itself as with the /dev/md parsing just in case,
                    # so look for the end of the base device name via 'n1'.
                    end = re.search('n1', disk).end()
                    return disk[:end]
                # catch all that assumes we have eg /dev/sda3 and want /dev/sda
                # remove the last char
                # /dev/sda3 = /dev/sda
                # TODO: consider changing to same method as in md devs above
                # TODO: to cope with more than one numeric in name.
                return disk[:-1]
    msg = ('root filesystem is not BTRFS. During Rockstor installation, '
           'you must select BTRFS instead of LVM and other options for '
           'root filesystem. Please re-install Rockstor properly.')
    raise NonBTRFSRootException(msg)


def get_md_members(device_name, test=None):
    """
    Returns the md members from a given device, if the given device is not an
    md device or the udevadm info command returns a non 0 (error) then an
    empty string is returned.
    Example lines to parse from udevadmin:-
    E: MD_DEVICE_sda_DEV=/dev/sda
    E: MD_DEVICE_sda_ROLE=0
    E: MD_DEVICE_sdb_DEV=/dev/sdb
    E: MD_DEVICE_sdb_ROLE=1
    Based on the get_disk_serial function.
    N.B. may be deprecated on scan_disks move to udevadmin, or integrated.
    Could consider parsing "mdadm --detail /dev/md1" instead
    :param device_name: eg /dev/md126 or /dev/md0p2
    :param test: if test is not None then it's contents is used in lieu of
    udevadm output.
    :return: String of all members listed in udevadm info --name=device_name
    example: "[2]-/dev/sda[0]-/dev/sdb[1]-raid1" = 2 devices with level info
    """
    line_fields = []
    # if non md device then return empty string
    if re.match('/dev/md', device_name) is None:
        return ''
    members_string = ''
    if test is None:
        out, err, rc = run_command([UDEVADM, 'info', '--name=' + device_name],
                                   throw=False)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return empty string
        return ''
    # search output of udevadmin to find all current md members.
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().replace('=', ' ').split()
        # fast replace of '=' with space so split() can divide all fields
        # example original line "E: ID_SERIAL_SHORT=S1D5NSAF111111K"
        # less than 3 fields are of no use so just in case:-
        if len(line_fields) < 3:
            continue
        # catch the lines that begin with MD_DEVICE or MD_LEVEL
        if (re.match('MD_DEVICE|MD_LEVEL', line_fields[1]) is not None):
            # add this entries value (3rd column) to our string
            if len(line_fields[2]) == 1:
                # Surround single digits with square brackets ie the number of
                # members and the member index (assumes max 9 md members)
                members_string += '[' + line_fields[2] + '] '
            else:
                if re.match('/dev', line_fields[2]) is not None:
                    # TODO: get_disk_serial can benefit from a device type
                    # TODO: consider calling lsblk -n -o 'TYPE' device_name
                    # TODO: may then allow for /dev/mapper raid members.
                    # We have a dev name so put it's serial in our string.
                    members_string += get_disk_serial(line_fields[2])
                else:
                    # > 1 char value that doesn't start with /dev, so raid
                    # level
                    members_string += line_fields[2]
    return members_string


def get_disk_serial(device_name, device_type=None, test=None):
    """Returns the serial number of device_name using udevadm to match that
    returned by lsblk. N.B. udevadm has been observed to return the following:-
    ID_SCSI_SERIAL  rarely seen
    ID_SERIAL_SHORT  often seen
    ID_SERIAL        thought to always be seen (see note below)
    N.B. if used in this order the serial is most likely to resemble that shown
    on the device label as well as that returned by the lsblk. ID_SERIAL seems
    always to appear but is sometimes accompanied by one or both of the others.
    When ID_SERIAL is accompanied by ID_SERIAL_SHORT the short variant is
    closer to lsblk and physical label. When they are both present the
    ID_SERIAL appears to be a combination of the model and the ID_SERIAL_SHORT
    --------- Additional personality added for md devices ie md0p1 or md126,
    these devices have no serial so we search for their MD_UUID and use that
    instead.
    :param device_name: eg /dev/sda as per lsblk output used in scan_disks()
    :param device_type: the lsblk TYPE for the given device eg: disk, crypt.
    The equivalent to the output of lsblk -n -o TYPE device_name. Defaults to
    None as an indication that the caller cannot provide this info.
    :param test: When not None this parameter's contents is substituted for the
    return of the udevadm info --name=device_name command output
    :return: 12345678901234567890 or empty string if no serial was retrieved.
    """
    serial_num = ''
    uuid_search_string = ''
    line_fields = []
    # udevadm requires the full path for Device Mapped (DM) disks so if our
    # type indicates this then add the '/dev/mapper' path to device_name
    # Set search string / flag for dm personality if need be.
    if device_type == 'crypt':
        # Assuming device mapped (DM) so without it's own serial.
        uuid_search_string = 'DM_UUID'
        # Note that we can't use "cryptsetup luksUUID <device>" as this is for
        # use with the container, not the consequent mapped virtual device of
        # the open container. Default udev rules include the virtual device
        # name so this precludes name changes of the vdev as it would also
        # change that devices serial which in turn makes it appear as a
        # different device to Rockstor.
    # Set search string / flag for md personality if need be.
    if re.match('/dev/md', device_name) is not None:
        uuid_search_string = 'MD_UUID'
    if test is None:
        out, err, rc = run_command([UDEVADM, 'info', '--name=' + device_name],
                                   throw=False)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return empty string
        return ''
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().replace('=', ' ').split()
        # fast replace of '=' with space so split() can divide all fields
        # example original line "E: ID_SERIAL_SHORT=S1D5NSAF111111K"
        # less than 3 fields are of no use so just in case:-
        if len(line_fields) < 3:
            continue
        # For md & dm devices, look for MD_UUID or DM_UUID respectively and use
        # as substitute for no hw serial.
        if uuid_search_string != '':
            # md or dm device so search for the appropriate uuid string
            if line_fields[1] == uuid_search_string:
                # TODO: in the case of DM_UUID consider extracting only the
                # TODO: UUID to cope with open container name changes
                serial_num = line_fields[2]
                # we have found our hw serial equivalent so break to return
                break
            else:  # we are md / dm device but haven't found our UUID line
                # move to next line of output and skip serial cascade search
                continue
        if line_fields[1] == 'ID_SCSI_SERIAL':
            # we have an instance of SCSI_SERIAL being more reliably unique
            # when present than SERIAL_SHORT or SERIAL so overwrite whatever
            # we have and look no further by breaking out of the search loop
            serial_num = line_fields[2]
            break
        elif line_fields[1] == 'ID_SERIAL_SHORT':
            # SERIAL_SHORT is better than SERIAL so just overwrite whatever we
            # have so far with SERIAL_SHORT
            serial_num = line_fields[2]
        else:
            if line_fields[1] == 'ID_SERIAL':
                # SERIAL is sometimes our only option but only use it if we
                # have found nothing else.
                if serial_num == '':
                    serial_num = line_fields[2]
    # should return one of the following in order of priority
    # SCSI_SERIAL, SERIAL_SHORT, SERIAL
    return serial_num


def get_virtio_disk_serial(device_name):
    """
    N.B. this function is deprecated by get_disk_serial
    Returns the serial number of device_name virtio disk eg /dev/vda
    Returns empty string if cat /sys/block/vda/serial command fails
    Note no serial entry in /sys/block/sda/ for real or KVM sata drives
    :param device_name: eg vda
    :return: 12345678901234567890

    Note maximum length of serial number reported = 20 chars
    But longer serial numbers can be specified in the VM XML spec file.
    The virtio block device is itself limited to 20 chars ie:-
    https://github.com/qemu/qemu/blob/
    a9392bc93c8615ad1983047e9f91ee3fa8aae75f/include/standard-headers/
    linux/virtio_blk.h
    #define VIRTIO_BLK_ID_BYTES 20  /* ID string length */

    This process may not deal well with spaces in the serial number
    but VMM does not allow this.
    """
    dev_path = ('/sys/block/%s/serial' % device_name)
    out, err, rc = run_command([CAT, dev_path], throw=False)
    if (rc != 0):
        return ''
    # our out list has one element that is the serial number, like
    # ['11111111111111111111']
    return out[0]


def system_shutdown(delta='now'):
    # New delta param default to now used to pass a 2 min delay
    # for scheduled tasks reboot/shutdown
    try:
        cmd = [SHUTDOWN, '-h', delta]
        o, e, rc = run_command(cmd)
    except CommandException as e:
        # Catch / log harmless -15 return code - command executes as expected.
        if e.rc == -15:
            logger.info('Ignoring rc=-15 from command ({}).'.format(cmd))
            return e.out, e.err, e.rc
        # otherwise we raise an exception as normal.
        raise e
    return o, e, rc

def system_reboot(delta='now'):
    # New delta param default to now used to pass a 2 min delay
    # for scheduled tasks reboot/shutdown
    try:
        cmd = [SHUTDOWN, '-r', delta]
        o, e, rc = run_command(cmd)
    except CommandException as e:
        # Catch / log harmless -15 return code - command executes as expected.
        if e.rc == -15:
            logger.info('Ignoring rc=-15 from command ({}).'.format(cmd))
            return e.out, e.err, e.rc
        # otherwise we raise an exception as normal.
        raise e
    return o, e, rc


def system_suspend():
    # This function perform system suspend to RAM via systemctl
    # while reboot and shutdown, both via shutdown command, can be delayed
    # systemctl suspend miss this option
    return run_command([SYSTEMCTL_BIN, 'suspend'])


def clean_system_rtc_wake():
    # Every time we write to rtc alarm file this get locked and
    # we have to clean it with a 0 before writing another epoch
    with open(RTC_WAKE_FILE, 'w') as rtc:
        rtc.write('%d' % 0)


def set_system_rtc_wake(wakeup_epoch):
    # This new function receive desired current and wake up time
    # and set right epoch time to rtc alarm file.
    # Epoch wake up time evaluated on every shutdown scheduled task
    clean_system_rtc_wake()
    with open(RTC_WAKE_FILE, 'w') as rtc:
        rtc.write('%d' % int(wakeup_epoch))
    return None


def md5sum(fpath):
    # return the md5sum of the given file
    if (not os.path.isfile(fpath)):
        return None
    md5 = hashlib.md5()
    with open(fpath) as tfo:
        for l in tfo.readlines():
            md5.update(l)
    return md5.hexdigest()


def get_base_device_byid(dev_byid, test_mode=False):
    """A by-id type name parser which simply removes any trailing partition
    indicators in a given dev_byid name. The remaining name will represent the
    base device ie:-
    dev_byid = ata-QEMU_HARDDISK_QM00005-part3
    base_dev_byid = ata-QEMU_HARDDISK_QM00005
    Given the structure of by-id type names this should always follow.
    At time of last update this function is used exclusively to derive the base
    name of a device for SMART interrogation purposes, ie currently called only
    by smart.py/dev_options which is a portal for pre-processing smart commands
    which have been found to be more reliable when acting on the base device ie
    not called on a partition but on the base device. Hence this functions part
    in dev_options pre-processing.
    Previously this was a by-id type compatibility wrapper for get_base_device
    which worked with sda type names.
    Since the move to by-id format Disk.name db entries the above simpler
    surface syntax method can be used to derive the base device. Previously a
    list order artifact in lsblk's output was relied upon to establish the base
    device.
    N.B. a caveat of this method is that it only works for by-id type names
    however given the fact that it's return is simply the passed dev_byid
    contents then if given any string with no '-part3' type ending then that
    same device name will be returned unaltered, only in the format expected by
    smart.py/dev_options.
    Also given we disable smart functions for all devices attributed with a
    fake-serial number by scan_disks which are also the only encountered
    devices which fail to get a by-id type name we should never actually be
    called using a non by-id type name anyway.
    :param dev_byid: device name as per db entry, ie by-id type without path
    although all path elements should be ignored anyway.
    :param test_mode: currently unused internal self test flag defined in
    system/smart.py
    :return: the original dev_byid string with any '-part#' type ending removed
    if found.
    N.B. No path is added to the device in either return case and irrespective
    of path status of passed dev_byid.
    """
    # split by by-id section delimiter '-'
    name_fields = dev_byid.split('-')
    if len(name_fields) > 2 and re.match('part', name_fields[-1]):
        # The passed device has at least 3 fields ie bus, uniqueid, partname
        # eg: busname-model_serial_or_uniqueid-part3 The passed device name has
        # a -part* ending so process it away by re-joining all elements except
        # the last from our previous split('-').
        base_dev_byid = '-'.join(name_fields[:-1])
    else:
        # our passed device name had no -part* ending so return unaltered.
        base_dev_byid = dev_byid
    # return the consequent result
    return base_dev_byid


def get_bcache_device_type(device):
    """
    Helper function for scan_disks() to identify specific bcache device types:
    We can either parse output of bcache-super-show for the following lines:
    sb.version....1 [backing device]
    sb.version....3 [cache device]
    or we can look for signature file entries within /sys/block/sdX/bcache :
    Backing devices have an "label" entry
    Cache devices have a "cache_replacement_policy"
    The passed device will have already been identified as having:
    lsblk FSTYPE=bcache
    :param device: as presented by lsblk output ie /dev/sdX type with path
    :return: "bdev" for "backing device" or "cdev" for "cache device" or
    None ie neither indicator is found.
    """
    device = device.split('/')[-1]  # strip off the path
    sys_path = ('/sys/block/%s/bcache/' % device)
    if os.path.isfile(sys_path + 'label'):
        return "bdev"
    if os.path.isfile(sys_path + 'cache_replacement_policy'):
        return "cdev"
    return None


def get_base_device(device, test_mode=False):
    """
    Redundant as of move to by-id type names in db Disk.name field, keeping for
    time being in case of oversight re redundancy.
    Replaced by get_base_device_byid()
    Helper function that returns the full path of the base device of a
    partition or if given a base device it will return it's full path,
    ie
    input sda3 output /dev/sda
    input sda output /dev/sda
    Works as a function of lsblk list order ie base devices first. So we return
    the first start of line match to our supplied device name with the pattern
    as the first element in lsblk's output and the match target as our device.
    :param device: device name as per db entry, ie as returned from scan_disks
    :param test_mode: True causes cat from file rather than smartctl command
    :return: base_dev: single item list containing the root device's full path
    ie device = sda3 the base_dev = /dev/sda or [''] if no lsblk entry was
    found to match.
    """
    base_dev = ['', ]
    if not test_mode:
        out, e, rc = run_command([LSBLK])
    else:
        out, e, rc = run_command([CAT, '/root/smartdumps/lsblk.out'])
    # now examine the output from lsblk line by line
    for line in out:
        line_fields = line.split()
        if len(line_fields) < 1:
            # skip empty lines
            continue
        if re.match(line_fields[0], device):
            # We have found a device string match to our device so record it.
            base_dev[0] = '/dev/' + line_fields[0]
            break
    # Return base_dev ie [''] or first character matches to line start in
    # lsblk.
    return base_dev


def is_rotational(device_name, test=None):
    """
    When given a device_name a udevadmin lookup takes place to look for either:
    E: ID_ATA_ROTATION_RATE_RPM non zero or
    ID_ATA_FEATURE_SET_AAM_CURRENT_VALUE AAM = Automatic Acoustic Mamanement -
    ie head speed / noise trade off. If neither is found then the device is
    assumed to be non rotational. This method appears more reliable than "cat
    /sys/block/sda/queue/rotational" and "lsblk -d -o name,rota" which will
    both often report usb sticks as 1 = rotational.  N.B. we use
    --query=property and so have only 2 fields rather than 3 and no spaces,
    only '=' this simplifies the parsing required.
    :param device: string containing device name eg sda or /dev/sda, ie any
    legal udevadm --name parameter. N.B. in the case of by-id type names they
    must contain a full path, by-id alone does not work.
    :return: True if rotational, false if error or unknown.
    """
    # Possible improvement: We could change
    # ID_ATA_FEATURE_SET_AAM_CURRENT_VALUE non zero value check to
    # ID_ATA_FEATURE_SET_AAM_VENDOR_RECOMMENDED_VALUE ie to account of a
    # current setting of zero on a rotational drive and assuming the
    # RECOMMENDED value for all rotational devices with this feature = non
    # zero. Needs more research on actual drive readings for these 2 values.
    rotational = False  # until we find otherwise
    if test is None:
        out, err, rc = run_command([UDEVADM, 'info', '--query=property',
                                    '--name=' + '%s' % device_name],
                                   throw=False)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return False
        return False
    # search output of udevadm to find signs of rotational media
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().split('=')
        # example original line "ID_ATA_FEATURE_SET_AAM=1"
        # less than 2 fields are of no use so just in case:-
        if len(line_fields) < 2:
            continue
        if line_fields[0] == 'ID_ATA_ROTATION_RATE_RPM':
            # we have a rotation rate entry
            if line_fields[1] != '0':
                # non zero rotation so flag and look no further
                rotational = True
                break
        if line_fields[0] == 'ID_ATA_FEATURE_SET_AAM_CURRENT_VALUE':
            # we have an Automatic Acoustic Managment entry
            if line_fields[1] != '0':
                # a non zero AAM entry so flag and look no further
                rotational = True
                break
    return rotational


def get_disk_power_status(dev_byid):
    """
    When given a disk name such as that stored in the db ie /dev/disk/by-id
    type we return it's current power state via hdparm -C
    /dev/disk/by-id/<dev_byid> Possible states are:
    unknown - command not supported by disk
    active/idle - normal operation
    standby - low power mode, ie drive motor not active ie -y will do this
    sleeping - lowest power mode, completely shut down ie -Y will do this
    N.B. -C shouldn't spin up a drive in standby but has been reported to wake
    a drive from sleeping but we aren't going to invoke sleeping as pretty much
    any request will wake a fully sleeping drive.
    Drives in 'sleeping' mode typically require a hard or soft reset before
    becoming available for use, the kernel does this automatically however.
    :param dev_byid: disk name as stored in db / Disk model ie without path
    :return: single word sting of state as indicated by hdparm -C /dev/<disk>
    and if we encounter an error line in the output we return unknown.
    """
    # TODO: candidate for move to system/hdparm
    # if we use the -C -q switches then we have only one line of output:
    # hdparm -C -q /dev/sda
    # drive state is:  active/idle
    out, err, rc = run_command(
        [HDPARM, '-C', '-q', get_device_path(dev_byid)], throw=False)
    if len(err) != 1:
        # In some instances an error can be returned even with rc=0.
        # ie SG_IO: bad/missing sense data, sb[]:  70 00 05 00 00 00 00 0a ...
        return 'unknown'  # don't trust any results in this instance
    if len(out) > 0:
        fields = out[0].split()
        # our line of interest has 4 fields when split by spaces, see above.
        if (len(fields) == 4):
            return fields[3]
    return 'unknown'


def get_disk_APM_level(dev_byid):
    """
    When given a disk name such as that stored in the db ie by-id type
    we return it's current APM level via hdparm -B /dev/disk/by-id/<dev_byid>
    Possible return values from the command are:
    1 to 254 ie min to max power use
    'off' = equivalent to 255 setting
    If we receive an error message, can happen even with rc=0, we ignore any
    reading and return 0. We also translate the 'off' setting back to it's
    number equivalent
    :param dev_byid: disk name as stored in db / Disk model ie by-id type
    :return: APM setting read from the drive ie 1 - 255 (off is translated to
    it's setting equivalent of 255. If there is an error, such as can happen
    when APM is not supported, then we return 0.
    """
    # TODO: candidate for move to system/hdparm
    # if we use the -B -q switches then we have only one line of output:
    # hdparm -B -q /dev/disk/by-id/dev_byid
    #  APM_level<tab>= 192
    #  APM_level<tab>= off
    #  APM_level<tab>= not supported
    out, err, rc = run_command(
        [HDPARM, '-B', '-q', get_device_path(dev_byid)], throw=False)
    if len(err) != 1:
        # In some instances an error can be returned even with rc=0.
        # ie SG_IO: bad/missing sense data, sb[]:  70 00 05 00 00 00 00 0a ...
        return 0  # don't trust any results in this instance
    if len(out) > 0:
        fields = out[0].split()
        # our line of interest has 3 fields when split by spaces, see above.
        if (len(fields) == 3):
            level = fields[2]
            if level == 'off':
                return 255
            return level
    return 0


def set_disk_spindown(dev_byid, spindown_time, apm_value,
                      spindown_message='no comment'):
    """
    Takes a value to be used with hdparm -S to set disk spindown time for the
    device specified.
    Executes hdparm -S spindown_time and ensures the systemd script to do the
    same on boot is also updated. Note we do not restart the systemd service
    to enact these changes in order to keep drive intervention to a minimum.
    :param dev_byid: The name of a disk device as used in the db ie by-id type
    without a path.
    :param spindown_time: Integer received from settings form ie 240
    :param apm_value: value to be used with hdparm's -B parameter to set the
    drives APM level. Should be between 1-255 and will be ignored if not. When
    ignored there will be no hdparm -B executed and no -B switch added to the
    relevant systemd line.
    :param spindown_message: message received from drop down as human presented
    selection, used later in systemd script to retrieve previous setting.
    :return: False if an hdparm command was not possible ie inappropriate dev,
    or an error was return by the command, True otherwise.
    """
    # TODO: candidate for move to system/hdparm
    # Deal elegantly with null dev_byid
    if dev_byid is None:
        return False
    # hdparm -S works on partitions so base_dev is not needed, but it does
    # require a full path ie /dev/disk/by-id/dev_byid; dev_by along is no good.
    dev_byid_withpath = get_device_path(dev_byid)
    # md devices arn't offered a spindown config: unknown status from hdparm
    # -C.  Their member disks are exposed on the Disks page so for the time
    # being their spin down times are addressed as regular disks are.  Don't
    # spin down non rotational devices, skip all and return True.
    if is_rotational(dev_byid_withpath) is not True:
        logger.info('Skipping hdparm settings: device %s '
                    'not confirmed as rotational' % dev_byid)
        return False
    # Execute the -B hdparm command first as if it fails we can then not
    # include it in the final command in systemd as it will trip the whole
    # command then.
    # TODO: Check if only rc != 0 throws systemd execution ie do error returns
    # TODO: also trip the script execution.
    switch_list = []
    # Do nothing with testing -B options if the value supplied is out of range.
    # Also skip if we have received the remove entry flag of spindown_time = -1
    if (apm_value > 0 and apm_value < 256) and spindown_time != -1:
        apm_switch_list = ['-q', '-B%s' % apm_value]
        hdparm_command = [HDPARM] + apm_switch_list + ['%s' %
                                                       dev_byid_withpath]
        # Try running this -B only hdparm to see if it will run without
        # error or non zero return code.
        out, err, rc = run_command(hdparm_command, throw=False)
        if rc == 0 and len(err) == 1:
            # if execution of the -B switch ran OK then add to switch list
            switch_list += apm_switch_list
        else:
            logger.error('non zero return code or error from hdparm '
                         'command %s with error %s and return code %s'
                         % (hdparm_command, err, rc))
    # setup -S hdparm command
    standby_switch_list = ['-q', '-S%s' % spindown_time]
    hdparm_command = [HDPARM] + standby_switch_list + ['%s' %
                                                       dev_byid_withpath]
    # Only run the command if we haven't received the spindown_time of -1
    # as this is our 'remove config' flag.
    if spindown_time != -1:
        out, err, rc = run_command(hdparm_command, throw=False)
        if rc != 0:
            logger.error('non zero return code from hdparm command %s with '
                         'error %s and return code %s' %
                         (hdparm_command, err, rc))
            return False
    hdparm_command = [HDPARM] + switch_list + standby_switch_list + [
        '%s' % dev_byid_withpath]
    # hdparm ran without issues or we are about to remove this devices setting
    # so attempt to edit rockstor-hdparm.service with the same entry
    if update_hdparm_service(hdparm_command, spindown_message) is not True:
        return False
    return True


def get_dev_byid_name(device_name, remove_path=False):
    """When given a standard dev name eg sda will return the /dev/disk/by-id
    name, or the original device_name and False as the second member of the
    returned tuple if an error occurred or no by-id type name was available.
    N.B. This latter condition is found with virtio devices that have no
    serial.
    Can optionally drop the path via the removePath parameter flag.
    Works by querying udev via udevadm info --query=property --name device_name
    The first line of which is matched to 'DEVLINKS' and parsed for the longest
    entry of the by-id type ie /dev/disk/by-id which is in turn a symlink to
    our device_name eg:
    DEVLINKS=/dev/disk/by-id/ata-QEMU_HARDDISK_QM00005
    /dev/disk/by-path/pci-0000:00:05.0-ata-1.0
    In the above example we have the by-id name made from type, model, & serial
    and a second by-path entry which is not used here.
    N.B. As the subsystem of the device is embedded in the by-id name a drive's
    by-id path will change if for example it is plugged in via usb rather than
    ata subsystem.
    :param device_name: eg /dev/sda or even the by-id name (with path)
    but only if the full path is specified with the by-id type name.
    :param remove_path: flag request to strip the path from the returned device
    name, if an error occurred or no by-id type name was found then the path
    strip flag will still be honoured but applied instead to the original
    'device_name'.
    :return: tuple of device_name and a boolean: where the device name is
    either the by-id name (with or without path as per remove_path) or in the
    case of an error or no by-id name found then the original device_name (with
    or without path as per remove_path). The second boolean element of the
    tuple indicates if a by-id type name was found. ie (return_name, is_byid)
    """
    # Until we find a by-id type name set this flag as False.
    is_byid = False
    # Until we find a by-id type name we will be returning device_name
    return_name = device_name
    byid_name = ''  # Should never be returned prior to reassignment.
    longest_byid_name_length = 0
    devlinks = []  # Doubles as a flag for DEVLINKS line found.
    # Special device name considerations / pre-processing can go here.
    cmd = [UDEVADM, 'info', '--query=property', '--name', str(device_name)]
    out, err, rc = run_command(cmd, throw=False)
    if len(out) > 0 and rc == 0:
        # The output has at least one line and our udevadm executed OK.
        # Some systemd/udev configs don't have DEVLINKS as the first line.
        for line in out:
            if re.match('DEVLINKS', line) is not None:
                # convert 'DEVLINKS=devpath devpath devpath' to list of paths
                devlinks = line.replace('=', ' ').split()[1:]
                break
        else:  # for loop else
            logger.debug('No DEVLINKS line from command ({}).'.format(cmd))
        if len(devlinks) > 0:
            # We have at least 1 devlink.
            # Sort to ensure deterministic behaviour with equal length members.
            devlinks.sort(reverse=True)
            for devname in devlinks:
                # check if device name is by-id type
                if re.match('/dev/disk/by-id', devname) is not None:
                    is_byid = True
                    # for openLUKS dm mapper device use dm-name-<dev-name>
                    # as we can most easily use this format for working
                    # from lsblk device name to by-id name via dm-name-
                    # patch on the front.
                    if re.match('/dev/disk/by-id/dm-name-',
                                devname) is not None:
                        # we have our dm-name match so assign it
                        byid_name = devname
                        break
                    dev_name_length = len(devname)
                    # check if longer than any found previously
                    if dev_name_length > longest_byid_name_length:
                        longest_byid_name_length = dev_name_length
                        # save the longest by-id type name so far.
                        byid_name = devname
    if err == ['device node not found', '']:
        logger.error('Device ({}) not found by '
                     'command ({})'.format(device_name, cmd))
    if is_byid:
        # Return the longest by-id name found in the DEVLINKS line
        # or the first if multiple by-id names were of equal length.
        return_name = byid_name
    # Honour our path strip request in all cases if we can, or if
    # no remove_path request by parameter flag or no path delimiter chars found
    # in return_name then leave as is.
    if remove_path:
        # Strip the path from the beginning of our return_name.
        # For use in Disk.name db field for example.
        # Split return_name by path delimiter char '/' into it's fields.
        return_name_fields = return_name.split('/')
        if len(return_name_fields) > 1:
            # Original device_name has path delimiters in: assume it has a path
            return_name = return_name_fields[-1]
    return return_name, is_byid


def get_byid_name_map():
    """Simple wrapper around 'ls -lr /dev/disk/by-id' which returns a current
    mapping of all attached by-id device names to their sdX counterparts. When
    multiple by-id names are found for the same sdX device then the longest is
    preferred, or when equal in length then the first listed is used. Intended
    as a light weight helper for the Dashboard disk activity widget or other
    non critical components. For critical components use only:
    get_dev_byid_name() and get_devname() as they contain sanity checks and
    validation mechanisms and are intended to have more repeatable behaviour
    but only work on a single device at a time.  A single call to this method
    can provide all current by-id device names mapped to their sdX counterparts
    with the latter being the index.
    :return: dictionary indexed (keyed) by sdX type names with associated by-id
    type names as the values, or an empty dictionary if a non zero return code
    was encountered by run_command or no by-id type names were encountered.
    """
    byid_name_map = {}
    out, err, rc = run_command([LS, '-lr', '/dev/disk/by-id'],
                               throw=True)
    if rc == 0:
        for each_line in out:
            # Split the line by spaces and '/' chars
            line_fields = each_line.replace('/', ' ').split()
            # Grab every sda type name from the last field in the line and add
            # it as a dictionary key with it's value as the by-id type name so
            # we can index by sda type name and retrieve the by-id. As there
            # are often multiple by-id type names for a given sda type name we
            # gain consistency in mapped by-id value by always preferring the
            # longest by-id for a given sda type name key.
            if len(line_fields) >= 5:
                # Ensure we have at least 5 elements to avoid index out of
                # range and to skip lines such as "total 0"
                if line_fields[-1] not in byid_name_map.keys():
                    # We don't yet have a record of this device so take one.
                    byid_name_map[line_fields[-1]] = line_fields[-5]
                    # ie {'sda': 'ata-QEMU_HARDDISK_QM00005'}
                else:
                    # We already have a record of this device so check if the
                    # current line's by-id name is longer.
                    if len(line_fields[-5]) > len(
                            byid_name_map[line_fields[-1]]):
                        # The current line's by-id name is longer so use it.
                        byid_name_map[line_fields[-1]] = line_fields[-5]
    return byid_name_map


def get_device_mapper_map():
    """
    Simple wrapper around 'ls -lr /dev/mapper' akin to get_byid_name_map() but
    without the assumption of multiple entries and with differing field count
    expectations.
    :return: dictionary indexed (keyed) by 'dm-0' type names with associated
    /dev/mapper names as the values (path included), or an empty dictionary if
    a non zero return code was encountered by run_command or no /dev/mapper
    names found.
    """
    device_mapper_map = {}
    out, err, rc = run_command([LS, '-lr', '/dev/mapper'], throw=True)
    if rc == 0 and len(out) > 3:  # len 3 is only control char dev listed.
        for each_line in out:
            if each_line == '':
                continue
            # Split the line by spaces and '/' chars
            line_fields = each_line.replace('/', ' ').split()
            # Grab every dm-0 type name from the last field in the line and add
            # it as a dictionary key with it's value as the mapped dir entry.
            # Our full path is added as a convenience to our caller.
            # {'dm-0': '/dev/mapper/luks-dd6589a6-14aa-4a5a-bcea-fe72e2dec333'}
            if len(line_fields) == 12:
                device_mapper_map[line_fields[-1]] = line_fields[-4]
    return device_mapper_map


def get_device_path(by_id):
    """
    Return full path for given device id.
    For testing and adaptations, this can be adjusted for supporting devices
    (like nbd) which have no device-by-id entry. That said, DO NOT put
    workarounds here if there is any other way to do it. The by-id treatment
    is for having stable device names across reboots and unplugging and
    re-plugging devices, our database can get confused if that consistency is
    not there. See https://github.com/rockstor/rockstor-core/pull/1704 for
    some discussion of this topic.
    """
    return '/dev/disk/by-id/%s' % by_id


def get_whole_dev_uuid(dev_byid):
    """
    Simple wrapper around "lsblk -n -o uuid <dev_name>" to retrieve a device's
    whole disk uuid. Where there are partitions multiple lines are output but
    the first is for the whole disk uuid if it exists eg (with headers):
    lsblk -o uuid,name /dev/disk/by-id/virtio-serial-1
    UUID                                 NAME
                                         vdc
    44a753bd-2805-452b-bc89-f6d4adbe1395 vdc2
    315A-5CBA                            vdc1
    Or a freshly formatted whole disk LUKS container:
    lsblk -o uuid,name /dev/disk/by-id/virtio-serial-3
    UUID                                 NAME
    6ca7a3eb-7c40-4f9e-925c-b109d68040dd vdf
    which is quicker and more versatile than
    """
    dev_uuid = ''
    dev_byid_withpath = get_device_path(dev_byid)
    out, err, rc = run_command([LSBLK, '-n', '-o', 'uuid', dev_byid_withpath],
                               throw=False)
    if rc != 0:
        return dev_uuid
    if len(out) > 0:
        # we have at least a single line of output and rc = 0
        # rapid rudimentary check on uuid formatting:
        if len(out[0].split('-')) > 1:
            # we have at least a vfat uuid format ie 315A-5CBA so use it:
            dev_uuid = out[0]
    return dev_uuid


def get_uuid_name_map():
    """
    Simple wrapper around 'ls -l /dev/disk/by-uuid' which returns a current
    mapping of all attached by-uuid device names to their sdX counterparts.
    Modeled on the existing get_byid_name_map() but simpler as no duplicate
    device by different names are expected. Ie one uuid name per device.
    :return: dictionary indexed (keyed) by sdX type names with associated
    by-uuid type names as the values, or an empty dictionary if a non zero
    return code was encountered by run_command or no by-uuid type names were
    found (unlikely).
    """
    uuid_name_map = {}
    out, err, rc = run_command([LS, '-l', '/dev/disk/by-uuid'],
                               throw=True)
    if rc == 0:
        for each_line in out:
            # Split the line by spaces and '/' chars
            line_fields = each_line.replace('/', ' ').split()
            # Grab every sda type name from the last field in the line and add
            # it as a dictionary key with it's value as the by-uuid name so
            # we can index by sda type name and retrieve the uuid.
            if len(line_fields) >= 5:
                # Ensure we have at least 5 elements to avoid index out of
                # range and to skip lines such as "total 0"
                if line_fields[-1] not in uuid_name_map.keys():
                    # We don't yet have a record of this device so take one.
                    uuid_name_map[line_fields[-1]] = line_fields[-5]
                    # ie {'vdd': '82fd9db1-e1c1-488d-9b42-536d0a82caeb'}
    return uuid_name_map


def get_dev_temp_name(dev_byid):
    """
    Returns the current canonical device name (of type 'sda') for a supplied
    by-id type name. Used to translate a single Disk.name db field by-id type
    name to it's current equivalent canonical sda type name.
    Works by parsing the output of os.readlink which returns the file target of
    a given link, all /dev/disk/by-id entries are links created by udev.
    os.readlink('/dev/disk/by-id/ata-QEMU_HARDDISK_QM005-part3') = '../../sda3'
    As db.name values are not guaranteed to have by-id entries, if no match is
    found, ie OSError, then the original by-id name is returned. This also
    servers as a fail safe in case any other OSError is encountered.
    This allows for 'no serial' devices where a by-id can't be created and for
    calls made on detached devices ie Disk.name = 'detached-<uuid>'.
    :param dev_byid: by-id type device name without path.
    :return: sda type device name without path or if no match is found then
    dev_byid is returned.
    """
    dev_byid_withpath = get_device_path(dev_byid)
    try:
        temp_name = os.readlink(dev_byid_withpath).split('/')[-1]
    except OSError:
        # the device name given may not have a listing in /dev/disk/by-id
        return dev_byid
    else:
        return temp_name


def get_devname_old(device_name):
    """Depricated / prior version of get_devname() Returns the value of DEVNAME
    as reported by udevadm when supplied with a legal device name ie a full
    path by-id or full path by-path ie any DEVLINKS. Also works when supplied
    with eg "sda". Primarily intended to retrieve the full path device name
    from a full path by-id name or an abbreviated DEVNAME eg sda.
    N.B. this is a partner function to get_dev_byid_name(device_name)
    Works by sampling the second line of udevadm and confirming it begins with
    DEVNAME, then returning the value found after the '=' char.
    example line:
    DEVNAME=/dev/sda
    :param device_name: sda, /dev/sda, full path by-id or by-path
    :return: Full path of device name eg /dev/sda or None if error or no
    DEVNAME found
    """
    out, err, rc = run_command(
        [UDEVADM, 'info', '--query=property', '--name', str(device_name)],
        throw=False)
    if len(out) > 1:
        # the output has at least two lines
        # split the second line by the '=' char
        fields = out[1].split('=')
        if len(fields) > 1:
            # we have at least 2 fields in this line
            if fields[0] == 'DEVNAME':
                # return the first value directly after DEVNAME
                return fields[1]
    # if no DEVNAME value found or an error occurred.
    return None


def get_devname(device_name, addPath=False):
    """Intended as a light and quicker way to retrieve a device name with or
    without (default) path from any legal udevadm --name parameter
    Simple wrapper around a call to:
    udevadm info --query=name device_name
    Works with device_name of eg sda /dev/sda /dev/disk/by-id/ and /dev/disk/
    If a device doesn't exist then udevadm returns multi word advise so if more
    than one word assume failure and return None.
    N.B. if given /dev/sdc3 or equivalent DEVLINKS this method will return sdc3
    if no path is requested.
    :param device_name: legal device name to --name in udevadmin
    :return: short device name ie sda (no path) or with path /dev/sda if
    addPath is True or None if multi word response from udevadm ie
    "Unknown device, .."
    """
    out, err, rc = run_command(
        [UDEVADM, 'info', '--query=name', '--name', str(device_name)],
        throw=False)
    if len(out) > 0:
        # we have at least a single line of output
        fields = out[0].split()
        if len(fields) == 1:
            # we have a single word output so return it with or without path
            if addPath:
                return '/dev/{}'.format(fields[0])
            # return the word (device name ie sda) without added /dev/
            return fields[0]
    # a non one word reply was received on the first line from udevadm or
    return None


def update_hdparm_service(hdparm_command_list, comment):
    """
    Updates or creates the /etc/systemd/system/rockstor-hdparm.service file for
    the device_name given. The creation of this file is based on the template
    file in conf named rockstor-hdparm.service.
    :param hdparm_command_list: list containing the hdparm command elements
    :param comment: test message to follow hdparm command on next line
    :return: None or the result of enabling the service via run_command which
    is only done when the service is freshly installed, ie when no existing
    /etc/systemd/system/rockstor-hdparm.service file exists in the first place.
    """
    # TODO: candidate for move to system/hdparm
    edit_done = False
    do_edit = False
    clear_line_count = 0
    remove_entry = False
    # Establish our systemd_template, needed when no previous config exists.
    service = 'rockstor-hdparm.service'
    systemd_template = ('%s/%s' % (settings.CONFROOT, service))
    systemd_target = ('/etc/systemd/system/%s' % service)
    # Check for the existence of this systemd template file.
    if not os.path.isfile(systemd_template):
        # We have no template file so log the error and return False.
        logger.error('Skipping hdparm settings: no %s '
                     'template file found.' % systemd_template)
        return False
    # Get the line count of our systemd_template, for use in recognizing when
    # we have removed all existing config entries.
    with open(systemd_template) as ino:
        systemd_template_line_count = len(ino.readlines())
    # get our by-id device name by extracting the last hdparm list item
    device_name_byid = hdparm_command_list[-1]
    # look four our flag of a -1 value for the -S parameter
    if hdparm_command_list[-2] == '-S-1':
        # When a user selects "Remove config" our -S value = -1, set flag.
        remove_entry = True
    # first create a temp file to use as our output until we are done editing.
    tfo, npath = mkstemp()
    # If there is already a rockstor-hdparm.service file then we use that
    # as our source file, otherwise use conf's empty template.
    if os.path.isfile(systemd_target):
        infile = systemd_target
        update = True
    else:
        # We have already checked for the existence of our template file.
        infile = systemd_template
        update = False
    # Create our proposed temporary file based on the source file plus edits.
    with open(infile) as ino, open(npath, 'w') as outo:
        for line in ino.readlines():  # readlines reads whole file in one go.
            if do_edit and edit_done and clear_line_count != 2:
                # We must have just edited an entry so we need to skip
                # a line as each entry consists of an ExecStart= line and a
                # remark line directly afterwards, but only if clear_line_count
                # doesn't indicate an addition.
                # reset our do_edit flag and continue
                do_edit = False
                continue
            if (re.match('ExecStart=', line) is not None) and not edit_done:
                # we have found a line beginning with "ExecStart="
                if update:
                    if device_name_byid == line.split()[-1]:
                        # matching device name entry so set edit flag
                        do_edit = True
                else:  # no update and ExecStart found so set edit flag
                    do_edit = True
            # process all lines with the following
            if line == '\n':  # empty line, or rather just a newline char
                clear_line_count += 1
            if clear_line_count == 2 and not edit_done:
                # we are looking at our second empty line and haven't yet
                # achieved edit_done so do our edit / addition in this case.
                do_edit = True
            if do_edit and not edit_done:
                # We are due to either add or overwrite our 2 line entry but
                # only if we are not in remove_entry mode.
                # When remove_entry = True our writes are skipped which equates
                # to an removal or in the case of a new addition, nothing added
                if not remove_entry:
                    outo.write(
                        'ExecStart=' + ' '.join(hdparm_command_list) + '\n')
                    outo.write('# %s' % comment + '\n')
                edit_done = True
            # mechanism to skip a line if we have just done an edit
            if not (do_edit and edit_done and clear_line_count != 2):
                # if do-edit and edit_done are both true it means we have just
                # done a line replacement so we skip copying the original line
                # over to the target file, but only if clear_line_count also
                # !=2 as this would indicate an addition where we do need to
                # copy over the original files line.
                outo.write(line)
    # Now count our temp files lines as if it has no more than our template
    # then we have no ExecStart lines and so need to disable our
    # rockstor-hdparm systemd service.  Pythons _candidate_tempdir_list()
    # should ensure our npath temp file is in memory (tmpfs) so not that heavy
    # to open again. Our previous 'with open()' is already complex enough.
    with open(npath) as ino:
        tempfile_length = len(ino.readlines())
    # Now to disable the service if our systemd file is of minimum length
    if tempfile_length == systemd_template_line_count:
        # our proposed systemd file is the same length as our template and so
        # contains no ExecStart lines so we disable the rockstor-hdparm
        # service.
        out, err, rc = run_command([SYSTEMCTL_BIN, 'disable', service])
        if rc != 0:
            return False
        # and remove our rockstor-hdparm.service file as it's absence indicates
        # a future need to restart this service via the update flag as not
        # True.
        if update:  # update was set true if file exists so we check first.
            # TODO: Is try clause needed as we know it exists already?
            os.remove(systemd_target)
    else:
        # Since we know our proposed systemd file has more than template
        # entries it's worth copying over to our destination as we are done
        # updating it.  There is an assumption here that !=
        # systemd_template_linecount = greater than. Should be so.
        shutil.move(npath, systemd_target)
        os.chmod(systemd_target, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP |
                 stat.S_IROTH)
    if update is not True and tempfile_length > systemd_template_line_count:
        # This is a fresh systemd instance so enable it but only if our line
        # count (ie entries) is greater than the template file's line count.
        # N.B. can't use systemctrl wrapper as then circular dependency ie:-
        # return systemctl('rockstor-hdparm', 'enable')
        out, err, rc = run_command([SYSTEMCTL_BIN, 'enable', service])
        if rc != 0:
            return False
    return True


def read_hdparm_setting(dev_byid):
    """
    Looks through /etc/systemd/system/rockstor-hdparm service for any comment
    following a matching device entry and returns it if found. Returns None if
    no file or no matching entry or comment there after was found.
    :param dev_byid: device name of by-id type without path
    :return: comment string immediately following an entry containing the given
    device name or None if None found or the systemd file didn't exist.
    """
    # TODO: candidate for move to system/hdparm
    if dev_byid is None:
        return None
    infile = '/etc/systemd/system/rockstor-hdparm.service'
    if not os.path.isfile(infile):
        return None
    dev_byid_withpath = get_device_path(dev_byid)
    dev_byid_found = False
    with open(infile) as ino:
        for line in ino.readlines():
            if line == '\n':
                # skip empty lines
                continue
            line_fields = line.split()
            if dev_byid_found:
                # we have already matched ExecStart line ending with dev_byid
                # so now look for a non empty (>= 2) comment line following it.
                if line_fields[0] == '#' and len(line_fields) >= 2:
                    # we have a comment after our target device entry so return
                    # that comment minus the #
                    return ' '.join(line_fields[1:])
                else:
                    # no comment found directly after target dev so return None
                    return None
            if line_fields[0] == '#' or len(line_fields) < 4:
                # Skip comment lines not directly after our target dev_byid.
                # Also no device line will be of interest if below 4, this way
                # we don't do slow re.match on non candidates.
                continue
            if re.match('ExecStart', line_fields[0]) \
                    and line_fields[-1] == dev_byid_withpath:
                # Found a line beginning with ExecStart and ending in dev_byid.
                dev_byid_found = True
    return None


def enter_standby(dev_byid):
    """Simple wrapper to execute hdparm -y /dev/disk/by-id/device_name which
    requests that the named device enter 'standby' mode which usually means it
    will spin down.  Should only be available if he power status of the device
    can be successfully read without errors (ui inforced)
    :param dev_byid: device name as stored in db ie /dev/disk/by-id type
    :return: None or out, err, rc of command
    """
    # TODO: candidate for move to system/hdparm
    hdparm_command = [HDPARM, '-q', '-y', get_device_path(dev_byid)]
    return run_command(hdparm_command)


def hostid():
    """Get the system's uuid from /sys/class/dmi/id/product_uuid. If the file
    doesn't exist for any reason, generate a uuid like we used to prior to this
    change.

    There's a lazy vendor problem where uuid is not set and defaults to
    03000200-0400-0500-0006-000700080009 or
    00020003-0004-0005-0006-000700080009. I don't know how these values are
    populated, but empirically it seems to be just these
    two. A non-persistent uuid is also generated in this case.

    Observed motherboards with these fake non unique puuids:
    - Examples of the first listed fake_puuids
    ASRock N3700-ITX
    ASRock C2550D4I
    ASRock J3455 ITX - Thanks to forum member adworacz for reporting this one.
    - Examples of the second listed fake_puuids
    ZOTAC 880G-ITX (880GITX-A-E) - Thanks to forum member mmmdonuts
    - Examples of the third listed fake_puuids
    GIADA N70E-DR - Thanks to forum member hammerite
    """

    fake_puuids = ('03000200-0400-0500-0006-000700080009',
                   '00020003-0004-0005-0006-000700080009',
                   '5C4606FA-192F-453A-B299-7B088C63BB9B')
    try:
        with open("/sys/class/dmi/id/product_uuid") as fo:
            puuid = fo.readline().strip()
            if (puuid in fake_puuids):
                raise CommandException
            return puuid
    except:
        return '%s-%s' % (run_command([HOSTID])[0][0], str(uuid.uuid4()))


def trigger_udev_update():
    """In some instances udev info can be out of date after some btrfs
    operations.  To cause a system wide update of all udev info, and the
    output of lsblk, we can execute: udevadm trigger
    This function is a simple wrapper to call the above command via run_command
    :return: o, e, rc as returned by run_command
    """
    return run_command([UDEVADM, 'trigger'])


def trigger_systemd_update():
    """Reruns all systemd generators (see man systemd.generator 7).
    In some instances systemd managed resources can be out of date with
    associated configuration file changes which can lead to a confusion via
    prior configurations being still current. An example of this is when
    /etc/crypttab is changed and it's systemd generated service files no
    longer reflect the 'source of truth' that /etc/crypttab represents.
    The systemd-cryptsetup-generator scans the contents of /etc/crypttab
    and establishes service files for each (eg LUKS) mapped device. An
    example of one of these generated files is:
    /var/run/systemd/generator/systemd-cryptsetup@<mapped-name>.service
    Running 'systemctl daemon-reload' requests that all such resources be
    updated to freshly represent the new state of the associated config files.
    :return: o, e, rc as returned by run_command
    """
    return run_command([SYSTEMCTL_BIN, 'daemon-reload'])


def systemd_name_escape(original_sting, template=''):
    """Wrapper around systemd-escape unit name pre-processor. Used to escape
    stings ready for use as systemd unit or service names. Eg (shortened):
    passed sting = 'luks-5037b320-95d6-4c74-94e7'
    output:
    'luks\x2d5037b320\x2d95d6\x2d4c74\x2d94e7'
    With optional template='systemd-cryptsetup@.service' the output would be:
    systemd-cryptsetup@luks\x2d5037b320\x2d95d6\x2d4c74\x2d94e7.service
    # N.B. there is currently an issue with the --template option:
    https://bugs.centos.org/view.php?id=13262
    :param template: if supplied passed as parameter to --template
    :param original_sting: pre-escaped  string for systemd service name use.
    :return: post-escaped string ie '\x2d' instead of '-' etc or '' if a non
    zero return code was encountered.
    """
    # future version when upstream --template bug fixed:
    # if template == '':
    #     out, err, rc = run_command([SYSTEMD_ESCAPE, original_sting])
    # else:
    #     out, err, rc = run_command(
    #         [SYSTEMD_ESCAPE, '--template=%s' % template, original_sting])
    # if rc == 0 and len(out) > 0:
    #     return out[0]
    # else:
    #     return ''
    # future version end
    # temp --template bug workaround version:
    out, err, rc = run_command([SYSTEMD_ESCAPE, original_sting])
    if rc == 0 and len(out) > 0:
        if template == '':
            return out[0]
        else:
            dot_index = template.find('.')
            if dot_index == -1:
                return ''
            # Put our command output into our template at position dot_index.
            out = template[:dot_index] + out[0] + template[dot_index:]
            return out
    else:
        return ''
