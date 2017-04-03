"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
import json


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from system.osi import (uptime, kernel_info)
from fs.btrfs import (mount_share, mount_root, qgroup_create, get_pool_info,
                      pool_raid, mount_snap)
from system.ssh import (sftp_mount_map, sftp_mount)
from system.services import systemctl
from system.osi import (is_share_mounted, system_shutdown, system_reboot,
                        system_suspend, set_system_rtc_wake)
from storageadmin.models import (Share, NFSExport, SFTP, Pool, Snapshot,
                                 UpdateSubscription, AdvancedNFSExport)
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from django.db import transaction
from share_helpers import (sftp_snap_toggle, import_shares, import_snapshots)
from rest_framework_custom.oauth_wrapper import RockstorOAuth2Authentication
from system.pkg_mgmt import (auto_update, current_version, update_check,
                             update_run, auto_update_status)
from nfs_exports import NFSExportMixin
import logging
logger = logging.getLogger(__name__)


class CommandView(NFSExportMixin, APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,
                              RockstorOAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @transaction.atomic
    def _refresh_pool_state():
        for p in Pool.objects.all():
            if (p.disk_set.count() == 0):
                p.delete()
                continue
            try:
                mount_root(p)
                first_dev = p.disk_set.first()
                first_dev_name = first_dev.name
                # if we are looking at a device with a redirect role then
                # redirect accordingly.
                if first_dev.role is not None:
                    disk_role_dict = json.loads(first_dev.role)
                    if 'redirect' in disk_role_dict:
                        # consider replacing None with first_dev.name
                        first_dev_name = disk_role_dict.get('redirect', None)
                pool_info = get_pool_info(first_dev_name)
                p.name = pool_info['label']
                p.raid = pool_raid('%s%s' % (settings.MNT_PT, p.name))['data']
                p.size = p.usage_bound()
                p.save()
            except Exception as e:
                logger.error('Exception while refreshing state for '
                             'Pool(%s). Moving on: %s' %
                             (p.name, e.__str__()))
                logger.exception(e)

    @transaction.atomic
    def post(self, request, command, rtcepoch=None):
        if (command == 'bootstrap'):

            self._refresh_pool_state()
            for p in Pool.objects.all():
                import_shares(p, request)

            for share in Share.objects.all():
                try:
                    if (share.pqgroup == settings.MODEL_DEFS['pqgroup']):
                        share.pqgroup = qgroup_create(share.pool)
                        share.save()
                    if (not is_share_mounted(share.name)):
                        mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                        mount_share(share, mnt_pt)
                except Exception as e:
                    e_msg = ('Exception while mounting a share(%s) during '
                             'bootstrap: %s' % (share.name, e.__str__()))
                    logger.error(e_msg)
                    logger.exception(e)

                try:
                    import_snapshots(share)
                except Exception as e:
                    e_msg = ('Exception while importing Snapshots of '
                             'Share(%s): %s' % (share.name, e.__str__()))
                    logger.error(e_msg)
                    logger.exception(e)

            for snap in Snapshot.objects.all():
                if (snap.uvisible):
                    try:
                        mount_snap(snap.share, snap.real_name)
                    except Exception as e:
                        e_msg = ('Failed to make the Snapshot(%s) visible. '
                                 'Exception: %s' %
                                 (snap.real_name, e.__str__()))
                        logger.error(e_msg)

            mnt_map = sftp_mount_map(settings.SFTP_MNT_ROOT)
            for sftpo in SFTP.objects.all():
                try:
                    sftp_mount(sftpo.share, settings.MNT_PT,
                               settings.SFTP_MNT_ROOT, mnt_map, sftpo.editable)
                    sftp_snap_toggle(sftpo.share)
                except Exception as e:
                    e_msg = ('Exception while exportin a sftp share during '
                             'bootstrap: %s' % e.__str__())
                    logger.error(e_msg)

            try:
                adv_entries = [a.export_str for a in
                               AdvancedNFSExport.objects.all()]
                exports_d = self.create_adv_nfs_export_input(adv_entries,
                                                             request)
                exports = self.create_nfs_export_input(NFSExport.objects.all())
                exports.update(exports_d)
                self.refresh_wrapper(exports, request, logger)
            except Exception as e:
                e_msg = ('Exception while bootstrapping NFS: %s' % e.__str__())
                logger.error(e_msg)

            #  bootstrap services
            try:
                systemctl('firewalld', 'stop')
                systemctl('firewalld', 'disable')
                systemctl('nginx', 'stop')
                systemctl('nginx', 'disable')
                systemctl('atd', 'enable')
                systemctl('atd', 'start')
            except Exception as e:
                e_msg = ('Exception while setting service statuses during '
                         'bootstrap: %s' % e.__str__())
                logger.error(e_msg)
                handle_exception(Exception(e_msg), request)

            logger.debug('Bootstrap operations completed')
            return Response()

        if (command == 'utcnow'):
            return Response(datetime.utcnow().replace(tzinfo=utc))

        if (command == 'uptime'):
            return Response(uptime())

        if (command == 'kernel'):
            try:
                return Response(kernel_info(settings.SUPPORTED_KERNEL_VERSION))
            except Exception as e:
                handle_exception(e, request)

        if (command == 'update-check'):
            try:
                subo = None
                try:
                    subo = UpdateSubscription.objects.get(name='Stable',
                                                          status='active')
                except UpdateSubscription.DoesNotExist:
                    try:
                        subo = UpdateSubscription.objects.get(name='Testing',
                                                              status='active')
                    except UpdateSubscription.DoesNotExist:
                        pass
                return Response(update_check(subscription=subo))
            except Exception as e:
                e_msg = ('Unable to check update due to a system error: %s'
                         % e.__str__())
                handle_exception(Exception(e_msg), request)

        if (command == 'update'):
            try:
                # Once again, like on system shutdown/reboot, we filter
                # incoming requests with request.auth: every update from
                # WebUI misses request.auth, while yum update requests from
                # data_collector APIWrapper have it, so we can avoid
                # an additional command for yum updates
                if request.auth is None:
                    update_run()
                else:
                    update_run(yum_update=True)
                return Response('Done')
            except Exception as e:
                e_msg = ('Update failed due to this exception: %s'
                         % e.__str__())
                handle_exception(Exception(e_msg), request)

        if (command == 'current-version'):
            try:
                return Response(current_version())
            except Exception as e:
                e_msg = ('Unable to check current version due to this '
                         'exception: ' % e.__str__())
                handle_exception(Exception(e_msg), request)

        # default has shutdown and reboot with delay set to now
        # having normal sytem power off with now = 1 min
        # reboot and shutdown requests from WebUI don't have request.auth
        # while same requests over rest api (ex. scheduled tasks) have
        # an auth token, so if we detect a token we delay with 3 mins
        # to grant connected WebUI user to close it or cancel shutdown/reboot
        delay = 'now'
        if request.auth is not None:
            delay = 3

        if (command == 'shutdown'):
            msg = ('The system will now be shutdown')
            try:
                # if shutdown request coming from a scheduled task
                # with rtc wake up time on we set it before
                # system shutdown starting
                if rtcepoch is not None:
                    set_system_rtc_wake(rtcepoch)
                request.session.flush()
                system_shutdown(delay)
            except Exception as e:
                msg = ('Failed to shutdown the system due to a low level '
                       'error: %s' % e.__str__())
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if (command == 'reboot'):
            msg = ('The system will now reboot')
            try:
                request.session.flush()
                system_reboot(delay)
            except Exception as e:
                msg = ('Failed to reboot the system due to a low level error: '
                       '%s' % e.__str__())
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if (command == 'suspend'):
            msg = ('The system will now be suspended to RAM')
            try:
                request.session.flush()
                set_system_rtc_wake(rtcepoch)
                system_suspend()
            except Exception as e:
                msg = ('Failed to suspend the system due to a low level '
                       'error: %s' % e.__str__())
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if (command == 'current-user'):
            return Response(request.user.username)

        if (command == 'auto-update-status'):
            status = True
            try:
                status = auto_update_status()
            except:
                status = False
            finally:
                return Response({'enabled': status, })

        if (command == 'enable-auto-update'):
            try:
                auto_update(enable=True)
                return Response({'enabled': True, })
            except Exception as e:
                msg = ('Failed to enable auto update due to this exception: '
                       '%s' % e.__str__())
                handle_exception(Exception(msg), request)

        if (command == 'disable-auto-update'):
            try:
                auto_update(enable=False)
                return Response({'enabled': False, })
            except Exception as e:
                msg = ('Failed to disable auto update due to this exception:  '
                       '%s' % e.__str__())
                handle_exception(Exception(msg), request)

        if (command == 'refresh-pool-state'):
            self._refresh_pool_state()
            return Response()

        if (command == 'refresh-share-state'):
            for p in Pool.objects.all():
                import_shares(p, request)
            return Response()

        if (command == 'refresh-snapshot-state'):
            for share in Share.objects.all():
                import_snapshots(share)
            return Response()
