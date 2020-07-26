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

from django.conf import settings
from django.db import models

from fs.btrfs import qgroup_exists
from storageadmin.models import Pool
from system.osi import mount_status

RETURN_BOOLEAN = True


class Share(models.Model):
    # pool that this share is part of
    pool = models.ForeignKey(Pool)
    """auto created 0/x qgroup"""
    qgroup = models.CharField(max_length=100)
    """quota group y/x explicitly created for this Share"""
    pqgroup = models.CharField(max_length=32, default=settings.MODEL_DEFS["pqgroup"])
    """name of the share, kind of like id"""
    name = models.CharField(max_length=4096, unique=True)
    """id of the share. numeric in case of btrfs"""
    uuid = models.CharField(max_length=100, null=True)
    """total size in KB"""
    size = models.BigIntegerField(default=0)
    owner = models.CharField(max_length=4096, default="root")
    group = models.CharField(max_length=4096, default="root")
    perms = models.CharField(max_length=9, default="755")
    toc = models.DateTimeField(auto_now=True)
    subvol_name = models.CharField(max_length=4096)
    replica = models.BooleanField(default=False)
    compression_algo = models.CharField(max_length=1024, null=True)
    # rusage and eusage reports original 0/x qgroup size
    # and this has only current share content without snapshots
    rusage = models.BigIntegerField(default=0)
    eusage = models.BigIntegerField(default=0)
    # Having Rockstor vol/subvols overriding btrfs standards
    # with snapshots(subvols) not under their vols, we use qgroup sizes
    # to report correct real vol sizes
    pqgroup_rusage = models.BigIntegerField(default=0)
    pqgroup_eusage = models.BigIntegerField(default=0)

    def __init__(self, *args, **kwargs):
        super(Share, self).__init__(*args, **kwargs)
        self.update_mnt_pt_var()

    def update_mnt_pt_var(self, *args, **kwargs):
        # Establish an instance variable of our mnt_pt.
        self.mnt_pt_var = "{}{}".format(settings.MNT_PT, self.name)

    @property
    def mnt_pt(self, *args, **kwargs):
        return self.mnt_pt_var

    @property
    def size_gb(self):
        return self.size / (1024.0 * 1024.0)

    @property
    def mount_status(self, *args, **kwargs):
        # Presents raw string of active mount options
        try:
            return mount_status(self.mnt_pt_var)
        except:
            return None

    @property
    def is_mounted(self, *args, **kwargs):
        # Calls mount_status in return boolean mode.
        try:
            return mount_status(self.mnt_pt_var, RETURN_BOOLEAN)
        except:
            return False

    @property
    def pqgroup_exist(self, *args, **kwargs):
        # Returns boolean status of pqgroup existence
        try:
            if str(self.pqgroup) == "-1/-1":
                return False
            else:
                return qgroup_exists(self.mnt_pt_var, "{}".format(self.pqgroup))
        except:
            return False

    class Meta:
        app_label = "storageadmin"
