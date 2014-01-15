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
from storageadmin.models import (Share, SambaShare, Disk)
from storageadmin.serializers import SambaShareSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from generic_view import GenericView
from share_helpers import validate_share
from system.osi import (refresh_smb_config, restart_samba)
from fs.btrfs import (mount_share, is_share_mounted, umount_root)

import logging
logger = logging.getLogger(__name__)

class SambaView(GenericView):
    serializer_class = SambaShareSerializer
    CREATE_MASKS = ('0777', '0755', '0744', '0700',)

    def get_queryset(self, *args, **kwargs):
        if ('id' in kwargs):
            self.paginate_by = 0
            try:
                return SambaShare.objects.get(id=kwargs['id'])
            except:
                return []
        return SambaShare.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        if ('shares' not in request.DATA):
            e_msg = ('Must provide share names')
            handle_exception(Exception(e_msg), request)
        shares = [validate_share(s, request) for s in request.DATA['shares']]
        options = {
            'comment': 'samba export',
            'browsable': 'yes',
            'guest_ok': 'no',
            'read_only': 'no',
            'create_mask': '0755',
            'admin_users': 'Administrator',
            }
        if ('comment' in request.DATA):
            options['comment'] = request.DATA['comment']
        if ('browsable' in request.DATA):
            if (request.DATA['browsable'] != 'yes' and
                request.DATA['browsable'] != 'no'):
                e_msg = ('Invalid choice for browsable. Possible '
                         'choices are yes or no.')
                handle_exception(Exception(e_msg), request)
            options['browsable'] = request.DATA['browsable']
        if ('guest_ok' in request.DATA):
            if (request.DATA['guest_ok'] != 'yes' and
                request.DATA['guest_ok'] != 'no'):
                e_msg = ('Invalid choice for guest_ok. Possible '
                         'options are yes or no.')
                handle_exception(Exception(e_msg), request)
                options['guest_ok'] = request.DATA['guest_ok']
        if ('read_only' in request.DATA):
            if (request.DATA['read_only'] != 'yes' and
                request.DATA['read_only'] != 'no'):
                e_msg = ('Invalid choice for read_only. Possible '
                         'options are yes or no.')
                handle_exception(Exception(e_msg), request)
            options['read_only'] = request.DATA['read_only']
        if ('create_mask' in request.DATA):
            if (request.DATA['create_mask'] not in self.CREATE_MASKS):
                e_msg = ('Invalid choice for create_mask. Possible '
                         'options are: %s' % self.CREATE_MASKS)
                handle_exception(Exception(e_msg), request)
        if ('admin_users' in request.DATA):
            options['admin_users'] = request.DATA['admin_users']

        for share in shares:
            if (SambaShare.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) is already exported via Samba' %
                         share.name)
                handle_exception(Exception(e_msg), request)

        try:
            for share in shares:
                mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
                smb_share = SambaShare(share=share, path=mnt_pt,
                                       comment=options['comment'],
                                       browsable=options['browsable'],
                                       read_only=options['read_only'],
                                       guest_ok=options['guest_ok'],
                                       create_mask=options['create_mask'],
                                       admin_users=options['admin_users'])
                smb_share.save()
                if (not is_share_mounted(share.name)):
                    pool_device = Disk.objects.filter(pool=share.pool)[0].name
                    mount_share(share.subvol_name, pool_device, mnt_pt)
            refresh_smb_config(list(SambaShare.objects.all()))
            restart_samba()
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, id):
        try:
            smbo = SambaShare.objects.get(id=id)
            smbo.delete()
        except:
            e_msg = ('Samba export for the id(%s) does not exist' % id)
            handle_exception(Exception(e_msg), request)

        try:
            refresh_smb_config(list(SambaShare.objects.all()))
            restart_samba()
            return Response()
        except Exception, e:
            e_msg = ('System error occured while restarting Samba server')
            handle_exception(Exception(e_msg), request)

