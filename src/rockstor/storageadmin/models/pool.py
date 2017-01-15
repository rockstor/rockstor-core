"""
Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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
from fs.btrfs import pool_usage, usage_bound


class Pool(models.Model):
    """Name of the pool"""
    name = models.CharField(max_length=4096, unique=True)
    """uuid given automatically by the client"""
    uuid = models.CharField(max_length=100, null=True)
    """size of the pool in KB"""
    size = models.BigIntegerField(default=0)
    raid = models.CharField(max_length=10)
    toc = models.DateTimeField(auto_now=True)
    compression = models.CharField(max_length=256, null=True)
    mnt_options = models.CharField(max_length=4096, null=True)
    """optional aux info. eg: role = root for OS Pool"""
    role = models.CharField(max_length=256, null=True)

    @property
    def free(self, *args, **kwargs):
        # Why do we compute pool usage on the fly like this and not like
        # share usage as part of state refresh? This is a lot simpler and
        # less code. For share usage, this type of logic could slow things
        # down quite a bit because there can be 100's of Shares, but number
        # of Pools even on a large instance is usually no more than a few.
        return self.size - pool_usage('%s%s' % (settings.MNT_PT, self.name))

    @property
    def reclaimable(self, *args, **kwargs):
        return 0

    def usage_bound(self):
        disk_sizes = [int(size) for size in self.disk_set
                      .values_list('size', flat=True)
                      .order_by('-size')]
        return usage_bound(disk_sizes, len(disk_sizes), self.raid)

    class Meta:
        app_label = 'storageadmin'
