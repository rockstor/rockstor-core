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
from storageadmin.models import Disk

class SMARTCapability(models.Model):
    info = models.ForeignKey('SMARTInfo')
    name = models.CharField(max_length=1024)
    flag = models.CharField(max_length=64)
    capabilities = models.CharField(max_length=2048)

    class Meta:
        app_label = 'storageadmin'

class SMARTAttribute(models.Model):
    info = models.ForeignKey('SMARTInfo')
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
        app_label = 'storageadmin'

class SMARTErrorLog(models.Model):
    info = models.ForeignKey('SMARTInfo')
    line = models.CharField(max_length=128)

    class Meta:
        app_label = 'storageadmin'

class SMARTErrorLogSummary(models.Model):
    info = models.ForeignKey('SMARTInfo')
    error_num = models.IntegerField()
    lifetime_hours = models.IntegerField()
    state = models.CharField(max_length=64)
    etype = models.CharField(max_length=256)
    details = models.CharField(max_length=1024)

    class Meta:
        app_label = 'storageadmin'

class SMARTInfo(models.Model):
    disk = models.ForeignKey(Disk)
    toc = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'storageadmin'

    def capabilities(self):
        return SMARTCapability.objects.filter(info=self)

    def attributes(self):
        return SMARTAttribute.objects.filter(info=self)

    def errorlog(self):
        return SMARTErrorLog.objects.filter(info=self).order_by('id')

    def errorlogsummary(self):
        return SMARTErrorLogSummary.objects.filter(info=self).order_by('id')

class SMARTTestLog(models.Model):
    disk = models.ForeignKey(Disk)
    test_num = models.IntegerField()
    ttype = models.CharField(max_length=64)
    status = models.CharField(max_length=256)
    pct_completed = models.IntegerField()
    lifetime_hours = models.IntegerField()
    lba_of_first_error = models.CharField(max_length=1024)
