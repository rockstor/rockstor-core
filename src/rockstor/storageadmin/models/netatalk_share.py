"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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


class NetatalkShare(models.Model):
    YES = 'yes'
    NO = 'no'
    """share that is exported"""
    share = models.OneToOneField('Share', related_name='netatalkshare')
    """mount point of the share"""
    path = models.CharField(max_length=4096, unique=True)
    description = models.CharField(max_length=1024, default='afp on rockstor')
    BOOLEAN_CHOICES = (
        (YES, 'yes'),
        (NO, 'no'),
        )
    time_machine = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                    default=YES)

    def share_name(self, *args, **kwargs):
        return self.share.name

    def share_id(self, *args, **kwargs):
        return self.share.id

    @property
    def vol_size(self):
        return self.share.size

    class Meta:
        app_label = 'storageadmin'
