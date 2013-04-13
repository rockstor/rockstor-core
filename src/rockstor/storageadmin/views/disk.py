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
Disk view, for anything at the disk level
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from storageadmin.forms import (DiskForm)
from storageadmin.models import (Disk)
from system.osi import (scan_disks)
from storageadmin.serializers import (DiskInfoSerializer,)
from storageadmin.util import handle_exception

import logging
logger = logging.getLogger(__name__)


class DiskView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication)
    permission_classes = (IsAuthenticated,)
    form = DiskForm

    def get(self, request, dname=None):
        try:
            if (dname is None):
                disks = Disk.objects.all()
                ds = DiskInfoSerializer(disks)
            else:
                ds = DiskInfoSerializer(Disk.objects.get(name=dname))
            return Response(ds.data)
        except Exception, e:
            logger.debug('request data: %s dname: %s' % (request.DATA, dname))
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request):
        try:
            d = Disk(name=self.CONTENT['name'], size=self.CONTENT['size'],
                    free=self.CONTENT['size'], parted=self.CONTENT['parted'])
            d.save()
            return Response(DiskInfoSerializer(d))
        except Exception, e:
            logger.debug('request data: %s dname: %s' % (request.DATA, dname))
            handle_exception(e, request)


"""
This view should become a setup view and move else where when setup becomes
more involved
"""
class SystemDiskView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication)
    permission_classes = (IsAuthenticated,)

    @transaction.commit_on_success
    def post(self, request):
        disks = scan_disks()
        for k,v in disks.items():
            if (Disk.objects.filter(name=v['name']).exists()):
                continue
            new_disk = Disk(name=v['name'], size=v['size'], free=v['free'], parted=v['parted'])
            new_disk.save()

        disks = Disk.objects.all()
        ds = DiskInfoSerializer(disks)
        return Response(ds.data)
