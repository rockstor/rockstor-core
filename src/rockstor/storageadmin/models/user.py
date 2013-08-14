"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
from django.contrib.auth.models import User as DjangoUser
from django.conf import settings

class User(models.Model):
    user = models.OneToOneField(DjangoUser, null=True, 
            related_name = 'suser')
    username = models.CharField(max_length=4096, unique=True, default='')
    uid = models.IntegerField(default=settings.START_UID)
    gid = models.IntegerField(default=settings.START_UID)

    class Meta:
        app_label = 'storageadmin'
