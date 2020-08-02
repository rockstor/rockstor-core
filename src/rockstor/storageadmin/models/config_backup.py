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

import os
from django.db import models
from django.conf import settings


class ConfigBackup(models.Model):
    filename = models.CharField(max_length=64)
    md5sum = models.CharField(max_length=32, null=True)
    size = models.IntegerField(null=True)
    config_backup = models.FileField(upload_to="config-backups", null=True)

    def __unicode__(self):
        return "{0}".format(self.filename)

    def full_path(self):
        return os.path.join(self.cb_dir(), self.filename)

    class Meta:
        app_label = "storageadmin"

    @staticmethod
    def cb_dir():
        return settings.DEFAULT_CB_DIR
