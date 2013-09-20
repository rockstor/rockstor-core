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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Snapshot, Share, Disk)
from fs.btrfs import (add_snap, remove_snap, rollback_snap, share_id,
                      update_quota, share_usage)
from storageadmin.serializers import SnapshotSerializer
from storageadmin.util import handle_exception
from generic_view import GenericView

import logging
logger = logging.getLogger(__name__)


class SnapshotView(GenericView):
    serializer_class = SnapshotSerializer

    def get_queryset(self, *args, **kwargs):
        try:
            share = Share.objects.get(name=kwargs['sname'])
        except:
            e_msg = ('Share with name: %s does not exist' % kwargs['sname'])
            handle_exception(Exception(e_msg), self.request)

        if ('snap_name' in kwargs):
            self.paginate_by = None
            try:
                return Snapshot.objects.get(share=share,
                                            name=kwargs['snap_name'])
            except:
                return []

        return Snapshot.objects.filter(share=share)

    @transaction.commit_on_success
    def post(self, request, sname, snap_name, command=None):
        share = self._validate_share(sname, request)
        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        if (command is None):
            if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
                e_msg = ('Snapshot with name: %s already exists for the '
                         'share: %s' % (snap_name, sname))
                handle_exception(Exception(e_msg), request)

            add_snap(share.pool.name, pool_device, share.subvol_name,
                     snap_name)
            snap_id = share_id(share.pool.name, pool_device, snap_name)
            qgroup_id = ('0/%s' % snap_id)
            snap_size = share_usage(share.pool.name, pool_device, qgroup_id)
            s = Snapshot(share=share, name=snap_name, size=snap_size,
                         qgroup=qgroup_id)
            s.save()
            return Response(SnapshotSerializer(s).data)

        if (command == 'rollback'):
            try:
                snap = Snapshot.objects.get(share=share, name=snap_name)
            except:
                e_msg = ('Snapshot with name: %s does not exist for the '
                         'share: %s' % (snap_name, sname))
                handle_exception(Exception(e_msg), request)
            try:
                rollback_snap(snap_name, sname, share.subvol_name,
                              share.pool.name, pool_device)
                share.subvol_name = snap_name
                update_quota(share.pool.name, pool_device, snap.qgroup,
                             share.size * 1024)
                share.qgroup = snap.qgroup
                share.save()
                snap.delete()
                return Response()
            except Exception, e:
                logger.exception(e)
                handle_exception(e, request)
        else:
            e_msg = ('Unknown command: %s' % command)
            handle_exception(Exception(e_msg), request)


    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

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
            remove_snap(share.pool.name, pool_device, sname, snap_name)
            snapshot.delete()
        return Response()

