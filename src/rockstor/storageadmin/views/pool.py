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
Pool view. for all things at pool level
"""
import re
from rest_framework.response import Response
from django.db import transaction
from storageadmin.serializers import PoolInfoSerializer
from storageadmin.models import (Disk, Pool, Share, PoolStatistic)
from fs.btrfs import (add_pool, pool_usage, remove_pool,
                      resize_pool, umount_root)
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from django.conf import settings
from generic_view import GenericView

import logging
logger = logging.getLogger(__name__)


class PoolView(GenericView):
    serializer_class = PoolInfoSerializer
    RAID_LEVELS = ('raid0', 'raid1', 'raid10', 'single',)

    def get_queryset(self, *args, **kwargs):
        if ('pname' in kwargs):
            self.paginate_by = 0
            try:
                return Pool.objects.get(name=kwargs['pname'])
            except:
                return []
        sort_col = self.request.QUERY_PARAMS.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.QUERY_PARAMS.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Pool.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Pool.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        """
        input is a list of disks, raid_level and name of the pool.
        """
        try:
            disks = request.DATA['disks'].split(',')
            pname = request.DATA['pname']
            if (re.match('%s$' % settings.POOL_REGEX, pname) is None):
                e_msg = ('Share name must start with a letter(a-z) and can'
                         ' be followed by any of the following characters: '
                         'letter(a-z), digits(0-9), hiphen(-), underscore'
                         '(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (Pool.objects.filter(name=pname).exists()):
                e_msg = ('Pool with name: %s already exists.' % pname)
                handle_exception(Exception(e_msg), request)

            for d in disks:
                if (not Disk.objects.filter(name=d).exists()):
                    e_msg = ('Unknown disk: %s' % d)
                    handle_exception(Exception(e_msg), request)

            raid_level = request.DATA['raid_level']
            if (raid_level not in self.RAID_LEVELS):
                e_msg = ('Unsupported raid level. use one of: %s' %
                         self.RAID_LEVELS)
                handle_exception(Exception(e_msg), request)
            if (raid_level in self.RAID_LEVELS[0:2] and len(disks) == 1):
                e_msg = ('More than one disk is required for the chosen raid '
                         'level: %s' % raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[2] and len(disks) < 4):
                e_msg = ('Four or more disks are required for the chose raid '
                         'level: %s' % raid_level)
                handle_exception(Exception(e_msg), request)

            p = Pool(name=pname, raid=raid_level)
            add_pool(pname, raid_level, raid_level, disks)
            usage = pool_usage(disks[0])
            p.size = usage[0]
            p.save()
            p.disk_set.add(*[Disk.objects.get(name=d) for d in disks])
            return Response(PoolInfoSerializer(p).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, pname, command):
        """
        resize a pool.
        @pname: pool's name
        @command: 'add' - add a list of disks and hence expand the pool
                  'remove' - remove a list of disks and hence shrink the pool
        """
        try:
            if (not Pool.objects.filter(name=pname).exists()):
                msg = ('pool: %s does not exist' % pname)
                raise Exception(msg)

            disks = request.DATA['disks'].split(',')
            if (len(disks) == 0):
                msg = ('list of disks in the input is empty')
                raise Exception(msg)

            pool = Pool.objects.get(name=pname)
            mount_disk = Disk.objects.filter(pool=pool)[0].name
            if (command == 'add'):
                for d in disks:
                    d_o = Disk.objects.get(name=d)
                    if (d_o.pool is not None):
                        msg = ('disk %s already part of pool %s' %
                            (d, d_o.pool.name))
                        raise Exception(msg)
                    d_o.pool = pool
                    d_o.save()
                resize_pool(pool.name, mount_disk, disks)
            elif (command == 'remove'):
                if (len(Disk.objects.filter(pool=pool)) == 1):
                    msg = ('pool %s had only one disk. use delete command instead')
                    raise Exception(msg)
                for d in disks:
                    d_o = Disk.objects.get(name=d)
                    if (d_o.pool != pool):
                        msg = ('disk %s not part of pool %s' % (d, d_o.pool.name))
                        raise Exception(msg)
                    d_o.pool = None
                    d_o.save()
                mount_disk = Disk.objects.filter(pool=pool)[0].name
                resize_pool(pool.name, mount_disk, disks, add=False)
            else:
                msg = ('unknown command: %s' % command)
                raise Exception(msg)
            usage = pool_usage(mount_disk)
            pool.size = usage[0]
            pool.save()
            return Response(PoolInfoSerializer(pool).data)

        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, pname):
        try:
            pool = Pool.objects.get(name=pname)
            if (Share.objects.filter(pool=pool).exists()):
                e_msg = ('Pool: %s is not empty. Cannot delete until all '
                         'shares in the pool are deleted' % (pname))
                handle_exception(Exception(e_msg), request)
            umount_root('%s%s' % (settings.MNT_PT, pname))
            remove_pool(pname)
            pool.delete()
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

