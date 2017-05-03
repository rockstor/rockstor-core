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
import os
import re
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Disk, Pool, Share)
from fs.btrfs import (enable_quota, btrfs_uuid, mount_root,
                      get_pool_info, pool_raid)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from share_helpers import (import_shares, import_snapshots)
from django.conf import settings
import rest_framework_custom as rfc
from system import smart
from system.luks import luks_format_disk, get_unlocked_luks_containers_uuids, \
    get_crypttab_entries, update_crypttab, native_keyfile_exists, \
    establish_keyfile
from system.osi import set_disk_spindown, enter_standby, get_dev_byid_name, \
    wipe_disk, blink_disk, scan_disks, get_whole_dev_uuid
from copy import deepcopy
import uuid
import json
import logging

logger = logging.getLogger(__name__)

# A list of scan_disks() assigned roles: ie those that can be identified from
# the output of lsblk with the following switches:
# -P -o NAME,MODEL,SERIAL,SIZE,TRAN,VENDOR,HCTL,TYPE,FSTYPE,LABEL,UUID
# and the post processing present in scan_disks()
# LUKS currently stands for full disk crypto container.
SCAN_DISKS_KNOWN_ROLES = ['mdraid', 'root', 'LUKS', 'openLUKS', 'bcache',
                          'bcache-cdev', 'partitions']


