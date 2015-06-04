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
from storageadmin.models import Share


class RockOn(models.Model):
    name = models.CharField(max_length=1024)
    description = models.CharField(max_length=2048)
    version = models.CharField(max_length=2048)
    state = models.CharField(max_length=2048)
    status = models.CharField(max_length=32)
    link = models.CharField(max_length=1024, null=True)
    website = models.CharField(max_length=2048, null=True)

    class Meta:
        app_label = 'storageadmin'


class DImage(models.Model):
    name = models.CharField(max_length=1024)
    tag = models.CharField(max_length=1024)
    repo = models.CharField(max_length=1024)

    class Meta:
        app_label = 'storageadmin'


class DContainer(models.Model):
    rockon = models.ForeignKey(RockOn)
    dimage = models.ForeignKey(DImage)
    name = models.CharField(max_length=1024, unique=True)
    link = models.ForeignKey('self', null=True)

    class Meta:
        app_label = 'storageadmin'


class DPort(models.Model):
    hostp = models.IntegerField(unique=True)
    containerp = models.IntegerField()
    container = models.ForeignKey(DContainer)
    protocol = models.CharField(max_length=32, null=True)
    uiport = models.BooleanField(default=False)

    class Meta:
        unique_together = ('container', 'containerp',)
        app_label = 'storageadmin'


class DVolume(models.Model):
    container = models.ForeignKey(DContainer)
    share = models.ForeignKey(Share, null=True)
    dest_dir = models.CharField(max_length=1024)
    uservol = models.BooleanField(default=False)

    @property
    def share_name(self):
        if (self.share is not None):
            return self.share.name
        return None

    class Meta:
        unique_together = ('container', 'dest_dir',)
        app_label = 'storageadmin'


class ContainerOption(models.Model):
    container = models.ForeignKey(DContainer)
    name = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024)

    class Meta:
        app_label = 'storageadmin'


class DCustomConfig(models.Model):
    rockon = models.ForeignKey(RockOn)
    key = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024, null=True)
    description = models.CharField(max_length=2048, null=True)

    class Meta:
        unique_together = ('rockon', 'key',)
        app_label = 'storageadmin'
