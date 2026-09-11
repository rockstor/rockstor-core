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

import re
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.db import transaction

from settings import (
    COMPRESSION_TYPES,
    MNT_PT,
    SFTP_MNT_ROOT,
    POOL_REGEX,
)
from smart_manager.models import TaskDefinition
from storageadmin.serializers import PoolInfoSerializer
from storageadmin.models import Disk, Pool, Share, PoolBalance
from fs.btrfs import (
    add_pool,
    resize_pool_cmd,
    balance_pool_cmd,
    umount_root,
    btrfs_uuid,
    mount_root,
    start_balance,
    usage_bound,
    enable_quota,
    disable_quota,
    rescan_quotas,
    start_resize_pool,
    balance_status_all,
    PROFILE,
    get_pool_labels,
)
from system.constants import NFS_EXPORT_ROOT
from system.docker import docker_status
from system.osi import remount, trigger_udev_update
from system.samba_util import remove_smb_export
from system.nfs_util import remove_nfs_export, nfs4_mount_teardown
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
import json

import logging

logger = logging.getLogger(__name__)

# Currently supported Rockstor btrfs raid profiles.
# See fs.btrfs.PROFILE for all definitions.
SUPPORTED_PROFILES = (
    "single",
    "single-dup",
    "raid0",
    "raid1",
    "raid10",
    "raid5",
    "raid6",
    "raid1c3",
    "raid1c4",
    "raid1-1c3",
    "raid1-1c4",
    "raid10-1c3",
    "raid10-1c4",
    "raid5-1",
    "raid5-1c3",
    "raid6-1c3",
    "raid6-1c4",
)