class DiskMixin(object):
    serializer_class = DiskInfoSerializer

    @staticmethod
    @transaction.atomic
    def _update_disk_state():
        """
        A db atomic method to update the database of attached disks / drives.
        Works only on device serial numbers for drive identification.
        Calls scan_disks to establish the current connected drives info.
        Initially removes duplicate by serial number db entries to deal
        with legacy db states and obfuscates all previous device names as they
        are transient. The drive database is then updated with the attached
        disks info and previously known drives no longer found attached are
        marked as offline. All offline drives have their SMART availability and
        activation status removed and all attached drives have their SMART
        availability assessed and activated if available.
        :return: serialized models of attached and missing disks via serial num
        """
        # Acquire a list (namedtupil collection) of attached drives > min size
        disks = scan_disks(settings.MIN_DISK_SIZE)
        # Acquire a list of uuid's for currently unlocked LUKS containers.
        # Although we could tally these as we go by noting fstype crypt_LUKS
        # and then loop through our db Disks again updating all matching
        # base device entries, this approach helps to abstract this component
        # and to localise role based db manipulations to our second loop.
        unlocked_luks_containers_uuids = get_unlocked_luks_containers_uuids()
        serial_numbers_seen = []
        # Acquire a dictionary of crypttab entries, dev uuid as indexed.
        dev_uuids_in_crypttab = get_crypttab_entries()
        # Make sane our db entries in view of what we know we have attached.
        # Device serial number is only known external unique entry, scan_disks
        # make this so in the case of empty or repeat entries by providing
        # fake serial numbers which are flagged via WebUI as unreliable.
        # 1) Scrub all device names with unique but nonsense uuid4.
        # 2) Mark all offline disks as such via db flag.
        # 3) Mark all offline disks smart available and enabled flags as False.
        for do in Disk.objects.all():
            # Replace all device names with a unique placeholder on each scan
            # N.B. do not optimize by re-using uuid index as this could lead
            # to a non refreshed webui acting upon an entry that is different
            # from that shown to the user.
            do.name = 'detached-' + str(uuid.uuid4()).replace('-', '')
            # Delete duplicate or fake by serial number db disk entries.
            # It makes no sense to save fake serial number drives between scans
            # as on each scan the serial number is re-generated (fake) anyway.
            # Serial numbers beginning with 'fake-serial-' are from scan_disks.
            if (do.serial in serial_numbers_seen) or (
                    re.match('fake-serial-', do.serial) is not None):
                logger.info('Deleting duplicate or fake (by serial) Disk db '
                            'entry. Serial = %s' % do.serial)
                do.delete()  # django >=1.9 returns a dict of deleted items.
                # Continue onto next db disk object as nothing more to process.
                continue
            # first encounter of this serial in the db so stash it for
            # reference
            serial_numbers_seen.append(deepcopy(do.serial))
            # Look for devices (by serial number) that are in the db but not in
            # our disk scan, ie offline / missing.
            if (do.serial not in [d.serial for d in disks]):
                # update the db entry as offline
                do.offline = True
                # disable S.M.A.R.T available and enabled flags.
                do.smart_available = do.smart_enabled = False
            do.save()  # make sure all updates are flushed to db
        # Our db now has no device name info: all dev names are place holders.
        # Iterate over attached drives to update the db's knowledge of them.
        # Kernel dev names are unique so safe to overwrite our db unique name.
        for d in disks:
            # start with an empty disk object
            dob = None
            # an empty dictionary of non scan_disk() roles
            non_scan_disks_roles = {}
            # and an empty dictionary of discovered roles
            disk_roles_identified = {}
            # Convert our transient but just scanned so current sda type name
            # to a more useful by-id type name as found in /dev/disk/by-id
            byid_disk_name, is_byid = get_dev_byid_name(d.name, True)
            # If the db has an entry with this disk's serial number then
            # use this db entry and update the device name from our new scan.
            if (Disk.objects.filter(serial=d.serial).exists()):
                dob = Disk.objects.get(serial=d.serial)
                dob.name = byid_disk_name
            else:
                # We have an assumed new disk entry as no serial match in db.
                # Build a new entry for this disk.  N.B. we may want to force a
                # fake-serial here if is_byid False, that way we flag as
                # unusable disk as no by-id type name found.  It may already
                # have been set though as the only by-id failures so far are
                # virtio disks with no serial so scan_disks will have already
                # given it a fake serial in d.serial.
                dob = Disk(name=byid_disk_name, serial=d.serial, role=None)
            # Update the db disk object (existing or new) with our scanned info
            dob.size = d.size
            dob.parted = d.parted
            dob.offline = False  # as we are iterating over attached devices
            dob.model = d.model
            dob.transport = d.transport
            dob.vendor = d.vendor
            # N.B. The Disk.btrfs_uuid is in some senses becoming misleading
            # as we begin to deal with Disk.role managed drives such as mdraid
            # members and full disk LUKS drives where we can make use of the
            # non btrfs uuids to track filesystems or LUKS containers.
            # Leaving as is for now to avoid db changes.
            dob.btrfs_uuid = d.uuid
            # If attached disk has an fs and it isn't btrfs
            if (d.fstype is not None and d.fstype != 'btrfs'):
                # blank any btrfs_uuid it may have had previously.
                dob.btrfs_uuid = None
            # ### BEGINNING OF ROLE FIELD UPDATE ###
            # Update the role field with scan_disks findings.
            # SCAN_DISKS_KNOWN_ROLES a list of scan_disks identifiable roles.
            # Deal with legacy non json role field contents by erasure.
            # N.B. We have a minor legacy issue in that prior to using json
            # format for the db role field we stored one of 2 strings.
            # If either of these 2 strings are found reset to db default of
            # None
            if dob.role == 'isw_raid_member'\
                    or dob.role == 'linux_raid_member':
                # These are the only legacy non json formatted roles used.
                # Erase legacy role entries as we are about to update the role
                # anyway and new entries will then be in the new json format.
                # This helps to keeps the following role logic cleaner and
                # existing mdraid members will be re-assigned if appropriate
                # using the new json format.
                dob.role = None
            # First extract all non scan_disks assigned roles so we can add
            # them back later; all scan_disks assigned roles will be identified
            # from our recent scan_disks data so we assert the new truth.
            if dob.role is not None:  # db default null=True so None here.
                # Get our previous roles into a dictionary
                previous_roles = json.loads(dob.role)
                # Preserve non scan_disks identified roles for this db entry
                non_scan_disks_roles = {role: v for role, v in
                                        previous_roles.items()
                                        if role not in SCAN_DISKS_KNOWN_ROLES}
            if d.fstype == 'isw_raid_member' \
                    or d.fstype == 'linux_raid_member':
                # MDRAID MEMBER: scan_disks() can informs us of the truth
                # regarding mdraid membership via d.fstype indicators.
                # create or update an mdraid dictionary entry
                disk_roles_identified['mdraid'] = str(d.fstype)
            if d.fstype == 'crypto_LUKS':
                # LUKS FULL DISK: scan_disks() can inform us of the truth
                # regarding full disk LUKS containers which on creation have a
                # unique uuid. Stash this uuid so we might later work out our
                # container mapping. Currently required as only btrfs uuids
                # are stored in the Disk model field. Also flag if we are the
                # container for a currently open LUKS volume.
                is_unlocked = d.uuid in unlocked_luks_containers_uuids
                disk_roles_identified['LUKS'] = {'uuid': str(d.uuid),
                                                 'unlocked': is_unlocked}
                # We also inform this role of the current crypttab status
                # of this device, ie: no entry = no "crypttab" key.
                # Device listed in crypttab = dict key entry of "crypttab".
                # If crypttab key entry then it's value is 3rd column ie:
                # 'none' = password on boot
                # '/root/keyfile-<uuid>' = full path to keyfile
                # Note that we also set a boolean in the LUKS disk role of
                # 'keyfileExists' true if a crypttab entry exists or if our
                # default /root/keyfile-<uuid> exists, false otherwise.
                # So the current keyfile takes priority when setting this flag.
                # This may have to be split out later to discern the two states
                # separately.
                if d.uuid in dev_uuids_in_crypttab.keys():
                    # Our device has a UUID= match in crypttab so save as
                    # value the current cryptfile 3rd column entry.
                    disk_roles_identified['LUKS']['crypttab'] \
                        = dev_uuids_in_crypttab[d.uuid]
                    # if crypttab 3rd column indicates keyfile: does that
                    # keyfile exist. N.B. non 'none' entry assumed to be
                    # keyfile. Allows for existing user created keyfiles.
                    # TODO: could be problematic during crypttab rewrite where
                    # keyfile is auto named but we should self correct on our
                    # next run, ie new file entry is checked there after.
                    if dev_uuids_in_crypttab[d.uuid] != 'none':
                        disk_roles_identified['LUKS']['keyfileExists'] \
                            = os.path.isfile(dev_uuids_in_crypttab[d.uuid])
                if 'keyfileExists' not in disk_roles_identified['LUKS']:
                    # We haven't yet set our keyfileExists flag: ie no entry,
                    # custom or otherwise, in crypttab to check or the entry
                    # was "none". Revert to defining this flag against the
                    # existence or otherwise of our native keyfile:
                    disk_roles_identified['LUKS']['keyfileExists'] \
                        = native_keyfile_exists(d.uuid)
            if d.type == 'crypt':
                # OPEN LUKS DISK: scan_disks() can inform us of the truth
                # regarding an opened LUKS container which appears as a mapped
                # device. Assign the /dev/disk/by-id name as a value.
                # TODO: Consider stashing cryptsetup status info in this role
                # TODO: as a dict/json.
                disk_roles_identified['openLUKS'] = 'dm-name-%s' % d.name
            if d.fstype == 'bcache':
                # BCACHE: scan_disks() can inform us of the truth regarding
                # bcache "backing devices" so we assign a role to avoid these
                # devices being seen as unused and accidentally deleted. Once
                # formatted with make-bcache -B they are accessed via a virtual
                # device which should end up with a serial of bcache-(d.uuid)
                # here we tag our backing device with it's virtual counterparts
                # serial number.
                disk_roles_identified['bcache'] = 'bcache-%s' % d.uuid
            if d.fstype == 'bcache-cdev':
                # BCACHE: continued; here we use the scan_disks() added info
                # of this bcache device being a cache device not a backing
                # device, so it will have no virtual block device counterpart
                # but likewise must be specifically attributed (ie to fast
                # ssd type drives) so we flag in the role system differently.
                disk_roles_identified['bcachecdev'] = 'bcache-%s' % d.uuid
            if d.root is True:
                # ROOT DISK: scan_disks() has already identified the current
                # truth regarding the device hosting our root '/' fs so update
                # our role accordingly.
                # N.B. value of d.fstype here is essentially a place holder as
                # the presence or otherwise of the 'root' key is all we need.
                disk_roles_identified['root'] = str(d.fstype)
            if d.partitions != {}:
                # PARTITIONS: scan_disks() has built an updated partitions dict
                # so create a partitions role containing this dictionary.
                # Convert scan_disks() transient (but just scanned so current)
                # sda type names to a more useful by-id type name as found
                # in /dev/disk/by-id for each partition name.
                byid_partitions = {
                    get_dev_byid_name(part, True)[0]:
                        d.partitions.get(part, "") for part in d.partitions}
                # In the above we fail over to "" on failed index for now.
                disk_roles_identified['partitions'] = byid_partitions
            # Now we join the previous non scan_disks identified roles dict
            # with those we have identified from our fresh scan_disks() data
            # and return the result to our db entry in json format.
            # Note that dict of {} isn't None
            if (non_scan_disks_roles != {}) or (disk_roles_identified != {}):
                combined_roles = dict(non_scan_disks_roles,
                                      **disk_roles_identified)
                dob.role = json.dumps(combined_roles)
            else:
                dob.role = None
            # END OF ROLE FIELD UPDATE
            # If our existing Pool db knows of this disk's pool via it's label:
            if (Pool.objects.filter(name=d.label).exists()):
                # update the disk db object's pool field accordingly.
                dob.pool = Pool.objects.get(name=d.label)

                # this is for backwards compatibility. root pools created
                # before the pool.role migration need this. It can safely be
                # removed a few versions after 3.8-11 or when we reset
                # migrations.
                if (d.root is True):
                    dob.pool.role = 'root'
                    dob.pool.save()
            else:  # this disk is not known to exist in any pool via it's label
                dob.pool = None
            # If no pool has yet been found with this disk's label in and
            # the attached disk is our root disk (flagged by scan_disks)
            if (dob.pool is None and d.root is True):
                # setup our special root disk db entry in Pool
                # TODO: dynamically retrieve raid level.
                p = Pool(name=d.label, raid='single', role='root')
                p.save()
                p.disk_set.add(dob)
                # update disk db object to reflect special root pool status
                dob.pool = p
                dob.save()
                p.size = p.usage_bound()
                enable_quota(p)
                p.uuid = btrfs_uuid(dob.name)
                p.save()
            # save our updated db disk object
            dob.save()
        # Update online db entries with S.M.A.R.T availability and status.
        for do in Disk.objects.all():
            # find all the not offline db entries
            if (not do.offline):
                # We have an attached disk db entry.
                # Since our Disk.name model now uses by-id type names we can
                # do cheap matches to the beginnings of these names to find
                # virtio, md, or sdcard devices which are assumed to have no
                # SMART capability.
                # We also disable devices smart support when they have a
                # fake serial number as ascribed by scan_disks as any SMART
                # data collected is then less likely to be wrongly associated
                # with the next device that takes this temporary drive's name.
                # Also note that with no serial number some device types will
                # not have a by-id type name expected by the smart subsystem.
                # This has only been observed in no serial virtio devices.
                if (re.match('fake-serial-', do.serial) is not None) or (
                    re.match('virtio-|md-|mmc-|nvme-|dm-name-luks-|bcache',
                             do.name) is not None):
                    # Virtio disks (named virtio-*), md devices (named md-*),
                    # and an sdcard reader that provides devs named mmc-* have
                    # no smart capability so avoid cluttering logs with
                    # exceptions on probing these with smart.available.
                    # nvme not yet supported by CentOS 7 smartmontools:
                    # https://www.smartmontools.org/ticket/657
                    # Thanks to @snafu in rockstor forum post 1567 for this.
                    do.smart_available = do.smart_enabled = False
                    continue
                # try to establish smart availability and status and update db
                try:
                    # for non ata/sata drives
                    do.smart_available, do.smart_enabled = smart.available(
                        do.name, do.smart_options)
                except Exception as e:
                    logger.exception(e)
                    do.smart_available = do.smart_enabled = False
            do.save()
        ds = DiskInfoSerializer(Disk.objects.all().order_by('name'), many=True)
        return Response(ds.data)


