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

from storageadmin.models import (Appliance, Disk, Group, NetworkInterface,
                                 Pool, Share, NFSExport, NFSExportGroup,
                                 )
from storageadmin.serializers import (ApplianceSerializer, DiskInfoSerializer,
                                      GroupSerializer, NetworkInterfaceSerializer,
                                      PoolInfoSerializer, ShareSerializer,
                                      NFSExportGroupSerializer)
from nfs_helpers import (create_nfs_export_input, parse_options,
                         dup_export_check, refresh_wrapper,
                         validate_export_group, teardown_wrapper)
from share_helpers import validate_share

import rest_framework_custom as rfc
from rest_framework.response import Response
from rest_framework.generics import UpdateAPIView
from storageadmin.util import handle_exception
from fs.btrfs import share_usage, share_id, update_quota
from django.db import transaction
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


class ApplianceDetailView(rfc.GenericView):
    serializer_class = ApplianceSerializer

    def get(self, *args, **kwargs):
        if 'ip' in self.kwargs or 'id' in self.kwargs:
            try:
                if 'ip' in self.kwargs:
                    data = Appliance.objects.get(ip=self.kwargs['ip'])
                else:
                    data = Appliance.objects.get(id=self.kwargs['id'])
                serialized_data = ApplianceSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()


class DiskDetailView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get(self, *args, **kwargs):
        if 'dname' in self.kwargs:
            try:
                data = Disk.objects.get(name=self.kwargs['dname'])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()


class GroupDetailView(rfc.GenericView):
    serializer_class = GroupSerializer

    def get(self, *args, **kwargs):
        try:
            data = Group.objects.get(username=self.kwargs['groupname'])
            serialized_data = GroupSerializer(data)
            return Response(serialized_data.data)
        except:
            # Render no response if no matches
            return Response()


class NetworkDetailView(rfc.GenericView):
    serializer_class = NetworkInterfaceSerializer

    def get(self, *args, **kwargs):
        try:
            data = NetworkInterface.objects.get(name=self.kwargs['iname'])
            serialized_data = NetworkInterfaceSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


class PoolDetailView(rfc.GenericView):
    serializer_class = PoolInfoSerializer

    def get(self, *args, **kwargs):
        try:
            data = Pool.objects.get(name=self.kwargs['pname'])
            serialized_data = PoolInfoSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


class DetailShareView(rfc.GenericView, UpdateAPIView):
    serializer_class = ShareSerializer

    def get(self, *args, **kwargs):
        try:
            data = Share.objects.get(name=self.kwargs['sname'])
            serialized_data = ShareSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()

    def _validate_share_size(self, request, pool):
        size = request.data.get('size', pool.size)
        try:
            size = int(size)
        except:
            handle_exception(Exception('Share size must be an integer'),
                             request)
        if (size < settings.MIN_SHARE_SIZE):
            e_msg = ('Share size should atleast be %dKB. Given size is %dKB'
                     % (settings.MIN_SHARE_SIZE, size))
            handle_exception(Exception(e_msg), request)
        if (size > pool.size):
            return pool.size
        return size

    def _update_quota(self, pool, disk_name, share_name, size):
        sid = share_id(pool, disk_name, share_name)
        qgroup_id = '0/' + sid
        update_quota(pool, disk_name, qgroup_id, size * 1024)
        return qgroup_id

    @transaction.atomic
    def put(self, request, sname):
        with self._handle_exception(request):
            if (not Share.objects.filter(name=sname).exists()):
                e_msg = ('Share(%s) does not exist.' % sname)
                handle_exception(Exception(e_msg), request)

            share = Share.objects.get(name=sname)
            new_size = self._validate_share_size(request, share.pool)
            disk = Disk.objects.filter(pool=share.pool)[0]
            qgroup_id = self._update_quota(share.pool, disk.name,
                                           share.subvol_name, new_size)
            cur_usage = share_usage(share.pool, disk.name, qgroup_id)
            if (new_size < cur_usage):
                e_msg = ('Unable to resize because requested new size(%dKB) '
                         'is less than current usage(%dKB) of the share.' %
                         (new_size, cur_usage))
                handle_exception(Exception(e_msg), request)
            share.size = new_size
            share.save()
            return Response(ShareSerializer(share).data)


class DetailShareNFSView(rfc.GenericView, UpdateAPIView):

    def get(self, *args, **kwargs):
        if ('export_id' in self.kwargs):
            self.paginate_by = 0
            try:
                return NFSExportGroup.objects.get(id=self.kwargs['export_id'])
            except:
                return Response()

    @transaction.commit_on_success
    def put(self, request, sname, export_id):
        with self._handle_exception(request):
            share = validate_share(sname, request)
            eg = validate_export_group(export_id, request)
            options = parse_options(request)
            dup_export_check(share, options['host_str'], request,
                             export_id=int(export_id))
            NFSExportGroup.objects.filter(id=export_id).update(**options)
            NFSExportGroup.objects.filter(id=export_id)[0].save()
            cur_exports = list(NFSExport.objects.all())
            exports = create_nfs_export_input(cur_exports)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)

    @transaction.commit_on_success
    def delete(self, request, sname, export_id):
        with self._handle_exception(request):
            share = validate_share(sname, request)
            eg = validate_export_group(export_id, request)
            cur_exports = list(NFSExport.objects.all())
            export = NFSExport.objects.get(export_group=eg, share=share)
            for e in NFSExport.objects.filter(share=share):
                if (e.export_group.host_str == eg.host_str):
                    export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT,
                                           share.name))
                    if (e.export_group.nohide):
                        snap_name = e.mount.split(e.share.name + '_')[-1]
                        export_pt = ('%s%s/%s' % (settings.NFS_EXPORT_ROOT,
                                                  e.share.name, snap_name))
                    teardown_wrapper(export_pt, request, logger)
                    cur_exports.remove(e)
            exports = create_nfs_export_input(cur_exports)
            export.delete()
            if (NFSExport.objects.filter(export_group=eg).count() == 0):
                #delete only when this is the only share in the group
                eg.delete()
            refresh_wrapper(exports, request, logger)
            return Response()
