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
from rest_framework import status
from django.db import transaction
from django.conf import settings
from storageadmin.util import handle_exception
from django.contrib.auth.models import User as DjangoUser
from storageadmin.serializers import SUserSerializer
from storageadmin.models import User, Group
import rest_framework_custom as rfc
from system.users import useradd, usermod, userdel, smbpasswd, add_ssh_key, update_shell
import pwd
from system.pinmanager import username_to_uid, flush_pincard
from system.ssh import is_pub_key
from ug_helpers import combined_users, combined_groups
import logging
import re

logger = logging.getLogger(__name__)


class UserMixin(object):
    serializer_class = SUserSerializer
    exclude_list = (
        "root",
        "nobody",
        "bin",
        "daemon",
        "adm",
        "sync",
        "shutdown",
        "halt",
        "mail",
        "operator",
        "dbus",
        "rpc",
        "avahi",
        "avahi-autoipd",
        "rpcuser",
        "nfsnobody",
        "postgres",
        "ntp",
        "nginx",
        "postfix",
        "sshd",
    )

    @classmethod
    def _validate_input(cls, request):
        input_fields = {}
        username = request.data.get("username", None)
        if username is None or re.match(settings.USERNAME_REGEX, username) is None:
            e_msg = ("Username is invalid. It must conform to the regex: ({}).").format(
                settings.USERNAME_REGEX
            )
            handle_exception(Exception(e_msg), request, status_code=400)
        if len(username) > 30:
            e_msg = "Username cannot be more than 30 characters long."
            handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["username"] = username
        password = request.data.get("password", None)
        if password is None or password == "":
            e_msg = "Password must be a valid string."
            handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["password"] = password
        admin = request.data.get("admin", True)
        if type(admin) != bool:
            e_msg = 'Element "admin" (user type) must be a boolean.'
            handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["admin"] = admin
        shell = request.data.get("shell", "/bin/bash")
        if shell not in settings.VALID_SHELLS:
            e_msg = ("Element shell ({}) is not valid. Valid shells are {}.").format(
                shell, settings.VALID_SHELLS
            )
            handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["shell"] = shell
        email = request.data.get("email", None)
        input_fields["email"] = email
        input_fields["homedir"] = request.data.get("homedir", "/home/%s" % username)
        input_fields["uid"] = request.data.get("uid", None)
        if input_fields["uid"] is not None:
            try:
                input_fields["uid"] = int(input_fields["uid"])
            except ValueError as e:
                e_msg = ("UID must be an integer, try again. Exception: ({}).").format(
                    e.__str__()
                )
                handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["gid"] = request.data.get("gid", None)
        if input_fields["gid"] is not None:
            try:
                input_fields["gid"] = int(input_fields["gid"])
            except ValueError as e:
                e_msg = ("GID must be an integer, try again. Exception: ({}).").format(
                    e.__str__()
                )
                handle_exception(Exception(e_msg), request, status_code=400)
        input_fields["group"] = request.data.get("group", None)
        input_fields["public_key"] = cls._validate_public_key(request)
        return input_fields

    @staticmethod
    def _validate_public_key(request):
        public_key = request.data.get("public_key", None)
        if public_key is not None:
            public_key = public_key.strip()
            if not is_pub_key(public_key):
                e_msg = "Public key is invalid."
                handle_exception(Exception(e_msg), request)
        return public_key


class UserListView(UserMixin, rfc.GenericView):
    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            return combined_users()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):

            invar = self._validate_input(request)
            # Check that a django user with the same name does not exist
            e_msg = (
                "User ({}) already exists. Please choose a different username."
            ).format(invar["username"])
            if (
                DjangoUser.objects.filter(username=invar["username"]).exists()
                or User.objects.filter(username=invar["username"]).exists()
            ):

                handle_exception(Exception(e_msg), request, status_code=400)
            users = combined_users()
            groups = combined_groups()
            # As we have not yet established a pre-existing group, set to None.
            admin_group = None
            if invar["group"] is not None:
                # We have a group setting so search for existing group name
                # match. Matching by group name has precedence over gid.
                for g in groups:
                    if g.groupname == invar["group"]:
                        # We have an existing group name match in invar
                        # so overwrite requested gid to match existing gid.
                        invar["gid"] = g.gid
                        # Set the admin_group to our existing group object.
                        admin_group = g
                        admin_group.save()
                        invar["group"] = g  # exchange name for db group item.
                        break

            for u in users:
                if u.username == invar["username"]:
                    handle_exception(Exception(e_msg), request, status_code=400)
                elif u.uid == invar["uid"]:
                    e_msg = (
                        "UID ({}) already exists. Please choose a different one."
                    ).format(invar["uid"])
                    handle_exception(Exception(e_msg), request)

            if invar["admin"]:
                # Create Django user
                auser = DjangoUser.objects.create_user(
                    invar["username"], None, invar["password"]
                )
                auser.is_active = True
                auser.save()
                invar["user"] = auser

            useradd(
                invar["username"], invar["shell"], uid=invar["uid"], gid=invar["gid"]
            )
            pw_entries = pwd.getpwnam(invar["username"])
            invar["uid"] = pw_entries[2]
            invar["gid"] = pw_entries[3]
            usermod(invar["username"], invar["password"])
            smbpasswd(invar["username"], invar["password"])
            if invar["public_key"] is not None:
                add_ssh_key(invar["username"], invar["public_key"])
            del invar["password"]
            if admin_group is None:
                # We have no identified pre-existing group by name but there
                # could still be an existing group match by gid, if so we
                # use that group object as our new User.group foreign key link.
                if Group.objects.filter(gid=invar["gid"]).exists():
                    admin_group = Group.objects.get(gid=invar["gid"])
                else:
                    # As we are creating a new group we set admin=True to
                    # flag this group as administered by Rockstor.
                    if invar["group"] is None:
                        admin_group = Group(
                            gid=invar["gid"], groupname=invar["username"], admin=True
                        )
                    else:
                        admin_group = Group(
                            gid=invar["gid"], groupname=invar["group"], admin=True
                        )
                    admin_group.save()  # save our new group object.
                # set our invar dict group entry to our admin_group object.
                invar["group"] = admin_group
            # now we create our user object based on the contents of invar[]
            suser = User(**invar)
            # validate and save our suser object.
            suser.full_clean()
            suser.save()
            return Response(SUserSerializer(suser).data)


