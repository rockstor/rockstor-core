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
view for anything at the share level
"""

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Share, Snapshot, Disk, Pool, Snapshot,
                                 NFSExport, SambaShare)
from fs.btrfs import (add_snap, share_id, update_quota, mount_share)
from storageadmin.serializers import (ShareSerializer, SnapshotSerializer)
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from django.conf import settings
from generic_view import GenericView
from clone_helpers import create_clone

import logging
logger = logging.getLogger(__name__)


class ShareCommandView(GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        if ('sname' in kwargs):
            self.paginate_by = 0
            try:
                return Share.objects.get(name=kwargs['sname'])
            except:
                return []
        sort_col = self.request.QUERY_PARAMS.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.QUERY_PARAMS.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Share.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Share.objects.all()

    @transaction.commit_on_success
    def post(self, request, sname, command):
        try:
            share = Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

        new_name = request.DATA['name']
        if (Share.objects.filter(name=new_name).exists()):
            e_msg = ('Share with name: %s already exists.' % new_name)
            handle_exception(Exception(e_msg), request)
        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        return create_clone(share, new_name, pool_device, request)
