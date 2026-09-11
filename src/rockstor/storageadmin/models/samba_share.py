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
from storageadmin.models.user import User
from system.samba_util import remove_smb_export


class SambaShare(models.Model):
    YES = "yes"
    NO = "no"
    """share that is exported"""
    share = models.OneToOneField("Share", related_name="sambashare", on_delete=models.CASCADE)
    """mount point of the share"""
    path = models.CharField(max_length=4096, unique=True)
    comment = models.CharField(max_length=100, default="foo bar")
    BOOLEAN_CHOICES = (
        (YES, "yes"),
        (NO, "no"),
    )
    browsable = models.CharField(max_length=3, choices=BOOLEAN_CHOICES, default=YES)
    read_only = models.CharField(max_length=3, choices=BOOLEAN_CHOICES, default=NO)
    guest_ok = models.CharField(max_length=3, choices=BOOLEAN_CHOICES, default=NO)
    shadow_copy = models.BooleanField(default=False)
    time_machine = models.BooleanField(default=False)
    snapshot_prefix = models.CharField(max_length=128, null=True)

    def delete(self, **kwargs):
        """
        We override model.delete to ensure, if SMB_CONFIG exists,
        that matching entries are removed: but this will fail for mass opperations:
        https://docs.djangoproject.com/en/6.0/topics/db/models/#overriding-predefined-model-methods
        "Overridden model methods are not called on bulk operations"
        Pre and Post delete signals are suggested as a work-around:
        Model.post_delete is
        "... sent at the end of a model’s delete() method and a queryset’s delete() method."
        Ergo do not depend on this opperation for bulk delete opperations.
        """
        # Model instance.id is set to None by super().delete so stash first.
        # Ref: https://docs.djangoproject.com/en/6.0/ref/models/instances/#django.db.models.Model.delete
        instance_id = self.id
        # Upstream call to do our SQL delete()
        super_return = super().delete(**kwargs)
        # "post_delete" signal equivalent.
        try:
            remove_smb_export([self.share.name])
        except Exception:
            pass
        return super_return

    def admin_users(self):
        return User.objects.filter(smb_share=self)

    def share_name(self, *args, **kwargs):
        return self.share.name

    def share_id(self, *args, **kwargs):
        return self.share.id

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']
