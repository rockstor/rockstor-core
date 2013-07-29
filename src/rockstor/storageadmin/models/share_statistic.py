"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
from storageadmin.models import Share


class ShareStatistic(models.Model):
    """share that this statistic represents"""
    share = models.ForeignKey(Share)
    """total capacity(KB) of the share at the time of this statistic"""
    total_capacity = models.IntegerField()
    """used capacity(KB) of this share at the time of this statistic"""
    used = models.IntegerField()
    """timestamp in utc of this statistic"""
    ts = models.DateTimeField(auto_now=True)

    class Meta:
        app_label = 'storageadmin'
