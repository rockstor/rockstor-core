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
from user import User


class SambaShare(models.Model):
    YES = 'yes'
    NO = 'no'
    """share that is exported"""
    share = models.OneToOneField('Share', related_name='sambashare')
    """mount point of the share"""
    path = models.CharField(max_length=4096, unique=True)
    comment = models.CharField(max_length=100, default='foo bar')
    BOOLEAN_CHOICES = (
        (YES, 'yes'),
        (NO, 'no'),
        )
    browsable = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                 default=YES)
    read_only = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                 default=NO)
    guest_ok = models.CharField(max_length=3, choices=BOOLEAN_CHOICES,
                                default=NO)
    create_mask = models.CharField(max_length=4, default='0755')
    custom_config = models.CharField(max_length=8192, null=True)

    def admin_users(self):
        return User.objects.filter(smb_share=self)

    def share_name(self, *args, **kwargs):
        return self.share.name

    class Meta:
        app_label = 'storageadmin'
