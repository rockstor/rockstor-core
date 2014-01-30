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
View for things at snapshot level
"""

from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import (Snapshot, Share, Disk, NFSExport,
                                 NFSExportGroup)
from fs.btrfs import (add_snap, remove_share, share_id, update_quota,
                      share_usage)
from system.osi import refresh_nfs_exports
from storageadmin.serializers import SnapshotSerializer
from storageadmin.util import handle_exception
from generic_view import GenericView
from nfs_helpers import create_nfs_export_input
from clone_helpers import create_clone

import logging
logger = logging.getLogger(__name__)


class SnapshotView(GenericView):
    serializer_class = SnapshotSerializer

    def get_queryset(self, *args, **kwargs):
        try:
            share = Share.objects.get(name=kwargs['sname'])
        except:
            e_msg = ('Share with name: %s does not exist' % kwargs['sname'])
            handle_exception(Exception(e_msg), self.request)

        if ('snap_name' in kwargs):
            self.paginate_by = 0
            try:
                return Snapshot.objects.get(share=share,
                                            name=kwargs['snap_name'])
            except:
                return []

        return Snapshot.objects.filter(share=share)

    @transaction.commit_on_success
    def _toggle_visibility(self, share, snap_name, on=True):
        cur_exports = list(NFSExport.objects.all())
        for se in NFSExport.objects.filter(share=share):
            mnt_pt = ('%s%s/%s' % (settings.MNT_PT, share.pool.name,
                                   snap_name))
            export_pt = mnt_pt.replace(settings.MNT_PT,
                                       settings.NFS_EXPORT_ROOT)
            export = None
            if (on):
                if (se.export_group.nohide is False):
                    continue

                export_group = NFSExportGroup(host_str=se.host_str,
                                              nohide=True)
                export_group.save()
                export = NFSExport(share=share, export_group=export_group,
                                   mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)
            else:
                try:
                    export = NFSExport.objects.get(share=share,
                                                   mount=export_pt)
                    export.delete()
                    export.export_group.delete()
                    cur_exports.remove(export)
                except Exception, e:
                    logger.exception(e)
                    continue
        exports = create_nfs_export_input(cur_exports)
        refresh_nfs_exports(exports)
        return True

    @transaction.commit_on_success
    def _create(self, share, snap_name, pool_device, request, uvisible):
        if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
            e_msg = ('Snapshot with name: %s already exists for the '
                     'share: %s' % (snap_name, share.name))
            handle_exception(Exception(e_msg), request)

        try:
            real_name = ('%s_%s' % (share.name, snap_name))
            add_snap(share.pool.name, pool_device, share.subvol_name,
                     real_name, share_prepend=False)
            snap_id = share_id(share.pool.name, pool_device, real_name)
            qgroup_id = ('0/%s' % snap_id)
            snap_size = share_usage(share.pool.name, pool_device, qgroup_id)
            s = Snapshot(share=share, name=snap_name, real_name=real_name,
                         size=snap_size, qgroup=qgroup_id, uvisible=uvisible)
            s.save()
            return Response(SnapshotSerializer(s).data)
        except Exception, e:
            e_msg = ('Failed to create snapshot due to a system error.')
            logger.error(e_msg)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    def post(self, request, sname, snap_name, command=None):
        share = self._validate_share(sname, request)
        uvisible = False
        if (request.DATA is not None and 'uvisible' in request.DATA):
            uvisible = request.DATA['uvisible']
            if (type(uvisible) != bool):
                e_msg = ('uvisible must be a boolean, not %s' % type(uvisible))
                handle_exception(Exception(e_msg), request)
        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        if (command is None):
            ret = self._create(share, snap_name, pool_device, request,
                               uvisible=uvisible)
            if (uvisible):
                try:
                    self._toggle_visibility(share, ret.data['real_name'])
                except Exception, e:
                    msg = ('snapshot created but nfs exporting it failed')
                    logger.error(msg)
                    logger.exception(e)
            return ret
        if (command == 'clone'):
            new_name = request.DATA['name']
            return create_clone(share, new_name, request, logger)
        e_msg = ('Unknown command: %s' % command)
        handle_exception(Exception(e_msg), request)

    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def put(self, request):
        """
        to make a snapshot writable etc..
        """
        pass

    @transaction.commit_on_success
    def delete(self, request, sname, snap_name):
        """
        deletes a snapshot
        """
        share = self._validate_share(sname, request)
        try:
            snapshot = Snapshot.objects.get(share=share, name=snap_name)
        except:
            e_msg = ('Snapshot with name: %s does not exist' % snap_name)
            handle_exception(Exception(e_msg), request)

        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        try:
            if (snapshot.uvisible):
                self._toggle_visibility(share, snapshot.real_name, on=False)
        except Exception, e:
            e_msg = ('Unable to nfs unexport the snapshot, requirement for '
                     'deletion. Try again later')
            logger.error(e_msg)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

        try:
            remove_share(share.pool.name, pool_device, snapshot.real_name)
            snapshot.delete()
            return Response()
        except Exception, e:
            e_msg = ('Unable to delete snapshot due to a system error. Try '
                     'again later.')
            logger.error(e_msg)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)
