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

"""
view for anything at the share level
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from storageadmin.auth import DigestAuthentication
from django.db import transaction
from storageadmin.models import (Share, Snapshot, Disk, Qgroup, Pool)
from fs.btrfs import (add_share, remove_share, share_id, update_quota,
                      share_usage)
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException


import logging
logger = logging.getLogger(__name__)


class ShareView(APIView):

    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, sname=None):
        try:
            if (sname is None):
                return Response(ShareSerializer(Share.objects.all()).data)
            return Response(ShareSerializer(Share.objects.get(name=sname)).data)
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, sname):
        try:
            if (not Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s does not exist' % sname)
                handle_exception(Exception(e_msg), request)

            share = Share.objects.get(name=sname)
            new_size = int(request.DATA['size'])

            #if new_size < cur_usage, throw exception

            disk = Disk.objects.filter(pool=share.pool)[0]
            qgroup_id = self._update_quota(share.pool.name, disk.name, sname,
                                           new_size)
            cur_usage = int(share_usage(share.pool.name, disk.name, qgroup_id))
            share.size = new_size
            share.free = new_size - cur_usage
            share.save()
            return Response(ShareSerializer(share).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request, sname):
        try:
            if (Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s already exists.' % sname)
                handle_exception(Exception(e_msg), request)

            pool_name = request.DATA['pool']
            size = int(request.DATA['size'])
            pool = None
            for p in Pool.objects.all():
                if (p.name == pool_name):
                    pool = p
                    break
            disk = Disk.objects.filter(pool=p)[0]
            add_share(pool_name, disk.name, sname)
            qgroup_id = self._update_quota(pool_name, disk.name, sname, size)
            cur_usage = int(share_usage(pool_name, disk.name, qgroup_id))
            qgroup = Qgroup(uuid=qgroup_id)
            qgroup.save()
            s = Share(pool=pool, qgroup=qgroup, name=sname, size=size,
                    free=(size - cur_usage))
            s.save()
            return Response(ShareSerializer(s).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def _update_quota(self, pool_name, disk_name, share_name, size):
        sid = share_id(pool_name, disk_name, share_name)
        qgroup_id = '0/' + sid
        update_quota(pool_name, disk_name, qgroup_id, str(size))
        return qgroup_id

    @transaction.commit_on_success
    def delete(self, request, sname):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        try:
            if (Share.objects.filter(name=sname).exists()):
                share = Share.objects.get(name=sname)
                pool_device = Disk.objects.filter(pool=share.pool)[0].name
                remove_share(share.pool.name, pool_device, sname)
                share.delete()
                return Response()
        except Exception, e:
            handle_exception(e, request)
