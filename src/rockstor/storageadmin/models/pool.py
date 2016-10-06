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
from django.conf import settings
from smart_manager.models import PoolUsage
from fs.btrfs import pool_usage
import logging

logger = logging.getLogger(__name__)


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

    def usage_bound(self, disk_sizes=[], num_devices=0):
        """Return the total amount of storage possible within this pool's set
        of disks, in bytes.

        Algorithm adapted from Hugo Mills' implementation at:
        http://carfax.org.uk/btrfs-usage/js/btrfs-usage.js
        """
        if not disk_sizes:
            disk_sizes = [int(size) for size in self.disk_set
                          .values_list('size', flat=True)
                          .order_by('-size')]
            num_devices = len(disk_sizes)

        for index, size in enumerate(disk_sizes):
            logger.info('Device %s size: %s' % (index, size))

        # Determine RAID parameters
        data_ratio = 1
        stripes = 1
        parity = 0
        chunks = num_devices

        if self.raid == 'single':
            chunks = 1
        elif self.raid == 'raid0':
            stripes = 2
        elif self.raid == 'raid1':
            data_ratio = 2
            chunks = 2
        elif self.raid == 'raid10':
            data_ratio = 2
            stripes = max(2, int(num_devices / 2))
        elif self.raid == 'raid5':
            parity = 1
        elif self.raid == 'raid6':
            parity = 2

        # Round down so that we have an exact number of duplicate copies
        chunks -= chunks % data_ratio

        # Number of chunks to write at a time: as many as possible within the
        # number of stripes
        logger.info('Allocate %s chunks at a time' % chunks)
        # Check for feasibility at the lower end
        if num_devices < data_ratio * (stripes + parity):
            return 0

        # Compute the trivial bound
        bound = int(sum(disk_sizes) / chunks)
        logger.info('Trivial bound is %s / %s = %s'
                    % (sum(disk_sizes), chunks, bound))

        # For each partition point q, compute B_q (the test predicate) and
        # modify the trivial bound if it passes.
        bounding_q = -1
        for q in range(chunks - 1):
            slice = sum(disk_sizes[q + 1:])
            b = int(slice / (chunks - q - 1))
            logger.info('q = %s, bound is %s / %s = %s'
                        % (q, slice, chunks-q-1, b))
            if disk_sizes[q] >= b and b < bound:
                bound = b
                bounding_q = q

        # The bound is the number of allocations we can make in total. If we
        # have no bounding_q, then we have hit the trivial bound, and exhausted
        # all space, so we can return immediately.
        if bounding_q == -1:
            return bound * ((chunks / data_ratio) - parity)

        # If we have a bounding_q, then all the devices past q are full, and
        # we can remove them. The devices up to q have been used in every one
        # of the allocations, so we can just reduce them by bound.
        disk_sizes = [size - bound for index, size in enumerate(disk_sizes)
                      if index <= bounding_q]

        new_bound = self.usage_bound(disk_sizes, bounding_q + 1)

        return bound * ((chunks / data_ratio) - parity) + new_bound

    class Meta:
        app_label = 'storageadmin'
