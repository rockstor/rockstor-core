"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import os
import re
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Disk, Pool, Share
from fs.btrfs import (
    enable_quota,
    mount_root,
    get_pool_info,
    get_pool_raid_levels,
    get_dev_pool_info,
    set_pool_label,
    get_devid_usage,
    get_pool_raid_profile,
)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from storageadmin.views.share_helpers import import_shares, import_snapshots
from django.conf import settings
import rest_framework_custom as rfc
from system import smart
from system.luks import (
    luks_format_disk,
    get_unlocked_luks_containers_uuids,
    get_crypttab_entries,
    update_crypttab,
    native_keyfile_exists,
    establish_keyfile,
    get_open_luks_volume_status,
    get_luks_container_uuid,
)
from system.osi import (
    set_disk_spindown,
    enter_standby,
    get_dev_byid_name,
    wipe_disk,
    blink_disk,
    scan_disks,
    get_byid_name_map,
    trigger_systemd_update,
    systemd_name_escape,
)
from system.services import systemctl
from copy import deepcopy
import uuid
import json
import logging

logger = logging.getLogger(__name__)

# Minimum disk size. Smaller disks will be ignored. Recommended minimum = 16 GiB.
# Btrfs works in chunks (units) of 1 GiB for data, and 256 MiB for metadata.
# Using very small disks requires mixed data/metadata chunks of 256 MiB.
# If a device is less than 16 GiB, the mixed (--mixed) mode is recommended.
# https://btrfs.wiki.kernel.org/index.php/FAQ
# https://btrfs.wiki.kernel.org/index.php/Glossary
# Rockstor does not enforce --mixed for any drive size.
# 5 GiB = (5 * 1024 * 1024) = 5242880 KiB
MIN_DISK_SIZE = 5242880

# A list of scan_disks() assigned roles: ie those that can be identified from
# the output of lsblk with the following switches:
# -P -p -o NAME,MODEL,SERIAL,SIZE,TRAN,VENDOR,HCTL,TYPE,FSTYPE,LABEL,UUID
# and the post processing present in scan_disks()
# LUKS currently stands for full disk crypto container.
SCAN_DISKS_KNOWN_ROLES = [
    "mdraid",
    "root",
    "LUKS",
    "openLUKS",
    "bcache",
    "bcachecdev",
    "partitions",
    "LVM2member",
]
WHOLE_DISK_FORMAT_ROLES = ["LUKS", "bcache", "bcachecdev", "LVM2member"]


