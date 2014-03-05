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


class BackupPolicy(models.Model):
    name = models.CharField(max_length=255, unique=True)
    source_ip = models.CharField(max_length=255)
    source_path = models.CharField(max_length=255)
    dest_share = models.CharField(max_length=255)
    notify_email = models.CharField(max_length=4096)
    start = models.DateTimeField(auto_now=True, db_index=True)
    frequency = models.IntegerField()
    num_retain = models.IntegerField()
    enabled = models.BooleanField(default=True)

    class Meta:
        unique_together = ('source_ip', 'source_path')
        app_label = 'backup'

class PolicyTrail(models.Model):
    policy = models.ForeignKey(BackupPolicy)
    start = models.DateTimeField(null=True, db_index=True)
    status = models.CharField(max_length=255, default='start')
    snap_created = models.DateTimeField(null=True)
    sync_started = models.DateTimeField(null=True)
    error = models.CharField(null=True, max_length=2048)
    status_ts = models.DateTimeField(null=True)

    class Meta:
        app_label = 'backup'
