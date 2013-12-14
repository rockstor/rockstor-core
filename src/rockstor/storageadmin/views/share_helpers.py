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

from django.conf import settings
from storageadmin.models import (Share, Disk)
from fs.btrfs import (mount_share, is_share_mounted)
from storageadmin.util import handle_exception

import logging
logger = logging.getLogger(__name__)

def helper_mount_share(share, mnt_pt=None):
    if (not is_share_mounted(share.name)):
        pool_device = Disk.objects.filter(pool=share.pool)[0].name
        if(mnt_pt is None):
            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
        mount_share(share.subvol_name, pool_device, mnt_pt)

def validate_share(sname, request):
    try:
        return Share.objects.get(name=sname)
    except:
        e_msg = ('Share with name: %s does not exist' % sname)
        handle_exception(Exception(e_msg), request)