class PoolMixin(object):
    serializer_class = PoolInfoSerializer

    @staticmethod
    def _validate_disk(d, request):
        # Used by post (create) pool
        # TODO: Consider moving this and related code to id based validation.
        try:
            return Disk.objects.get(name=d)
        except:
            e_msg = f"Disk with name ({d}) does not exist."
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_disk_id(diskId, request):
        # Used by put (modify) pool
        try:
            return Disk.objects.get(id=diskId)
        except:
            e_msg = f"Disk with id ({diskId}) does not exist."
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _role_filter_disk_names(disks, request):
        """
        Takes a series of disk objects and filters them based on their roles.
        For disk with a redirect role the role's value is substituted for that
        disks name. This effects a name re-direction for redirect role disks.
        N.B. Disk model now has sister code under Disk.target_name property.
        :param disks:  list of disks object
        :param request:
        :return: list of disk names post role filter processing
        """
        # TODO: Consider revising to use new Disk.target_name property.
        try:
            # Build dictionary of disks with roles
            role_disks = {d for d in disks if d.role is not None}
            # Build a dictionary of redirected disk names with their
            # associated redirect role values.
            # By using only role_disks we avoid json.load(None)
            redirect_disks = {
                d.name: json.loads(d.role).get("redirect", None)
                for d in role_disks
                if "redirect" in json.loads(d.role)
            }
            # Replace d.name with redirect role value for redirect role disks.
            # Our role system stores the /dev/disk/by-id name (without path)
            # for redirected disks so use that value instead as our disk name:
            dnames = [
                d.name if d.name not in redirect_disks else redirect_disks[d.name]
                for d in disks
            ]
            return dnames
        except:
            e_msg = "Problem with role filter of disks."
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_new_quota_state(request):
        logger.debug(
            "#### validate_new_quota_state received new_state "
            f"=({request.data.get('quotas')})."
        )
        new_val = request.data.get("quotas", "Enabled")
        if new_val is None:
            # We default to Quotas enabled if input is in doubt.
            new_val = "Enabled"
        if new_val != "Enabled" and new_val != "Disabled":
            e_msg = (
                f"Unsupported quotas request ({new_val}). "
                'Expecting "Enabled" or "Disabled"'
            )
            handle_exception(Exception(e_msg), request)
        return new_val

    @staticmethod
    def _validate_compression(request):
        # Define default compression value, if not entered, as 'no'.
        compression = request.data.get("compression", "no")
        if compression is None or compression == "":
            compression = "no"
        if compression not in COMPRESSION_TYPES:
            e_msg = (
                f"Unsupported compression algorithm ({compression}). "
                f"Use one of {COMPRESSION_TYPES}."
            )
            handle_exception(Exception(e_msg), request)
        return compression

    @staticmethod
    def _validate_mnt_options(request):
        mnt_options = request.data.get("mnt_options", None)
        if mnt_options is None:
            return ""
        allowed_options = {
            "autodefrag": None,
            "clear_cache": None,
            "commit": int,
            "compress-force": COMPRESSION_TYPES,
            "degraded": None,
            "discard": None,
            "enospc_debug": None,
            "fatal_errors": None,
            "flushoncommit": None,
            "max_inline": int,
            "metadata_ratio": int,
            "noacl": None,
            "noatime": None,
            "nobarrier": None,
            "nodatacow": None,
            "nodatasum": None,
            "nologreplay": None,
            "nospace_cache": None,
            "nossd": None,
            "notreelog": None,
            "ro": None,
            "rw": None,
            "skip_balance": None,
            "space_cache": None,
            "ssd": None,
            "ssd_spread": None,
            "thread_pool": int,
            "usebackuproot": None,
            "user_subvol_rm_allowed": None,
            "": None,
        }
        o_fields = mnt_options.split(",")
        for o in o_fields:
            v = None
            if re.search("=", o) is not None:
                o, v = o.split("=")
            if o not in allowed_options:
                e_msg = (
                    f"mount option ({o}) not allowed. Make sure there are "
                    f"no whitespaces in the input. Allowed options: ({sorted(allowed_options.keys())})."
                )
                handle_exception(Exception(e_msg), request)
            if o == "compress-force" and v not in allowed_options["compress-force"]:
                e_msg = f"compress-force is only allowed with {COMPRESSION_TYPES}."
                handle_exception(Exception(e_msg), request)
            # changed conditional from "if (type(allowed_options[o]) is int):"
            if allowed_options[o] is int:
                try:
                    int(v)
                except:
                    e_msg = f"Value for mount option ({o}) must be an integer."
                    handle_exception(Exception(e_msg), request)
        return mnt_options

    @classmethod
    def _remount(cls, request, pool):
        compression = cls._validate_compression(request)
        mnt_options = cls._validate_mnt_options(request)
        if compression == pool.compression and mnt_options == pool.mnt_options:
            return Response()

        with transaction.atomic():
            pool.compression = compression
            pool.mnt_options = mnt_options
            pool.save()

        if re.search("noatime", mnt_options) is None:
            mnt_options = f"{mnt_options},relatime,atime"

        if re.search("compress-force", mnt_options) is None:
            mnt_options = f"{mnt_options},compress={compression}"

        with open("/proc/mounts") as mfo:
            mount_map = {}
            for l in mfo.readlines():
                share_name = None
                if re.search(f"{NFS_EXPORT_ROOT}|{MNT_PT}", l) is not None:
                    share_name = l.split()[1].split("/")[2]
                elif re.search(SFTP_MNT_ROOT, l) is not None:
                    share_name = l.split()[1].split("/")[3]
                else:
                    continue
                if share_name not in mount_map:
                    mount_map[share_name] = [l.split()[1]]
                else:
                    mount_map[share_name].append(l.split()[1])
        failed_remounts = []
        try:
            pool_mnt = f"/mnt2/{pool.name}"
            remount(pool_mnt, mnt_options)
        except:
            failed_remounts.append(pool_mnt)
        for share in mount_map.keys():
            if Share.objects.filter(pool=pool, name=share).exists():
                for m in mount_map[share]:
                    try:
                        remount(m, mnt_options)
                    except Exception as e:
                        logger.exception(e)
                        failed_remounts.append(m)
        if len(failed_remounts) > 0:
            e_msg = (
                f"Failed to remount the following mounts.\n {failed_remounts}.\n "
                "Try again or do the following as root (may cause "
                "downtime):\n1. systemctl stop rockstor.\n"
                "2. unmount manually.\n"
                "3. systemctl start rockstor.\n"
            )
            handle_exception(Exception(e_msg), request)
        return Response(PoolInfoSerializer(pool).data)

    @classmethod
    def _quotas(cls, request, pool):
        new_quota_state = cls._validate_new_quota_state(request)
        # If no change from current pool quota state then do nothing
        current_state = "Enabled"
        if not pool.quotas_enabled:
            current_state = "Disabled"
        if new_quota_state == current_state:
            return Response()
        try:
            if new_quota_state == "Enabled":
                # Current issue with requiring enable to be executed twice !!!
                # As of 4.12.4-1.el7.elrepo.x86_64
                # this avoids "ERROR: quota rescan failed: Invalid argument"
                # when attempting a rescan.
                # Look similar to https://patchwork.kernel.org/patch/9928635/
                enable_quota(pool)
                enable_quota(pool)
                # As of 4.12.4-1.el7.elrepo.x86_64
                # The second above enable_quota() call currently initiates a
                # rescan so the following is redundant; however this may not
                # always be the case so leaving as it will auto skip if a scan
                # in in progress anyway.
                rescan_quotas(pool)
            else:
                disable_quota(pool)
        except:
            e_msg = (
                "Failed to Enable (and rescan) / Disable Quotas for "
                f"Pool ({pool.name}). Requested quota state "
                f"was ({new_quota_state})."
            )
            handle_exception(Exception(e_msg), request)
        return Response(PoolInfoSerializer(pool).data)

    def _balance_start(self, pool, force=False, convert=None):
        mnt_pt = mount_root(pool)
        if convert is None and pool.raid == "single":
            # Btrfs balance without convert filters will convert dup level
            # metadata on a single level data pool to raid1 on multi disk
            # pools. Avoid by explicit convert in this instance.
            logger.info("Preserve single data, dup metadata by explicit convert.")
            convert = "single"
        cmd = balance_pool_cmd(mnt_pt, force=force, convert=convert)
        task_result_handle = start_balance(cmd)
        tid = task_result_handle.id
        logger.debug(f"balance tid = ({tid}).")
        return tid

    def _resize_pool_start(self, pool, dnames, add=True):
        """
        Async initiator for resize_pool(pool, dnames, add=False) as when a
        device is deleted it initiates a btrfs internal balance which is not
        accessible to 'btrfs balance status' but is a balance nevertheless.
        Based on _balance_start()
        :param pool:  Pool object.
        :param dnames: list of by-id device names without paths.
        :param add: True if adding dnames, False if deleting (removing) dnames.
        :return: 0 if
        """
        # default tid: flags non async task calls i.e. task.call_local() or None cmd.
        tid = 0
        cmd = resize_pool_cmd(pool, dnames, add)
        if cmd is None:
            return tid
        logger.info(
            f"Beginning device resize on pool ({pool.name}). "
            f"Changed member devices:({dnames})."
        )
        if add:
            # Mostly instantaneous so avoid complexity/overhead of huey
            start_resize_pool.call_local(cmd)
            return tid
        # Device delete initiates long running internal balance: start async.
        task_result_handle = start_resize_pool(cmd)
        tid = task_result_handle.id
        logger.debug(f"Pool resize tid = ({tid}).")
        return tid


