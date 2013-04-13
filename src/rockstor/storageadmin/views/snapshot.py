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
View for things at snapshot level
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from storageadmin.auth import DigestAuthentication
from django.db import transaction

from storageadmin.models import (Snapshot, Share, Disk)
from fs.btrfs import (add_snap, remove_snap)
from storageadmin.serializers import SnapshotSerializer

import logging
logger = logging.getLogger(__name__)


class SnapshotView(APIView):

    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, sname, snap_name=None):
        try:
            share = Share.objects.get(name=sname)
        except:
            msg = ('Share with name: %s does not exist' % sname)
            logger.error(msg)
            raise Exception(msg)

        snap_info = None
        if (snap_name is None):
            snap_info = Response(SnapshotSerializer(share.snapshot_set.all()).data)
        else:
            try:
                snapshot = Snapshot.objects.get(share=share, name=snap_name)
                snap_info = Response(SnapshotSerializer(snapshot).data)
            except:
                msg = ('Snapshot with name: %s does not exist' % snap_name)
                logger.error(msg)
                raise Exception(msg)
        return snap_info

    @transaction.commit_on_success
    def post(self, request, sname):
        snap_name = request.DATA['name']
        share = Share.objects.get(name=sname)
        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        s = Snapshot(share=share, name=snap_name)
        add_snap(share.pool.name, pool_device, sname, snap_name)
        s.save()
        return Response(SnapshotSerializer(s).data)

    @transaction.commit_on_success
    def put(self, request):
        """
        to make a snapshot writable etc..
        """
        pass

    @transaction.commit_on_success
    def delete(self, request, sname, snap_name):
        """
        deletes a snapshot
        """
        share = Share.objects.get(name=sname)
        if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
            snapshot = Snapshot.objects.get(share=share, name=snap_name)
            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            remove_snap(share.pool.name, pool_device, snap_name)
            snapshot.delete()
        return Response()

