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


class PoolUsage(models.Model):
    """pool usage information as time series"""

    pool = models.CharField(max_length=4096)
    free = models.BigIntegerField(default=0)
    reclaimable = models.BigIntegerField(default=0)
    ts = models.DateTimeField(auto_now=True, db_index=True)
    count = models.BigIntegerField(default=1)

    class Meta:
        app_label = "smart_manager"
