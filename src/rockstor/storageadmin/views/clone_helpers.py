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

from storageadmin.models import (Share, Disk, Snapshot)
from storageadmin.util import handle_exception
from fs.btrfs import (add_snap, share_id, mount_share, update_quota)
from django.conf import settings
from rest_framework.response import Response
from storageadmin.serializers import ShareSerializer

def create_clone(share, new_name, request, logger):
    if (Share.objects.filter(name=new_name).exists()):
        e_msg = ('Share with name: %s already exists.' % new_name)
        handle_exception(Exception(e_msg), request)
    pool_device = Disk.objects.filter(pool=share.pool)[0].name
    snap_name = ('%s-clone-%s-snapshot' % (share.name, new_name))
    if (Snapshot.objects.filter(share=share, name=snap_name).exists()):
        e_msg = ('Snapshot with name: %s already exists for the '
                 'share: %s' % (snap_name, share.name))
        handle_exception(Exception(e_msg), request)

    try:
        add_snap(share.pool.name, pool_device, share.subvol_name,
                 snap_name, share_prepend=False)
        snap_id = share_id(share.pool.name, pool_device, snap_name)
        qgroup_id = ('0/%s' % snap_id)
        update_quota(share.pool.name, pool_device, qgroup_id,
                     share.size * 1024)
        new_share = Share(pool=share.pool, qgroup=qgroup_id, name=new_name,
                          size=share.size, subvol_name=snap_name)
        new_share.save()
        return Response(ShareSerializer(new_share).data)
    except Exception, e:
        e_msg = ('Failed to create clone due to a system error.')
        logger.error(e_msg)
        logger.exception(e)
        handle_exception(Exception(e_msg), request)
