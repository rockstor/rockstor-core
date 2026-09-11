"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from settings import SFTP_MNT_ROOT, MNT_PT
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from storageadmin.views import DiskMixin
from system.osi import uptime, kernel_info, get_device_mapper_map
from fs.btrfs import (
    mount_share,
    mount_root,
    get_dev_pool_info,
    get_pool_raid_levels,
    mount_snap,
    get_pool_raid_profile,
)
from system.ssh import sftp_mount_map, sftp_mount
from system.osi import (
    system_shutdown,
    system_reboot,
    system_suspend,
    set_system_rtc_wake,
)
from storageadmin.models import (
    Share,
    NFSExport,
    SFTP,
    Pool,
    Snapshot,
    UpdateSubscription,
    AdvancedNFSExport,
)
from storageadmin.util import handle_exception
from datetime import datetime, UTC
from django.db import transaction
from storageadmin.views.share_helpers import (
    sftp_snap_toggle,
    import_shares,
    import_snapshots,
)
from rest_framework_custom.oauth_wrapper import RockstorOAuth2Authentication
from system.pkg_mgmt import (
    auto_update,
    current_version,
    rockstor_pkg_update_check,
    update_run,
    auto_update_status,
)
from storageadmin.views.nfs_exports import NFSExportMixin
import logging

logger = logging.getLogger(__name__)


