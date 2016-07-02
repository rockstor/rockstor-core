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
from system.osi import get_disk_power_status, read_hdparm_setting, \
    get_disk_APM_level, get_dev_temp_name


class Disk(models.Model):
    """Pool can be null for disks that are not part of any pool currently"""
    pool = models.ForeignKey(Pool, null=True, on_delete=models.SET_NULL)
    """ Previously the name field contained sda, sdb etc..
    Revised to contain device names for use with the udev created links at
    /dev/disk/by-id/ which in turn are symlinks to sda, sdb etc.
    eg ata-QEMU_HARDDISK_QM00005 ie mostly derived from model and serial number.
    """
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
    """custom smart options for drive, ie for USB bridges / enclosures
    eg "-d usbjmicron,p" or "-s on -d 3ware,0".
    """
    smart_options = models.CharField(max_length=64, null=True)
    """role is json formatted aux info to flag special use disks
    ie "import" or "backup" flags for temp external drive connection.
    Also flags mdraid status eg {"mdraid": "isw_raid_member"} or
    {"mdraid": "linux_raid_member"}.
    role can be Null if no flags are in use.
    """
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
            return read_hdparm_setting(str(self.name))
        except:
            return None

    @property
    def apm_level(self, *args, **kwargs):
        try:
            return get_disk_APM_level(str(self.name))
        except:
            return None

    @property
    def temp_name(self, *args, **kwargs):
        try:
            return get_dev_temp_name(str(self.name))
        except:
            return None

    class Meta:
        app_label = 'storageadmin'
