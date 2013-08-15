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
    toc = models.DateTimeField(auto_now=True)

    def cur_usage(self, *args, **kwargs):
        try:
            pu = PoolUsage.objects.filter(pool=self.name).order_by('-ts')[0]
            return pu.usage
        except:
            return -1

    class Meta:
        app_label = 'storageadmin'
