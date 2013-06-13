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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from django.db import transaction
from django.conf import settings
from storageadmin.auth import DigestAuthentication
from storageadmin.models import (Share, SambaShare, NFSExport, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import NFSExportSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (mount_share, is_share_mounted, umount_root)
from system.osi import refresh_nfs_exports

import logging
logger = logging.getLogger(__name__)


class ShareNFSView(APIView):

    def get(self, request, sname, export_id=None):
        try:
            share = Share.objects.get(name=sname)
            try:
                exports = None
                if (export_id is not None):
                    exports = NFSExport.objects.get(id=export_id)
                else:
                    exports = NFSExport.objects.filter(share=share)
                ns = NFSExportSerializer(exports)
                return Response(ns.data)
            except:
                return Response()
        except Exception, e:
            handle_exception(e, request)

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
                mount_share(share.name, pool_device, mnt_pt)

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

            if (is_share_mounted(share.name) and
                not SambaShare.objects.filter(share=share).exists() and
                not len(NFSExport.objects.filter(share=share)) > 1):
                umount_root(export.mount)
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
            exports.append(s_exports)
        logger.debug('exports: %s' % repr(exports))
        return exports
