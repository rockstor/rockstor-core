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
from django.conf import settings


class Replica(models.Model):
    task_name = models.CharField(max_length=1024)
    share = models.CharField(max_length=4096)
    pool = models.CharField(max_length=4096)
    """ip from the appliance model of storageadmin"""
    appliance = models.CharField(max_length=4096)
    dpool = models.CharField(max_length=4096)
    dshare = models.CharField(max_length=4096, null=True)
    enabled = models.BooleanField(default=False)
    data_port = models.IntegerField(default=settings.REPLICATION.get("listener_port"))
    meta_port = models.IntegerField(default=settings.REPLICATION.get("listener_port"))
    """enabled/disabled state change ts"""
    ts = models.DateTimeField(null=True, db_index=True)
    crontab = models.CharField(max_length=64, null=True)
    replication_ip = models.CharField(max_length=4096, null=True)

    class Meta:
        app_label = "smart_manager"


class ReplicaTrail(models.Model):
    """
    valid paths for the trail
    1. snapshot_failed (DOA)
    2. snapshot_created -> send_pending -> send_succeeded (happy path)
    3. snapshot_created -> send_pending -> send_failed (error)
    """

    replica = models.ForeignKey(Replica)
    snap_name = models.CharField(max_length=1024)
    kb_sent = models.BigIntegerField(default=0)
    snapshot_created = models.DateTimeField(null=True)
    snapshot_failed = models.DateTimeField(null=True)
    send_pending = models.DateTimeField(null=True)
    send_succeeded = models.DateTimeField(null=True)
    send_failed = models.DateTimeField(null=True)
    end_ts = models.DateTimeField(null=True, db_index=True)
    STATUS_CHOICES = [
        ("pending",) * 2,
        ("succeeded",) * 2,
        ("failed",) * 2,
    ]
    status = models.CharField(max_length=10)
    error = models.CharField(max_length=4096, null=True)

    class Meta:
        app_label = "smart_manager"


class ReplicaShare(models.Model):
    share = models.CharField(max_length=4096, unique=True)
    pool = models.CharField(max_length=4096)
    """ip from the appliance model of storageadmin"""
    appliance = models.CharField(max_length=4096)
    src_share = models.CharField(max_length=4096, null=True)
    data_port = models.IntegerField(default=settings.REPLICATION.get("listener_port"))
    meta_port = models.IntegerField(default=settings.REPLICATION.get("listener_port"))
    """enabled/disabled state change ts"""
    ts = models.DateTimeField(null=True, db_index=True)

    class Meta:
        app_label = "smart_manager"


class ReceiveTrail(models.Model):
    """
    valid paths for the trail
    1. snapshot_failed (DOA)
    2. snapshot_created -> send_pending -> send_succeeded (happy path)
    3. snapshot_created -> send_pending -> send_failed (error)
    """

    rshare = models.ForeignKey(ReplicaShare)
    snap_name = models.CharField(max_length=1024)
    kb_received = models.BigIntegerField(default=0)
    receive_pending = models.DateTimeField(null=True)
    receive_succeeded = models.DateTimeField(null=True)
    receive_failed = models.DateTimeField(null=True)
    end_ts = models.DateTimeField(null=True, db_index=True)
    STATUS_CHOICES = [
        ("pending",) * 2,
        ("succeeded",) * 2,
        ("failed",) * 2,
    ]
    status = models.CharField(max_length=10)
    error = models.CharField(max_length=4096, null=True)

    class Meta:
        app_label = "smart_manager"
