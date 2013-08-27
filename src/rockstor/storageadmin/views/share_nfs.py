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
from storageadmin.models import (Share, SambaShare, NFSExport, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import NFSExportSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (mount_share, is_share_mounted, umount_root)
from system.osi import refresh_nfs_exports
from generic_view import GenericView

import logging
logger = logging.getLogger(__name__)


class ShareNFSView(GenericView):
    serializer_class = NFSExportSerializer

    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share with name: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        share = self._validate_share(kwargs['sname'], self.request)
        if ('export_id' in kwargs):
            self.paginate_by = 0
            try:
                return NFSExport.objects.get(id=kwargs['export_id'])
            except:
                return []
        return NFSExport.objects.filter(share=share)

    @transaction.commit_on_success
    def post(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
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

            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
            if (not is_share_mounted(share.name)):
                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                mount_share(share.subvol_name, pool_device, mnt_pt)

            export = NFSExport(share=share, mount=mnt_pt,
                               host_str=options['host_str'],
                               editable=options['mod_choice'],
                               syncable=options['sync_choice'],
                               mount_security=options['security'])
            export.full_clean()
            export.save()

            exports = self._create_nfs_export_input(export)
            refresh_nfs_exports(exports)
            nfs_serializer = NFSExportSerializer(export)
            return Response(nfs_serializer.data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, sname, export_id):
        try:
            share = Share.objects.get(name=sname)
            if (not NFSExport.objects.filter(id=export_id).exists()):
                e_msg = ('NFS export with id: %d does not exist' % export_id)
                handle_exception(Exception(e_msg), request)
            export = NFSExport.objects.get(id=export_id)

            if (len(NFSExport.objects.filter(share=share)) == 1):
                export_mnt_pt = ('/export/%s' % sname)
                umount_root(export_mnt_pt)
                if (is_share_mounted(sname, mnt_prefix='/export/')):
                    e_msg = ('Cannot delete nfs export with id: %d due to '
                             'busy mount. Try again later.' % export_id)
                    handle_exception(Exception(e_msg), request)

            export.enabled = False
            exports = self._create_nfs_export_input(export)
            export.delete()
            refresh_nfs_exports(exports)
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def _client_input(self, export):
        return {'client_str': export.host_str,
                'option_list': ('%s,%s,%s,no_root_squash' %
                                (export.editable, export.syncable,
                                 export.mount_security))}

    def _create_nfs_export_input(self, cur_export):
        exports = []
        for s in Share.objects.all():
            s_exports = {'clients': [],}
            if (cur_export.share.id == s.id and cur_export.enabled is True):
                s_exports['mount_point'] = cur_export.mount
                s_exports['clients'].append(self._client_input(cur_export))
            for e in NFSExport.objects.filter(share=s):
                s_exports['mount_point'] = e.mount
                if (e.id != cur_export.id):
                    s_exports['clients'].append(self._client_input(e))
            if (len(s_exports['clients']) > 0):
                exports.append(s_exports)
        logger.debug('exports: %s' % repr(exports))
        return exports
