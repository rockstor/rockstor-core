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
from storageadmin.models import Share


class RockOn(models.Model):
    name = models.CharField(max_length=1024)
    description = models.CharField(max_length=2048)
    version = models.CharField(max_length=2048)
    state = models.CharField(max_length=2048)
    status = models.CharField(max_length=2048)
    link = models.CharField(max_length=1024, null=True)
    website = models.CharField(max_length=2048, null=True)
    https = models.BooleanField(default=False)
    icon = models.URLField(max_length=1024, null=True)
    ui = models.BooleanField(default=False)
    volume_add_support = models.BooleanField(default=False)
    more_info = models.CharField(max_length=4096, null=True)

    @property
    def ui_port(self):
        if not self.ui:
            return None
        for co in self.dcontainer_set.all():
            for po in co.dport_set.all():
                if po.uiport:
                    return po.hostp
        return None

    class Meta:
        app_label = "storageadmin"


class DImage(models.Model):
    name = models.CharField(max_length=1024)
    tag = models.CharField(max_length=1024)
    repo = models.CharField(max_length=1024)

    class Meta:
        app_label = "storageadmin"


class DContainer(models.Model):
    rockon = models.ForeignKey(RockOn)
    dimage = models.ForeignKey(DImage)
    name = models.CharField(max_length=1024, unique=True)
    launch_order = models.IntegerField(default=1)
    # if uid is None, container's owner is not set. defaults to root.  if it's
    # -1, then owner is set to the owner of first volume, if any.  if it's an
    # integer other than -1, like 0, then owner is set to that uid.
    uid = models.IntegerField(null=True)

    class Meta:
        app_label = "storageadmin"


class DContainerLink(models.Model):
    source = models.OneToOneField(DContainer)
    destination = models.ForeignKey(DContainer, related_name="destination_container")
    name = models.CharField(max_length=64, null=True)

    class Meta:
        unique_together = ("destination", "name")
        app_label = "storageadmin"


class DPort(models.Model):
    description = models.CharField(max_length=1024, null=True)
    hostp = models.IntegerField(unique=True)
    hostp_default = models.IntegerField(null=True)
    containerp = models.IntegerField()
    container = models.ForeignKey(DContainer)
    protocol = models.CharField(max_length=32, null=True)
    uiport = models.BooleanField(default=False)
    label = models.CharField(max_length=1024, null=True)

    class Meta:
        unique_together = (
            "container",
            "containerp",
        )
        app_label = "storageadmin"


class DVolume(models.Model):
    container = models.ForeignKey(DContainer)
    share = models.ForeignKey(Share, null=True)
    dest_dir = models.CharField(max_length=1024)
    uservol = models.BooleanField(default=False)
    description = models.CharField(max_length=1024, null=True)
    min_size = models.IntegerField(null=True)
    label = models.CharField(max_length=1024, null=True)

    @property
    def share_name(self):
        if self.share is not None:
            return self.share.name
        return None

    class Meta:
        unique_together = (
            "container",
            "dest_dir",
        )
        app_label = "storageadmin"


class ContainerOption(models.Model):
    container = models.ForeignKey(DContainer)
    name = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024, blank=True)

    class Meta:
        app_label = "storageadmin"


class DContainerArgs(models.Model):
    container = models.ForeignKey(DContainer)
    name = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024, blank=True)

    class Meta:
        app_label = "storageadmin"


class DCustomConfig(models.Model):
    rockon = models.ForeignKey(RockOn)
    key = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024, null=True)
    description = models.CharField(max_length=2048, null=True)
    label = models.CharField(max_length=64, null=True)

    class Meta:
        unique_together = (
            "rockon",
            "key",
        )
        app_label = "storageadmin"


class DContainerEnv(models.Model):
    container = models.ForeignKey(DContainer)
    key = models.CharField(max_length=1024)
    val = models.CharField(max_length=1024, null=True)
    description = models.CharField(max_length=2048, null=True)
    label = models.CharField(max_length=64, null=True)


class DContainerDevice(models.Model):
    container = models.ForeignKey(DContainer)
    dev = models.CharField(max_length=1024, null=True)
    val = models.CharField(max_length=1024, null=True)
    description = models.CharField(max_length=2048, null=True)
    label = models.CharField(max_length=64, null=True)

    class Meta:
        unique_together = ("container", "dev")
        app_label = "storageadmin"


class DContainerLabel(models.Model):
    container = models.ForeignKey(DContainer)
    key = models.CharField(max_length=1024, null=True)
    val = models.CharField(max_length=1024, null=True)

    class Meta:
        unique_together = ("container", "val")
        app_label = "storageadmin"
