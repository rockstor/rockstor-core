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

from django.db import transaction
from storageadmin.models import Share, Snapshot, NFSExport, SambaShare
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from clone_helpers import create_clone, create_repclone
from share import ShareMixin
from django.core.exceptions import ObjectDoesNotExist
import logging

logger = logging.getLogger(__name__)


class ShareCommandView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def _validate_share(self, request, sid):
        try:
            return Share.objects.get(id=sid)
        except ObjectDoesNotExist:
            e_msg = "Share id ({}) does not exist.".format(sid)
            handle_exception(Exception(e_msg), request)

    def _validate_snapshot(self, request, share):
        try:
            snap_name = request.data.get("name", "")
            return Snapshot.objects.get(share=share, name=snap_name)
        except ObjectDoesNotExist:
            e_msg = ("Snapshot ({}) does not exist for share ({}).").format(
                snap_name, share.name
            )
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, sid, command):
        with self._handle_exception(request):
            share = self._validate_share(request, sid)

            if command == "clone":
                new_name = request.data.get("name", "")
                return create_clone(share, new_name, request, logger)

            if command == "rollback":
                snap = self._validate_snapshot(request, share)

                if NFSExport.objects.filter(share=share).exists():
                    e_msg = (
                        "Share ({}) cannot be rolled back as it is "
                        "exported via NFS. Delete NFS exports and "
                        "try again."
                    ).format(share.name)
                    handle_exception(Exception(e_msg), request)

                if SambaShare.objects.filter(share=share).exists():
                    e_msg = (
                        "Share ({}) cannot be rolled back as it is "
                        "shared via Samba. Unshare and "
                        "try again."
                    ).format(share.name)
                    handle_exception(Exception(e_msg), request)
                return create_repclone(share, request, logger, snap)
