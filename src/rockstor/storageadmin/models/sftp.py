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
from storageadmin.models import Share  # noqa F401


class SFTP(models.Model):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    share = models.OneToOneField("Share", on_delete=models.CASCADE)
    """read only by default"""
    MODIFY_CHOICES = (
        (READ_ONLY, "ro"),
        (READ_WRITE, "rw"),
    )
    editable = models.CharField(max_length=2, choices=MODIFY_CHOICES, default=READ_ONLY)

    def share_name(self, *args, **kwargs):
        return self.share.name

    def share_id(self, *args, **kwargs):
        return self.share.id

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']