class DiskListView(DiskMixin, rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            return Disk.objects.all().order_by('name')

    def post(self, request, command, dname=None):
        with self._handle_exception(request):
            if (command == 'scan'):
                return self._update_disk_state()

        e_msg = ('Unsupported command(%s).' % command)
        handle_exception(Exception(e_msg), request)


class DiskDetailView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    @staticmethod
    def _validate_disk(dname, request):
        try:
            return Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk(%s) does not exist' % dname)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _role_filter_disk_name(disk, request):
        """
        Takes a disk object and filters it based on it's roles.
        If disk has a redirect role the redirect role value is substituted
        for that disk's name. This effects a device name re-direction:
        ie base dev to partition on base dev for example.
        :param disk:  disk object
        :param request:
        :return: by-id disk name (without path) post role filter processing
        """
        try:
            disk_name = disk.name
            if disk.role is not None:
                disk_role_dict = json.loads(disk.role)
                if 'redirect' in disk_role_dict:
                    disk_name = disk_role_dict.get('redirect', None)
            return disk_name
        except:
            e_msg = ('Problem with role filter of disk(%s)' % disk)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _reverse_role_filter_name(disk_name, request):
        """
        Simple syntactic reversal of what _update_disk_state does to assign
        disk role name values.
        Here we reverse the special role assigned names and return the original
        db disks base name.
        Initially only aware of partition redirection from base dev name.
        :param disk_name: role based disk name
        :param request:
        :return: tuple of disk_name and isPartition: Disk_name is as passed
        unless the name matches a known syntactic pattern assigned in
        _update_disk_state() in which case the name returned is the original
        db disk base name.
        """
        # until we find otherwise we assume False on partition status.
        isPartition = False
        try:
            # test for role redirect type re-naming, ie a partition name:
            # base name "ata-QEMU_DVD-ROM_QM00001"
            # partition redirect name "ata-QEMU_DVD-ROM_QM00001-part1"
            fields = disk_name.split('-')
            # check the last field for part#
            if len(fields) > 0:
                if re.match('part.+', fields[-1]) is not None:
                    isPartition = True
                    # strip the redirection to partition device.
                    return '-'.join(fields[:-1]), isPartition
            # we have found no indication of redirect role name changes.
            return disk_name, isPartition
        except:
            e_msg = ('Problem reversing role filter disk name(%s)' % disk_name)
            handle_exception(Exception(e_msg), request)

    def get(self, *args, **kwargs):
        if 'dname' in self.kwargs:
            try:
                data = Disk.objects.get(name=self.kwargs['dname'])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()

    @transaction.atomic
    def delete(self, request, dname):
        try:
            disk = Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk: %s does not exist' % dname)
            handle_exception(Exception(e_msg), request)

        if (disk.offline is not True):
            e_msg = ('Disk: %s is not offline. Cannot delete' % dname)
            handle_exception(Exception(e_msg), request)

        try:
            disk.delete()
            return Response()
        except Exception as e:
            e_msg = ('Could not remove disk(%s) due to system error' % dname)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    def post(self, request, command, dname):
        with self._handle_exception(request):
            if (command == 'wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs-wipe'):
                return self._wipe(dname, request)
            if (command == 'luks-format'):
                return self._luks_format(dname, request, passphrase='')
            if (command == 'btrfs-disk-import'):
                return self._btrfs_disk_import(dname, request)
            if (command == 'blink-drive'):
                return self._blink_drive(dname, request)
            if (command == 'enable-smart'):
                return self._toggle_smart(dname, request, enable=True)
            if (command == 'disable-smart'):
                return self._toggle_smart(dname, request)
            if (command == 'smartcustom-drive'):
                return self._smartcustom_drive(dname, request)
            if (command == 'spindown-drive'):
                return self._spindown_drive(dname, request)
            if (command == 'pause'):
                return self._pause(dname, request)
            if (command == 'role-drive'):
                return self._role_disk(dname, request)
            if (command == 'luks-drive'):
                return self._luks_disk(dname, request)

        e_msg = ('Unsupported command(%s). Valid commands are wipe, '
                 'btrfs-wipe, luks-format, btrfs-disk-import, blink-drive, '
                 'enable-smart, disable-smart, smartcustom-drive, '
                 'spindown-drive, pause, role-drive, luks-drive' % command)
        handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _wipe(self, dname, request):
        disk = self._validate_disk(dname, request)
        disk_name = self._role_filter_disk_name(disk, request)
        # Double check sanity of role_filter_disk_name by reversing back to
        # whole disk name (db name). Also we get isPartition in the process.
        reverse_name, isPartition = self._reverse_role_filter_name(disk_name,
                                                                   request)
        if reverse_name != disk.name:
            e_msg = ('Wipe operation on whole or partition of device (%s) was '
                     'rejected as there was a discrepancy in device name '
                     'resolution. Wipe was called with device name (%s) which '
                     'redirected to (%s) but a check on this redirection '
                     'returned device name (%s), which is not equal to the '
                     'caller name as was expected. A Disks page Rescan may '
                     'help.'
                     % (dname, dname, disk_name, reverse_name))
            raise Exception(e_msg)
        wipe_disk(disk_name)
        disk.parted = isPartition
        # The following value may well be updated with a more informed truth
        # from the next scan_disks() run via _update_disk_state()
        disk.btrfs_uuid = None
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _luks_format(self, dname, request, passphrase):
        disk = self._validate_disk(dname, request)
        disk_name = self._role_filter_disk_name(disk, request)
        # Double check sanity of role_filter_disk_name by reversing back to
        # whole disk name (db name). Also we get isPartition in the process.
        reverse_name, isPartition = self._reverse_role_filter_name(disk_name,
                                                                   request)
        if reverse_name != disk.name:
            e_msg = ('LUKS operation on whole or partition of device (%s) was '
                     'rejected as there was a discrepancy in device name '
                     'resolution. _make_luks was called with device name (%s) '
                     'which redirected to (%s) but a check on this redirect '
                     'returned device name (%s), which is not equal to the '
                     'caller name as was expected. A Disks page Rescan may '
                     'help.'
                     % (dname, dname, disk_name, reverse_name))
            raise Exception(e_msg)
        # Check if we are a partition as we don't support LUKS in partition.
        # Front end should filter this out as an presented option but be
        # should block at this level as well.
        if isPartition:
            e_msg = ('A LUKS format was requested on device name (%s) which '
                     'was identifyed as a partiton. Rockstor does not '
                     'support LUKS in partition, only whole disk.'
                     % dname)
            raise Exception(e_msg)
        luks_format_disk(disk_name, passphrase)
        disk.parted = isPartition  # should be False by now.
        # The following value may well be updated with a more informed truth
        # from the next scan_disks() run via _update_disk_state()
        disk.btrfs_uuid = None
        # Rather than await the next _update_disk_state() we populate our
        # LUKS container role.
        roles = {}
        # Get our roles, if any, into a dictionary.
        if disk.role is not None:
            roles = json.loads(disk.role)
        # Now we assert what we know given our above LUKS format operation.
        # Not unlocked and no keyfile (as we have a fresh uuid from format)
        # TODO: Might be better to use cryptset luksUUID <dev-name>
        dev_uuid = get_whole_dev_uuid(disk.name)
        # update or create a basic LUKS role entry.
        # Although we could use native_keyfile_exists(dev_uuid) we can be
        # pretty sure there is no keyfile with our new uuid.
        roles['LUKS'] = {'uuid': str(dev_uuid),
                         'unlocked': False,
                         'keyfileExists': False}
        # now we return our updated roles
        disk.role = json.dumps(roles)
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _smartcustom_drive(self, dname, request):
        disk = self._validate_disk(dname, request)
        # TODO: Check on None, null, or '' for default in next command
        custom_smart_options = str(
            request.data.get('smartcustom_options', ''))
        # strip leading and trailing white space chars before entry in db
        disk.smart_options = custom_smart_options.strip()
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _btrfs_disk_import(self, dname, request):
        try:
            disk = self._validate_disk(dname, request)
            disk_name = self._role_filter_disk_name(disk, request)
            p_info = get_pool_info(disk_name)
            # get some options from saved config?
            po = Pool(name=p_info['label'], raid="unknown")
            # need to save it so disk objects get updated properly in the for
            # loop below.
            po.save()
            for device in p_info['disks']:
                disk_name, isPartition = \
                    self._reverse_role_filter_name(device, request)
                do = Disk.objects.get(name=disk_name)
                do.pool = po
                # update this disk's parted property
                do.parted = isPartition
                if isPartition:
                    # ensure a redirect role to reach this partition; ie:
                    # "redirect": "virtio-serial-3-part2"
                    if do.role is not None:  # db default is null / None.
                        # Get our previous roles into a dictionary
                        roles = json.loads(do.role)
                        # update or add our "redirect" role with our part name
                        roles['redirect'] = '%s' % device
                        # convert back to json and store in disk object
                        do.role = json.dumps(roles)
                    else:
                        # role=None so just add a json formatted redirect role
                        do.role = '{"redirect": "%s"}' % device.name
                do.save()
                mount_root(po)
            po.raid = pool_raid('%s%s' % (settings.MNT_PT, po.name))['data']
            po.size = po.usage_bound()
            po.save()
            enable_quota(po)
            import_shares(po, request)
            for share in Share.objects.filter(pool=po):
                import_snapshots(share)
            return Response(DiskInfoSerializer(disk).data)
        except Exception as e:
            e_msg = ('Failed to import any pool on this device(%s). Error: %s'
                     % (dname, e.__str__()))
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _role_disk(self, dname, request):
        """
        Resets device role db entries and wraps _wipe() but will only call
        _wipe() if no redirect role changes are also requested. If we fail
        to associate these 2 tasks then there is a risk of the redirect not
        coming into play prior to the wipe.
        :param dname: disk name
        :param request:
        :return:
        """
        # Until we find otherwise:
        prior_redirect = ''
        redirect_role_change = False
        luks_passwords_match = False
        try:
            disk = self._validate_disk(dname, request)
            # We can use this disk name directly as it is our db reference
            # no need to user _role_filter_disk_name as we only want to change
            # the db fields anyway.
            # And when we call _wipe() it honours any existing redirect role
            # so we make sure to not wipe and redirect at the same time.
            new_redirect_role = str(request.data.get('redirect_part', ''))
            is_delete_ticked = request.data.get('delete_tick', False)
            is_luks_format_ticked = request.data.get('luks_tick', False)
            luks_pass_one = str(request.data.get('luks_pass_one', ''))
            luks_pass_two = str(request.data.get('luks_pass_two', ''))
            if luks_pass_one == luks_pass_two:
                luks_passwords_match = True
            # Get our previous roles into a dictionary.
            if disk.role is not None:
                roles = json.loads(disk.role)
            else:
                # roles default to None, substitute empty dict for simplicity.
                roles = {}
            # If we have received a redirect role then add/update our dict
            # with it's value (the by-id partition)
            # First establish our prior_redirect if it exists.
            # A redirect removal is indicated by '', so our prior_redirect
            # default is the same to aid comparison.
            if 'redirect' in roles:
                prior_redirect = roles['redirect']
            if new_redirect_role != prior_redirect:
                redirect_role_change = True
                if new_redirect_role != '':
                    # add or update our new redirect role
                    roles['redirect'] = new_redirect_role
                else:
                    # no redirect role requested (''), so remove if present
                    if 'redirect' in roles:
                        del roles['redirect']
            # Having now checked our new_redirect_role against the disks
            # prior redirect role we can perform validation tasks.
            if redirect_role_change:
                if is_delete_ticked:
                    # changing redirect and wiping concurrently are blocked
                    e_msg = ("Wiping a device while changing it's redirect "
                             "role is not supported. Please do one at a time")
                    raise Exception(e_msg)
                if is_luks_format_ticked:
                    # changing redirect and requesting LUKS format are blocked
                    e_msg = ("LUKS formating a device while changing it's "
                             "redirect role is not supported. Please do one "
                             "at a time")
                    raise Exception(e_msg)
                # We have a redirect role change and no delete or LUKS ticks so
                # return our dict back to a json format and stash in disk.role
                disk.role = json.dumps(roles)
                disk.save()
            else:
                # No redirect role change so we can wipe if requested by tick
                # but only if disk is not a pool member and no LUKS request
                # and we arn't trying to wipe an unlocked LUKS container or
                # one with an existing crypttab entry.
                if is_delete_ticked:
                    if disk.pool is not None:
                        # Disk is a member of a Rockstor pool so refuse to wipe
                        e_msg = ('Wiping a Rockstor pool member is '
                                 'not supported. Please use pool resize to '
                                 'remove this disk from the pool first.')
                        raise Exception(e_msg)
                    if is_luks_format_ticked:
                        # Simultaneous request to LUKS format and wipe.
                        # Best if we avoid combining wiping and LUKS format as
                        # although they are mostly equivalent this helps to
                        # keep these activities separated, which should help
                        # with future development and cleaner error reporting.
                        # I.e one thing at a time, especially if serious.
                        e_msg = ('Wiping a device while also requesting a '
                                 'LUKS format for the same device is not '
                                 'supported. Please do one at a time.')
                        raise Exception(e_msg)
                    if 'LUKS' in roles:
                        if 'unlocked' in roles['LUKS'] and \
                                roles['LUKS']['unlocked']:
                            e_msg = ('Wiping an unlocked LUKS container is '
                                     'not supported. Only locked LUKS '
                                     'containers can be wiped.')
                            raise Exception(e_msg)
                        if 'crypttab' in roles['LUKS']:
                            # The crypttab key itself is indication of an
                            # existing cryptab configuration
                            e_msg = ('Wiping a LUKS container with an '
                                     'existing /etc/crypttab entry is not '
                                     'supported. First ensure "Boot up '
                                     'configuration" of "No auto unlock."')
                            raise Exception(e_msg)
                    # Not sure if this is the correct way to call our wipe.
                    return self._wipe(dname, request)
                if is_luks_format_ticked:
                    if not luks_passwords_match:
                        # Simple password mismatch, should be caught by front
                        # end but we check as well
                        e_msg = ('LUKS format requested but passwords do not '
                                 'match. Aborting. Please try again.')
                        raise Exception(e_msg)
                    if luks_pass_one == '':
                        # Check of password = '', front end should
                        # filter this out but check anyway.
                        e_msg = ('LUKS passphase empty. Aborting. Please try '
                                 'again')
                        raise Exception(e_msg)
                    if len(luks_pass_one) < 14:
                        e_msg = ('LUKS passphrase of less then 14 characters'
                                 'is not supported. Please re-enter.')
                        raise Exception(e_msg)
                    if re.search('[^\x20-\x7E]', luks_pass_one) is not None:
                        e_msg = ('A LUKS passphrase containing non 7-bit '
                                 'ASCII(32-126) characters is not supported '
                                 'as boot entry character codes may differ. '
                                 'Please re-enter.')
                        raise Exception(e_msg)
                    if 'openLUKS' in roles:
                        e_msg = ('LUKS format requested but device is '
                                 'identified as an Open LUKS volume. This '
                                 'configuration is not supported.')
                        raise Exception(e_msg)
                    if 'LUKS' in roles:
                        e_msg = ('LUKS format requested but device is '
                                 'already LUKS formatted. If you wish to '
                                 're-deploy as a different LUKS container '
                                 'please select wipe first then return and '
                                 're-select LUKS format.')
                        raise Exception(e_msg)
                    return self._luks_format(dname, request, luks_pass_one)
            return Response(DiskInfoSerializer(disk).data)
        except Exception as e:
            e_msg = ('Failed to configure drive role, or wipe existing '
                     'filesystem, or do LUKS format on device (%s). Error: %s'
                     % (dname, e.__str__()))
            handle_exception(Exception(e_msg), request)

    @classmethod
    def _luks_disk(cls, dname, request):
        disk = cls._validate_disk(dname, request)
        crypttab_selection = str(
            request.data.get('crypttab_selection', 'false'))
        is_create_keyfile_ticked = request.data.get('create_keyfile_tick',
                                                    False)
        luks_passphrase = str(request.data.get('luks_passphrase', ''))
        # Constrain crypttab_selection to known sane entries
        # TODO: regex to catch legit dev names and sanitize via list match
        # known_crypttab_selection = ['false', 'none', '/dev/*']
        # Check that we are in fact a LUKS container.
        roles = {}
        # Get our roles, if any, into a dictionary.
        if disk.role is not None:
                roles = json.loads(disk.role)
        if 'LUKS' not in roles:
            e_msg = ('LUKS operation not support on this Disk(%s) as it is '
                     'not recognized as a LUKS container (ie no "LUKS" role '
                     'found.)'
                     % dname)
            handle_exception(Exception(e_msg), request)
        # Retrieve the uuid of our LUKS container.
        # Disk model currently only stores btrfs_uuid.
        luks_role = roles['LUKS']
        if 'uuid' not in luks_role:
            e_msg = ('Cannot complete LUKS configuration request as no uuid '
                     'key was found in Disk(%s) LUKS role value. ' % dname)
            handle_exception(Exception(e_msg), request)
        disk_uuid = luks_role['uuid']
        if crypttab_selection == 'none' or crypttab_selection == 'false':
            if is_create_keyfile_ticked:
                e_msg = ('Inconsistent LUKS configuration request for '
                         'Disk(%s). Keyfile creation requested without '
                         'compatible "Boot up configuratin" option'
                         % dname)
                handle_exception(Exception(e_msg), request)
        if is_create_keyfile_ticked and luks_passphrase == '':
            e_msg = ('Cannot create LUKS keyfile without authorization via '
                     'passphrase. Empty passphrase received for Disk(%s).'
                     % dname)
            handle_exception(Exception(e_msg), request)
        # Having performed the basic parameter validation above, we are ready
        # to try and apply the requested config. This is a multipart process.
        # With a keyfile config we have to first ensure the existence of our
        # keyfile and create it if need be, then register this keyfile (via
        # an existing passphrase) with our LUKS container.
        # In all cases there after we must also update /etc/crypttab.
        # Fist call our keyfile creation + register wrapper if needed:
        if crypttab_selection != 'none' and crypttab_selection != 'false':
            # None 'none' and None 'false' is assumed to be keyfile config.
            # We ensure / create our keyfile and register it using
            # cryptsetup luksAddKeyfile via the following wrapper function:
            if not establish_keyfile(disk.name, crypttab_selection,
                                     luks_passphrase):
                e_msg = ('There was an unknown problem with establish_keyfile '
                         'when called by _luks_disk() for Disk(%s). Keyfile '
                         'may not have been established.' % dname)
                handle_exception(Exception(e_msg), request)
        # In all cases we try to ensure /etc/crypttab is updated:
        if not update_crypttab(disk_uuid, crypttab_selection):
            e_msg = ('There was an unknown problem with update_crypttab when '
                     'called by _luks_disk() for Disk(%s). No /etc/crypttab '
                     'changes were made.' % dname)
            handle_exception(Exception(e_msg), request)
        return Response()

    @classmethod
    @transaction.atomic
    def _toggle_smart(cls, dname, request, enable=False):
        disk = cls._validate_disk(dname, request)
        if (not disk.smart_available):
            e_msg = ('S.M.A.R.T support is not available on this Disk(%s)'
                     % dname)
            handle_exception(Exception(e_msg), request)
        smart.toggle_smart(disk.name, disk.smart_options, enable)
        disk.smart_enabled = enable
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @classmethod
    def _blink_drive(cls, dname, request):
        disk = cls._validate_disk(dname, request)
        total_time = int(request.data.get('total_time', 90))
        blink_time = int(request.data.get('blink_time', 15))
        sleep_time = int(request.data.get('sleep_time', 5))
        blink_disk(disk.name, total_time, blink_time, sleep_time)
        return Response()

    @classmethod
    def _spindown_drive(cls, dname, request):
        disk = cls._validate_disk(dname, request)
        spindown_time = int(request.data.get('spindown_time', 20))
        spindown_message = str(
            request.data.get('spindown_message', 'message issue!'))
        apm_value = int(request.data.get('apm_value', 0))
        set_disk_spindown(disk.name, spindown_time, apm_value,
                          spindown_message)
        return Response()

    @classmethod
    def _pause(cls, dname, request):
        disk = cls._validate_disk(dname, request)
        enter_standby(disk.name)
        return Response()
