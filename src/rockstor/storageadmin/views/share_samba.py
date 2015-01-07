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

from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import (Share, SambaShare, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import SambaShareSerializer
from fs.btrfs import (mount_share, is_share_mounted)
from system.samba import (refresh_smb_config, restart_samba)

import logging
logger = logging.getLogger(__name__)


class ShareSambaView(APIView):

    CREATE_MASKS = ('0777', '0755', '0744', '0700',)

    def get(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
            try:
                samba_o = SambaShare.objects.get(share=share)
                samba_serializer = SambaShareSerializer(samba_o)
                return Response(samba_serializer.data)
            except:
                return Response()
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request, sname):
        with self._handle_exception(request):
            share = Share.objects.get(name=sname)
            try:
                samba_o = SambaShare.objects.get(share=share)
                samba_serializer = SambaShareSerializer(samba_o)
                return Response(samba_serializer.data)
            except:
                options = {
                    'comment': ('samba for %s' % sname),
                    'browsable': 'yes',
                    'guest_ok': 'no',
                    'read_only': 'no',
                    'create_mask': '0755',
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

            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
            smb_share = SambaShare(share=share, path=mnt_pt,
                                   comment=options['comment'],
                                   browsable=options['browsable'],
                                   read_only=options['read_only'],
                                   guest_ok=options['guest_ok'],
                                   create_mask=options['create_mask'])
            smb_share.save()
            if (not is_share_mounted(share.name)):
                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                mount_share(share, pool_device, mnt_pt)
            refresh_smb_config(list(SambaShare.objects.all()))
            restart_samba()
            samba_serializer = SambaShareSerializer(smb_share)
            return Response(samba_serializer.data)

    @transaction.commit_on_success
    def delete(self, request, sname):
        with self._handle_exception(request):
            share = Share.objects.get(name=sname)
            if (not SambaShare.objects.filter(share=share).exists()):
                e_msg = ('Share is not exported via Samba. Nothing to delete')
                handle_exception(Exception(e_msg), request)
            samba_share = SambaShare.objects.get(share=share)
            samba_share.delete()
            refresh_smb_config(list(SambaShare.objects.all()))
            restart_samba()
            return Response()