class DiskMixin(object):
    serializer_class = DiskInfoSerializer

    @staticmethod
    @transaction.atomic
    def _update_disk_state():
        """
        A DB atomic method to update the database from attached disks / drives.
        Works only on device serial for drive identification.
        Calls scan_disks() to establish the current connected drives info.
        Initially removes duplicate by serial DB entries to deal
        with legacy DB states and obfuscates all previous device names as they
        are transient. The drive database is then updated with the attached
        disks info and previously known drives no longer found attached are
        marked as offline. All offline drives have their SMART availability and
        activation status removed and all attached drives have their SMART
        availability assessed and activated if available.
        :return: serialized models of attached and missing disks via serial num
        """
        attached_disks = scan_disks(MIN_DISK_SIZE)
        all_attached_serials: list[str] = [d.serial for d in attached_disks]
        # Acquire a list of uuid's for currently unlocked LUKS containers.
        # Although we could tally these as we go by noting fstype crypt_LUKS
        # and then loop through our DB Disks again updating all matching
        # base device entries, this approach helps to abstract this component
        # and to localise role based DB manipulations to our second loop.
        unlocked_luks_containers_uuids = get_unlocked_luks_containers_uuids()
        db_serial_numbers_seen = []
        # Acquire a dictionary of crypttab entries, dev uuid as indexed.
        dev_uuids_in_crypttab = get_crypttab_entries()
        # Acquire a dictionary of temp_names (no path) to /dev/disk/by-id names
        byid_name_map = get_byid_name_map()
        # Make sane our DB entries in view of attached_disks.
        # Device serial is only-known external unique entity, scan_disks()
        # retrieves & reports these where possible, but otherwise substitutes a
        # fake-serial-* as a flag for the WebUI to indicate an un-trackable disk.
        # 1) Replace all device names with detached-uuid4: until established otherwise.
        # 2) Mark all offline disks as such via DB flag.
        # 3) Mark all offline disks smart available and enabled flags as False.
        for db_disk in Disk.objects.all():
            # Replace all device names with a unique placeholder on each scan.
            # N.B. do not optimize by re-using uuid index as this could lead
            # to a non refreshed WebUi acting upon an entry that is different
            # from that shown to the user.
            db_disk.name = "detached-" + str(uuid.uuid4()).replace("-", "")
            db_disk.save(update_fields=["name"])
            # Delete duplicate or fake by serial DB disk entries.
            # It makes no sense to save DB entries with fake serials between scans
            # as on each scan the serial is re-generated (fake) anyway.
            # Serials beginning with 'fake-serial-' are from scan_disks().
            if (
                (db_disk.serial in db_serial_numbers_seen)
                or (db_disk.serial is None)
                or (re.match("fake-serial-", db_disk.serial) is not None)
            ):
                logger.info(
                    "Deleting duplicate or fake (by serial) disk DB entry. "
                    f"Serial = ({db_disk.serial})."
                )
                db_disk.delete()
                continue
            db_serial_numbers_seen.append(deepcopy(db_disk.serial))
            if db_disk.serial not in all_attached_serials:
                db_disk.offline = True
                db_disk.smart_available = db_disk.smart_enabled = False
            db_disk.save()  # make sure all updates are flushed to DB
        # Our DB now has no device name info: all dev names are detached-uuid4 placeholders.
        # Iterate over attached drives to update the DB accordingly.
        # Get temp_name (kernel dev names) to btrfs pool info for all attached.
        dev_pool_info = get_dev_pool_info()
        for attached in attached_disks:
            pool_name = None  # Until we find otherwise.
            non_scan_disks_roles = {}
            disk_roles_identified = {}
            # Convert our transient, but just scanned so current, sda type name
            # to a more useful by-id type name as found in /dev/disk/by-id.
            # Note path is removed as we store, ideally, byid in DB Disk.name.
            byid_disk_name, is_byid = get_dev_byid_name(attached.name, remove_path=True)
            # Use an existing DB entry if attached serial match exists.
            if Disk.objects.filter(serial=attached.serial).exists():
                dob = Disk.objects.get(serial=attached.serial)
                dob.name = byid_disk_name
                dob.save(update_fields=["name"])
            else:
                dob = Disk(name=byid_disk_name, serial=attached.serial, role=None)
            dob.size = attached.size
            dob.parted = attached.parted
            dob.offline = False  # as we are iterating over attached devices
            dob.model = attached.model
            dob.transport = attached.transport
            dob.vendor = attached.vendor
            # N.B. The Disk.btrfs_uuid is in some senses becoming misleading
            # as we begin to deal with Disk.role managed drives such as mdraid
            # members and full disk LUKS drives where we make use of
            # non btrfs uuids to track filesystems or LUKS containers.
            # Leaving as-is to avoid Disk DB field name changes.
            # Used within Web-UI front-end via Handlebars Helper
            # ('isNullPoolBtrfs', function (btrfsUid, poolName) to inform:
            # import icon / existing unmanaged pool association.
            dob.btrfs_uuid = attached.uuid

            if attached.fstype == "btrfs":
                # Find pool association, if any, of attached disk
                # Use canonical 'btrfs fi show' source via get_dev_pool_info()
                dev_name = attached.name
                if attached.partitions != {}:  # could have btrfs fs from a partition?
                    # d.partitions={'/dev/vdc1': 'vfat', '/dev/vdc2': 'btrfs'}
                    for partition, fs in iter(attached.partitions.items()):
                        if fs == "btrfs":  # We only allow one btrfs part / dev
                            dev_name = partition
                            if attached.root:  # btrfs-in-partition, on system disk:
                                part_byid_name, is_byid = get_dev_byid_name(
                                    partition, True
                                )
                                if is_byid:
                                    disk_roles_identified["redirect"] = part_byid_name
                            break
                pool_info = dev_pool_info[dev_name]
                # TODO: pool_info.uuid should be canonical: not pool_info.label
                #  As we move to this posture the following will need attention.
                #  And we already have btrfs uuid from attached.uuid.
                pool_name = pool_info.label
                # TODO: First call we reset none pool label member-count times!
                # Corner case but room for efficiency improvement.
                # Consider building a list of pools relabeled to address issue.
                # N.B. 'system' for early source to rpm installs - openSUSE
                if pool_name == "none" or pool_name == "system":
                    pool_name = set_pool_label(pool_info.uuid, dev_name, attached.root)
                # Update our disk database entry with btrfs specific data.
                dob.devid = pool_info.devid
                dob.size = pool_info.size
                dob.allocated = pool_info.allocated
            dob.save()

            # ### BEGINNING OF ROLE FIELD UPDATE ###
            # Update the role field with scan_disks() findings.
            # SCAN_DISKS_KNOWN_ROLES a list of scan_disks() identifiable roles.
            # First extract all non scan_disks() assigned roles so we can add
            # them back later; all scan_disks() assigned roles will be identified
            # from our recent scan_disks() data so we assert as truth.
            if dob.role is not None:  # DB default null=True so None here.
                # Get our previous roles into a dictionary
                previous_roles = json.loads(dob.role)
                # Preserve non scan_disks() identified roles for this DB entry
                non_scan_disks_roles = {
                    role: v
                    for role, v in previous_roles.items()
                    if role not in SCAN_DISKS_KNOWN_ROLES
                }
            match attached.fstype:
                case "crypto_LUKS":  # LUKS FULL DISK container:
                    # On creation these have a unique uuid.
                    # Stash this uuid so we might later work out our
                    # container mapping. Currently required as only btrfs uuids
                    # are stored in the Disk model field. Also flag if we are the
                    # container for a currently open LUKS volume.
                    is_unlocked = attached.uuid in unlocked_luks_containers_uuids
                    disk_roles_identified["LUKS"] = {
                        "uuid": str(attached.uuid),
                        "unlocked": is_unlocked,
                    }
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
                    if attached.uuid in dev_uuids_in_crypttab.keys():
                        # Our device has a UUID= match in crypttab so save as
                        # value the current cryptfile 3rd column entry.
                        disk_roles_identified["LUKS"][
                            "crypttab"
                        ] = dev_uuids_in_crypttab[attached.uuid]
                        # if crypttab 3rd column indicates keyfile: does that
                        # keyfile exist. N.B. non 'none' entry assumed to be
                        # keyfile. Allows for existing user created keyfiles.
                        # TODO: could be problematic during crypttab rewrite where
                        # keyfile is auto named but we should self correct on our
                        # next run, ie new file entry is checked there after.
                        if dev_uuids_in_crypttab[attached.uuid] != "none":
                            disk_roles_identified["LUKS"][
                                "keyfileExists"
                            ] = os.path.isfile(dev_uuids_in_crypttab[attached.uuid])
                    if "keyfileExists" not in disk_roles_identified["LUKS"]:
                        # We haven't yet set our keyfileExists flag: ie no entry,
                        # custom or otherwise, in crypttab to check or the entry
                        # was "none". Revert to defining this flag against the
                        # existence or otherwise of our native keyfile:
                        disk_roles_identified["LUKS"][
                            "keyfileExists"
                        ] = native_keyfile_exists(attached.uuid)
                case "bcache":  # bcache "backing devices" avoidance role.
                    # Once formatted with make-bcache -B they are accessed via a virtual
                    # device which should end up with a serial of bcache-(d.uuid)
                    # Tag our backing device with its virtual counterparts serial.
                    disk_roles_identified["bcache"] = "bcache-%s" % attached.uuid
                case "bcachecdev":  # bcache cache device
                    disk_roles_identified["bcachecdev"] = "bcache-%s" % attached.uuid
                case "isw_raid_member" | "linux_raid_member":
                    disk_roles_identified["mdraid"] = str(attached.fstype)
                case "LVM2_member":  # Use avoidance role: value is placeholder and unused.
                    disk_roles_identified["LVM2member"] = str(attached.fstype)
            if (
                attached.type == "crypt"
            ):  # OPEN LUKS DISK: opened LUKS containers appears as mapped dev.
                luks_volume_status = get_open_luks_volume_status(attached.name, byid_name_map)
                disk_roles_identified["openLUKS"] = luks_volume_status
            if attached.root is True:
                # ROOT DISK: scan_disks() has already identified the current
                # truth regarding the device hosting our root '/' mount.
                # N.B. the value of d.fstype here is unused.
                # The presence or otherwise of the 'root' key is all we need.
                disk_roles_identified["root"] = str(attached.fstype)
            if attached.partitions != {}:
                # PARTITIONS: scan_disks() has built an updated partitions dict
                # so create a partitions role containing this dictionary.
                # Convert scan_disks() transient (but just scanned so current)
                # sda type names to a more useful by-id type name as found
                # in /dev/disk/by-id for each partition name.
                byid_partitions = {
                    get_dev_byid_name(part, True)[0]: attached.partitions.get(part, "")
                    for part in attached.partitions
                }
                # In the above we fail over to "" on failed index for now.
                disk_roles_identified["partitions"] = byid_partitions
            # Join the saved non scan_disks() identified roles dict with those
            # we have just identified/updated from our fresh scan_disks() run.
            # Return the combination to our DB entry in json format.
            # Note that dict of {} isn't None
            if (non_scan_disks_roles != {}) or (disk_roles_identified != {}):
                combined_roles = dict(non_scan_disks_roles, **disk_roles_identified)
                dob.role = json.dumps(combined_roles)
            else:
                dob.role = None
            dob.save(update_fields=["role"])
            # ### END OF ROLE FIELD UPDATE ###

            # Does our existing DB know of this disks' established pool association?
            # Quick 'not None' test first to avoid redundant lengthy DB filter.
            if pool_name is not None and Pool.objects.filter(name=pool_name).exists():
                # update the Disk DB object's pool field accordingly.
                dob.pool = Pool.objects.get(name=pool_name)
                # this is for backwards compatibility. root pools created
                # before the pool.role migration need this. It can safely be
                # removed a few versions after 3.8-11 or when we reset
                # migrations.
                if attached.root is True:
                    dob.pool.role = "root"
                    dob.pool.save()
            else:  # DB Disk not member of Rockstor Managed Pool via get_dev_pool_info()
                # N.B. dob.btrfs_uuid unaltered as Web-UI indicator of existing btrfs.
                dob.devid = 0
                dob.allocated = 0
                dob.pool = None
            dob.save()
        # Update online DB entries with S.M.A.R.T availability and status.
        for db_disk in Disk.objects.all():
            if not db_disk.offline:
                if (re.match("fake-serial-", db_disk.serial) is not None) or (
                    re.match("virtio-|md-|mmc-|nvme-|dm-name-luks-|bcache|nbd", db_disk.name)
                    is not None
                ):
                    # Fake serial ignored as unreliable dev name.
                    # Also note that with no serial, some device types will
                    # not have a by-id type name: expected by the smart subsystem.
                    # Virtio, md, and sdcards, have no smart capability: avoid logs spam.
                    # Nvme was previously now supported by smartmontools.
                    db_disk.smart_available = db_disk.smart_enabled = False
                    continue
                # try to establish smart availability and status and update DB
                try:
                    # for non ata/sata drives
                    db_disk.smart_available, db_disk.smart_enabled = smart.available(
                        db_disk.name, db_disk.smart_options
                    )
                except Exception as e:
                    logger.exception(e)
                    db_disk.smart_available = db_disk.smart_enabled = False
            else:  # We have offline / detached Disk DB entries.
                # Update detached disks previously know to a pool i.e. missing.
                # After a reboot device name is lost and replaced by 'missing'
                # so we compare via btrfs devid stored prior to detached state.
                # N.B. potential flag mechanism to denote required reboot if
                # missing device has non-existent dev entry rather than missing
                # otherwise remove missing / detached fails with:
                # "no missing devices found to remove".
                # Suspect this will be fixed in future btrfs variants.
                if db_disk.pool is not None and db_disk.pool.is_mounted:
                    mnt_pt = f"{settings.MNT_PT}{db_disk.pool.name}"
                    devid_usage = get_devid_usage(mnt_pt)
                    if db_disk.devid in devid_usage:
                        dev_info = devid_usage[db_disk.devid]
                        db_disk.size = dev_info.size
                        db_disk.allocated = dev_info.allocated
                    else:
                        # Our device has likely been removed from this pool:
                        # its devid no longer shows up in its associated pool.
                        # Reset all btrfs related elements for disk DB object:
                        db_disk.pool = None
                        db_disk.btrfs_uuid = None
                        db_disk.devid = 0  # DB default and int flag for None.
                        db_disk.allocated = 0  # No devid_usage = no allocation.
            db_disk.save()
        ds = DiskInfoSerializer(Disk.objects.all().order_by("name"), many=True)
        return Response(ds.data)


