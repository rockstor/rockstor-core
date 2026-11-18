"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

from django.db import transaction
from rest_framework.response import Response

import rest_framework_custom as rfc
from fs.btrfs import mount_share
from settings import SFTP_MNT_ROOT, MNT_PT
from storageadmin.views.share_helpers import (
    validate_share,
    user_chroot_setup,
)
from storageadmin.models import SFTP
from storageadmin.serializers import SFTPSerializer
from storageadmin.util import handle_exception
from system.ssh import (
    sftp_mount_map,
    sftp_mount,
    remove_sftp_share_bindmount,
)

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
            share_obj_list = [
                validate_share(s, request) for s in request.data["shares"]
            ]
            editable = "rw"
            if "read_only" in request.data and request.data["read_only"] is True:
                editable = "ro"

            mnt_map = sftp_mount_map(SFTP_MNT_ROOT)
            user_chroot_map = {}
            for share in share_obj_list:
                if SFTP.objects.filter(share=share).exists():
                    e_msg = f"Share ({share.name}) is already exported via SFTP."
                    handle_exception(Exception(e_msg), request)
                if share.owner == "root":
                    e_msg = (
                        f"Share ({share.name}) is owned by root. It cannot be "
                        "exported via SFTP with "
                        "root ownership."
                    )
                    handle_exception(Exception(e_msg), request)
            for share in share_obj_list:
                sftpo = SFTP(share=share, editable=editable)
                sftpo.save()
                #  mount if not already mounted
                mount_share(share, f"{MNT_PT}{share.name}")
                #  bindmount if not already
                sftp_mount(share, MNT_PT, SFTP_MNT_ROOT, mnt_map, editable)
                # Above sftp_mount() is now a recursive bind mount, and so also mirrors
                # changes in the Share's submounts (user visible snapshots).
            user_chroot_setup()
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
                e_msg = f"SFTP config for the id ({id}) does not exist."
                handle_exception(Exception(e_msg), request)
            # Visible snapshots within this bind mount are inherited, via recursive
            # bind mount (rbind), from their canonical mount for all exports within
            # the /mnt2/Share/.snap-name mnt point that is expected to already exist.
            remove_sftp_share_bindmount(sftpo.share.name, sftpo.share.owner)
            sftpo.delete()
            user_chroot_setup()
            return Response()
