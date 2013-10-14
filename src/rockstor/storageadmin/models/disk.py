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

class Disk(models.Model):
    """Pool can be null for disks that are not part of any pool currently"""
    pool = models.ForeignKey(Pool, null=True, on_delete=models.SET_NULL )
    """typically sda, sdb etc.. max_length = 0 supports 100s of disks"""
    name = models.CharField(max_length=10, unique=True)
    """total size in GB"""
    size = models.IntegerField()
    """true if disk went offline"""
    offline = models.BooleanField(default=False)
    """whether the disk is partitioned at the moment. relevent for root disks
    and such that may not be part of any pool but need to be in the model"""
    parted = models.BooleanField()

    def pool_name(self, *args, **kwargs):
        try:
            return self.pool.name
        except:
            return None

    class Meta:
        app_label = 'storageadmin'
