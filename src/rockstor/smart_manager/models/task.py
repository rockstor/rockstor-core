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


class Task(models.Model):

    name = models.CharField(max_length=255)
    json_meta = models.CharField(max_length=8192)
    STATE_CHOICES = [
        ('scheduled',) * 2,
        ('aborted',) * 2,
        ('running',) * 2,
        ('finished',) * 2,
        ]
    state = models.CharField(max_length=7, choices=STATE_CHOICES)
    start = models.DateTimeField(auto_now=True)
    end = models.DateTimeField(null=True)

    class Meta:
        app_label = 'smart_manager'
