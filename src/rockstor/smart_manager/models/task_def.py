"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import json
from django.db import models
from storageadmin.models import Pool, Share
from smart_manager.constants import TASK_TYPES, TASK_SCRIPTS
from system.task_util import remove_crontab


class TaskDefinition(models.Model):
    name = models.CharField(max_length=255, unique=True)
    task_type = models.CharField(max_length=100, choices=TASK_TYPES)
    json_meta = models.CharField(max_length=8192)
    enabled = models.BooleanField(default=True)
    crontab = models.CharField(max_length=64, null=True)
    crontabwindow = models.CharField(max_length=64, null=True)
    # Added crontabwindow field to storage exec window value - null to true for
    # backward compatibility with old scheduled tasks

    class Meta:
        app_label = "smart_manager"

    def delete(self, **kwargs):
        """
        We override model.delete to ensure, if CRONTAB_FILE exists,
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
        script = self.script
        instance_id = self.id
        # Upstream call to do our SQL delete()
        super_return = super().delete(**kwargs)
        # "post_delete" signal equivalent.
        try:
            remove_crontab(script, instance_id)
        except Exception:
            pass
        return super_return

    @property
    def share_name(self, *args, **kwargs):
        sn = None
        if self.task_type == "snapshot":
            task_metadata = json.loads(self.json_meta)
            try:
                sn = Share.objects.get(id=task_metadata["share"]).name
            except Exception:
                sn = "N/A"
        return sn

    @property
    def pool_name(self, *args, **kwargs):
        pn = None
        if self.task_type == "scrub":
            task_metadata = json.loads(self.json_meta)
            try:
                pn = Pool.objects.get(id=task_metadata["pool"]).name
            except Exception:
                pn = "N/A"
        return pn

    @property
    def script(self, *args, **kwargs):
        """
        Returns the script to be executed for this task based on task_type.
        Sources smart_manager.constants.
        :param args:
        :param kwargs:
        :return:
        """
        script: str = ""
        if self.task_type in TASK_TYPES["power"]:
            script: str = TASK_SCRIPTS["power"]
        elif self.task_type in TASK_SCRIPTS:
            script: str = TASK_SCRIPTS[self.task_type]
        return script
