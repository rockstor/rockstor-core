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
from storageadmin.models import (Share, SambaShare, NFSExport,
                                 NFSExportGroup, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import NFSExportGroupSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (mount_share, is_share_mounted, umount_root)
from system.osi import (refresh_nfs_exports, nfs4_mount_teardown)
from generic_view import GenericView
from nfs_helpers import (create_nfs_export_input, parse_options,
                         dup_export_check, validate_share, refresh_wrapper,
                         teardown_wrapper, validate_export_group)

import logging
logger = logging.getLogger(__name__)


class ShareNFSView(GenericView):
    serializer_class = NFSExportGroupSerializer

    def get_queryset(self, *args, **kwargs):
        share = validate_share(kwargs['sname'], self.request)
        if ('export_id' in kwargs):
            self.paginate_by = 0
            try:
                return NFSExportGroup.objects.get(id=kwargs['export_id'])
            except:
                return []
        exports = NFSExport.objects.filter(share=share)
        ids = [e.export_group.id for e in exports]
        return NFSExportGroup.objects.filter(nohide=False, id__in=ids)

    @transaction.commit_on_success
    def post(self, request, sname):
        try:
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
                mount_share(share.subvol_name, pool_device, mnt_pt)
            export = NFSExport(export_group=eg, share=share, mount=export_pt)
            export.full_clean()
            export.save()
            cur_exports.append(export)

            exports = create_nfs_export_input(cur_exports)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, sname, export_id):
        try:
            share = validate_share(sname, request)
            eg = validate_export_group(export_id, request)
            options = parse_options(request)
            dup_export_check(share, options['host_str'], request)
            NFSExportGroup.objects.filter(id=export_id).update(**options)
            NFSExportGroup.objects.filter(id=export_id)[0].save()
            cur_exports = list(NFSExport.objects.all())
            exports = create_nfs_export_input(cur_exports)
            refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, sname, export_id):
        try:
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
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
