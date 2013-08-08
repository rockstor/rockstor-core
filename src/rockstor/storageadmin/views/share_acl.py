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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.conf import settings
from storageadmin.auth import DigestAuthentication
from storageadmin.models import (Share, SambaShare, NFSExport, Disk)
from storageadmin.util import handle_exception
from storageadmin.serializers import ShareSerializer
from storageadmin.exceptions import RockStorAPIException
from fs.btrfs import (mount_share, is_share_mounted, umount_root)
from system.osi import refresh_nfs_exports
from storageadmin.views import ShareView
from system.acl import (chown, chmod)

import logging
logger = logging.getLogger(__name__)


class ShareACLView(ShareView):

    @transaction.commit_on_success
    def post(self, request, sname):
        try:
            share = Share.objects.get(name=sname)
            options = {
                'owner': 'root',
                'group': 'root',
                'perms': '755',
                'orecursive': False,
                'precursive': False,
                }
            if ('owner' in request.DATA):
                options['owner'] = request.DATA['owner']
            if ('group' in request.DATA):
                options['group'] = request.DATA['group']
            else:
                options['group'] = options['owner']
            if ('orecursive' in request.DATA):
                options['orecursive'] = True
            if ('perms' in request.DATA):
                options['perms'] = request.DATA['perms']
            if ('precursive' in request.DATA):
                options['precursive'] = True

            share.owner = options['owner']
            share.group = options['group']
            share.perms = options['perms']
            share.save()

            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
            force_mount = False
            if (not is_share_mounted(share.name)):
                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                mount_share(share.name, pool_device, mnt_pt)
                force_mount = True
            chown(mnt_pt, options['owner'], options['group'],
                  options['orecursive'])
            chmod(mnt_pt, options['perms'], options['precursive'])
            if (force_mount is True):
                umount_root(mnt_pt)
            return Response(ShareSerializer(share).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def delete(self, request, sname):
        pass

