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
                                 NFSExportGroup, AdvancedNFSExport)
from fs.btrfs import (add_snap, share_id, share_usage, remove_snap,
                      umount_root, mount_snap)
from system.osi import refresh_nfs_exports
from storageadmin.serializers import SnapshotSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from nfs_helpers import (create_nfs_export_input, create_adv_nfs_export_input)
from share_helpers import toggle_sftp_visibility
from clone_helpers import create_clone

import logging
logger = logging.getLogger(__name__)


class SnapshotView(rfc.GenericView):
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

        snap_type = self.request.QUERY_PARAMS.get('snap_type', None)
        if (snap_type is not None and snap_type != ''):
            return Snapshot.objects.filter(
                share=share, snap_type=snap_type).order_by('-id')

        return Snapshot.objects.filter(share=share).order_by('-id')

    @transaction.commit_on_success
    def _toggle_visibility(self, share, snap_name, on=True):
        cur_exports = list(NFSExport.objects.all())
        snap_mnt_pt = ('%s%s/.%s' % (settings.MNT_PT, share.name, snap_name))
        export_pt = snap_mnt_pt.replace(settings.MNT_PT,
                                        settings.NFS_EXPORT_ROOT)
        if (on):
            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            mount_snap(share, snap_name, pool_device)

            if (NFSExport.objects.filter(share=share).exists()):
                se = NFSExport.objects.filter(share=share)[0]
                export_group = NFSExportGroup(
                    host_str=se.export_group.host_str, nohide=True)
                export_group.save()
                export = NFSExport(share=share, export_group=export_group,
                                   mount=snap_mnt_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)
        else:
            try:
                export = NFSExport.objects.get(share=share, mount=snap_mnt_pt)
                cur_exports.remove(export)
                export.export_group.delete()
                export.delete()
            except Exception, e:
                logger.exception(e)
            finally:
                umount_root(export_pt)
                umount_root(snap_mnt_pt)
        exports = create_nfs_export_input(cur_exports)
        adv_entries = [x.export_str for x in AdvancedNFSExport.objects.all()]
        exports_d = create_adv_nfs_export_input(adv_entries, self.request)
        exports.update(exports_d)
        refresh_nfs_exports(exports)

    @transaction.commit_on_success
    def _create(self, share, snap_name, pool_device, request, uvisible,
                snap_type, writable):
        if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
            e_msg = ('Snapshot with name: %s already exists for the '
                     'share: %s' % (snap_name, share.name))
            handle_exception(Exception(e_msg), request)

        try:
            real_name = snap_name
            snap_size = 0
            qgroup_id = '0/na'
            if (snap_type != 'receiver'):
                if (snap_type == 'replication'):
                    writable = False
                add_snap(share.pool, pool_device, share.subvol_name,
                         real_name, readonly=not writable)
                snap_id = share_id(share.pool, pool_device, real_name)
                qgroup_id = ('0/%s' % snap_id)
                snap_size = share_usage(share.pool, pool_device,
                                        qgroup_id)
            s = Snapshot(share=share, name=snap_name, real_name=real_name,
                         size=snap_size, qgroup=qgroup_id,
                         uvisible=uvisible, snap_type=snap_type,
                         writable=writable)
            s.save()
            return Response(SnapshotSerializer(s).data)
        except Exception, e:
            e_msg = ('Failed to create snapshot due to a system error.')
            logger.error(e_msg)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    def post(self, request, sname, snap_name, command=None):
        with self._handle_exception(request):
            share = self._validate_share(sname, request)
            uvisible = request.DATA.get('uvisible', False)
            if (type(uvisible) != bool):
                e_msg = ('uvisible must be a boolean, not %s' % type(uvisible))
                handle_exception(Exception(e_msg), request)

            snap_type = request.DATA.get('snap_type', 'admin')
            writable = request.DATA.get('writable', 'rw')
            writable = True if (writable == 'rw') else False
            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            if (command is None):
                ret = self._create(share, snap_name, pool_device, request,
                                   uvisible=uvisible, snap_type=snap_type,
                                   writable=writable)

                if (uvisible):
                    try:
                        self._toggle_visibility(share, ret.data['real_name'])
                    except Exception, e:
                        msg = ('Failed to make the Snapshot(%s) visible.' %
                               snap_name)
                        logger.error(msg)
                        logger.exception(e)

                    try:
                        toggle_sftp_visibility(share, ret.data['real_name'])
                    except Exception, e:
                        msg = ('Failed to make the Snapshot(%s) visible for '
                               'SFTP.' % snap_name)
                        logger.error(msg)
                        logger.exception(e)

                return ret
            if (command == 'clone'):
                new_name = request.DATA.get('name', None)
                snapshot = Snapshot.objects.get(share=share, name=snap_name)
                return create_clone(share, new_name, request, logger,
                                    snapshot=snapshot)
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
                e_msg = ('Snapshot with id: %s does not exist' % id)
            else:
                e_msg = ('Snapshot with name: %s does not exist' % snap_name)
            handle_exception(Exception(e_msg), request)

        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        if (snapshot.uvisible):
            e_msg = ('A low level error occured while deleting '
                     'snapshot(%s). Try again later.' % snapshot.name)
            try:
                self._toggle_visibility(share, snapshot.real_name, on=False)
            except Exception, e:
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

            try:
                toggle_sftp_visibility(share, snapshot.real_name, on=False)
            except Exception, e:
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

        try:
            remove_snap(share.pool, pool_device, sname, snapshot.name)
            snapshot.delete()
            return Response()
        except Exception, e:
            e_msg = ('Unable to delete snapshot due to a system error. Try '
                     'again later.')
            logger.error(e_msg)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    def delete(self, request, sname, snap_name=None):
        """
        deletes a snapshot
        """
        with self._handle_exception(request):
            if (snap_name is None):
                snap_qp = self.request.QUERY_PARAMS.get('id', None)
                if (snap_qp is not None):
                    for si in snap_qp.split(','):
                        self._delete_snapshot(request, sname, id=si)
            else:
                self._delete_snapshot(request, sname, snap_name=snap_name)
            return Response()
