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
from storageadmin.models import (Disk, Pool, Share)
from fs.btrfs import (add_pool, pool_usage, remove_pool,
                      resize_pool, umount_root, btrfs_uuid)
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from django.conf import settings
import rest_framework_custom as rfc
from contextlib import contextmanager

import logging
logger = logging.getLogger(__name__)


class PoolView(rfc.GenericView):
    serializer_class = PoolInfoSerializer
    RAID_LEVELS = ('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')

    @staticmethod
    @contextmanager
    def _handle_exception(request, msg=None):
        try:
            yield
        except RockStorAPIException:
            raise
        except Exception, e:
            if (msg is None):
                msg = ('An unhandled low level exception occured while '
                       'processing the request.')
            handle_exception(e, request, msg)

    def _pool_size(self, disks, raid_level):
        disk_size = None
        for d in disks:
            size = Disk.objects.get(name=d).size
            if (disk_size is None or disk_size > size):
                disk_size = size

        if (raid_level == self.RAID_LEVELS[0]):
            return disk_size
        if (raid_level == self.RAID_LEVELS[1]):
            return disk_size * len(disks)
        if (raid_level in self.RAID_LEVELS[2:4]):
            return disk_size * (len(disks) / 2)
        if (raid_level == self.RAID_LEVELS[4]):
            return disk_size * (len(disks) - 1)
        if (raid_level == self.RAID_LEVELS[5]):
            return disk_size * (len(disks) - 2)

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
        with self._handle_exception(request):
            disks = [self._validate_disk(d, request) for d in
                     request.DATA.get('disks')]
            pname = request.DATA['pname']
            if (re.match('%s$' % settings.POOL_REGEX, pname) is None):
                e_msg = ('Pool name must start with a letter(a-z) and can'
                         ' be followed by any of the following characters: '
                         'letter(a-z), digits(0-9), hyphen(-), underscore'
                         '(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (Pool.objects.filter(name=pname).exists()):
                e_msg = ('Pool with name: %s already exists.' % pname)
                handle_exception(Exception(e_msg), request)

            for d in disks:
                if (d.btrfs_uuid is not None):
                    e_msg = ('Another BTRFS filesystem exists on this '
                             'disk(%s). Erase the disk and try again.'
                             % d.name)
                    handle_exception(Exception(e_msg), request)

            raid_level = request.DATA['raid_level']
            if (raid_level not in self.RAID_LEVELS):
                e_msg = ('Unsupported raid level. use one of: %s' %
                         self.RAID_LEVELS)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[0] and len(disks) != 1):
                e_msg = ('Exactly one disk is required for the raid level: '
                         '%s' % raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[1] and len(disks) == 1):
                e_msg = ('More than one disk is required for the raid '
                         'level: %s' % raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[2] and len(disks) != 2):
                e_msg = ('Exactly two disks are required for the raid level: '
                         '%s' % raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[3]):
                if (len(disks) < 4):
                    e_msg = ('A minimum of Four drives are required for the '
                             'raid level: %s' % raid_level)
                    handle_exception(Exception(e_msg), request)
                elif (len(disks) % 2 != 0):
                    e_msg = ('Even number of drives are required for the '
                             'raid level: %s' % raid_level)
                    handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[4] and len(disks) < 3):
                e_msg = ('Three or more disks are required for the raid '
                         'level: %s' % raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[5] and len(disks) < 4):
                e_msg = ('Four or more disks are required for the raid '
                         'level: %s' % raid_level)
                handle_exception(Exception(e_msg), request)

            dnames = [d.name for d in disks]
            pool_size = self._pool_size(dnames, raid_level)
            add_pool(pname, raid_level, raid_level, dnames)
            pool_uuid = btrfs_uuid(dnames[0])
            p = Pool(name=pname, raid=raid_level, size=pool_size,
                     uuid=pool_uuid)
            p.save()
            p.disk_set.add(*disks)
            return Response(PoolInfoSerializer(p).data)

    def _validate_disk(self, d, request):
        try:
            return Disk.objects.get(name=d)
        except:
            e_msg = ('Disk(%s) does not exist' % d)
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def put(self, request, pname, command):
        """
        resize a pool.
        @pname: pool's name
        @command: 'add' - add a list of disks and hence expand the pool
                  'remove' - remove a list of disks and hence shrink the pool
        """
        try:
            try:
                pool = Pool.objects.get(name=pname)
            except:
                e_msg = ('pool: %s does not exist' % pname)
                handle_exception(Exception(e_msg), request)

            disks = [self._validate_disk(d, request) for d in
                     request.DATA.get('disks')]
            if (len(disks) == 0):
                msg = ('list of disks in the input is empty')
                raise Exception(msg)
            dnames = [d.name for d in disks]

            for d in disks:
                if (d.pool is not None and d.pool != pool):
                    e_msg = ('Disk(%s) belongs to another pool(%s)' %
                             (d.name, d.pool.name))
                    handle_exception(Exception(e_msg), request)

            mount_disk = Disk.objects.filter(pool=pool)[0].name
            if (command == 'add'):
                for d_o in disks:
                    d_o.pool = pool
                    d_o.save()
                resize_pool(pool.name, mount_disk, dnames)
            elif (command == 'remove'):
                if (pool.raid == 'raid0' or pool.raid == 'raid1' or
                    pool.raid == 'raid10' or pool.raid == 'single'):
                    e_msg = ('Removing drives from this(%s) raid '
                             'configuration is not supported' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                if (pool.raid == 'raid5' and len(disks) < 3):
                    e_msg = ('Resize not possible because a minimum of 3 '
                             'drives is required for this(%s) '
                             'raid configuration.' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                if (pool.raid == 'raid6' and len(disks) < 4):
                    e_msg = ('Resize not possible because a minimum of 4 '
                             'drives is required for this(%s) raid '
                             'configuration' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                for d in disks:
                    d_o = Disk.objects.get(name=d)
                    d_o.pool = None
                    d_o.save()
                mount_disk = Disk.objects.filter(pool=pool)[0].name
                resize_pool(pool.name, mount_disk, dnames, add=False)
            else:
                msg = ('unknown command: %s' % command)
                raise Exception(msg)
            usage = pool_usage(mount_disk)
            pool.size = usage[0]
            pool.save()
            return Response(PoolInfoSerializer(pool).data)
        except RockStorAPIException:
            raise
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
            pool_path = ('%s%s' % (settings.MNT_PT, pname))
            remove_pool(pool_path)
            umount_root(pool_path)
            pool.delete()
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
