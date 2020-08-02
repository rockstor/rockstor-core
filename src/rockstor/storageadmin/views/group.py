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
from django.db import transaction
from storageadmin.util import handle_exception
from storageadmin.serializers import GroupSerializer
from storageadmin.models import Group
import rest_framework_custom as rfc
from system.users import groupadd, groupdel
import grp
from ug_helpers import combined_groups
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class GroupListView(rfc.GenericView):
    serializer_class = GroupSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            return combined_groups()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            groupname = request.data.get("groupname", None)
            gid = request.data.get("gid", None)
            if gid is not None:
                gid = int(gid)
            admin = request.data.get("admin", True)
            if (
                groupname is None
                or re.match(settings.USERNAME_REGEX, groupname) is None
            ):
                e_msg = (
                    "Groupname is invalid. It must conform to the regex: ({})."
                ).format(settings.USERNAME_REGEX)
                handle_exception(Exception(e_msg), request, status_code=400)
            if len(groupname) > 30:
                e_msg = "Groupname cannot be more than 30 characters long."
                handle_exception(Exception(e_msg), request, status_code=400)

            for g in combined_groups():
                if g.groupname == groupname:
                    e_msg = (
                        "Group ({}) already exists. Choose a different one."
                    ).format(g.groupname)
                    handle_exception(Exception(e_msg), request, status_code=400)
                if g.gid == gid:
                    e_msg = ("GID ({}) already exists. Choose a different one.").format(
                        gid
                    )
                    handle_exception(Exception(e_msg), request, status_code=400)

            groupadd(groupname, gid)
            grp_entries = grp.getgrnam(groupname)
            gid = grp_entries[2]
            group = Group(gid=gid, groupname=groupname, admin=admin)
            group.save()

            return Response(GroupSerializer(group).data)


class GroupDetailView(rfc.GenericView):
    exclude_list = (
        "root",
        "bin",
        "daemon",
        "sys",
        "adm",
        "tty",
        "disk",
        "lp",
        "mem",
        "kmem",
        "wheel",
        "cdrom",
        "mail",
        "man",
        "dialout",
        "floppy",
        "games",
        "tape",
        "video",
        "ftp",
        "lock",
        "audio",
        "nobody",
        "users",
        "utmp",
        "utempter",
        "ssh_keys",
        "systemd-journal",
        "dbus",
        "rpc",
        "polkitd",
        "avahi",
        "avahi-autoipd",
        "wbpriv",
        "rpcuser",
        "nfsnobody",
        "postgres",
        "ntp",
        "dip",
        "stapusr",
        "stapsys",
        "stapdev",
        "nginx",
        "postdrop",
        "postfix",
        "sshd",
        "chrony",
        "usbmuxd",
    )

    def get(self, *args, **kwargs):
        try:
            data = Group.objects.get(username=self.kwargs["groupname"])
            serialized_data = GroupSerializer(data)
            return Response(serialized_data.data)
        except:
            # Render no response if no matches
            return Response()

    def put(self, request, groupname):
        e_msg = "Group edit is not supported."
        handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def delete(self, request, groupname):
        with self._handle_exception(request):
            if groupname in self.exclude_list:
                e_msg = ("Delete of restricted group ({}) is not supported.").format(
                    groupname
                )
                handle_exception(Exception(e_msg), request, status_code=400)

            if Group.objects.filter(groupname=groupname).exists():
                g = Group.objects.get(groupname=groupname)
                g.delete()
            else:
                found = False
                for g in combined_groups():
                    if g.groupname == groupname:
                        found = True
                        break
                if found is False:
                    e_msg = "Group ({}) does not exist.".format(groupname)
                    handle_exception(Exception(e_msg), request)

            try:
                groupdel(groupname)
            except Exception as e:
                handle_exception(e, request)

            return Response()
