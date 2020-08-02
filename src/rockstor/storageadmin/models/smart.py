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
from storageadmin.models import Disk


class SMARTCapability(models.Model):
    info = models.ForeignKey("SMARTInfo")
    name = models.CharField(max_length=1024)
    flag = models.CharField(max_length=64)
    capabilities = models.CharField(max_length=2048)

    class Meta:
        app_label = "storageadmin"


class SMARTAttribute(models.Model):
    info = models.ForeignKey("SMARTInfo")
    aid = models.IntegerField()
    name = models.CharField(max_length=256)
    flag = models.CharField(max_length=64)
    normed_value = models.IntegerField(default=0)
    worst = models.IntegerField(default=0)
    threshold = models.IntegerField(default=0)
    atype = models.CharField(max_length=64)
    raw_value = models.CharField(max_length=256)
    updated = models.CharField(max_length=64)
    failed = models.CharField(max_length=64)

    class Meta:
        app_label = "storageadmin"


class SMARTErrorLog(models.Model):
    info = models.ForeignKey("SMARTInfo")
    line = models.CharField(max_length=128)

    class Meta:
        app_label = "storageadmin"


class SMARTErrorLogSummary(models.Model):
    info = models.ForeignKey("SMARTInfo")
    error_num = models.IntegerField()
    lifetime_hours = models.IntegerField()
    state = models.CharField(max_length=64)
    etype = models.CharField(max_length=256)
    details = models.CharField(max_length=1024)

    class Meta:
        app_label = "storageadmin"


class SMARTTestLog(models.Model):
    info = models.ForeignKey("SMARTInfo")
    test_num = models.IntegerField()
    description = models.CharField(max_length=64)
    status = models.CharField(max_length=256)
    pct_completed = models.IntegerField()
    lifetime_hours = models.IntegerField()
    lba_of_first_error = models.CharField(max_length=1024)

    class Meta:
        app_label = "storageadmin"


class SMARTTestLogDetail(models.Model):
    info = models.ForeignKey("SMARTInfo")
    line = models.CharField(max_length=128)

    class Meta:
        app_label = "storageadmin"


class SMARTIdentity(models.Model):
    info = models.ForeignKey("SMARTInfo")
    CHOICES = [
        ("Model Family",) * 2,
        ("Device Model",) * 2,
        ("Serial Number",) * 2,
        ("World Wide Name",) * 2,
        ("Firmware Version",) * 2,
        ("Capacity",) * 2,
        ("Sector Size",) * 2,
        ("Rotation Rate",) * 2,
        ("In Smartctl Database",) * 2,
        ("ATA Version",) * 2,
        ("SATA Version",) * 2,
        ("Scanned on",) * 2,
        ("SMART Supported",) * 2,
        ("SMART Enabled",) * 2,
        ("Overall Health Self-Assessment Test",) * 2,
    ]
    model_family = models.CharField("Model Family", max_length=64)
    device_model = models.CharField("Device Model", max_length=64)
    serial_number = models.CharField("Serial Number", max_length=64)
    world_wide_name = models.CharField("World Wide Name", max_length=64)
    firmware_version = models.CharField("Firmware Version", max_length=64)
    capacity = models.CharField("Capacity", max_length=64)
    sector_size = models.CharField("Sector Size", max_length=64)
    rotation_rate = models.CharField("Rotation Rate", max_length=64)
    in_smartdb = models.CharField("In Smartctl Database", max_length=64)
    ata_version = models.CharField("ATA Version", max_length=64)
    sata_version = models.CharField("SATA Version", max_length=64)
    scanned_on = models.CharField("Scanned on", max_length=64)
    supported = models.CharField("SMART Supported", max_length=64)
    enabled = models.CharField("SMART Enabled", max_length=64)
    version = models.CharField("Smartctl Version", max_length=64)
    assessment = models.CharField("Overall Health Self-Assessment Test", max_length=64)

    class Meta:
        app_label = "storageadmin"


class SMARTInfo(models.Model):
    disk = models.ForeignKey(Disk)
    toc = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = "storageadmin"

    def capabilities(self):
        return SMARTCapability.objects.filter(info=self)

    def attributes(self):
        return SMARTAttribute.objects.filter(info=self)

    def errorlog(self):
        return SMARTErrorLog.objects.filter(info=self).order_by("id")

    def errorlogsummary(self):
        return SMARTErrorLogSummary.objects.filter(info=self).order_by("id")

    def identity(self):
        if SMARTIdentity.objects.filter(info=self).exists():
            return SMARTIdentity.objects.get(info=self)
        return None

    def testlog(self):
        return SMARTTestLog.objects.filter(info=self).order_by("id")

    def testlogdetail(self):
        return SMARTTestLogDetail.objects.filter(info=self).order_by("id")
