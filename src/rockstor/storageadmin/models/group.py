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

from django.db import models


class Group(models.Model):
    gid = models.IntegerField(unique=True)
    groupname = models.CharField(max_length=1024, null=True)
    # 'admin' field represents indicator of Rockstor managed group;
    # ie pre-existing group (eg audio) will be False. Rockstor created groups
    # are admin=True.
    admin = models.BooleanField(default=False)

    class Meta:
        app_label = "storageadmin"