class DiskListView(DiskMixin, rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            return Disk.objects.all().order_by("name")

    def post(self, request, command, did=None):
        with self._handle_exception(request):
            if command == "scan":
                return self._update_disk_state()

        e_msg = "Unsupported command ({}).".format(command)
        handle_exception(Exception(e_msg), request)


class DiskDetailView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    @staticmethod
    def _validate_disk(did, request):
        try:
            return Disk.objects.get(id=did)
        except:
            e_msg = "Disk id ({}) does not exist.".format(did)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _role_filter_disk_name(disk, request):
        """
        Takes a disk object and filters it based on it's roles.
        If disk has a redirect role the redirect role value is substituted
        for that disk's name. This effects a device name re-direction:
        ie base dev to partition on base dev for example.
        N.B. Disk model now has sister code under Disk.target_name property.
        :param disk:  disk object
        :param request:
        :return: by-id disk name (without path) post role filter processing
        """
        # TODO: Consider revising to use new Disk.target_name property.
        try:
            disk_name = disk.name
            if disk.role is not None:
                disk_role_dict = json.loads(disk.role)
                if "redirect" in disk_role_dict:
                    disk_name = disk_role_dict.get("redirect", None)
            return disk_name
        except:
            e_msg = "Problem with role filter of disk ({}).".format(disk.name)
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
            fields = disk_name.split("-")
            # check the last field for part#
            if len(fields) > 0:
                if re.match("part.+", fields[-1]) is not None:
                    isPartition = True
                    # strip the redirection to partition device.
                    return "-".join(fields[:-1]), isPartition
            # we have found no indication of redirect role name changes.
            return disk_name, isPartition
        except:
            e_msg = ("Problem reversing role filter disk name ({}).").format(disk_name)
            handle_exception(Exception(e_msg), request)

    def get(self, *args, **kwargs):
        if "did" in self.kwargs:
            try:
                data = Disk.objects.get(id=self.kwargs["did"])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()

    @transaction.atomic
    def delete(self, request, did):
        try:
            disk = Disk.objects.get(id=did)
        except:
            e_msg = "Disk id ({}) does not exist.".format(did)
            handle_exception(Exception(e_msg), request)

        if disk.offline is not True:
            e_msg = ("Disk ({}) is not offline. Cannot delete.").format(disk.name)
            handle_exception(Exception(e_msg), request)

        try:
            disk.delete()
            return Response()
        except Exception as e:
            e_msg = ("Could not remove disk ({}) due to a system error.").format(
                disk.name
            )
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    def post(self, request, did, command):
        with self._handle_exception(request):
            if command in ("wipe", "btrfs-wipe"):
                return self._wipe(did, request)
            if command == "luks-format":
                return self._luks_format(did, request, passphrase="")
            if command == "btrfs-disk-import":
                return self._btrfs_disk_import(did, request)
            if command == "blink-drive":
                return self._blink_drive(did, request)
            if command == "enable-smart":
                return self._toggle_smart(did, request, enable=True)
            if command == "disable-smart":
                return self._toggle_smart(did, request)
            if command == "smartcustom-drive":
                return self._smartcustom_drive(did, request)
            if command == "spindown-drive":
                return self._spindown_drive(did, request)
            if command == "pause":
                return self._pause(did, request)
            if command == "role-drive":
                return self._role_disk(did, request)
            if command == "luks-drive":
                return self._luks_disk(did, request)

        e_msg = (
            "Unsupported command ({}). Valid commands are; wipe, "
            "btrfs-wipe, luks-format, btrfs-disk-import, blink-drive, "
            "enable-smart, disable-smart, smartcustom-drive, "
            "spindown-drive, pause, role-drive, "
            "luks-drive."
        ).format(command)
        handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _wipe(self, did, request):
        disk = self._validate_disk(did, request)
        disk_name = self._role_filter_disk_name(disk, request)
        # Double check sanity of role_filter_disk_name by reversing back to
        # whole disk name (db name). Also we get isPartition in the process.
        reverse_name, isPartition = self._reverse_role_filter_name(disk_name, request)
        if reverse_name != disk.name:
            e_msg = (
                "Wipe operation on whole or partition of device ({}) was "
                "rejected as there was a discrepancy in device name "
                "resolution. Wipe was called with device name ({}) which "
                "redirected to ({}) but a check on this redirection "
                "returned device name ({}), which is not equal to the "
                "caller name as was expected. A Disks page Rescan may "
                "help."
            ).format(disk.name, disk.name, disk_name, reverse_name)
            raise Exception(e_msg)
        wipe_disk(disk_name)
        disk.parted = isPartition
        # Rather than await the next _update_disk_state() we update our role.
        roles = {}
        # Get our roles, if any, into a dictionary.
        if disk.role is not None:
            roles = json.loads(disk.role)
        if isPartition:
            # Special considerations for partitioned devices.
            # Be sure to clear our fstype from the partition role dictionary.
            if "partitions" in roles:  # just in case
                if disk_name in roles["partitions"]:
                    roles["partitions"][disk_name] = ""
        else:  # Whole disk wipe considerations:
            # In the case of Open LUKS Volumes, whenever a whole disk file
            # system is wiped as we have just done. The associated systemd
            # service /var/run/systemd/generator/systemd-cryptsetup@
            # <mapper-name>.service runs systemd-cryptsetup detach mapper-name.
            # Where mapper-name = first column in /etc/crypttab = by-id name
            # without the additional "dm-name-".
            # This results in the removal of the associated block devices.
            # So we need to start the associated service which in turn will
            # attach the relevant block mappings. This action requires
            # re-authentication via existing keyfile or via local console.
            if "openLUKS" in roles:
                if re.match("dm-name", disk_name) is not None:
                    mapper_name = disk_name[8:]
                    service_name = systemd_name_escape(
                        mapper_name, "systemd-cryptsetup@.service"
                    )
                    service_path = "/var/run/systemd/generator/"
                    if service_name != "" and os.path.isfile(
                        service_path + service_name
                    ):
                        # Start our devs cryptsetup service to re-establish
                        # it's now removed (by systemd) /dev nodes.
                        # This action is only possible with an existing
                        # crypttab entry, ie none or keyfile; but only
                        # a keyfile config will allow non interactive
                        # re-activation.
                        out, err, rc = systemctl(service_name, "start")
                        if rc != 0:
                            e_msg = (
                                "Systemd cryptsetup start after a "
                                "wipefs -a for Open LUKS Volume device "
                                "({}) encountered an error: out={}, "
                                "err={}, rc={}."
                            ).format(disk_name, out, err, rc)
                            raise Exception(e_msg)
            # Wiping a whole disk will remove all whole disk formats: ie LUKS
            # containers and bcache backing and caching device formats.
            # So remove any pertinent role if it exists
            for whole_role in WHOLE_DISK_FORMAT_ROLES:
                if whole_role in roles:
                    del roles[whole_role]
            # Wiping a whole disk will also remove all partitions:
            if "partitions" in roles:
                del roles["partitions"]
        # now we return our potentially updated roles
        if roles == {}:
            # if we have an empty role dict then we avoid json conversion and
            # go with re-asserting db default.
            disk.role = None
        else:
            disk.role = json.dumps(roles)
        # The following value may well be updated with a more informed truth
        # from the next scan_disks() run via _update_disk_state(). Since we
        # only allow redirect to a btrfs partition, if one exist, then we can
        # be assured that any redirect role would be to an existing btrfs. So
        # either way (partitioned or not) we have just wiped any btrfs so we
        # universally remove the btrfs_uuid.
        disk.btrfs_uuid = None
        disk.devid = 0
        disk.allocated = 0
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _luks_format(self, did, request, passphrase):
        disk = self._validate_disk(did, request)
        disk_name = self._role_filter_disk_name(disk, request)
        # Double check sanity of role_filter_disk_name by reversing back to
        # whole disk name (db name). Also we get isPartition in the process.
        reverse_name, isPartition = self._reverse_role_filter_name(disk_name, request)
        if reverse_name != disk.name:
            e_msg = (
                "LUKS operation on whole or partition of device ({}) was "
                "rejected as there was a discrepancy in device name "
                "resolution. _make_luks was called with device name ({}) "
                "which redirected to ({}) but a check on this redirect "
                "returned device name ({}), which is not equal to the "
                "caller name as was expected. A Disks page Rescan may "
                "help."
            ).format(disk.name, disk.name, disk_name, reverse_name)
            raise Exception(e_msg)
        # Check if we are a partition as we don't support LUKS in partition.
        # Front end should filter this out, but be should block at this level as well.
        if isPartition:
            e_msg = (
                "A LUKS format was requested on device name ({}) which "
                "was identifyed as a partiton. Rockstor does not "
                "support LUKS in partition, "
                "only whole disk."
            ).format(disk.name)
            raise Exception(e_msg)
        luks_format_disk(disk_name, passphrase)
        disk.parted = isPartition  # should be False by now.
        # The following values may well be updated with a more informed truth
        # from the next scan_disks() run via _update_disk_state()
        disk.btrfs_uuid = None
        disk.devid = 0
        disk.allocated = 0
        # Rather than await the next _update_disk_state() we populate our
        # LUKS container role.
        roles = {}
        # Get our roles, if any, into a dictionary.
        if disk.role is not None:
            roles = json.loads(disk.role)
        # Now we assert what we know given our above LUKS format operation.
        # Not unlocked and no keyfile (as we have a fresh uuid from format)
        dev_uuid = get_luks_container_uuid(disk.name)
        # update or create a basic LUKS role entry.
        # Although we could use native_keyfile_exists(dev_uuid) we can be
        # pretty sure there is no keyfile with our new uuid.
        roles["LUKS"] = {
            "uuid": str(dev_uuid),
            "unlocked": False,
            "keyfileExists": False,
        }
        # now we return our updated roles
        disk.role = json.dumps(roles)
        disk.save(update_fields=["parted", "btrfs_uuid", "devid", "allocated", "role"])
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _smartcustom_drive(self, did, request):
        disk = self._validate_disk(did, request)
        # TODO: Check on None, null, or '' for default in next command
        custom_smart_options = str(request.data.get("smartcustom_options", ""))
        # strip leading and trailing white space chars before entry in db
        disk.smart_options = custom_smart_options.strip()
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _btrfs_disk_import(self, did, request):
        try:
            disk = self._validate_disk(did, request)
            disk_name = self._role_filter_disk_name(disk, request)
            p_info = get_pool_info(disk_name)
            # Create our initial pool object, default to no compression.
            po = Pool(
                name=p_info["label"],
                raid="unknown",
                compression="no",
                uuid=p_info["uuid"],
            )
            # need to save it so disk objects get updated properly in the for
            # loop below.
            po.save()
            # p_info['disks'] = by_id name indexed dict with named tuple values
            for device in p_info["disks"]:
                # Database uses base dev names in by-id format: acquire via;
                disk_name, isPartition = self._reverse_role_filter_name(device, request)
                # All bar system disk are stored in db as base byid name,
                # a partition, if used, is then held in a redirect role.
                # System's partition name is considered it's base name; but
                # we don't have to import our system pool.
                do = Disk.objects.get(name=disk_name)
                do.pool = po
                # Update this disk's parted, devid, and used properties.
                do.parted = isPartition
                do.devid = p_info["disks"][device].devid
                do.size = p_info["disks"][device].size
                do.allocated = p_info["disks"][device].allocated
                if isPartition:
                    # ensure a redirect role to reach this partition; ie:
                    # "redirect": "virtio-serial-3-part2"
                    if do.role is not None:  # db default is null / None.
                        # Get our previous roles into a dictionary
                        roles = json.loads(do.role)
                        # update or add our "redirect" role with our part name
                        roles["redirect"] = "%s" % device
                        # convert back to json and store in disk object
                        do.role = json.dumps(roles)
                    else:
                        # role=None so just add a json formatted redirect role
                        do.role = '{"redirect": "%s"}' % device.name
                do.save()
                mount_root(po)
            pool_raid_info = get_pool_raid_levels(
                "{}{}".format(settings.MNT_PT, po.name)
            )
            po.raid = get_pool_raid_profile(pool_raid_info)
            po.size = po.usage_bound()
            po.save()
            enable_quota(po)
            import_shares(po, request)
            for share in Share.objects.filter(pool=po):
                import_snapshots(share)
            return Response(DiskInfoSerializer(disk).data)
        except Exception as e:
            e_msg = (
                "Failed to import any pool on device db id ({}). Error: ({})."
            ).format(did, e.__str__())
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _role_disk(self, did, request):
        """
        Resets device role db entries and wraps _wipe() but will only call
        _wipe() if no redirect role changes are also requested. If we fail
        to associate these 2 tasks then there is a risk of the redirect not
        coming into play prior to the wipe.
        :param did: disk id
        :param request:
        :return:
        """
        # Until we find otherwise:
        prior_redirect = ""
        redirect_role_change = False
        luks_passwords_match = False
        try:
            disk = self._validate_disk(did, request)
            # We can use this disk name directly as it is our db reference
            # no need to user _role_filter_disk_name as we only want to change
            # the db fields anyway.
            # And when we call _wipe() it honours any existing redirect role
            # so we make sure to not wipe and redirect at the same time.
            new_redirect_role = str(request.data.get("redirect_part", ""))
            is_delete_ticked = request.data.get("delete_tick", False)
            is_luks_format_ticked = request.data.get("luks_tick", False)
            luks_pass_one = str(request.data.get("luks_pass_one", ""))
            luks_pass_two = str(request.data.get("luks_pass_two", ""))
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
            if "redirect" in roles:
                prior_redirect = roles["redirect"]
            if new_redirect_role != prior_redirect:
                redirect_role_change = True
                if new_redirect_role != "":
                    # add or update our new redirect role
                    roles["redirect"] = new_redirect_role
                else:
                    # no redirect role requested (''), so remove if present
                    if "redirect" in roles:
                        del roles["redirect"]
            # Having now checked our new_redirect_role against the disks
            # prior redirect role we can perform validation tasks.
            if redirect_role_change:
                if is_delete_ticked:
                    # changing redirect and wiping concurrently are blocked
                    e_msg = (
                        "Wiping a device while changing it's redirect "
                        "role is not supported. Please do one at a time."
                    )
                    raise Exception(e_msg)
                if is_luks_format_ticked:
                    # changing redirect and requesting LUKS format are blocked
                    e_msg = (
                        "LUKS formating a device while changing it's "
                        "redirect role is not supported. Please do one "
                        "at a time."
                    )
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
                        e_msg = (
                            "Wiping a Rockstor pool member is "
                            "not supported. Please use pool resize to "
                            "remove this disk from the pool first."
                        )
                        raise Exception(e_msg)
                    if is_luks_format_ticked:
                        # Simultaneous request to LUKS format and wipe.
                        # Best if we avoid combining wiping and LUKS format as
                        # although they are mostly equivalent this helps to
                        # keep these activities separated, which should help
                        # with future development and cleaner error reporting.
                        # I.e one thing at a time, especially if serious.
                        e_msg = (
                            "Wiping a device while also requesting a "
                            "LUKS format for the same device is not "
                            "supported. Please do one at a time."
                        )
                        raise Exception(e_msg)
                    if "LUKS" in roles:
                        if "unlocked" in roles["LUKS"] and roles["LUKS"]["unlocked"]:
                            e_msg = (
                                "Wiping an unlocked LUKS container is "
                                "not supported. Only locked LUKS "
                                "containers can be wiped."
                            )
                            raise Exception(e_msg)
                        if "crypttab" in roles["LUKS"]:
                            # The crypttab key itself is indication of an
                            # existing cryptab configuration
                            e_msg = (
                                "Wiping a LUKS container with an "
                                "existing /etc/crypttab entry is not "
                                'supported. First ensure "Boot up '
                                'configuration" of "No auto unlock."'
                            )
                            raise Exception(e_msg)
                    # Not sure if this is the correct way to call our wipe.
                    return self._wipe(disk.id, request)
                if is_luks_format_ticked:
                    if not luks_passwords_match:
                        # Simple password mismatch, should be caught by front
                        # end but we check as well
                        e_msg = (
                            "LUKS format requested but passwords do not "
                            "match. Aborting. Please try again."
                        )
                        raise Exception(e_msg)
                    if luks_pass_one == "":
                        # Check of password = '', front end should
                        # filter this out but check anyway.
                        e_msg = "LUKS passphase empty. Aborting. Please try again."
                        raise Exception(e_msg)
                    if len(luks_pass_one) < 14:
                        e_msg = (
                            "LUKS passphrase of less then 14 characters "
                            "is not supported. Please re-enter."
                        )
                        raise Exception(e_msg)
                    if re.search("[^\x20-\x7E]", luks_pass_one) is not None:
                        e_msg = (
                            "A LUKS passphrase containing non 7-bit "
                            "ASCII (32-126) characters is not supported "
                            "as boot entry character codes may differ. "
                            "Please re-enter."
                        )
                        raise Exception(e_msg)
                    if "openLUKS" in roles:
                        e_msg = (
                            "LUKS format requested but device is "
                            "identified as an Open LUKS volume. This "
                            "configuration is not supported."
                        )
                        raise Exception(e_msg)
                    if "LUKS" in roles:
                        e_msg = (
                            "LUKS format requested but device is "
                            "already LUKS formatted. If you wish to "
                            "re-deploy as a different LUKS container "
                            "please select wipe first then return and "
                            "re-select LUKS format."
                        )
                        raise Exception(e_msg)
                    if "LVM2member" in roles:
                        # shouldn't happen but guard against it anyway.
                        e_msg = (
                            "LUKS format requested on an LVM2 member. "
                            "Please first wipe this device."
                        )
                        raise Exception(e_msg)
                    return self._luks_format(disk.id, request, luks_pass_one)
            return Response(DiskInfoSerializer(disk).data)
        except Exception as e:
            e_msg = (
                "Failed to configure drive role, or wipe existing "
                "filesystem, or do LUKS format on device id ({}). "
                "Error: ({})."
            ).format(did, e.__str__())
            handle_exception(Exception(e_msg), request)

    @classmethod
    @transaction.atomic
    def _luks_disk(cls, did, request):
        disk = cls._validate_disk(did, request)
        crypttab_selection = str(request.data.get("crypttab_selection", "false"))
        is_create_keyfile_ticked = request.data.get("create_keyfile_tick", False)
        luks_passphrase = str(request.data.get("luks_passphrase", ""))
        # Constrain crypttab_selection to known sane entries
        # TODO: regex to catch legit dev names and sanitize via list match
        # known_crypttab_selection = ['false', 'none', '/dev/*']
        # Check that we are in fact a LUKS container.
        roles = {}
        # Get our roles, if any, into a dictionary.
        if disk.role is not None:
            roles = json.loads(disk.role)
        if "LUKS" not in roles:
            e_msg = (
                "LUKS operation not support on this disk ({}) as it is "
                'not recognized as a LUKS container (ie no "LUKS" role '
                "found)."
            ).format(disk.name)
            handle_exception(Exception(e_msg), request)
        # Retrieve the uuid of our LUKS container.
        if "uuid" not in roles["LUKS"]:
            e_msg = (
                "Cannot complete LUKS configuration request as no uuid "
                "key was found in disk ({}) LUKS "
                "role value."
            ).format(disk.name)
            handle_exception(Exception(e_msg), request)
        disk_uuid = roles["LUKS"]["uuid"]
        # catch create keyfile without pass request (shouldn't happen)
        if is_create_keyfile_ticked and luks_passphrase == "":
            e_msg = (
                "Cannot create LUKS keyfile without authorization via "
                "passphrase. Empty passphrase received for "
                "disk ({})."
            ).format(disk.name)
            handle_exception(Exception(e_msg), request)
        # catch keyfile request without compatible "Boot up config" selection.
        if crypttab_selection == "none" or crypttab_selection == "false":
            if is_create_keyfile_ticked:
                e_msg = (
                    "Inconsistent LUKS configuration request for "
                    "disk ({}). Keyfile creation requested without "
                    'compatible "Boot up configuration" '
                    "option."
                ).format(disk.name)
                handle_exception(Exception(e_msg), request)
        # Having performed the basic parameter validation above, we are ready
        # to try and apply the requested config. This is a multipart process.
        # With a keyfile config we have to first ensure the existence of our
        # keyfile and create it if need be, then register this keyfile (via
        # an existing passphrase) with our LUKS container if the keyfile is
        # newly created (handled by establish_keyfile().
        # In almost all cases there after we must also update /etc/crypttab.
        # Setup helper flags
        # The source of true re current state is our roles['LUKS'] value
        # having been updated via _update_disk_state() so we can see if a
        # custom keyfile config exists to inform our actions here.
        custom_keyfile = False
        if "crypttab" in roles["LUKS"]:
            role_crypttab = roles["LUKS"]["crypttab"]
            if (
                role_crypttab != "none"
                and role_crypttab != "/root/keyfile-%s" % disk_uuid
            ):
                custom_keyfile = True
        if crypttab_selection != "none" and crypttab_selection != "false":
            # None 'none' and None 'false' is assumed to be keyfile config.
            # We ensure / create our keyfile and register it using
            # cryptsetup luksAddKeyfile:
            # With the following exception. Our current UI layer has no
            # custom keyfile option, although it does recognize this state and
            # indicates it to the user. But it still sends the native keyfile
            # crypttab_selection value. So here we guard against overwriting
            # a custom keyfile config if one is found, which in turn allows
            # a user to "Submit" harmlessly an existing custom config whilst
            # also requiring a definite re-configuration to remove an existing
            # custom config. I.e. the selection of 'none' or 'false' first.
            # Fist call our keyfile creation + register wrapper if needed:
            if not custom_keyfile and not establish_keyfile(
                disk.name, crypttab_selection, luks_passphrase
            ):
                e_msg = (
                    "There was an unknown problem with establish_keyfile "
                    "when called by _luks_disk() for disk ({}). Keyfile "
                    "may not have been established."
                ).format(disk.name)
                handle_exception(Exception(e_msg), request)
            # Having established our keyfile we update our LUKS role but only
            # for non custom keyfile config. As we don't change custom keyfile
            # configs we need not update our keyfileExists LUKS role value.
            if not custom_keyfile:
                roles["LUKS"]["keyfileExists"] = True
            # Note there is no current keyfile delete mechanism. If this
            # was established we should make sure to remove this key and it's
            # value appropriately.
            # Update /etc/crypttab except when an existing custom ctypttab
            # entry exists ie if not custom_keyfile in role then update.
            if not custom_keyfile and not update_crypttab(
                disk_uuid, crypttab_selection
            ):
                e_msg = (
                    "There was an unknown problem with update_crypttab "
                    "when called by _luks_disk() for disk ({}). "
                    "No custom keyfile config found. No /etc/crypttab "
                    "changes were made."
                ).format(disk.name)
                handle_exception(Exception(e_msg), request)
        else:
            # crypttab_selection = 'none' or 'false' so update crypttab
            # irrespective of existing custom keyfile config.
            if not update_crypttab(disk_uuid, crypttab_selection):
                e_msg = (
                    "There was an unknown problem with update_crypttab "
                    "when called by _luks_disk() for disk ({}). No "
                    "/etc/crypttab changes were made."
                ).format(disk.name)
                handle_exception(Exception(e_msg), request)
        # Reflect the crypttab changes in our LUKS role.
        if crypttab_selection == "false":
            # A 'false' value is a flag to indicate no crypttab entry
            if "crypttab" in roles["LUKS"]:
                # no crypttab entry is indicated by no 'crypttab' key:
                del roles["LUKS"]["crypttab"]
        else:  # crypttab_selection = 'none' or keyfile path.
            if crypttab_selection == "none":
                roles["LUKS"]["crypttab"] = crypttab_selection
            else:  # we have a keyfile crypttab_selection
                if not custom_keyfile:
                    # Only change non custom keyfile roles.
                    roles["LUKS"]["crypttab"] = crypttab_selection
        # Now we save our updated roles as json in the database.
        disk.role = json.dumps(roles)
        disk.save()
        # Ensure systemd generated files are updated re /etc/crypttab changes:
        out, err, rc = trigger_systemd_update()
        if rc != 0:
            e_msg = (
                "There was an unknown problem with systemd update when "
                "called by _luks_disk() for disk ({})."
            ).format(disk.name)
            handle_exception(Exception(e_msg), request)
        return Response()

    @classmethod
    @transaction.atomic
    def _toggle_smart(cls, did, request, enable=False):
        disk = cls._validate_disk(did, request)
        if not disk.smart_available:
            e_msg = ("S.M.A.R.T support is not available on disk ({}).").format(
                disk.name
            )
            handle_exception(Exception(e_msg), request)
        smart.toggle_smart(disk.name, disk.smart_options, enable)
        disk.smart_enabled = enable
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @classmethod
    def _blink_drive(cls, did, request):
        disk = cls._validate_disk(did, request)
        total_time = int(request.data.get("total_time", 90))
        blink_time = int(request.data.get("blink_time", 15))
        sleep_time = int(request.data.get("sleep_time", 5))
        blink_disk(disk.name, total_time, blink_time, sleep_time)
        return Response()

    @classmethod
    def _spindown_drive(cls, did, request):
        disk = cls._validate_disk(did, request)
        spindown_time = int(request.data.get("spindown_time", 20))
        spindown_message = str(request.data.get("spindown_message", "message issue!"))
        apm_value = int(request.data.get("apm_value", 0))
        set_disk_spindown(disk.name, spindown_time, apm_value, spindown_message)
        return Response()

    @classmethod
    def _pause(cls, did, request):
        disk = cls._validate_disk(did, request)
        enter_standby(disk.name)
        return Response()
