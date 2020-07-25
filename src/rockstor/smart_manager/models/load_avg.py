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

from django.db import models


class LoadAvg(models.Model):

    load_1 = models.FloatField()
    load_5 = models.FloatField()
    load_15 = models.FloatField()
    active_threads = models.IntegerField()
    total_threads = models.IntegerField()
    latest_pid = models.IntegerField()
    idle_seconds = models.IntegerField()
    ts = models.DateTimeField(auto_now=True, db_index=True)

    @property
    def uptime(self, *args, **kwargs):
        with open("/proc/uptime") as ufo:
            return int(float(ufo.readline().split()[0]))

    class Meta:
        app_label = "smart_manager"
