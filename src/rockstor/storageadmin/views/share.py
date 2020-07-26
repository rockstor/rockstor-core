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

import re
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from storageadmin.models import (
    Share,
    Pool,
    Snapshot,
    NFSExport,
    SambaShare,
    SFTP,
    RockOn,
)
from smart_manager.models import Replica
from fs.btrfs import (
    add_share,
    remove_share,
    update_quota,
    volume_usage,
    set_property,
    mount_share,
    qgroup_id,
    qgroup_create,
    share_pqgroup_assign,
)
from system.services import systemctl
from storageadmin.serializers import ShareSerializer, SharePoolSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
import json
from smart_manager.models import Service

import logging

logger = logging.getLogger(__name__)

# The following model/db default setting is also used when quotas are disabled
# or when a Read-only state prevents creation of a new pqgroup.
PQGROUP_DEFAULT = settings.MODEL_DEFS["pqgroup"]


class ShareMixin(object):
    @staticmethod
    def _validate_share_size(request, pool):
        size = request.data.get("size", pool.size)
        try:
            size = int(size)
        except:
            handle_exception(Exception("Share size must be an integer."), request)
        if size < settings.MIN_SHARE_SIZE:
            e_msg = (
                "Share size should be at least {} KB. Given size is {} KB."
            ).format(settings.MIN_SHARE_SIZE, size)
            handle_exception(Exception(e_msg), request)
        if size > pool.size:
            return pool.size
        return size

    @staticmethod
    def _validate_compression(request):
        compression = request.data.get("compression", "no")
        if compression is None:
            compression = "no"
        if compression not in settings.COMPRESSION_TYPES:
            e_msg = ("Unsupported compression algorithm ({}). Use one of {}.").format(
                compression, settings.COMPRESSION_TYPES
            )
            handle_exception(Exception(e_msg), request)
        return compression

    @staticmethod
    def _validate_share(request, sid):
        try:
            share = Share.objects.get(id=sid)
            if share.name == "home" or share.name == "root":
                e_msg = (
                    "Operation not permitted on this share ({}) because "
                    "it is a special system share."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)
            return share
        except Share.DoesNotExist:
            e_msg = "Share id ({}) does not exist.".format(sid)
            handle_exception(Exception(e_msg), request)


