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
from storageadmin.models import (Share, Snapshot, Disk, NFSExport, SambaShare)
from fs.btrfs import (update_quota, rollback_snap, set_property, mount_share)
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from clone_helpers import create_clone
from django.conf import settings
from system.osi import is_share_mounted
import logging
logger = logging.getLogger(__name__)


class ShareCommandView(rfc.GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        if ('sname' in self.kwargs):
            self.paginate_by = 0
            try:
                return Share.objects.get(name=self.kwargs['sname'])
            except:
                return []
        sort_col = self.request.query_params.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.query_params.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Share.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Share.objects.all()

    def _validate_share(self, request, sname):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share(%s) does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def _validate_snapshot(self, request, share):
        try:
            snap_name = request.data.get('name', '')
            return Snapshot.objects.get(share=share, name=snap_name)
        except:
            e_msg = ('Snapshot(%s) does not exist for this Share(%s)' %
                     (snap_name, share.name))
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def post(self, request, sname, command):
        with self._handle_exception(request):
            share = self._validate_share(request, sname)

            if (command == 'clone'):
                new_name = request.data.get('name', '')
                return create_clone(share, new_name, request, logger)

            if (command == 'rollback'):
                snap = self._validate_snapshot(request, share)

                if (NFSExport.objects.filter(share=share).exists()):
                    e_msg = ('Share(%s) cannot be rolled back as it is '
                             'exported via nfs. Delete nfs exports and '
                             'try again' % sname)
                    handle_exception(Exception(e_msg), request)

                if (SambaShare.objects.filter(share=share).exists()):
                    e_msg = ('Share(%s) cannot be rolled back as it is shared'
                             ' via Samba. Unshare and try again' % sname)
                    handle_exception(Exception(e_msg), request)

                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                rollback_snap(snap.real_name, share.name, share.subvol_name,
                              share.pool, pool_device)
                update_quota(share.pool, pool_device, snap.qgroup,
                             share.size * 1024)
                share.qgroup = snap.qgroup
                share.save()
                snap.delete()
                return Response()
