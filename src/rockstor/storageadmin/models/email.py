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


class EmailClient(models.Model):
    smtp_server = models.CharField(max_length=1024)
    port = models.IntegerField(default=587)
    name = models.CharField(max_length=1024, unique=True)
    sender = models.CharField(max_length=1024)
    username = models.CharField(max_length=1024)
    receiver = models.CharField(max_length=1024)

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']
