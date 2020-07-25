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


class Service(models.Model):

    name = models.CharField(max_length=24, unique=True)
    display_name = models.CharField(max_length=24, unique=True)
    config = models.CharField(max_length=8192, null=True)

    class Meta:
        app_label = "smart_manager"


class ServiceStatus(models.Model):

    service = models.ForeignKey(Service)
    status = models.BooleanField(default=False)
    count = models.BigIntegerField(default=1)
    ts = models.DateTimeField(auto_now=True, db_index=True)

    @property
    def config(self, *args, **kwargs):
        return self.service.config

    @property
    def name(self, *args, **kwargs):
        return self.service.name

    @property
    def display_name(self, *args, **kwargs):
        return self.service.display_name

    class Meta:
        app_label = "smart_manager"
