"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from django.db import models
from smart_manager.models import SProbe


class NFSDShareClientDistribution(models.Model):

    """
    for a given ts and share, number and i/o size of various nfs calls
    """

    rid = models.ForeignKey(SProbe, on_delete=models.CASCADE)
    ts = models.DateTimeField(db_index=True)
    share = models.CharField(max_length=255)
    client = models.CharField(max_length=100)
    num_lookup = models.BigIntegerField(default=0)
    num_read = models.BigIntegerField(default=0)
    num_write = models.BigIntegerField(default=0)
    num_create = models.BigIntegerField(default=0)
    num_commit = models.BigIntegerField(default=0)
    num_remove = models.BigIntegerField(default=0)

    """
    sums are in KB
    """
    sum_read = models.BigIntegerField(default=0)
    sum_write = models.BigIntegerField(default=0)

    class Meta:
        app_label = "smart_manager"