class ShareListView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            sort_col = self.request.query_params.get("sortby", None)
            if sort_col is not None:
                reverse = self.request.query_params.get("reverse", "no")
                if reverse == "yes":
                    reverse = True
                else:
                    reverse = False
                if sort_col == "usage":
                    sort_col = "rusage"
                return sorted(
                    Share.objects.all(),
                    key=lambda u: getattr(u, sort_col),
                    reverse=reverse,
                )
            # If this box is receiving replication backups, the first full-send
            # is interpreted as a Share(because it does not have a parent
            # subvol/snapshot) It is a transient subvolume that gets rolled
            # into a proper Share after max_snap_retain + 1 incremental-sends.
            # Until then, keep such transient shares hidden from the UI, mostly
            # for cosmetic and UX reasons.
            # TODO: This currently fails to work, needs investigating, leaving
            # TODO: for now as good for indicting the initial rep phases.
            return Share.objects.exclude(
                name__regex=r"^\.snapshots/.*/.*_replication_"
            ).order_by("-id")

    @transaction.atomic
    def post(self, request):
        # qgroup notes for shares. we need to create a qgroup prior to share
        # creation. qgroup ids 0/<subvol_id> automatically get created when a
        # subvolume(i.e., a Share or a Snapshot) is created. So let's create a
        # new qgroup: 2015/<some_number> whenever a Share is
        # created. <some_number> starts from 1 and is incremented as more
        # Shares are created. So, for the very first Share in a pool, it's
        # qgroup will be 1/1. 2015 is arbitrarily chose.

        # Before creating a new Share, we create the qgroup for it. And during
        # it's creation, we assign this qgroup to it. During it's creation a
        # 0/x qgroup will automatically be created, but it will become the
        # child of our explicitly-created qgroup(2015/x).

        # We will set the qgroup limit on our qgroup and it will enforce the
        # quota on every subvolume(i.e., Share and Snapshot) in that qgroup.

        # When a Share is deleted, we need to destroy two qgroups. One is it's
        # auto 0/x qgroup and the other is our explicitly-created 2015/y
        # qgroup.

        with self._handle_exception(request):
            pool_name = request.data.get("pool", None)
            try:
                pool = Pool.objects.get(name=pool_name)
            except:
                e_msg = "Pool ({}) does not exist.".format(pool_name)
                handle_exception(Exception(e_msg), request)
            compression = self._validate_compression(request)
            size = self._validate_share_size(request, pool)
            sname = request.data.get("sname", None)
            if sname is None or re.match("%s$" % settings.SHARE_REGEX, sname) is None:
                e_msg = (
                    "Invalid characters in share name. Following are "
                    "allowed: letter(a-z or A-Z), digit(0-9), "
                    "hyphen(-), underscore(_) or a period(.)."
                )
                handle_exception(Exception(e_msg), request)

            if len(sname) > 254:
                # btrfs subvolume names cannot exceed 254 characters.
                e_msg = "Share name length cannot exceed 254 characters."
                handle_exception(Exception(e_msg), request)

            if Share.objects.filter(name=sname).exists():
                # Note e_msg is consumed by replication/util.py create_share()
                e_msg = ("Share ({}) already exists. Choose a different name.").format(
                    sname
                )
                handle_exception(Exception(e_msg), request)

            if Pool.objects.filter(name=sname).exists():
                e_msg = (
                    "A pool with this name ({}) exists. Share "
                    "and pool names must be distinct. Choose "
                    "a different name."
                ).format(sname)
                handle_exception(Exception(e_msg), request)
            replica = False
            if "replica" in request.data:
                replica = request.data["replica"]
                if type(replica) != bool:
                    # TODO: confirm this 'type' call works as format parameter.
                    e_msg = ("Replica must be a boolean, not ({}).").format(
                        type(replica)
                    )
                    handle_exception(Exception(e_msg), request)
            pqid = qgroup_create(pool)
            add_share(pool, sname, pqid)
            qid = qgroup_id(pool, sname)
            s = Share(
                pool=pool,
                qgroup=qid,
                pqgroup=pqid,
                name=sname,
                size=size,
                subvol_name=sname,
                replica=replica,
                compression_algo=compression,
            )
            # The following pool.save() was informed by test_share.py
            pool.save()
            s.save()
            if pqid != PQGROUP_DEFAULT:
                update_quota(pool, pqid, size * 1024)
                share_pqgroup_assign(pqid, s)
            mnt_pt = "%s%s" % (settings.MNT_PT, sname)
            if not s.is_mounted:
                mount_share(s, mnt_pt)
            if compression != "no":
                set_property(mnt_pt, "compression", compression)
            return Response(ShareSerializer(s).data)


class PoolShareListView(ShareMixin, rfc.GenericView):
    serializer_class = SharePoolSerializer

    def get_queryset(self, *args, **kwargs):
        pool = Pool.objects.get(id=self.kwargs.get("pid"))
        return pool.share_set.all()


