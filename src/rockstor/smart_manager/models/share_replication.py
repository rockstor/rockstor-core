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


class Replica(models.Model):
    share = models.CharField(max_length=4096)
    pool = models.CharField(max_length=4096)
    appliance = models.CharField(max_length=4096)
    dpool = models.CharField(max_length=4096)
    dshare = models.CharField(max_length=4096, null=True)
    enabled = models.BooleanField(default=False)
    frequency = models.IntegerField()

    class Meta:
        app_label = 'smart_manager'


class ReplicaTrail(models.Model):
    """
    valid paths for the trail
    1. snapshot_failed (DOA)
    2. snapshot_created -> send_pending -> send_succeeded (happy path)
    3. snapshot_created -> send_pending -> send_failed (error)
    """
    replica = models.ForeignKey(Replica)
    snap_name = models.CharField(max_length=1024)
    kb_sent = models.IntegerField(default=0)
    snapshot_created = models.DateTimeField(null=True)
    snapshot_failed = models.DateTimeField(null=True)
    send_pending = models.DateTimeField(null=True)
    send_succeeded = models.DateTimeField(null=True)
    send_failed = models.DateTimeField(null=True)
    end_ts = models.DateTimeField(null=True)
    STATUS_CHOICES = [
        ('pending',) * 2,
        ('succeeded',) * 2,
        ('failed',) * 2,
        ]
    status = models.CharField(max_length=10)
    error = models.CharField(max_length=4096, null=True)

    class Meta:
        app_label = 'smart_manager'
