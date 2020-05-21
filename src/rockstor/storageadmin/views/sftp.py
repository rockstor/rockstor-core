"""
Copyright (c) 2012-2020 Rockstor, Inc. <http://rockstor.com>
This file is part of Rockstor.

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import logging
import os
import shutil

from django.conf import settings
from django.db import transaction
from rest_framework.response import Response

import rest_framework_custom as rfc
from fs.btrfs import is_share_mounted, umount_root
from share_helpers import helper_mount_share, validate_share, sftp_snap_toggle
from storageadmin.models import SFTP
from storageadmin.serializers import SFTPSerializer
from storageadmin.util import handle_exception
from system.ssh import update_sftp_config, sftp_mount_map, sftp_mount, rsync_for_sftp

logger = logging.getLogger(__name__)


class SFTPListView(rfc.GenericView):
    serializer_class = SFTPSerializer

    def get_queryset(self, *args, **kwargs):
        return SFTP.objects.all()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            if "shares" not in request.data:
                e_msg = "Must provide share names."
                handle_exception(Exception(e_msg), request)
            shares = [validate_share(s, request) for s in request.data["shares"]]
            editable = "rw"
            if "read_only" in request.data and request.data["read_only"] is True:
                editable = "ro"

            mnt_map = sftp_mount_map(settings.SFTP_MNT_ROOT)
            input_map = {}
            for share in shares:
                if SFTP.objects.filter(share=share).exists():
                    e_msg = ("Share ({}) is already exported via SFTP.").format(
                        share.name
                    )
                    handle_exception(Exception(e_msg), request)
                if share.owner == "root":
                    e_msg = (
                        "Share ({}) is owned by root. It cannot be "
                        "exported via SFTP with "
                        "root ownership."
                    ).format(share.name)
                    handle_exception(Exception(e_msg), request)
            for share in shares:
                sftpo = SFTP(share=share, editable=editable)
                sftpo.save()
                #  mount if not already mounted
                helper_mount_share(share)
                #  bindmount if not already
                sftp_mount(
                    share, settings.MNT_PT, settings.SFTP_MNT_ROOT, mnt_map, editable
                )
                sftp_snap_toggle(share)

                chroot_loc = "{}{}".format(settings.SFTP_MNT_ROOT, share.owner)
                rsync_for_sftp(chroot_loc)
                input_map[share.owner] = chroot_loc
            for sftpo in SFTP.objects.all():
                if sftpo.share not in shares:
                    input_map[sftpo.share.owner] = "{}{}".format(
                        settings.SFTP_MNT_ROOT, sftpo.share.owner,
                    )
            update_sftp_config(input_map)
            return Response()


class SFTPDetailView(rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            data = SFTP.objects.get(id=self.kwargs["id"])
            serialized_data = SFTPSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()

    @transaction.atomic
    def delete(self, request, id):
        with self._handle_exception(request):
            try:
                sftpo = SFTP.objects.get(id=id)
            except:
                e_msg = ("SFTP config for the id ({}) does not exist.").format(id)
                handle_exception(Exception(e_msg), request)

            mnt_prefix = "{}{}/".format(settings.SFTP_MNT_ROOT, sftpo.share.owner)

            if is_share_mounted(sftpo.share.name, mnt_prefix):
                sftp_snap_toggle(sftpo.share, mount=False)
                mnt_pt = "{}{}".format(mnt_prefix, sftpo.share.name)
                umount_root(mnt_pt)
                if os.path.isdir(mnt_pt):
                    shutil.rmtree(mnt_pt)
            sftpo.delete()
            input_map = {}
            for so in SFTP.objects.all():
                if so.id != sftpo.id:
                    input_map[so.share.owner] = "{}{}".format(
                        settings.SFTP_MNT_ROOT, so.share.owner,
                    )
            update_sftp_config(input_map)
            return Response()