class CommandView(DiskMixin, NFSExportMixin, APIView):
    authentication_classes = (
        DigestAuthentication,
        SessionAuthentication,
        BasicAuthentication,
        RockstorOAuth2Authentication,
    )
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @transaction.atomic
    def _refresh_pool_state():
        # Get map of dm-0 to /dev/mapper members ie luks-.. devices.
        mapped_devs = get_device_mapper_map()
        # Get temp_names (kernel names) to btrfs pool info for attached devs.
        dev_pool_info = get_dev_pool_info()
        for p in Pool.objects.all():
            # If our pool has no disks, detached included, then delete it.
            # We leave pools with all detached members in place intentionally.
            if p.disk_set.count() == 0:
                p.delete()
                continue
            # Log if no attached members are found, ie all devs are detached.
            if p.disk_set.attached().count() == 0:
                logger.error(
                    f"Skipping Pool ({p.name}) mount as there "
                    "are no attached devices. Moving on."
                )
                continue
            # If pool has no missing remove all detached disk pool associations.
            # Accounts for 'end of run' clean-up in removing a detached disk and for cli
            # maintenance re pool returned to no missing dev status. Also re-establishes
            # pool info as source of truth re missing.
            if not p.has_missing_dev:
                for disk in p.disk_set.filter(name__startswith="detached-"):
                    logger.info(
                        f"Removing detached disk from Pool {p.name}: no missing "
                        "devices found."
                    )
                    disk.pool = None
                    disk.save()
            try:
                # Get and save what info we can prior to mount.
                first_dev = p.disk_set.attached().first()
                # Use target_name to account for redirect role.
                if first_dev.target_name == first_dev.temp_name:
                    logger.error(
                        f"Skipping pool ({p.name}) mount as attached disk "
                        f"({first_dev.target_name}) has no by-id name (no serial # ?)"
                    )
                    continue
                if first_dev.temp_name in mapped_devs:
                    dev_tmp_name = f"/dev/mapper/{mapped_devs[first_dev.temp_name]}"
                else:
                    dev_tmp_name = f"/dev/{first_dev.temp_name}"
                # For now we call get_dev_pool_info() once for each pool.
                pool_info = dev_pool_info[dev_tmp_name]
                p.name = pool_info.label
                p.uuid = pool_info.uuid
                p.save()
                mount_root(p)
                pool_raid_info = get_pool_raid_levels(p.mnt_pt)
                p.raid = get_pool_raid_profile(pool_raid_info)
                p.size = p.usage_bound()
                # Consider using mount_status() parse to update root pool db on
                # active (fstab initiated) compression setting.
                p.save()
            except Exception as e:
                logger.error(
                    "Exception while refreshing state for "
                    f"Pool({p.name}). Moving on: {e.__str__()}"
                )
                logger.exception(e)

    @transaction.atomic
    def post(self, request, command, rtcepoch=None):
        if command == "bootstrap":
            self._update_disk_state()
            self._refresh_pool_state()
            for p in Pool.objects.all():
                if p.disk_set.attached().count() == 0:
                    continue
                if not p.is_mounted:
                    # Prior _refresh_pool_state() should have ensure a mount.
                    logger.error(
                        "Skipping import/update of prior known "
                        f"shares for pool ({p.name}) as it is not mounted. "
                        "(see previous errors)"
                        "."
                    )
                    continue
                # Import / update db shares counterpart for managed pool.
                # Includes owner:group & permissions DB update from Pool subvol path.
                import_shares(p, request)
                p.save()

            for share in Share.objects.all():
                if share.pool.disk_set.attached().count() == 0:
                    continue
                if not share.pool.is_mounted:
                    logger.error(
                        f"Skipping mount of share ({share.name}) as pool "
                        f"({share.pool.name}) is not mounted (see previous errors)."
                    )
                    continue
                try:
                    if not share.is_mounted:
                        # System mounted shares i.e. home will already be mounted.
                        mnt_pt = f"{MNT_PT}{share.name}"
                        mount_share(share, mnt_pt)
                        share.save()
                except Exception as e:
                    e_msg = f"Exception while mounting a share ({share.name}) during bootstrap: ({e.__str__()})."
                    logger.error(e_msg)
                    logger.exception(e)

                try:
                    import_snapshots(share)
                except Exception as e:
                    e_msg = f"Exception while importing snapshots of share ({share.name}): ({e.__str__()})."
                    logger.error(e_msg)
                    logger.exception(e)

            for snap in Snapshot.objects.all():
                if snap.uvisible:
                    try:
                        mount_snap(snap.share, snap.real_name, snap.qgroup)
                    except Exception as e:
                        e_msg = f"Failed to make the snapshot ({snap.real_name}) visible. Exception: ({e.__str__()})."
                        logger.error(e_msg)

            mnt_map = sftp_mount_map(SFTP_MNT_ROOT)
            logger.info(f"Bootstrap command, via sftp_mount_map() received {mnt_map}.")
            for sftpo in SFTP.objects.all():
                # The following may be buggy when used with system mounted (fstab) /home
                # but we currently don't allow /home to be exported.
                try:
                    sftp_mount(
                        sftpo.share,
                        MNT_PT,
                        SFTP_MNT_ROOT,
                        mnt_map,
                        sftpo.editable,
                    )
                    sftp_snap_toggle(sftpo.share)
                except Exception as e:
                    e_msg = f"Exception while exporting a SFTP share during bootstrap: ({e.__str__()})."
                    logger.error(e_msg)

            try:
                adv_entries = [a.export_str for a in AdvancedNFSExport.objects.all()]
                exports_d = self.create_adv_nfs_export_input(adv_entries, request)
                exports = self.create_nfs_export_input(NFSExport.objects.all())
                exports.update(exports_d)
                self.refresh_wrapper(exports, request, logger)
            except Exception as e:
                e_msg = f"Exception while bootstrapping NFS: ({e.__str__()})."
                logger.error(e_msg)

            logger.debug("Bootstrap operations completed")
            return Response()

        if command == "utcnow":
            return Response(datetime.now(UTC))

        if command == "uptime":
            return Response(uptime())

        if command == "kernel":
            try:
                return Response(kernel_info())
            except Exception as e:
                handle_exception(e, request)

        if command == "update-check":
            try:
                sub_object: None | UpdateSubscription = None
                try:
                    sub_object = UpdateSubscription.objects.get(status="active")
                except UpdateSubscription.DoesNotExist:
                    pass
                return Response(rockstor_pkg_update_check(subscription=sub_object))
            except Exception as e:
                e_msg = (
                    f"Unable to check update due to a system error: ({e.__str__()})."
                )
                handle_exception(Exception(e_msg), request)

        if command == "update":
            try:
                # Once again, like on system shutdown/reboot, we filter
                # incoming requests with request.auth: every update from
                # WebUI misses request.auth, while yum update requests from
                # data_collector APIWrapper have it, so we can avoid
                # an additional command for yum updates
                if request.auth is None:
                    update_run()
                else:
                    update_run(update_all_other=True)
                return Response("Done")
            except Exception as e:
                e_msg = f"Update failed due to this exception: ({e.__str__()})."
                handle_exception(Exception(e_msg), request)

        if command == "current-version":
            try:
                return Response(current_version()[0])
            except Exception as e:
                e_msg = f"Unable to check current version due to this exception: ({e.__str__()})."
                handle_exception(Exception(e_msg), request)

        # Default has shutdown and reboot with delay set to "now".
        # Reboot and shutdown requests from WebUI don't have request.auth,
        # while same requests over rest api (e.g. scheduled tasks) have
        # an auth token, so if we detect a token we set delay to 3 minutes
        # to notify cli users ahead of time.
        delay: str = "now"
        if request.auth is not None:
            delay = "3"

        if command == "shutdown":
            msg = "The system will now be shutdown."
            try:
                # if shutdown request coming from a scheduled task
                # with rtc wake up time on we set it before
                # system shutdown starting
                if rtcepoch is not None:
                    set_system_rtc_wake(rtcepoch)
                request.session.flush()
                system_shutdown(delay)
            except Exception as e:
                msg = f"Failed to shutdown the system due to a low level error: ({e.__str__()})."
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if command == "reboot":
            msg = "The system will now reboot."
            try:
                request.session.flush()
                system_reboot(delay)
            except Exception as e:
                msg = f"Failed to reboot the system due to a low level error: ({e.__str__()})."
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if command == "suspend":
            msg = "The system will now be suspended to RAM."
            try:
                request.session.flush()
                set_system_rtc_wake(rtcepoch)
                system_suspend()
            except Exception as e:
                msg = f"Failed to suspend the system due to a low level error: ({e.__str__()})."
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if command == "current-user":
            return Response(request.user.username)

        if command == "auto-update-status":
            status = True
            try:
                status = auto_update_status()
            except:
                status = False
            finally:
                return Response({"enabled": status})

        if command == "enable-auto-update":
            try:
                auto_update(enable=True)
                return Response({"enabled": True})
            except Exception as e:
                msg = f"Failed to enable auto update due to this exception: ({e.__str__()})."
                handle_exception(Exception(msg), request)

        if command == "disable-auto-update":
            try:
                auto_update(enable=False)
                return Response({"enabled": False})
            except Exception as e:
                msg = f"Failed to disable auto update due to this exception:  ({e.__str__()})."
                handle_exception(Exception(msg), request)

        if command == "refresh-disk-state":
            self._update_disk_state()
            return Response()

        if command == "refresh-pool-state":
            self._refresh_pool_state()
            return Response()

        if command == "refresh-share-state":
            for p in Pool.objects.all():
                import_shares(p, request)
            return Response()

        if command == "refresh-snapshot-state":
            for share in Share.objects.all():
                import_snapshots(share)
            return Response()
