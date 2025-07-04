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
from storageadmin.models import Share


class IscsiTarget(models.Model):
    share = models.ForeignKey(Share, on_delete=models.CASCADE)
    """target id"""
    tid = models.IntegerField(unique=True)
    """target name"""
    tname = models.CharField(max_length=128, unique=True)
    """for now, this is the file created inside the share"""
    dev_name = models.CharField(max_length=128, unique=True)
    """size. this is static for now"""
    dev_size = models.IntegerField()

    class Meta:
        app_label = "storageadmin"
