"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
from storageadmin.models import NFSExport, NFSExportGroup, AdvancedNFSExport
from storageadmin.util import handle_exception
from storageadmin.serializers import (
    NFSExportGroupSerializer,
    AdvancedNFSExportSerializer,
)
from fs.btrfs import mount_share
from system.osi import refresh_nfs_exports, nfs4_mount_teardown
from share_helpers import validate_share
import rest_framework_custom as rfc
from rest_framework.exceptions import NotFound
import logging

logger = logging.getLogger(__name__)


class NFSExportMixin(object):
    @staticmethod
    def client_input(export):
        eg = export.export_group
        ci = {
            "client_str": eg.host_str,
            "option_list": ("%s,%s,%s" % (eg.editable, eg.syncable, eg.mount_security)),
        }

        ci["mnt_pt"] = export.mount.replace(settings.NFS_EXPORT_ROOT, settings.MNT_PT)
        if eg.admin_host is not None:
            if eg.admin_host == eg.host_str:
                ci["option_list"] = "rw,no_root_squash,%s,%s" % (
                    eg.syncable,
                    eg.mount_security,
                )
            else:
                ci["admin_host"] = eg.admin_host
        if eg.nohide:
            ci["option_list"] = "%s,nohide" % ci["option_list"]
        return ci

    @staticmethod
    def create_adv_nfs_export_input(exports, request):
        exports_d = {}
        for e in exports:
            fields = e.split()
            if len(fields) < 2:
                e_msg = "Invalid exports input -- ({}).".format(e)
                handle_exception(Exception(e_msg), request)
            share = fields[0].split("/")[-1]
            s = validate_share(share, request)
            mnt_pt = "%s%s" % (settings.MNT_PT, s.name)
            if not s.is_mounted:
                mount_share(s, mnt_pt)
            exports_d[fields[0]] = []
            for f in fields[1:]:
                cf = f.split("(")
                if len(cf) != 2 or cf[1][-1] != ")":
                    e_msg = (
                        "Invalid exports input -- ({}). Offending section: ({})."
                    ).format(e, f)
                    handle_exception(Exception(e_msg), request)
                exports_d[fields[0]].append(
                    {
                        "client_str": cf[0],
                        "option_list": cf[1][:-1],
                        "mnt_pt": ("%s%s" % (settings.MNT_PT, share)),
                    }
                )
        return exports_d

    @classmethod
    def create_nfs_export_input(cls, exports):
        exports_d = {}
        for e in exports:
            e_list = []
            export_pt = "%s%s" % (settings.NFS_EXPORT_ROOT, e.share.name)
            if e.export_group.nohide:
                snap_name = e.mount.split("/")[-1]
                export_pt = "%s/%s" % (export_pt, snap_name)
            if export_pt in exports_d:
                e_list = exports_d[export_pt]
            e_list.append(cls.client_input(e))
            exports_d[export_pt] = e_list
        return exports_d

    @staticmethod
    def parse_options(request):
        options = {
            "host_str": "*",
            "editable": "ro",
            "syncable": "async",
            "mount_security": "insecure",
            "admin_host": None,
        }
        options["host_str"] = request.data.get("host_str", options["host_str"])
        options["editable"] = request.data.get("mod_choice", options["editable"])
        options["syncable"] = request.data.get("sync_choice", options["syncable"])
        options["admin_host"] = request.data.get("admin_host", options["admin_host"])
        if (
            options["admin_host"] is not None
            and len(options["admin_host"].strip()) == 0
        ):
            options["admin_host"] = None
        return options

    @staticmethod
    def dup_export_check(share, host_str, request, export_id=None):
        for e in NFSExport.objects.filter(share=share):
            if e.export_group.host_str == host_str:
                if e.export_group.id == export_id:
                    continue
                e_msg = ("An export already exists for the host string: ({}).").format(
                    host_str
                )
                handle_exception(Exception(e_msg), request)

    @staticmethod
    def validate_export_group(export_id, request):
        try:
            return NFSExportGroup.objects.get(id=export_id)
        except:
            e_msg = ("NFS export with id ({}) does not exist.").format(export_id)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def refresh_wrapper(exports, request, logger):
        try:
            refresh_nfs_exports(exports)
        except Exception as e:
            e_msg = (
                "A lower level error occurred while refreshing NFS exports: ({})."
            ).format(e.__str__())
            handle_exception(Exception(e_msg), request)


class NFSExportGroupListView(NFSExportMixin, rfc.GenericView):
    serializer_class = NFSExportGroupSerializer

    def get_queryset(self, *args, **kwargs):
        return NFSExportGroup.objects.filter(nohide=False)

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            if "shares" not in request.data:
                e_msg = "Cannot export without specifying shares."
                handle_exception(Exception(e_msg), request)
            shares = [validate_share(s, request) for s in request.data["shares"]]
            options = self.parse_options(request)
            for s in shares:
                self.dup_export_check(s, options["host_str"], request)

            cur_exports = list(NFSExport.objects.all())
            eg = NFSExportGroup(**options)
            eg.save()
            for s in shares:
                mnt_pt = "%s%s" % (settings.MNT_PT, s.name)
                export_pt = "%s%s" % (settings.NFS_EXPORT_ROOT, s.name)
                mount_share(s, mnt_pt)
                export = NFSExport(export_group=eg, share=s, mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)

            exports = self.create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in AdvancedNFSExport.objects.all()]
            exports_d = self.create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            self.refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)


