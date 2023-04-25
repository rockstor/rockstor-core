"""
Copyright (c) 2012-2023 RockStor, Inc. <http://rockstor.com>
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

import grp

import chardet
from django.conf import settings
from django.contrib.auth.models import User as DjangoUser
from django.core.validators import validate_email
from django.db import models

from storageadmin.models import Group
from system.users import ifp_get_properties_from_name_or_id


class User(models.Model):
    user = models.OneToOneField(DjangoUser, null=True, blank=True, related_name="suser")
    username = models.CharField(max_length=4096, unique=True, default="")
    uid = models.IntegerField(default=settings.START_UID)
    gid = models.IntegerField(default=settings.START_UID)
    public_key = models.CharField(max_length=4096, null=True, blank=True)
    smb_shares = models.ManyToManyField("SambaShare", related_name="admin_users")
    shell = models.CharField(max_length=1024, null=True)
    homedir = models.CharField(max_length=1024, null=True)
    email = models.CharField(
        max_length=1024, null=True, blank=True, validators=[validate_email]
    )
    # 'admin' field represents indicator of Rockstor web admin capability.
    admin = models.BooleanField(default=True)
    group = models.ForeignKey(Group, null=True, blank=True)

    @property
    def groupname(self, *args, **kwargs):
        """Get user's groupname

        Get the user's groupname from the following sources, in order:
          - linked Group model entry
          - from the system, using `grp`
          - from InfoPipe: useful for domain users
        """
        if self.group is not None:
            return self.group.groupname
        if self.gid is not None:
            try:
                groupname = grp.getgrgid(self.gid).gr_name
                charset = chardet.detect(groupname)
                groupname = groupname.decode(charset["encoding"])
                return groupname
            except KeyError:
                # Failed to fetch user using grp, so let's try with InfoPipe
                ifp_res = ifp_get_properties_from_name_or_id(
                    "ifp_groups", int(self.gid), "name"
                )
                if ifp_res is not None:
                    return str(ifp_res["name"])
        return None

    @property
    def managed_user(self, *args, **kwargs):
        return getattr(self, "editable", True)

    @managed_user.setter
    def managed_user(self, val, *args, **kwargs):
        self.editable = val

    @property
    def has_pincard(self, *args, **kwargs):
        return getattr(self, "pincard_exist", False)

    @has_pincard.setter
    def has_pincard(self, val, *args, **kwargs):
        self.pincard_exist = val

    @property
    def pincard_allowed(self, *args, **kwargs):
        return getattr(self, "pincard_enabled", "no")

    @pincard_allowed.setter
    def pincard_allowed(self, val, *args, **kwargs):
        self.pincard_enabled = val

    class Meta:
        app_label = "storageadmin"
