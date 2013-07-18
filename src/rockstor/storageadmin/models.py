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

import re
from django.db import models
from fs.btrfs import (add_pool, pool_usage, remove_pool, resize_pool)
from django.contrib.auth.models import User
from validators import (validate_nfs_host_str, validate_nfs_modify_str,
                        validate_nfs_sync_choice)
from smart_manager.models import PoolUsage


class Pool(models.Model):
    """Name of the pool"""
    name = models.CharField(max_length=4096, unique=True)
    """uuid given automatically by the client"""
    uuid = models.CharField(max_length=100, null=True)
    """size of the pool"""
    size = models.IntegerField(default=0)
    """raid choices"""
    RAID_CHOICES = [
        ('raid0',) * 2,
        ('raid1',) * 2,
        ('raid10',) * 2,
        ('dup',) * 2,
        ('single',) * 2,
        ]
    """raid type"""
    raid = models.CharField(max_length=10, choices=RAID_CHOICES)

    def cur_usage(self, *args, **kwargs):
        try:
            pu = PoolUsage.objects.filter(pool=self.name).order_by('-ts')[0]
            return pu.usage
        except:
            return -1

class Disk(models.Model):
    """Pool can be null for disks that are not part of any pool currently"""
    pool = models.ForeignKey(Pool, null=True, on_delete=models.SET_NULL )
    """typically sda, sdb etc.. max_length = 0 supports 100s of disks"""
    name = models.CharField(max_length=10, unique=True)
    """total size in GB"""
    size = models.IntegerField()
    """free space in GB"""
    free = models.IntegerField()
    """whether the disk is partitioned at the moment. relevent for root disks
    and such that may not be part of any pool but need to be in the model"""
    parted = models.BooleanField()

class Share(models.Model):
    """pool that this share is part of"""
    pool = models.ForeignKey(Pool)
    """quota group this share is part of"""
    qgroup = models.CharField(max_length=100)
    """name of the share, kind of like id"""
    name = models.CharField(max_length=4096, unique=True)
    """id of the share. numeric in case of btrfs"""
    uuid = models.CharField(max_length=100, null=True)
    """total size in GB"""
    size = models.IntegerField()
    """free space in GB"""
    free = models.IntegerField()

class Snapshot(models.Model):
    """share which this snapshot belongs to"""
    share = models.ForeignKey(Share)
    """name of the snapshot"""
    name = models.CharField(max_length=4096)
    """read-only by default"""
    writable = models.BooleanField(default=False)
    """size of the snapshot"""
    size = models.IntegerField(default=0)

    class Meta:
        unique_together = ('share', 'name',)

"""
Statistics, may need to split into a different app. but for alpha this will do.
"""
class PoolStatistic(models.Model):
    """pool that this statistic represents"""
    pool = models.ForeignKey(Pool)
    """total capacity(KB) of the pool at the time of this statistic"""
    total_capacity = models.IntegerField()
    """used capacity(KB) of the pool at the time of this statistic"""
    used = models.IntegerField()
    """timestamp in utc of this statistic"""
    ts = models.DateTimeField(auto_now=True)

class ShareStatistic(models.Model):
    """share that this statistic represents"""
    share = models.ForeignKey(Share)
    """total capacity(KB) of the share at the time of this statistic"""
    total_capacity = models.IntegerField()
    """used capacity(KB) of this share at the time of this statistic"""
    used = models.IntegerField()
    """timestamp in utc of this statistic"""
    ts = models.DateTimeField(auto_now=True)

