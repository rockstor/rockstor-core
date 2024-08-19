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
from storageadmin.models import validators


class NFSExportGroup(models.Model):
    READ_ONLY = "ro"
    READ_WRITE = "rw"
    ASYNC = "async"
    SYNC = "sync"
    SECURE = "secure"
    INSECURE = "insecure"

    """hostname string in /etc/exports"""
    host_str = models.CharField(max_length=4096, validators=[validators.validate_nfs_host_str])
    """mount options"""
    """mount read only by default"""
    MODIFY_CHOICES = (
        (READ_ONLY, "ro"),
        (READ_WRITE, "rw"),
    )
    editable = models.CharField(
        max_length=2,
        choices=MODIFY_CHOICES,
        default=READ_WRITE,
        validators=[validators.validate_nfs_modify_str],
    )
    """mount async by default"""
    SYNC_CHOICES = (
        (ASYNC, "async"),
        (SYNC, "sync"),
    )
    syncable = models.CharField(
        max_length=5,
        choices=SYNC_CHOICES,
        default=ASYNC,
        validators=[validators.validate_nfs_sync_choice],
    )
    """allow mounting from a >1024 port by default"""
    MSECURITY_CHOICES = (
        (SECURE, "secure"),
        (INSECURE, "insecure"),
    )
    mount_security = models.CharField(
        max_length=8, choices=MSECURITY_CHOICES, default=INSECURE
    )
    nohide = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)

    """export to this host with rw, no_root_squash meant of acl administration
    via nis"""
    admin_host = models.CharField(max_length=1024, null=True)

    class Meta:
        app_label = "storageadmin"
