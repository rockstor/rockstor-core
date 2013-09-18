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
    replica = models.ForeignKey(Replica)
    snap_name = models.CharField(max_length=1024)
    STATUS_CHOICES = [
        ('snap_created',) * 2,
        ('snap_failed',) * 2,
        ('send_pending',) * 2,
        ('send_succeeded',) * 2,
        ('send_failed',) * 2,
        ]
    status = models.CharField(max_length=10)
    state_ts = models.DateTimeField(null=True)


    class Meta:
        app_label = 'smart_manager'