class PoolListView(PoolMixin, rfc.GenericView):
    def get_queryset(self, *args, **kwargs):
        sort_col = self.request.query_params.get("sortby", None)
        if sort_col is not None and sort_col == "usage":
            reverse = self.request.query_params.get("reverse", "no")
            if reverse == "yes":
                reverse = True
            else:
                reverse = False
            return sorted(
                Pool.objects.all(), key=lambda u: u.cur_usage(), reverse=reverse
            )
        return Pool.objects.all()

    @transaction.atomic
    def post(self, request):
        """
        input is a list of disks, raid_level and name of the pool.
        """
        with self._handle_exception(request):
            # TODO Add check for None and iterable before the following disk validation
            #  else we end up "TypeError: 'NoneType' object is not iterable"
            #  when no disks are entered via API (Web-UI has sanity check already).
            #  N.B. we have an existing test for this 'NoneType' response !!
            disks = [self._validate_disk(d, request) for d in request.data.get("disks")]
            pname = request.data["pname"]
            if re.match(f"{POOL_REGEX}$", pname) is None:
                e_msg = (
                    "Invalid characters in pool name. Following "
                    "characters are allowed: letter(a-z or A-Z), "
                    "digit(0-9), "
                    "hyphen(-), underscore(_) or a period(.)."
                )
                handle_exception(Exception(e_msg), request)

            if len(pname) > 255:
                e_msg = "Pool name must be less than 255 characters."
                handle_exception(Exception(e_msg), request)

            if Pool.objects.filter(name=pname).exists():
                e_msg = (
                    f"A managed Pool with the name/label ({pname}) already exists. "
                    f"Choose a different name."
                )
                handle_exception(Exception(e_msg), request)

            if pname in get_pool_labels():
                e_msg = (
                    f"An unmanaged Pool with the name/label ({pname}) exists. "
                    f"Either importing that Pool via a disk member, "
                    f"or choose a different name."
                )
                handle_exception(Exception(e_msg), request)

            if Share.objects.filter(name=pname).exists():
                e_msg = (
                    f"A share with this name ({pname}) exists. Pool and share "
                    "names must be distinct. "
                    "Choose a different name."
                )
                handle_exception(Exception(e_msg), request)

            for d in disks:
                if d.btrfs_uuid is not None:
                    e_msg = (
                        "Another BTRFS filesystem exists on this "
                        f"disk ({d.name}). "
                        "Erase the disk and try again."
                    )
                    handle_exception(Exception(e_msg), request)

            raid_level = request.data["raid_level"]
            # Reject creation of unsupported raid_level:
            if raid_level not in SUPPORTED_PROFILES:
                e_msg = f"Unsupported raid level. Use one of: {SUPPORTED_PROFILES}."
                handle_exception(Exception(e_msg), request)

            # Reject below minium device count for selected profile
            profile_min_dev_count = PROFILE[raid_level].min_dev_count
            if len(disks) < profile_min_dev_count:
                e_msg = f"{profile_min_dev_count} or more disks are required for the raid level: {raid_level}."
                handle_exception(Exception(e_msg), request)

            compression = self._validate_compression(request)
            mnt_options = self._validate_mnt_options(request)
            dnames = self._role_filter_disk_names(disks, request)
            p = Pool(
                name=pname,
                raid=raid_level,
                compression=compression,
                mnt_options=mnt_options,
            )
            p.save()
            # p.disk_set.add(*disks)
            p.disk_set.add(*disks, bulk=False)
            # added for loop to save disks appears p.disk_set.add(*disks) was
            # not saving disks in test environment
            # N.B. but we now have bulk=False in above so loop may be redundant now.
            for d in disks:
                d.pool = p
                d.save()
            add_pool(p, dnames)
            p.size = p.usage_bound()
            p.uuid = btrfs_uuid(dnames[0])
            p.save()
            # Now we ensure udev info is updated via system wide trigger
            # as per pool resize add, only here it is for a new pool.
            trigger_udev_update()
            return Response(PoolInfoSerializer(p).data)