"""
NFS export history
"""
class NFSExport(models.Model):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    ASYNC = "async"
    SYNC = "sync"
    SECURE = "secure"
    INSECURE = "insecure"

    """share that is exported"""
    share = models.ForeignKey(Share)
    """mount point of the share"""
    mount = models.CharField(max_length=4096)
    """hostname string in /etc/exports"""
    host_str = models.CharField(max_length=4096,
                                validators=[validate_nfs_host_str])
    """mount options"""
    """mount read only by default"""
    MODIFY_CHOICES = (
        (READ_ONLY, 'ro'),
        (READ_WRITE, 'rw'),
        )
    editable = models.CharField(max_length=2, choices=MODIFY_CHOICES,
                                default=READ_ONLY,
                                validators=[validate_nfs_modify_str])
    """mount async by default"""
    SYNC_CHOICES = (
        (ASYNC, 'async'),
        (SYNC, 'sync'),
        )
    syncable = models.CharField(max_length=5, choices=SYNC_CHOICES,
                                default=ASYNC,
                                validators=[validate_nfs_sync_choice])
    """allow mouting from a >1024 port by default"""
    MSECURITY_CHOICES = (
        (SECURE, 'secure'),
        (INSECURE, 'insecure'),
        )
    mount_security = models.CharField(max_length=8, choices=MSECURITY_CHOICES,
                                      default=INSECURE)
    enabled = models.BooleanField(default=True)

"""
Samba share history
"""
class SambaShare(models.Model):
    YES = 'yes'
    NO = 'no'
    """share that is exported"""
    share = models.ForeignKey(Share)
    """mount point of the share"""
    path = models.CharField(max_length=4096, unique=True)
    comment = models.CharField(max_length=100, default='foo bar')
    BOOLEAN_CHOICES = (
        (YES, 'yes'),
        (NO, 'no'),
        )
    browsable = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                 default=YES)
    read_only = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                 default=NO)
    guest_ok = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                default=NO)
    create_mask = models.CharField(max_length=4, default='0755')


"""
Iscsi target
"""
class IscsiTarget(models.Model):
    share = models.ForeignKey(Share)
    """target id"""
    tid = models.IntegerField(unique=True)
    """target name"""
    tname = models.CharField(max_length=128, unique=True)
    """for now, this is the file created inside the share"""
    dev_name = models.CharField(max_length=128, unique=True)
    """size. this is static for now"""
    dev_size = models.IntegerField()


class PosixACLs(models.Model):
    smb_share = models.ForeignKey(SambaShare)
    USER = 'user'
    GROUP = 'group'
    OTHER = 'other'
    OWNER_CHOICES = (
        (USER, 'user'),
        (GROUP, 'group'),
        (OTHER, 'other'),
        )
    PERM_CHOICES = (
        ('r', 'r'),
        ('w', 'w'),
        ('x', 'x'),
        ('rw', 'rw'),
        ('rx', 'rx'),
        ('wx', 'wx'),
        ('rwx', 'rwx'),
        )
    owner = models.CharField(max_length=5, choices=OWNER_CHOICES)
    perms = models.CharField(max_length=3, choices=PERM_CHOICES)


class APIKeys(models.Model):
    user = models.CharField(max_length=8, unique=True)
    key = models.CharField(max_length=10, unique=True)


class Appliance(models.Model):
    """uuid is hostid-uid"""
    uuid = models.CharField(max_length=64, unique=True)
    ip = models.CharField(max_length=4096, unique=True)
    current_appliance = models.BooleanField(default=False)


class SupportCase(models.Model):
    """we use default id as the case number"""
    notes = models.TextField()
    """location of the zipped logfile(s)"""
    zipped_log = models.CharField(max_length=128)
    STATUS_CHOICES = (
        ('created', 'created'),
        ('submitted', 'submitted'),
        ('resolved', 'resolved'),
        )
    status = models.CharField(max_length=9, choices=STATUS_CHOICES)
    TYPE_CHOICES = (
        ('auto', 'auto'),
        ('manual', 'manual'),
        )
    case_type = models.CharField(max_length=6, choices=TYPE_CHOICES)

class DashboardConfig(models.Model):
    user = models.ForeignKey(User, null=False, unique=True)
    widgets = models.CharField(max_length=4096)

class NetworkInterface(models.Model):
    name = models.CharField(max_length=100)
    mac = models.CharField(max_length=100)
    boot_proto = models.CharField(max_length=100, null=True)
    onboot = models.CharField(max_length=100, null=True)
    network = models.CharField(max_length=100, null=True)
    netmask = models.CharField(max_length=100, null=True)
    ipaddr = models.CharField(max_length=100, null=True)

