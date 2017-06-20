"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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

from django.conf import settings
from django.db import models
from django.db.models.signals import (post_save, post_delete)
from django.dispatch import receiver

from storageadmin.models import Pool
from .netatalk_share import NetatalkShare
from system.services import (systemctl, refresh_afp_config)


class Share(models.Model):
    "pool that this share is part of"""
    pool = models.ForeignKey(Pool)
    """auto created 0/x qgroup"""
    qgroup = models.CharField(max_length=100)
    """quota group y/x explicitly created for this Share"""
    pqgroup = models.CharField(max_length=32,
                               default=settings.MODEL_DEFS['pqgroup'])
    """name of the share, kind of like id"""
    name = models.CharField(max_length=4096, unique=True)
    """id of the share. numeric in case of btrfs"""
    uuid = models.CharField(max_length=100, null=True)
    """total size in KB"""
    size = models.BigIntegerField(default=0)
    owner = models.CharField(max_length=4096, default='root')
    group = models.CharField(max_length=4096, default='root')
    perms = models.CharField(max_length=9, default='755')
    toc = models.DateTimeField(auto_now=True)
    subvol_name = models.CharField(max_length=4096)
    replica = models.BooleanField(default=False)
    compression_algo = models.CharField(max_length=1024, null=True)
    # rusage and eusage reports original 0/x qgroup size
    # and this has only current share content without snapshots
    rusage = models.BigIntegerField(default=0)
    eusage = models.BigIntegerField(default=0)
    # Having Rockstor vol/subvols overriding btrfs standards
    # with snapshots(subvols) not under their vols, we use qgroup sizes
    # to report correct real vol sizes
    pqgroup_rusage = models.BigIntegerField(default=0)
    pqgroup_eusage = models.BigIntegerField(default=0)

    @property
    def size_gb(self):
        return self.size / (1024.0 * 1024.0)

    class Meta:
        app_label = 'storageadmin'


def refresh_afp():
    refresh_afp_config(list(NetatalkShare.objects.all()))
    systemctl('netatalk', 'reload-or-restart')


@receiver(post_save, sender=Share, dispatch_uid='update_afp')
def update_afp(sender, instance, **kwargs):
    try:
        # throws exception and short circuits if netatalkshare doesn't exist.
        instance.netatalkshare
        refresh_afp()
    except Exception:
        pass


@receiver(post_delete, sender=Share, dispatch_uid='clean_afp')
def clean_afp(sender, instance, **kwargs):
    try:
        refresh_afp()
    except Exception:
        pass
