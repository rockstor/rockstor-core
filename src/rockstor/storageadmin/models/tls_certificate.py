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


class TLSCertificate(models.Model):
    # support upto 12K length certs.
    name = models.CharField(max_length=1024, unique=True)
    certificate = models.CharField(max_length=12288, null=True)
    key = models.CharField(max_length=12288, null=True)

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']