class PoolDetailView(PoolMixin, rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            pool = Pool.objects.get(id=self.kwargs["pid"])
            serialized_data = PoolInfoSerializer(pool)
            return Response(serialized_data.data)
        except Pool.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @transaction.atomic
    def put(self, request, pid, command):
        """
        resize a pool.
        :param pid: id of Pool object in db
        :param command:
        'add' - add a list of disks and hence expand the pool
        'remove' - remove a list of disks and hence shrink the pool
        'remount' - remount the pool, to apply changed mount options
        'quotas' - request pool quota setting change
        """
        logger.debug(f"######## PUT request on pool id ({pid}) ###############")
        logger.debug(f"######## request = ({request.data})")
        logger.debug(f"######## request disks = ({request.data.get('disks')})")
        logger.debug(f"######## command = ({command})")
        with self._handle_exception(request):
            try:
                pool = Pool.objects.get(id=pid)
            except:
                e_msg = f"Pool with id ({pid}) does not exist."
                handle_exception(Exception(e_msg), request)

            logger.debug(f"######## pool name ({pool.name}) ###############")
            if pool.role == "root" and command != "quotas":
                e_msg = (
                    f"Edit operations are not allowed on this pool ({pool.name}) "
                    "as it contains the operating system."
                )
                handle_exception(Exception(e_msg), request)

            if command == "remount":
                return self._remount(request, pool)

            if command == "quotas":
                # There is a pending btrfs change that allows for quota state
                # change on unmounted Volumes (pools).
                return self._quotas(request, pool)

            # Establish missing and detached disk removal request flag defaults:
            remove_missing_disk_request = False
            all_members_detached = False
            if command == "remove" and request.data.get("disks", []) == ["missing"]:
                remove_missing_disk_request = True
            if (
                pool.disk_set.filter(name__startswith="detached-").count()
                == pool.disk_set.count()
            ):
                all_members_detached = True

            if not pool.is_mounted:
                # If we are asked to remove the last disk in a pool and it's detached
                # then user has already been notified to not remove it if it's to be
                # re-attached. So skip our mount exception as not possible anyway unless
                # re-attached and we have already indicated that possible path.
                # All works accounts for all pool members in detached state.
                if all_members_detached:
                    logger.info(
                        "Skipping mount requirement: all pool's member are detached."
                    )
                else:
                    e_msg = (
                        "Pool member / raid edits require an active mount. "
                        'Please see the "Maintenance required" section.'
                    )
                    handle_exception(Exception(e_msg), request)

            if remove_missing_disk_request:
                disks = []
                logger.debug("Remove missing request, so skipping disk validation")
            else:
                disks = [
                    self._validate_disk_id(diskId, request)
                    for diskId in request.data.get("disks", [])
                ]

            num_disks_selected = len(disks)
            dnames = self._role_filter_disk_names(disks, request)
            new_raid = request.data.get("raid_level", pool.raid)

            if command == "add":
                # Only attached disks can be selected during an add operation.
                num_total_attached_disks = (
                    pool.disk_set.attached().count() + num_disks_selected
                )
                for d in disks:
                    if d.pool is not None:
                        e_msg = (
                            f"Disk ({d.name}) cannot be added to this pool ({pool.name}) "
                            f"because it belongs to another pool ({d.pool.name})."
                        )
                        handle_exception(Exception(e_msg), request)
                    if d.btrfs_uuid is not None:
                        e_msg = (
                            f"Disk ({d.name}) has a BTRFS filesystem from the "
                            "past. If you really like to add it, wipe it "
                            "from the Storage -> Disks screen of the "
                            "web-ui."
                        )
                        handle_exception(Exception(e_msg), request)

                # Avoid extreme raid level change upwards (space issues).
                # TODO: Consider removing once we have better space calc.
                if pool.raid == "single" and new_raid == "raid10":
                    e_msg = f"Pool migration from {pool.raid} to {new_raid} is not supported."
                    handle_exception(Exception(e_msg), request)

                # Avoid add if to-be attached < minium device count for proposed profile
                profile_min_dev_count = PROFILE[new_raid].min_dev_count
                if num_total_attached_disks < profile_min_dev_count:
                    e_msg = (
                        f"A minimum of {profile_min_dev_count} drives are required for the "
                        f"raid level: {new_raid}."
                    )
                    handle_exception(Exception(e_msg), request)

                # Check for ongoing balance:
                # We could use api status command /api/pools/PoolID/balance/status
                # but we are mid PUT COMMAND transaction.atomic and status command is
                # likewise transaction.atomic:
                bstatus = balance_status_all(pool)
                # TODO we can receive multiple instances here.
                #  We are only interested in the last object to match by start_time
                if (
                    bstatus.active
                    or PoolBalance.objects.filter(
                        pool=pool,
                        status__regex=r"(started|running|cancelling|pausing|paused)",
                    ).exists()
                ):  # noqa E501
                    e_msg = (
                        "A Balance process is already running or paused "
                        f"for this pool ({pool.name}). Resize is not supported "
                        "during a balance process."
                    )
                    temp_poolBalances = PoolBalance.objects.filter(pool=pool)
                    for record in temp_poolBalances:
                        logger.debug(
                            f"====== Recorded status = ({record.status})."
                            f"000000 full info = {record}"
                        )
                    handle_exception(Exception(e_msg), request)

                # _resize_pool_start() add dev mode is quick so no async or tid
                self._resize_pool_start(pool, dnames)
                force = False
                # During dev add we also offer raid level change, if selected
                # blanket apply '-f' to allow for reducing metadata integrity.
                if new_raid != pool.raid:
                    force = True
                # Huey async initialization as balance is long running.
                tid = self._balance_start(pool, force=force, convert=new_raid)
                ps = PoolBalance(pool=pool, tid=tid)
                ps.save()

                pool.raid = new_raid
                for d_o in disks:
                    d_o.pool = pool
                    d_o.save()
                # Now we ensure udev info is updated via system wide trigger
                trigger_udev_update()

            elif command == "remove":
                if new_raid != pool.raid:
                    e_msg = "Raid configuration cannot be changed while removing disks."
                    handle_exception(Exception(e_msg), request)
                detached_disks_selected = 0
                for d in disks:  # to be removed
                    if d.pool is None or d.pool != pool:
                        e_msg = (
                            f"Disk ({d.name}) cannot be removed because it does "
                            "not belong to this "
                            f"pool ({pool.name})."
                        )
                        handle_exception(Exception(e_msg), request)
                    if re.match("detached-", d.name) is not None:
                        detached_disks_selected += 1
                if detached_disks_selected >= 2:
                    # We translate the removal of a detached device into:
                    # "btrfs device delete missing mnt_pt"
                    # but only when appropriate, this removes the first 'missing' dev.
                    # A detached disk is not necessarily missing, but an indication of
                    # prior pool association.
                    e_msg = (
                        "Detached disk selection is limited to a single device. "
                        "If all Pool members are detached all will be removed "
                        "and their pool automatically deleted there after."
                    )
                    handle_exception(Exception(e_msg), request)
                attached_disks_selected = num_disks_selected - detached_disks_selected
                remaining_attached_disks = (
                    pool.disk_set.attached().count() - attached_disks_selected
                )

                # Add check for attempt to remove detached & attached disks concurrently
                if detached_disks_selected > 0 and attached_disks_selected > 0:
                    e_msg = (
                        "Mixed detached and attached disk selection is "
                        "not supported. Limit your selection to only attached "
                        "disks, or a single detached disk."
                    )
                    handle_exception(Exception(e_msg), request)
                # Skip all further sanity checks when all members are detached.
                if not all_members_detached:
                    # Avoid remove if to-be attached < minium device count for profile
                    profile_min_dev_count = PROFILE[pool.raid].min_dev_count
                    if remaining_attached_disks < profile_min_dev_count:
                        e_msg = (
                            "Disks cannot be removed from this pool "
                            f"because its raid configuration ({pool.raid}) "
                            f"requires a minimum of {profile_min_dev_count} disk/s."
                        )
                        handle_exception(Exception(e_msg), request)

                    size_cut = 0
                    for d in disks:  # to be removed
                        size_cut += d.allocated
                        logger.debug(
                            f"++++++++ adding disk {d.name} allocated space {d.allocated} to size_cut"
                        )
                    available_free = pool.free
                    logger.debug(f"available_free = {available_free}")
                    logger.debug(f"pool size = {pool.size}")
                    # TODO improve disk list presentation in the following msg.
                    #  currently we have: "Removing disks ([u'virtio-1']) may shrink"
                    if size_cut >= available_free:
                        e_msg = (
                            f"Removing disk/s ({" ".join(dnames)}) may shrink the pool by "
                            f"{size_cut} KB, which is greater than available free "
                            f"space {available_free} KB. This is not supported."
                        )
                        handle_exception(Exception(e_msg), request)

                    # Unlike resize_pool_start() with add=True a remove has an
                    # implicit balance where the removed disks contents are
                    # re-distributed across the remaining pool members.
                    # This internal balance cannot currently be monitored by the
                    # usual 'btrfs balance status /mnt_pt' command. So we have to
                    # use our own mechanism to assess it's status.
                    # Huey async initialization:
                    tid = self._resize_pool_start(pool, dnames, add=False)
                    ps = PoolBalance(pool=pool, tid=tid, internal=True)
                    ps.save()
                    # Setting disk.pool = None for all removed members is redundant
                    # as our next disk scan will re-find them until such time as
                    # our async task, and it's associated dev remove, has completed
                    # it's internal balance. This can take hours. Except for db only
                    # event of all_members_detached.

                else:  # all_members_detached:
                    # If all members are detached then delete pool associations for all.
                    # We cannot mount and so cannot perform any resize or any further
                    # pool member validation anyway.
                    # N.B. on next pool refresh, no members leads to pool removal.
                    for d in pool.disk_set.all():
                        d.pool = None
                        d.save()

            else:
                e_msg = f"Command ({command}) is not supported."
                handle_exception(Exception(e_msg), request)
            pool.size = pool.usage_bound()
            pool.save()
            return Response(PoolInfoSerializer(pool).data)

    @transaction.atomic
    def delete(self, request, pid, command=""):
        force = True if (command == "force") else False
        with self._handle_exception(request):
            try:
                pool = Pool.objects.get(id=pid)
            except:
                e_msg = f"Pool with id ({pid}) does not exist."
                handle_exception(Exception(e_msg), request)
            if not pool.is_mounted:
                logger.info(
                    f"Pool ({pool.name}) to be deleted is not mounted. "
                    "Proceeding with database removal only."
                )
            elif pool.redundancy_exceeded:
                logger.info(
                    f"Pool ({pool.name}) to be deleted has exceeded its redundancy limits. "
                    "Proceeding with database removal only."
                )
            # SCRUB TASKS
            # Delete DB config for scrub type tasks: no Share is required for these.
            if TaskDefinition.objects.filter(task_type="scrub").exists():
                for taskdef in TaskDefinition.objects.filter(task_type="scrub").all():
                    if taskdef.pool_name == pool.name:
                        logger.info(
                            f"Deleting scheduled scrub task ({taskdef.name}) for ({pool.name})."
                        )
                        # The following, via ForeignKey on_delete=models.CASCADE,
                        # removes scheduled scrub history in linked Task model entries.
                        # A TaskDefinition.delete() override updates our CRONTAB_FILE.
                        taskdef.delete()
            share_name_list = []
            nfs_exports_list = []
            if Share.objects.filter(pool=pool).exists():
                if not force:
                    e_msg = (
                        f"Pool ({pool.name}) is not empty. Delete is not allowed "
                        "until all shares in the pool "
                        "are deleted."
                    )
                    handle_exception(Exception(e_msg), request)
                if docker_status():
                    # We cannot know for sure if a Rock-on uses a Pool, but if it has
                    # subvols (Shares) it is possible. Ergo block Pool delete & advise.
                    # Can be refined by reporting Pool hosted Rock-on (DVolume) Shares.
                    e_msg = (
                        f"Pool ({pool.name}) cannot have management deleted while the "
                        "Rock-on service is ON: Shares on this Pool may be in use.\n"
                        "Turn the Rock-on service OFF before deleting Pool management.\n"
                        "Note: some Rock-ons may take around a minute to fully stop."
                    )
                    handle_exception(Exception(e_msg), request)
                logger.info("Proceeding with unmount and database (DB) removal of:")
                logger.info(f"- Pool ({pool.name}) mount point {pool.mnt_pt}.")
                for so in Share.objects.filter(pool=pool):
                    share_name_list.append(so.name)
                    # NFS EXPORTS
                    # Unlike Samba & SFTP exports, NFS exports don't get auto-deleted
                    # on pool.delete - via Share.ForeignKey to host Pool.
                    # They just lose their Share reference - so itteratively remove all
                    # linked export_groups before removing all related export_sets.
                    if so.nfsexport_set.exists():
                        logger.info(f"- Deleting NFS DB configs for Share ({so.name}).")
                        nfs_exports_list.append(f"{NFS_EXPORT_ROOT}{so.name}")
                        for export_set in so.nfsexport_set.all():
                            logger.info(
                                f"- Deleting config for host {export_set.export_group.host_str}"
                            )
                            export_set.export_group.delete()
                        so.nfsexport_set.all().delete()
                    # SNAPSHOT TASKS
                    # Akin to NFS EXPORTS, we have no Share cascade delete for these
                    # tasks. Find and remove all of this Share's snapshot tasks before
                    # proceeding.
                    if TaskDefinition.objects.filter(task_type="snapshot").exists():
                        for taskdef in TaskDefinition.objects.filter(
                            task_type="snapshot"
                        ).all():
                            if taskdef.share_name == so.name:
                                logger.info(
                                    f"- Deleting scheduled snapshot task ({taskdef.name}) for ({so.name})."
                                )
                                # The following, via ForeignKey on_delete=models.CASCADE,
                                # also removes scheduled snap history in linked Task entries.
                                # A TaskDefinition.delete() override updates our CRONTAB_FILE.
                                taskdef.delete()
                    logger.info(
                        f"-- Unmounting subvol ({so.name}) mount point {so.mnt_pt}."
                    )
                    umount_root(so.mnt_pt)
            logger.info(f"- Unmounting Pool ({pool.name}) mount point {pool.mnt_pt}.")
            umount_root(pool.mnt_pt)
            logger.info(
                f"Removing Pool ({pool.name}) management and associated configuration. "
            )
            pool.delete()
            # We may need to update disk state here.
            if share_name_list:
                logger.debug(f"Share names affected: {share_name_list}.")
                # Our SambaShare.delete() override to update smb.conf is bypassed
                # during mass deletes; such as the pool.delete we just enacted:
                # SambaShare.share = models.OneToOneField
                #  ("Share", related_name="sambashare", on_delete=models.CASCADE)
                # Share.pool = models.ForeignKey(Pool, on_delete=models.CASCADE)
                # Ergo we opportunistically mass config remove all now unmanaged Pool
                # Shares; irrespective of their prior export status.
                # fast & singular smb.conf edit.
                smb_config_updated: bool = remove_smb_export(share_name_list)
                if smb_config_updated:
                    logger.info("SMB config updated.")
                    # TODO: Background samba service restart
                # Remove all current or past NFS exports for all affected Shares.
                nfs_config_updated: bool = remove_nfs_export(share_name_list)
                if nfs_config_updated:
                    logger.info("NFS config updated.")
                    # TODO: the following can be long running so do in background task.
                    nfs4_mount_teardown(nfs_exports_list)
                    # TODO: Background NFS service restart
            return Response()


@api_view()
def get_usage_bound(request):
    """Simple view to relay the computed usage bound to the front end."""
    disk_sizes = [int(size) for size in request.query_params.getlist("disk_sizes[]")]
    raid_level = request.query_params.get("raid_level", "single")
    return Response(usage_bound(disk_sizes, len(disk_sizes), raid_level))
