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

from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import SFTP
from storageadmin.util import handle_exception
from storageadmin.serializers import SFTPSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (is_share_mounted, umount_root)
from system.ssh import (update_sftp_config, sftp_mount_map, sftp_mount,
                        rsync_for_sftp)
from share_helpers import (helper_mount_share, validate_share)
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)


class SFTPView(rfc.GenericView):
    serializer_class = SFTPSerializer

    def get_queryset(self, *args, **kwargs):
        if ('id' in kwargs):
            self.paginate_by = 0
            try:
                return SFTP.objects.get(id=kwargs['id'])
            except:
                return []
        return SFTP.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        if ('shares' not in request.DATA):
            e_msg = ('Must provide share names')
            handle_exception(Exception(e_msg), request)
        shares = [validate_share(s, request) for s in request.DATA['shares']]
        editable = 'rw'
        if ('read_only' in request.DATA and request.DATA['read_only'] is True):
            editable = 'ro'
        try:
            mnt_map = sftp_mount_map(settings.SFTP_MNT_ROOT)
            logger.info('mount map: %s' % mnt_map)
            input_list = []
            for share in shares:
                if (SFTP.objects.filter(share=share).exists()):
                    e_msg = ('Share(%s) is already exported via SFTP' %
                             share.name)
                    handle_exception(Exception(e_msg), request)
                if (share.owner == 'root'):
                    e_msg = ('Share(%s) is owned by root. It cannot be '
                             'exported via SFTP with root ownership' %
                             share.name)
                    handle_exception(Exception(e_msg), request)
            for share in shares:
                sftpo = SFTP(share=share, editable=editable)
                sftpo.save()
                #  mount if not already mounted
                helper_mount_share(share)
                #  bindmount if not already
                sftp_mount(share, settings.MNT_PT, settings.SFTP_MNT_ROOT,
                           mnt_map, editable)
                chroot_loc = ('%s%s' % (settings.SFTP_MNT_ROOT, share.owner))
                rsync_for_sftp(chroot_loc)
                input_list.append({'user': share.owner,
                                   'dir': chroot_loc, })
            for sftpo in SFTP.objects.all():
                if (sftpo.share not in shares):
                    input_list.append({'user': sftpo.share.owner,
                                       'dir': ('%s%s' %
                                               (settings.SFTP_MNT_ROOT,
                                                sftpo.share.owner)), })
            update_sftp_config(input_list)
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, id):
        try:
            sftpo = SFTP.objects.get(id=id)
        except:
            e_msg = ('SFTP config for the id(%s) does not exist' % id)
            handle_exception(Exception(e_msg), request)

        try:
            mnt_prefix = ('%s%s/' % (settings.SFTP_MNT_ROOT,
                                     sftpo.share.owner))
            if (is_share_mounted(sftpo.share.name, mnt_prefix)):
                umount_root(('%s%s' % (mnt_prefix, sftpo.share.name)))
                import shutil
                shutil.rmtree(mnt_prefix)
            sftpo.delete()
            input_list = []
            for so in SFTP.objects.all():
                if (so.id != sftpo.id):
                    input_list.append({'user': so.share.owner,
                                       'dir': ('%s%s' %
                                               (settings.SFTP_MNT_ROOT,
                                                so.share.name)),})
            update_sftp_config(input_list)
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
