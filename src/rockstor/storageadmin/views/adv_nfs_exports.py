"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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
from storageadmin.models import (NFSExport, AdvancedNFSExport)
from storageadmin.util import handle_exception
from storageadmin.serializers import AdvancedNFSExportSerializer
import rest_framework_custom as rfc
import logging
from nfs_exports import NFSMixin

logger = logging.getLogger(__name__)


class AdvancedNFSExportView(NFSMixin, rfc.GenericView):
    serializer_class = AdvancedNFSExportSerializer

    def get_queryset(self, *args, **kwargs):
        conventional_exports = []
        exports_by_share = {}
        for e in NFSExport.objects.all():
            eg = e.export_group
            export_str = ('%s(%s,%s,%s)' % (eg.host_str, eg.editable,
                                            eg.syncable, eg.mount_security))
            if (e.share.name in exports_by_share):
                exports_by_share[e.share.name] += (' %s' % export_str)
            else:
                exports_by_share[e.share.name] = ('%s %s' %
                                                  (e.mount, export_str))
        for e in exports_by_share:
            exports_by_share[e] = ('Normally added -- %s' %
                                   exports_by_share[e])
            conventional_exports.append(
                AdvancedNFSExport(export_str=exports_by_share[e]))

        for ae in AdvancedNFSExport.objects.all():
            conventional_exports.append(ae)
        return conventional_exports

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            if ('entries' not in request.data):
                e_msg = ('Cannot export without specifying entries')
                handle_exception(Exception(e_msg), request)

            AdvancedNFSExport.objects.all().delete()
            cur_entries = []
            for e in request.data.get('entries'):
                logger.debug('adv export entry -- %s' % e)
                ce = AdvancedNFSExport(export_str=e)
                ce.save()
                cur_entries.append(ce)
            exports_d = self._create_adv_nfs_export_input(request.data['entries'],
                                                    request)
            cur_exports = list(NFSExport.objects.all())
            exports = self._create_nfs_export_input(cur_exports)
            exports.update(exports_d)
            self._refresh_wrapper(exports, request, logger)
            nfs_serializer = AdvancedNFSExportSerializer(cur_entries)
            return Response(nfs_serializer.data)
