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

from datetime import datetime
from django.utils.timezone import utc
from rest_framework.response import Response
from django.db import transaction
from django.conf import settings
from storageadmin.models import (Snapshot, Share, Disk, NFSExport,
                                 NFSExportGroup, AdvancedNFSExport)
from smart_manager.models import ShareUsage
from fs.btrfs import (add_snap, share_id, share_usage, remove_snap,
                      umount_root, mount_snap, snaps_info, qgroup_assign)
from system.osi import refresh_nfs_exports
from storageadmin.serializers import SnapshotSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from share_helpers import toggle_sftp_visibility
from clone_helpers import create_clone
from nfs_exports import NFSExportMixin

import logging
logger = logging.getLogger(__name__)


class SnapshotView(NFSExportMixin, rfc.GenericView):
    serializer_class = SnapshotSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            try:
                share = Share.objects.get(name=self.kwargs['sname'])
            except:
                if ('sname' not in self.kwargs):
                    return Snapshot.objects.filter().order_by('-id')

                e_msg = ('Share with name: %s does not exist' % self.kwargs['sname'])
                handle_exception(Exception(e_msg), self.request)

            if ('snap_name' in self.kwargs):
                self.paginate_by = 0
                try:
                    return Snapshot.objects.get(share=share,
                                                name=self.kwargs['snap_name'])
                except:
                    return []

            snap_type = self.request.query_params.get('snap_type', None)
            if (snap_type is not None and snap_type != ''):
                return Snapshot.objects.filter(
                    share=share, snap_type=snap_type).order_by('-id')

            return Snapshot.objects.filter(share=share).order_by('-id')

    @transaction.atomic
    def _toggle_visibility(self, share, snap_name, on=True):
        cur_exports = list(NFSExport.objects.all())
        snap_mnt_pt = ('%s%s/.%s' % (settings.MNT_PT, share.name, snap_name))
        export_pt = snap_mnt_pt.replace(settings.MNT_PT,
                                        settings.NFS_EXPORT_ROOT)
        if (on):
            mount_snap(share, snap_name)

            if (NFSExport.objects.filter(share=share).exists()):
                se = NFSExport.objects.filter(share=share)[0]
                export_group = NFSExportGroup(
                    host_str=se.export_group.host_str, nohide=True)
                export_group.save()
                export = NFSExport(share=share, export_group=export_group,
                                   mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)
        else:
            for mnt in (snap_mnt_pt, export_pt):
                try:
                    export = NFSExport.objects.get(share=share, mount=mnt)
                    cur_exports.remove(export)
                    export.export_group.delete()
                    export.delete()
                except NFSExport.DoesNotExist:
                    pass
                except Exception, e:
                    logger.exception(e)
                finally:
                    umount_root(export_pt)
                    umount_root(snap_mnt_pt)
        exports = self.create_nfs_export_input(cur_exports)
        adv_entries = [x.export_str for x in AdvancedNFSExport.objects.all()]
        exports_d = self.create_adv_nfs_export_input(adv_entries, self.request)
        exports.update(exports_d)
        refresh_nfs_exports(exports)

    @transaction.atomic
    def _create(self, share, snap_name, request, uvisible, snap_type, writable):
        if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
            e_msg = ('Snapshot(%s) already exists for the Share(%s).' %
                     (snap_name, share.name))
            handle_exception(Exception(e_msg), request)

        snap_size = 0
        qgroup_id = '0/na'
        if (snap_type != 'receiver'):
            if (snap_type == 'replication'):
                writable = False
            add_snap(share.pool, share.subvol_name, snap_name, readonly=not
                     writable)
            snap_id = share_id(share.pool, snap_name)
            qgroup_id = ('0/%s' % snap_id)
            qgroup_assign(qgroup_id, share.pqgroup, ('%s/%s' % (settings.MNT_PT, share.pool.name)))
            snap_size, eusage = share_usage(share.pool, qgroup_id)
        s = Snapshot(share=share, name=snap_name, real_name=snap_name,
                     size=snap_size, qgroup=qgroup_id,
                     uvisible=uvisible, snap_type=snap_type,
                     writable=writable)
        s.save()
        return Response(SnapshotSerializer(s).data)

    def post(self, request, sname, snap_name, command=None):
        with self._handle_exception(request):
            share = self._validate_share(sname, request)
            uvisible = request.data.get('uvisible', False)
            if (type(uvisible) != bool):
                e_msg = ('uvisible must be a boolean, not %s' % type(uvisible))
                handle_exception(Exception(e_msg), request)

            snap_type = request.data.get('snap_type', 'admin')
            writable = request.data.get('writable', 'rw')
            writable = True if (writable == 'rw') else False
            if (command is None):
                ret = self._create(share, snap_name, request,
                                   uvisible=uvisible, snap_type=snap_type,
                                   writable=writable)

                if (uvisible):
                    try:
                        self._toggle_visibility(share, ret.data['real_name'])
                    except Exception, e:
                        msg = ('Failed to make the Snapshot(%s) visible. '
                               'Exception: %s' % (snap_name, e.__str__()))
                        logger.error(msg)
                        logger.exception(e)

                    try:
                        toggle_sftp_visibility(share, ret.data['real_name'])
                    except Exception, e:
                        msg = ('Failed to make the Snapshot(%s) visible for '
                               'SFTP. Exception: %s' % (snap_name, e.__str__()))
                        logger.error(msg)
                        logger.exception(e)

                return ret
            if (command == 'clone'):
                new_name = request.data.get('name', None)
                snapshot = Snapshot.objects.get(share=share, name=snap_name)
                return create_clone(share, new_name, request, logger,
                                    snapshot=snapshot)
            e_msg = ('Unknown command: %s' % command)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_share(sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _delete_snapshot(self, request, sname, id=None, snap_name=None):
        share = self._validate_share(sname, request)
        try:
            snapshot = None
            if (id is not None):
                snapshot = Snapshot.objects.get(id=id)
            elif (snap_name is not None):
                snapshot = Snapshot.objects.get(share=share, name=snap_name)
            else:
                return True
        except:
            e_msg = ''
            if (id is not None):
                e_msg = ('Snapshot(%s) does not exist.' % id)
            else:
                e_msg = ('Snapshot(%s) does not exist.' % snap_name)
            handle_exception(Exception(e_msg), request)

        if (snapshot.uvisible):
            self._toggle_visibility(share, snapshot.real_name, on=False)
            toggle_sftp_visibility(share, snapshot.real_name, on=False)

        remove_snap(share.pool, sname, snapshot.name)
        snapshot.delete()
        return Response()

    def delete(self, request, sname, snap_name=None):
        """
        deletes a snapshot
        """
        with self._handle_exception(request):
            if (snap_name is None):
                snap_qp = self.request.query_params.get('id', None)
                if (snap_qp is not None):
                    for si in snap_qp.split(','):
                        self._delete_snapshot(request, sname, id=si)
            else:
                self._delete_snapshot(request, sname, snap_name=snap_name)
            return Response()
