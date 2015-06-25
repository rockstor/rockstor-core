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
from storageadmin.models import (NFSExport, NFSExportGroup, Disk,
                                 AdvancedNFSExport)
from storageadmin.util import handle_exception
from storageadmin.serializers import NFSExportGroupSerializer
from fs.btrfs import (mount_share, is_share_mounted)
import rest_framework_custom as rfc
from nfs_helpers import (dup_export_check, refresh_wrapper,
                         teardown_wrapper, validate_export_group)
from share import ShareMixin
import logging
logger = logging.getLogger(__name__)

class NFSMixin(ShareMixin, object):


    @staticmethod
    def _client_input(export):
        eg = export.export_group
        ci = {'client_str': eg.host_str,
              'option_list': ('%s,%s,%s' % (eg.editable, eg.syncable,
                                            eg.mount_security))}
        if (eg.nohide):
            ci['option_list'] = ('%s,nohide' % ci['option_list'])
        ci['mnt_pt'] = export.mount.replace(settings.NFS_EXPORT_ROOT,
                                            settings.MNT_PT)
        if (eg.admin_host is not None):
            ci['admin_host'] = eg.admin_host
        return ci


    def _create_nfs_export_input(self, exports):
        exports_d = {}
        for e in exports:
            e_list = []
            export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, e.share.name))
            if (e.export_group.nohide):
                snap_name = e.mount.split('/')[-1]
                export_pt = ('%s/%s' % (export_pt, snap_name))
            if (export_pt in exports_d):
                e_list = exports_d[export_pt]
            e_list.append(self._client_input(e))
            exports_d[export_pt] = e_list
        return exports_d


    def _create_adv_nfs_export_input(self, exports, request):
        exports_d = {}
        for e in exports:
            fields = e.split()
            if (len(fields) < 2):
                e_msg = ('Invalid exports input -- %s' % e)
                handle_exception(Exception(e_msg), request)
            share = fields[0].split('/')[-1]
            s = self._validate_share(share, request)
            mnt_pt = ('%s%s' % (settings.MNT_PT, s.name))
            if (not is_share_mounted(s.name)):
                pool_device = Disk.objects.filter(pool=s.pool)[0].name
                mount_share(s, pool_device, mnt_pt)
            exports_d[fields[0]] = []
            for f in fields[1:]:
                cf = f.split('(')
                if (len(cf) != 2 or cf[1][-1] != ')'):
                    e_msg = ('Invalid exports input -- %s. offending '
                             'section: %s' % (e, f))
                    handle_exception(Exception(e_msg), request)
                exports_d[fields[0]].append(
                    {'client_str': cf[0], 'option_list': cf[1][:-1],
                     'mnt_pt': ('%s%s' % (settings.MNT_PT, share))})
        return exports_d


    @staticmethod
    def _parse_options(request):
            options = {
                'host_str': '*',
                'editable': 'ro',
                'syncable': 'async',
                'mount_security': 'insecure',
                'admin_host': None,
                }
            if ('host_str' in request.data):
                options['host_str'] = request.data['host_str']
            if ('mod_choice' in request.data and
                (request.data['mod_choice'] == 'ro' or
                 request.data['mod_choice'] == 'rw')):
                options['editable'] = request.data['mod_choice']
            if ('sync_choice' in request.data and
                (request.data['sync_choice'] == 'sync' or
                 request.data['sync_choice'] == 'async')):
                options['syncable'] = request.data['sync_choice']
            if ('admin_host' in request.data and
                len(request.data['admin_host']) > 0):
                options['admin_host'] = request.data['admin_host']
            return options


class NFSExportGroupListView(NFSMixin, rfc.GenericView):
    serializer_class = NFSExportGroupSerializer

    def get_queryset(self, *args, **kwargs):
        return NFSExportGroup.objects.filter(nohide=False)

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            if ('shares' not in request.data):
                e_msg = ('Cannot export without specifying shares')
                handle_exception(Exception(e_msg), request)
            shares = [self._validate_share(s, request) for s in request.data['shares']]
            options = self._parse_options(request)
            for s in shares:
                dup_export_check(s, options['host_str'], request)

            cur_exports = list(NFSExport.objects.all())
            eg = NFSExportGroup(**options)
            eg.save()
            for s in shares:
                mnt_pt = ('%s%s' % (settings.MNT_PT, s.name))
                export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, s.name))
                if (not is_share_mounted(s.name)):
                    pool_device = Disk.objects.filter(pool=s.pool)[0].name
                    mount_share(s, pool_device, mnt_pt)
                export = NFSExport(export_group=eg, share=s, mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)

            exports = self._create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in
                           AdvancedNFSExport.objects.all()]
            exports_d = self._create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)


class NFSExportGroupDetailView(ShareMixin, rfc.GenericView):
    serializer_class = NFSExportGroupSerializer

    def get(self, *args, **kwargs):
        try:
            data = NFSExportGroup.objects.get(id=self.kwargs['export_id'])
            serialized_data = NFSExportGroupSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


    @transaction.atomic
    def delete(self, request, export_id):
        with self._handle_exception(request):
            eg = validate_export_group(export_id, request)
            cur_exports = list(NFSExport.objects.all())
            for e in NFSExport.objects.filter(export_group=eg):
                export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, e.share.name))
                if (e.export_group.nohide):
                    snap_name = e.mount.split(e.share.name + '_')[-1]
                    export_pt = ('%s/%s' % (export_pt, snap_name))
                teardown_wrapper(export_pt, request, logger)
                cur_exports.remove(e)
                e.delete()
            eg.delete()
            exports = self._create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in
                           AdvancedNFSExport.objects.all()]
            exports_d = self._create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            refresh_wrapper(exports, request, logger)
            return Response()

    @transaction.atomic
    def put(self, request, export_id):
        with self._handle_exception(request):
            if ('shares' not in request.data):
                e_msg = ('Cannot export without specifying shares')
                handle_exception(Exception(e_msg), request)
            shares = [self._validate_share(s, request) for s in request.data['shares']]
            eg = validate_export_group(export_id, request)
            options = self._parse_options(request)
            for s in shares:
                dup_export_check(s, options['host_str'], request,
                                 export_id=int(export_id))
            NFSExportGroup.objects.filter(id=export_id).update(**options)
            NFSExportGroup.objects.filter(id=export_id)[0].save()
            cur_exports = list(NFSExport.objects.all())
            for e in NFSExport.objects.filter(export_group=eg):
                if (e.share not in shares):
                    cur_exports.remove(e)
                    e.delete()
                else:
                    shares.remove(e.share)
            for s in shares:
                mnt_pt = ('%s%s' % (settings.MNT_PT, s.name))
                export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, s.name))
                if (not is_share_mounted(s.name)):
                    pool_device = Disk.objects.filter(pool=s.pool)[0].name
                    mount_share(s, pool_device, mnt_pt)
                export = NFSExport(export_group=eg, share=s, mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)
            exports = self._create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in
                           AdvancedNFSExport.objects.all()]
            exports_d = self._create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)
