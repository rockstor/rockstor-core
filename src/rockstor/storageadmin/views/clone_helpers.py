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

from storageadmin.models import (Share, Snapshot)
from storageadmin.util import handle_exception
from fs.btrfs import (add_clone, share_id, update_quota)
from rest_framework.response import Response
from storageadmin.serializers import ShareSerializer
import re
from django.conf import settings


def create_clone(share, new_name, request, logger, snapshot=None):
    # if snapshot is None, create clone of the share.
    # If it's not, then clone it.
    if (re.match(settings.SHARE_REGEX + '$', new_name) is None):
        e_msg = ('Clone name is invalid. It must start with a letter and can'
                 ' contain letters, digits, _, . and - characters')
        handle_exception(Exception(e_msg), request)
    if (Share.objects.filter(name=new_name).exists()):
        e_msg = ('Another Share with name: %s already exists.' % new_name)
        handle_exception(Exception(e_msg), request)
    if (Snapshot.objects.filter(share=share, name=new_name).exists()):
        e_msg = ('Snapshot with name: %s already exists for the '
                 'share: %s. Choose a different name' %
                 (new_name, share.name))
        handle_exception(Exception(e_msg), request)

    try:
        share_name = share.subvol_name
        snap = None
        if (snapshot is not None):
            snap = snapshot.real_name
        add_clone(share.pool, share_name, new_name, snapshot=snap)
        snap_id = share_id(share.pool, new_name)
        qgroup_id = ('0/%s' % snap_id)
        update_quota(share.pool, qgroup_id, share.size * 1024)
        new_share = Share(pool=share.pool, qgroup=qgroup_id, name=new_name,
                          size=share.size, subvol_name=new_name)
        new_share.save()
        return Response(ShareSerializer(new_share).data)
    except Exception as e:
        handle_exception(e, request)