class ShareDetailView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def get(self, *args, **kwargs):
        try:
            data = Share.objects.get(id=self.kwargs["sid"])
            serialized_data = ShareSerializer(data)
            return Response(serialized_data.data)
        except Share.DoesNotExist:
            raise NotFound(detail=None)

    @transaction.atomic
    def put(self, request, sid):
        with self._handle_exception(request):
            share = self._validate_share(request, sid)
            if "size" in request.data:
                new_size = self._validate_share_size(request, share.pool)
                qid = qgroup_id(share.pool, share.subvol_name)
                cur_rusage, cur_eusage = volume_usage(share.pool, qid)
                if new_size < cur_rusage:
                    e_msg = (
                        "Unable to resize because requested new "
                        "size {} KB is less than current usage {} KB "
                        "of the share."
                    ).format(new_size, cur_rusage)
                    handle_exception(Exception(e_msg), request)
                # quota maintenance
                if share.pool.quotas_enabled:
                    # Only try create / update quotas if they are enabled,
                    # pqgroup of PQGROUP_DEFAULT (-1/-1) indicates no pqgroup,
                    # ie quotas were disabled when update was requested.
                    if share.pqgroup == PQGROUP_DEFAULT or not share.pqgroup_exist:
                        # if quotas were disabled or pqgroup non-existent.
                        share.pqgroup = qgroup_create(share.pool)
                        share.save()
                    if share.pqgroup != PQGROUP_DEFAULT:
                        # Only update quota and assign if now non default as
                        # default can also indicate Read-only fs at this point.
                        update_quota(share.pool, share.pqgroup, new_size * 1024)
                        share_pqgroup_assign(share.pqgroup, share)
                else:
                    # Our pool's quotas are disabled so reset pqgroup to -1/-1.
                    if share.pqgroup != PQGROUP_DEFAULT:
                        # Only reset if necessary
                        share.pqgroup = PQGROUP_DEFAULT
                        share.save()
                share.size = new_size
            if "compression" in request.data:
                new_compression = self._validate_compression(request)
                if share.compression_algo != new_compression:
                    share.compression_algo = new_compression
                    mnt_pt = "%s%s" % (settings.MNT_PT, share.name)
                    if new_compression == "no":
                        new_compression = ""
                    set_property(mnt_pt, "compression", new_compression)
            share.save()
            return Response(ShareSerializer(share).data)

    @staticmethod
    def _rockon_check(request, sname, force):
        s = Service.objects.get(name="docker")
        if s.config is None:
            return

        config = json.loads(s.config)
        if config.get("root_share") == sname:
            if force:
                # turn off docker service, nullify config.
                systemctl(s.name, "stop")
                systemctl(s.name, "disable")
                s.config = None
                s.save()

                # delete all rockon metadata.
                RockOn.objects.all().delete()
                return
            e_msg = (
                "Share ({}) cannot be deleted because it is in use "
                "by the Rock-on service. To override this block select "
                "the force checkbox and try again."
            ).format(sname)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def delete(self, request, sid, command=""):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        force = True if (command == "force") else False
        with self._handle_exception(request):
            share = self._validate_share(request, sid)
            if Snapshot.objects.filter(share=share, snap_type="replication").exists():
                e_msg = (
                    "Share ({}) cannot be deleted as it has replication "
                    "related snapshots."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            if NFSExport.objects.filter(share=share).exists():
                e_msg = (
                    "Share ({}) cannot be deleted as it is exported via "
                    "NFS. Delete NFS exports and "
                    "try again."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            if SambaShare.objects.filter(share=share).exists():
                e_msg = (
                    "Share ({}) cannot be deleted as it is shared via "
                    "Samba. Unshare and try again."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            if Snapshot.objects.filter(share=share).exists():
                e_msg = (
                    "Share ({}) cannot be deleted as it has "
                    "snapshots. Delete snapshots and "
                    "try again."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            if SFTP.objects.filter(share=share).exists():
                e_msg = (
                    "Share ({}) cannot be deleted as it is exported via "
                    "SFTP. Delete SFTP export and "
                    "try again."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            if Replica.objects.filter(share=share.name).exists():
                e_msg = (
                    "Share ({}) is configured for replication. If you "
                    "are sure, delete the replication task and "
                    "try again."
                ).format(share.name)
                handle_exception(Exception(e_msg), request)

            self._rockon_check(request, share.name, force=force)

            try:
                remove_share(share.pool, share.subvol_name, share.pqgroup, force=force)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "Failed to delete the share ({}). Error from the OS: {}"
                ).format(share.name, e.__str__())
                handle_exception(Exception(e_msg), request)
            share.delete()
            return Response()