class NFSExportGroupDetailView(NFSExportMixin, rfc.GenericView):
    serializer_class = NFSExportGroupSerializer

    def get(self, *args, **kwargs):
        try:
            data = NFSExportGroup.objects.get(id=self.kwargs["export_id"])
            serialized_data = NFSExportGroupSerializer(data)
            return Response(serialized_data.data)
        except NFSExportGroup.DoesNotExist:
            raise NotFound(detail=None)

    @transaction.atomic
    def delete(self, request, export_id):
        with self._handle_exception(request):
            eg = self.validate_export_group(export_id, request)
            cur_exports = list(NFSExport.objects.all())
            for e in NFSExport.objects.filter(export_group=eg):
                export_pt = "%s%s" % (settings.NFS_EXPORT_ROOT, e.share.name)
                if e.export_group.nohide:
                    snap_name = e.mount.split(e.share.name + "_")[-1]
                    export_pt = "%s/%s" % (export_pt, snap_name)
                nfs4_mount_teardown(export_pt)
                cur_exports.remove(e)
                e.delete()
            # Following conditional delete was informed by test_nfs_export.py:
            if eg.id is not None:
                eg.delete()
            exports = self.create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in AdvancedNFSExport.objects.all()]
            exports_d = self.create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            self.refresh_wrapper(exports, request, logger)
            return Response()

    @transaction.atomic
    def put(self, request, export_id):
        with self._handle_exception(request):
            if "shares" not in request.data:
                e_msg = "Cannot export without specifying shares."
                handle_exception(Exception(e_msg), request)
            shares = [validate_share(s, request) for s in request.data["shares"]]
            eg = self.validate_export_group(export_id, request)
            options = self.parse_options(request)
            for s in shares:
                self.dup_export_check(
                    s, options["host_str"], request, export_id=int(export_id)
                )
            NFSExportGroup.objects.filter(id=export_id).update(**options)
            NFSExportGroup.objects.filter(id=export_id)[0].save()
            cur_exports = list(NFSExport.objects.all())
            for e in NFSExport.objects.filter(export_group=eg):
                if e.share not in shares:
                    cur_exports.remove(e)
                    e.delete()
                else:
                    shares.remove(e.share)
            for s in shares:
                mnt_pt = "%s%s" % (settings.MNT_PT, s.name)
                export_pt = "%s%s" % (settings.NFS_EXPORT_ROOT, s.name)
                if not s.is_mounted:
                    mount_share(s, mnt_pt)
                export = NFSExport(export_group=eg, share=s, mount=export_pt)
                export.full_clean()
                export.save()
                cur_exports.append(export)
            exports = self.create_nfs_export_input(cur_exports)
            adv_entries = [e.export_str for e in AdvancedNFSExport.objects.all()]
            exports_d = self.create_adv_nfs_export_input(adv_entries, request)
            exports.update(exports_d)
            self.refresh_wrapper(exports, request, logger)
            nfs_serializer = NFSExportGroupSerializer(eg)
            return Response(nfs_serializer.data)


class AdvancedNFSExportView(NFSExportMixin, rfc.GenericView):
    serializer_class = AdvancedNFSExportSerializer

    def get_queryset(self, *args, **kwargs):
        conventional_exports = []
        exports_by_share = {}
        for e in NFSExport.objects.all():
            eg = e.export_group
            export_str = "%s(%s,%s,%s)" % (
                eg.host_str,
                eg.editable,
                eg.syncable,
                eg.mount_security,
            )
            if e.mount in exports_by_share:
                exports_by_share[e.mount] += " %s" % export_str
            else:
                exports_by_share[e.mount] = "%s %s" % (e.mount, export_str)
        for e in exports_by_share:
            exports_by_share[e] = "Normally added -- %s" % exports_by_share[e]
            conventional_exports.append(
                AdvancedNFSExport(export_str=exports_by_share[e])
            )

        for ae in AdvancedNFSExport.objects.all():
            conventional_exports.append(ae)
        return conventional_exports

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            if "entries" not in request.data:
                e_msg = "Cannot export without specifying entries."
                handle_exception(Exception(e_msg), request)

            AdvancedNFSExport.objects.all().delete()
            cur_entries = []
            for e in request.data.get("entries"):
                ce = AdvancedNFSExport(export_str=e)
                ce.save()
                cur_entries.append(ce)
            exports_d = self.create_adv_nfs_export_input(
                request.data["entries"], request
            )
            cur_exports = list(NFSExport.objects.all())
            exports = self.create_nfs_export_input(cur_exports)
            exports.update(exports_d)
            self.refresh_wrapper(exports, request, logger)
            nfs_serializer = AdvancedNFSExportSerializer(cur_entries, many=True)
            return Response(nfs_serializer.data)
