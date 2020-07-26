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
from storageadmin.models import Pool


class PoolScrub(models.Model):

    pool = models.ForeignKey(Pool)
    # with a max of 10 chars we use 'halted' to indicated 'interrupted'
    status = models.CharField(max_length=10, default="started")
    # pid is the process id of a scrub job
    pid = models.IntegerField()
    start_time = models.DateTimeField(auto_now=True)
    end_time = models.DateTimeField(null=True)
    time_left = models.BigIntegerField(default=0)
    eta = models.DateTimeField(null=True)
    rate = models.CharField(max_length=15, default="")
    kb_scrubbed = models.BigIntegerField(null=True)
    data_extents_scrubbed = models.BigIntegerField(default=0)
    tree_extents_scrubbed = models.BigIntegerField(default=0)
    tree_bytes_scrubbed = models.BigIntegerField(default=0)
    read_errors = models.IntegerField(default=0)
    csum_errors = models.IntegerField(default=0)
    verify_errors = models.IntegerField(default=0)
    no_csum = models.IntegerField(default=0)
    csum_discards = models.IntegerField(default=0)
    super_errors = models.IntegerField(default=0)
    malloc_errors = models.IntegerField(default=0)
    uncorrectable_errors = models.IntegerField(default=0)
    unverified_errors = models.IntegerField(default=0)
    corrected_errors = models.IntegerField(default=0)
    last_physical = models.BigIntegerField(default=0)

    class Meta:
        app_label = "storageadmin"
