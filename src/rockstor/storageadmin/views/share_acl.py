"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

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

from os import stat, stat_result
from stat import S_IMODE

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Share
from storageadmin.serializers import ShareSerializer
from fs.btrfs import mount_share, umount_root, get_property
from storageadmin.views import ShareListView
from system.acl import chown, chmod
from system.users import user_name, group_name


class ShareACLView(ShareListView):
    @transaction.atomic
    def post(self, request, sid):
        with self._handle_exception(request):
            share = Share.objects.get(id=sid)
            # OWNER, GROUP, AND PERMISSIONS UPDATE.
            # Get the on disk subvol info.
            mnt_pt = share.mnt_pt
            share_stat: stat_result = stat(mnt_pt)
            subvol_owner = user_name(share_stat.st_uid)
            subvol_group = group_name(share_stat.st_gid)
            subvol_perms = oct(S_IMODE(share_stat.st_mode))[2:].zfill(3)
            # Establish the requested owner, group, perms, defaulting to on disk info.
            options: dict[str, str | bool] = {
                "owner": request.data.get("owner", subvol_owner),
                "group": request.data.get("group", subvol_group),
                "perms": request.data.get("perms", subvol_perms),
                # Owner and group recursive (unimplemented in Web-UI)
                "orecursive": request.data.get("orecursive", True),
                # Permissions recursive (unimplemented in Web-UI)
                "precursive": request.data.get("precursive", True),
            }
            # Align Share DB with requested owner, group, perms: if required.
            changed_fields: list[str] = []
            if share.owner != options["owner"]:
                share.owner = options["owner"]
                changed_fields.append("owner")
            if share.group != options["group"]:
                share.group = options["group"]
                changed_fields.append("group")
            if share.perms != options["perms"]:
                share.perms = options["perms"]
                changed_fields.append("perms")
            # COMPRESSION SETTING FROM DISK
            # Opportunistically update DB Share.compression_algo.
            compression: str = get_property(mnt_pt, "compression")
            if share.compression_algo != compression:
                share.compression_algo = compression
                changed_fields.append("compression_algo")
            share.save(update_fields=changed_fields)

            force_mount = False
            if not share.is_mounted:
                mount_share(share, mnt_pt)
                force_mount = True
            # TODO: Huey task that will return immediately, but are run asynchronously
            #  around a second after being called.
            chown(mnt_pt, options["owner"], options["group"], options["orecursive"])
            chmod(mnt_pt, options["perms"], options["precursive"])
            if force_mount is True:
                umount_root(mnt_pt)
            return Response(ShareSerializer(share).data)
