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
System info etc..
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from system.osi import (uptime, refresh_nfs_exports, kernel_info)
from fs.btrfs import (mount_share, device_scan, mount_root, qgroup_create,
                      get_pool_info, pool_raid, pool_usage, shares_info,
                      share_usage, snaps_info, mount_snap)
from system.ssh import (sftp_mount_map, sftp_mount)
from system.services import systemctl
from system.osi import (is_share_mounted, system_shutdown, system_reboot)
from storageadmin.models import (Share, Disk, NFSExport, SFTP, Pool, Snapshot,
                                 UpdateSubscription)
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from django.db import transaction
from share_helpers import (sftp_snap_toggle, import_shares, import_snapshots)
from oauth2_provider.ext.rest_framework import OAuth2Authentication
from system.pkg_mgmt import (auto_update, current_version, update_check,
                             update_run, auto_update_status)
from nfs_exports import NFSExportMixin
import logging
logger = logging.getLogger(__name__)


class CommandView(NFSExportMixin, APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication, OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    @transaction.atomic
    def post(self, request, command):
        if (command == 'bootstrap'):

            for pool in Pool.objects.all():
                try:
                    mount_root(pool)
                except Exception, e:
                    e_msg = ('Exception while mounting a pool(%s) during '
                             'bootstrap: %s' % (pool.name, e.__str__()))
                    logger.error(e_msg)

            for share in Share.objects.all():
                try:
                    if (share.pqgroup == settings.MODEL_DEFS['pqgroup']):
                        share.pqgroup = qgroup_create(share.pool)
                        share.save()
                    if (not is_share_mounted(share.name)):
                        mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                        mount_share(share, mnt_pt)
                except Exception, e:
                    e_msg = ('Exception while mounting a share(%s) during '
                             'bootstrap: %s' % (share.name, e.__str__()))
                    logger.error(e_msg)

            for snap in Snapshot.objects.all():
                if (snap.uvisible):
                    try:
                        mount_snap(snap.share, snap.real_name)
                    except Exception, e:
                        e_msg = ('Failed to make the Snapshot(%s) visible. '
                                 'Exception: %s' % (snap.real_name, e.__str__()))
                        logger.error(e_msg)
                        logger.exception(e)

            mnt_map = sftp_mount_map(settings.SFTP_MNT_ROOT)
            for sftpo in SFTP.objects.all():
                try:
                    sftp_mount(sftpo.share, settings.MNT_PT,
                               settings.SFTP_MNT_ROOT, mnt_map, sftpo.editable)
                    sftp_snap_toggle(sftpo.share)
                except Exception, e:
                    e_msg = ('Exception while exportin a sftp share during '
                             'bootstrap: %s' % e.__str__())
                    logger.error(e_msg)

            try:
                exports = self.create_nfs_export_input(NFSExport.objects.all())
                refresh_nfs_exports(exports)
            except Exception, e:
                e_msg = ('Exception while exporting NFS: %s' % e.__str__())
                logger.error(e_msg)

            #  bootstrap services
            try:
                systemctl('firewalld', 'stop')
                systemctl('firewalld', 'disable')
                systemctl('nginx', 'stop')
                systemctl('nginx', 'disable')
                systemctl('atd', 'enable')
                systemctl('atd', 'start')
            except Exception, e:
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
            except Exception, e:
                handle_exception(e, request)

        if (command == 'update-check'):
            try:
                subo = None
                try:
                    subo = UpdateSubscription.objects.get(name='Stable', status='active')
                except UpdateSubscription.DoesNotExist:
                    try:
                        subo = UpdateSubscription.objects.get(name='Testing', status='active')
                    except UpdateSubscription.DoesNotExist:
                        pass
                return Response(update_check(subscription=subo))
            except Exception, e:
                e_msg = ('Unable to check update due to a system error: %s' % e.__str__())
                handle_exception(Exception(e_msg), request)

        if (command == 'update'):
            try:
                update_run()
                return Response('Done')
            except Exception, e:
                e_msg = ('Update failed due to this exception: %s' % e.__str__())
                handle_exception(Exception(e_msg), request)

        if (command == 'current-version'):
            try:
                return Response(current_version())
            except Exception, e:
                e_msg = ('Unable to check current version due to a this '
                         'exception: ' % e.__str__())
                handle_exception(Exception(e_msg), request)

        if (command == 'shutdown'):
            msg = ('The system will now be shutdown')
            try:
                request.session.flush()
                system_shutdown()
            except Exception, e:
                msg = ('Failed to shutdown the system due to a low level '
                       'error')
                logger.exception(e)
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        if (command == 'reboot'):
            msg = ('The system will now reboot')
            try:
                request.session.flush()
                system_reboot()
            except Exception, e:
                msg = ('Failed to reboot the system due to a low level error')
                logger.exception(e)
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
            except Exception, e:
                msg = ('Failed to enable auto update due to this exception: '
                       '%s' % e.__str__())
                handle_exception(Exception(msg), request)

        if (command == 'disable-auto-update'):
            try:
                auto_update(enable=False)
                return Response({'enabled': False, })
            except Exception, e:
                msg = ('Failed to disable auto update due to this exception:  '
                       '%s' % e.__str__())
                handle_exception(Exception(msg), request)

        if (command == 'refresh-pool-state'):
            for p in Pool.objects.all():
                fd = p.disk_set.first()
                if (fd is None):
                    p.delete()
                mount_root(p)
                pool_info = get_pool_info(fd.name)
                p.name = pool_info['label']
                p.raid = pool_raid('%s%s' % (settings.MNT_PT, p.name))['data']
                p.size = pool_usage('%s%s' % (settings.MNT_PT, p.name))[0]
                p.save()
            return Response()

        if (command == 'refresh-share-state'):
            for p in Pool.objects.all():
                import_shares(p, request)
            return Response()

        if (command == 'refresh-snapshot-state'):
            for share in Share.objects.all():
                import_snapshots(share)
            return Response()
