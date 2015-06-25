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
from system.osi import (uptime, refresh_nfs_exports, update_check,
                        update_run, current_version, kernel_info)
from fs.btrfs import (mount_share, device_scan, mount_root)
from system.ssh import (sftp_mount_map, sftp_mount)
from system.services import (systemctl, join_winbind_domain, ads_join_status)
from system.osi import (is_share_mounted, system_shutdown, system_reboot)
from storageadmin.models import (Share, Disk, NFSExport, SFTP, Pool)
from nfs_helpers import create_nfs_export_input
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from sftp import SFTPMixin
from oauth2_provider.ext.rest_framework import OAuth2Authentication
from system.pkg_mgmt import install_pkg

import logging
logger = logging.getLogger(__name__)


class CommandView(SFTPMixin, APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication, OAuth2Authentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, command):
        if (command == 'bootstrap'):
            try:
                device_scan()
            except Exception, e:
                e_msg = ('Unabled to scan disk drives on the system.')
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            try:
                for pool in Pool.objects.all():
                    disk = Disk.objects.filter(pool=pool)[0].name
                    mount_root(pool, '/dev/%s' % disk)
            except Exception, e:
                e_msg = ('Unable to mount a pool(%s) during bootstrap.'
                         % pool.name)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            try:
                for share in Share.objects.all():
                    if (not is_share_mounted(share.name)):
                        mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                        pool_device = Disk.objects.filter(
                            pool=share.pool)[0].name
                        mount_share(share, pool_device, mnt_pt)
            except Exception, e:
                e_msg = ('Unable to mount a share(%s, %s) during bootstrap.' %
                         (pool_device, mnt_pt))
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            try:
                mnt_map = sftp_mount_map(settings.SFTP_MNT_ROOT)
                for sftpo in SFTP.objects.all():
                    sftp_mount(sftpo.share, settings.MNT_PT,
                               settings.SFTP_MNT_ROOT, mnt_map, sftpo.editable)
                    self._sftp_snap_toggle(sftpo.share)
            except Exception, e:
                e_msg = ('Unable to export all sftp shares due to a system'
                         ' error')
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            try:
                exports = create_nfs_export_input(NFSExport.objects.all())
                logger.info('export = %s' % exports)
                refresh_nfs_exports(exports)
            except Exception, e:
                e_msg = ('Unable to export all nfs shares due to a system'
                         'error')
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            #  bootstrap services
            try:
                systemctl('firewalld', 'stop')
                systemctl('firewalld', 'disable')
                systemctl('nginx', 'stop')
                systemctl('nginx', 'disable')
                systemctl('atd', 'enable')
                systemctl('atd', 'start')
            except Exception, e:
                e_msg = ('Unable to bootstrap services due to a system error')
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            return Response()

        elif (command == 'utcnow'):
            return Response(datetime.utcnow().replace(tzinfo=utc))

        elif (command == 'uptime'):
            return Response(uptime())

        elif (command == 'kernel'):
            try:
                return Response(kernel_info(settings.SUPPORTED_KERNEL_VERSION))
            except Exception, e:
                handle_exception(e, request)

        elif (command == 'update-check'):
            try:
                return Response(update_check())
            except Exception, e:
                e_msg = ('Unable to check update due to a system error')
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

        elif (command == 'update'):
            try:
                update_run()
                return Response('Done')
            except Exception, e:
                e_msg = ('Update failed due to a system error')
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

        elif (command == 'current-version'):
            try:
                return Response(current_version())
            except Exception, e:
                e_msg = ('Unable to check current version due to a system'
                         ' error')
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

        elif (command == 'join-winbind-domain'):
            try:
                systemctl('winbind', 'restart')
                username = request.data['administrator']
                passwd = request.data['password']
                join_winbind_domain(username, passwd)
                return Response('Done')
            except Exception, e:
                handle_exception(e, request)

        elif (command == 'winbind-domain-status'):
            msg = 'Yes'
            try:
                username = request.data['administrator']
                passwd = request.data['password']
            except Exception, e:
                handle_exception(e, request)

            try:
                ads_join_status(username, passwd)
            except Exception, e:
                logger.exception(e)
                msg = ('Domain join check failed. Low level error: %s %s' %
                       (e.out, e.err))
            finally:
                return Response(msg)

        elif (command == 'shutdown'):
            msg = ('The system will be shutdown after 1 minute')
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

        elif (command == 'reboot'):
            msg = ('The system will reboot after 1 minute')
            try:
                request.session.flush()
                system_reboot()
            except Exception, e:
                msg = ('Failed to reboot the system due to a low level error')
                logger.exception(e)
                handle_exception(Exception(msg), request)
            finally:
                return Response(msg)

        elif (command == 'current-user'):
            return Response(request.user.username)

        elif (command == 'auto-update-status'):
            status = True
            try:
                systemctl('yum-cron', 'status')
            except:
                status = False
            finally:
                return Response({'enabled': status, })

        elif (command == 'enable-auto-update'):
            try:
                install_pkg('yum-cron')
                systemctl('yum-cron', 'enable')
                systemctl('yum-cron', 'start')
            except Exception, e:
                msg = ('Failed to enable auto update due to a low level error')
                logger.exception(e)
                handle_exception(Exception(msg), request)
            finally:
                return Response({'enabled': True, })

        elif (command == 'disable-auto-update'):
            try:
                systemctl('yum-cron', 'stop')
                systemctl('yum-cron', 'disable')
            except Exception, e:
                msg = ('Failed to disable auto update due to a low level '
                       'error')
                logger.exception(e)
                handle_exception(Exception(msg), request)
            finally:
                return Response({'enabled': False, })
