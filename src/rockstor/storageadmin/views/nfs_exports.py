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
from nfs_helpers import create_nfs_export_input

import logging
logger = logging.getLogger(__name__)


class NFSExportGroupView(GenericView):
    serializer_class = NFSExportGroupSerializer

    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share with name: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        if ('export_id' in kwargs):
            self.paginate_by = 0
            try:
                return NFSExportGroup.objects.get(id=kwargs['export_id'])
            except:
                return []
        return NFSExportGroup.objects.filter(nohide=False)

    @transaction.commit_on_success
    def post(self, request):
        if ('shares' not in request.DATA):
            e_msg = ('Cannot export without specifying shares')
            handle_exception(Exception(e_msg), request)
        shares = [self._validate_share(s, request) for s in
                  request.DATA['shares']]
        try:
            options = {
                'host_str': '*',
                'mod_choice': 'ro',
                'sync_choice': 'async',
                'security': 'insecure',
                'id': -1,
                }
            if ('host_str' in request.DATA):
                options['host_str'] = request.DATA['host_str']
            if ('mod_choice' in request.DATA):
                options['mod_choice'] = request.DATA['mod_choice']
            if ('sync_choice' in request.DATA):
                options['sync_choice'] = request.DATA['sync_choice']

            cur_exports = list(NFSExport.objects.all())
            eg = NFSExportGroup(host_str=options['host_str'],
                                editable=options['mod_choice'],
                                syncable=options['sync_choice'],
                                mount_security=options['security'])
            eg.save()
            for s in shares:
                mnt_pt = ('%s%s' % (settings.MNT_PT, s.name))
                export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, s.name))
                if (not is_share_mounted(s.name)):
                    pool_device = Disk.objects.filter(pool=s.pool)[0].name
                    mount_share(s.subvol_name, pool_device, mnt_pt)
                export = NFSExport(export_group=eg, share=s, mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)

            exports = create_nfs_export_input(cur_exports)
            refresh_nfs_exports(exports)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, export_id):
        try:
            if (not NFSExportGroup.objects.filter(id=export_id).exists()):
                e_msg = ('NFS export group with id: %d does not exist' %
                         export_id)
                handle_exception(Exception(e_msg), request)
            eg = NFSExportGroup.objects.get(id=export_id)
            cur_exports = list(NFSExport.objects.all())
            for e in NFSExport.objects.filter(export_group=eg):
                export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, e.share.name))
                if (e.export_group.nohide):
                    snap_name = e.mount.split(e.share.name + '_')[-1]
                    export_pt = ('%s/%s' % (export_pt, snap_name))
                try:
                    nfs4_mount_teardown(export_pt)
                except Exception, e:
                    e_msg = ('Unable to delete the export(%s) because it is '
                             'in use' % (export_pt))
                    logger.exception(e)
                    handle_exception(Exception(e_msg), request)
                cur_exports.remove(e)
                e.delete()
            eg.delete()
            exports = create_nfs_export_input(cur_exports)
            try:
                refresh_nfs_exports(exports)
            except Exception, e:
                e_msg = ('Unable to delete the export because it is in use.'
                         ' Try again Later')
                logger.exception(e)
                handle_exception(Exception(e_msg), request)
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
