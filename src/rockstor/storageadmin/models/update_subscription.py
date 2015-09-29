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
from storageadmin.models import Appliance


class UpdateSubscription(models.Model):
    """name of the channel. eg: stable"""
    name = models.CharField(max_length=64, unique=True)
    """detailed description or a longer name"""
    description = models.CharField(max_length=128)
    """url of the repo"""
    url = models.CharField(max_length=512)
    appliance = models.ForeignKey(Appliance)
    password = models.CharField(max_length=64, null=True)
    """status of subscription: active, inactive, expired etc.."""
    status = models.CharField(max_length=64)


    class Meta:
        app_label = 'storageadmin'