class UserDetailView(UserMixin, rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            data = User.objects.get(username=self.kwargs["username"])
            serialized_data = SUserSerializer(data)
            return Response(serialized_data.data)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @transaction.atomic
    def put(self, request, username):
        with self._handle_exception(request):
            if username in self.exclude_list:
                if username != "root":
                    e_msg = ("Editing restricted user ({}) is not supported.").format(
                        username
                    )
                    handle_exception(Exception(e_msg), request)
            email = request.data.get("email", None)
            new_pw = request.data.get("password", None)
            shell = request.data.get("shell", None)
            public_key = self._validate_public_key(request)
            cur_public_key = None
            admin = request.data.get("admin", False)
            if User.objects.filter(username=username).exists():
                u = User.objects.get(username=username)
                if admin is True:
                    if u.user is None:
                        if new_pw is None:
                            e_msg = (
                                "Password reset is required to "
                                "enable admin access. Please provide "
                                "a new password."
                            )
                            handle_exception(Exception(e_msg), request)
                        auser = DjangoUser.objects.create_user(username, None, new_pw)
                        auser.is_active = True
                        auser.save()
                        u.user = auser
                        u.full_clean()
                        u.save()
                    elif new_pw is not None:
                        u.user.set_password(new_pw)
                        u.user.save()
                else:
                    if u.user is not None:
                        auser = u.user
                        u.user = None
                        auser.delete()
                u.admin = admin
                if u.public_key is not None and u.public_key != public_key:
                    cur_public_key = u.public_key
                u.public_key = public_key
                if email is not None and email != "":
                    u.email = email
                if shell is not None and shell != u.shell:
                    u.shell = shell
                u.full_clean()
                u.save()

            sysusers = combined_users()
            suser = None
            for u in sysusers:
                if u.username == username:
                    suser = u
                    if new_pw is not None:
                        usermod(username, new_pw)
                        smbpasswd(username, new_pw)
                    if shell is not None:
                        update_shell(username, shell)
                    add_ssh_key(username, public_key, cur_public_key)
                    break
            if suser is None:
                e_msg = "User ({}) does not exist.".format(username)
                handle_exception(Exception(e_msg), request)

            return Response(SUserSerializer(suser).data)

    @transaction.atomic
    def delete(self, request, username):
        with self._handle_exception(request):
            if request.user.username == username:
                e_msg = "Cannot delete the currently logged in user."
                handle_exception(Exception(e_msg), request)

            if username in self.exclude_list:
                e_msg = ("Delete of restricted user ({}) is not supported.").format(
                    username
                )
                handle_exception(Exception(e_msg), request)

            gid = None
            if User.objects.filter(username=username).exists():
                u = User.objects.get(username=username)
                if u.user is not None:
                    u.user.delete()
                gid = u.gid
                u.delete()
            else:
                sysusers = combined_users()
                found = False
                for u in sysusers:
                    if u.username == username:
                        found = True
                        break
                if found is False:
                    e_msg = "User ({}) does not exist.".format(username)
                    handle_exception(Exception(e_msg), request)

            for g in combined_groups():
                if (
                    g.gid == gid
                    and g.admin
                    and not User.objects.filter(gid=gid).exists()
                ):
                    g.delete()

            # When user deleted destroy all Pincard entries
            flush_pincard(username_to_uid(username))

            try:
                userdel(username)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "A low level error occurred while deleting the user ({})."
                ).format(username)
                handle_exception(Exception(e_msg), request)

            return Response()
