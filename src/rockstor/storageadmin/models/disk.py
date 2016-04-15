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
from storageadmin.models import Pool
from system.osi import get_disk_power_status, get_dev_byid_name, \
    read_hdparm_setting, get_disk_APM_level


class Disk(models.Model):
    """Pool can be null for disks that are not part of any pool currently"""
    pool = models.ForeignKey(Pool, null=True, on_delete=models.SET_NULL)
    """typically sda, sdb etc.. max_length = 0 supports 100s of disks"""
    name = models.CharField(max_length=64, unique=True)
    """total size in KB"""
    size = models.BigIntegerField(default=0)
    """true if disk went offline"""
    offline = models.BooleanField(default=False)
    """whether the disk is partitioned at the moment. relevent for root disks
    and such that may not be part of any pool but need to be in the model"""
    parted = models.BooleanField()
    """previously created btrfs filesystem on the disk"""
    btrfs_uuid = models.CharField(max_length=1024, null=True)
    model = models.CharField(max_length=1024, null=True)
    serial = models.CharField(max_length=1024, null=True)
    transport = models.CharField(max_length=1024, null=True)
    vendor = models.CharField(max_length=1024, null=True)
    smart_available = models.BooleanField(default=False)
    smart_enabled = models.BooleanField(default=False)
    """custom smart options for drive, ie for USB bridges / enclosures"""
    """eg "-d usbjmicron,p" or "-s on -d 3ware,0"."""
    smart_options = models.CharField(max_length=64, null=True)
    """drive role ie "isw_raid_member" or "linux_raid_member"."""
    """could also be "import" or "backup" for temp external drive connection."""
    """role is aux info to flag special use disks"""
    role = models.CharField(max_length=256, null=True)

    @property
    def pool_name(self, *args, **kwargs):
        try:
            return self.pool.name
        except:
            return None

    @property
    def power_state(self, *args, **kwargs):
        try:
            return get_disk_power_status(str(self.name))
        except:
            return None

    @property
    def hdparm_setting(self, *args, **kwargs):
        try:
            return read_hdparm_setting(get_dev_byid_name(self.name))
        except:
            return None

    @property
    def apm_level(self, *args, **kwargs):
        try:
            return get_disk_APM_level(str(self.name))
        except:
            return None

    class Meta:
        app_label = 'storageadmin'
