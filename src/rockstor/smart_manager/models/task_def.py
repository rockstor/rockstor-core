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

import json

from django.db import models
from storageadmin.models import Pool, Share


class TaskDefinition(models.Model):
    name = models.CharField(max_length=255, unique=True)
    TASK_TYPES = [
        ("scrub",) * 2,
        ("snapshot",) * 2,
        ("reboot",) * 2,
        ("shutdown",) * 2,
        ("suspend",) * 2,
        ("custom",) * 2,
    ]
    task_type = models.CharField(max_length=100, choices=TASK_TYPES)
    json_meta = models.CharField(max_length=8192)
    enabled = models.BooleanField(default=True)
    crontab = models.CharField(max_length=64, null=True)
    crontabwindow = models.CharField(max_length=64, null=True)
    # Added crontabwindow field to storage exec window value - null to true for
    # backward compatibility with old scheduled tasks

    class Meta:
        app_label = "smart_manager"

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
