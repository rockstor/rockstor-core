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
from storageadmin.models import (NFSExport, NFSExportGroup, Disk)
from storageadmin.serializers import NFSExportGroupSerializer
from fs.btrfs import (mount_share, is_share_mounted)
import rest_framework_custom as rfc
from nfs_helpers import (create_nfs_export_input, parse_options,
                         dup_export_check, refresh_wrapper,
                         teardown_wrapper, validate_export_group)
from share_helpers import validate_share

import logging
logger = logging.getLogger(__name__)


class ListShareNFSView(rfc.GenericView):
    serializer_class = NFSExportGroupSerializer

    def get_queryset(self, *args, **kwargs):
        share = validate_share(self.kwargs['sname'], self.request)
        exports = NFSExport.objects.filter(share=share)
        ids = [e.export_group.id for e in exports]
        return NFSExportGroup.objects.filter(nohide=False, id__in=ids)

    @transaction.commit_on_success
    def post(self, request, sname):
        with self._handle_exception(request):
            share = validate_share(sname, request)
            options = parse_options(request)
            dup_export_check(share, options['host_str'], request)
            cur_exports = list(NFSExport.objects.all())
            eg = NFSExportGroup(**options)
            eg.save()
            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
            export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, share.name))
            if (not is_share_mounted(share.name)):
                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                mount_share(share, pool_device, mnt_pt)
            export = NFSExport(export_group=eg, share=share, mount=export_pt)
            export.full_clean()
            export.save()
            cur_exports.append(export)

            exports = create_nfs_export_input(cur_exports)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)
