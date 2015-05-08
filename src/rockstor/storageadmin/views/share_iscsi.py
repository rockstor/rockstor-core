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
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from django.db import transaction
from storageadmin.auth import DigestAuthentication
from storageadmin.models import (Share, SambaShare, NFSExport, Disk,
                                 IscsiTarget)
from storageadmin.util import handle_exception
from storageadmin.serializers import IscsiSerializer
from system.iscsi import export_iscsi
from fs.btrfs import mount_share

import logging
logger = logging.getLogger(__name__)


class ShareIscsiView(APIView):

    def get(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
            if (IscsiTarget.objects.filter(share=share).exists()):
                iscsi_o = IscsiTarget.objects.get(share=share)
                iscsi_serializer = IscsiSerializer(iscsi_o)
                return Response(iscsi_serializer.data)
            return Response()
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
            if (SambaShare.objects.filter(share=share).exists()):
                raise Exception('Already exported via Samba')

            if (NFSExport.objects.filter(share=share).exists()):
                raise Exception('Already exported via nfs')

            if (IscsiTarget.objects.filter(share=share).exists()):
                raise Exception('Already exported via iscsi')

            options = {
                'tname': 'fooscsi',
                'tid': -1,
                'dev_name': 'iscsi.img',
                'dev_size': 10,
                }
            if ('tname' in request.data):
                options['tname'] = request.data['tname']
            if ('tid' in request.data):
                try:
                    options['tid'] = int(request.data['tid'])
                except:
                    raise Exception('tid must be an integer')

            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            mnt_pt = '/mnt2/' + share.name
            mount_share(share.name, pool_device, mnt_pt)
            dev_name = mnt_pt + '/' + options['dev_name']
            export_iscsi(options['tid'], options['tname'], options['tid'],
                         dev_name, options['dev_size'])
            iscsi_target = IscsiTarget(share=share, tid=options['tid'],
                                       tname=options['tname'],
                                       dev_name=dev_name,
                                       dev_size=options['dev_size'])
            iscsi_target.save()
            iscsi_serializer = IscsiSerializer(iscsi_target)
            return Response(iscsi_serializer.data)

        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
            iscsi_target = IscsiTarget.objects.get(share=share)
            iscsi_target.delete()
            return Response()
        except Exception, e:
            handle_exception(e, request)
