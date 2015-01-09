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
from fs.btrfs import (add_pool, pool_usage, resize_pool, umount_root,
                      btrfs_uuid, mount_root, remount)
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)


class PoolView(rfc.GenericView):
    serializer_class = PoolInfoSerializer
    RAID_LEVELS = ('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')

    def _pool_size(self, disks, raid_level):
        disk_size = None
        total_size = 0
        for d in disks:
            size = Disk.objects.get(name=d).size
            total_size = total_size + size
            if (disk_size is None or disk_size > size):
                disk_size = size

        if (raid_level == self.RAID_LEVELS[0]):
            return disk_size
        if (raid_level == self.RAID_LEVELS[1]):
            return total_size
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

    def _validate_mnt_options(self, request):
        mnt_options = request.DATA.get('mnt_options', None)
        if (mnt_options is None):
            return ''
        allowed_options = {
            'alloc_start': int,
            'autodefrag': None,
            'clear_cache': None,
            'commit': int,
            'compress-force': settings.COMPRESSION_TYPES,
            'discard': None,
            'fatal_errors': None,
            'inode_cache': None,
            'max_inline': int,
            'metadata_ratio': int,
            'noacl': None,
            'nodatacow': None,
            'nodatasum': None,
            'nospace_cache': None,
            'space_cache': None,
            'ssd': None,
            'ssd_spread': None,
            'thread_pool': int,
            'noatime': None,
            '': None,
        }
        o_fields = mnt_options.split(',')
        for o in o_fields:
            v = None
            if (re.search('=', o) is not None):
                o, v = o.split('=')
            if (o not in allowed_options):
                e_msg = ('mount option(%s) not allowed. Make sure there are '
                         'no whitespaces in the input. Allowed options: %s' %
                         (o, allowed_options.keys()))
                handle_exception(Exception(e_msg), request)
            if (o == 'compress-force' and
                v not in allowed_options['compress-force']):
                e_msg = ('compress-force is only allowed with %s' %
                         (settings.COMPRESSION_TYPES))
                handle_exception(Exception(e_msg), request)
            if (type(allowed_options[o]) is int):
                try:
                    int(v)
                except:
                    e_msg = ('Value for mount option(%s) must be an integer' %
                             (o))
                    handle_exception(Exception(e_msg), request)
        return mnt_options

    def _validate_compression(self, request):
        compression = request.DATA.get('compression', 'no')
        if (compression is None):
            compression = 'no'
        if (compression not in settings.COMPRESSION_TYPES):
            e_msg = ('Unsupported compression algorithm(%s). Use one of '
                     '%s' % (compression, settings.COMPRESSION_TYPES))
            handle_exception(Exception(e_msg), request)
        return compression

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

            compression = self._validate_compression(request)
            mnt_options = self._validate_mnt_options(request)
            dnames = [d.name for d in disks]
            pool_size = self._pool_size(dnames, raid_level)
            p = Pool(name=pname, raid=raid_level, size=pool_size,
                     compression=compression, mnt_options=mnt_options)
            add_pool(p, dnames)
            p.uuid = btrfs_uuid(dnames[0])
            p.save()
            p.disk_set.add(*disks)
            mount_root(p, dnames[0])
            return Response(PoolInfoSerializer(p).data)

    def _validate_disk(self, d, request):
        try:
            return Disk.objects.get(name=d)
        except:
            e_msg = ('Disk(%s) does not exist' % d)
            handle_exception(Exception(e_msg), request)

    def _remount(self, request, pool):
        compression = self._validate_compression(request)
        mnt_options = self._validate_mnt_options(request)
        if ((compression == pool.compression and
             mnt_options == pool.mnt_options)):
            return Response()

        with transaction.commit_on_success():
            pool.compression = compression
            pool.mnt_options = mnt_options
            pool.save()

        if (re.search('noatime', mnt_options) is None):
            mnt_options = ('%s,relatime,atime' % mnt_options)

        if (re.search('compress-force', mnt_options) is None):
            mnt_options = ('%s,compress=%s' % (mnt_options, compression))

        with open('/proc/mounts') as mfo:
            mount_map = {}
            for l in mfo.readlines():
                share_name = None
                if (re.search(
                        '%s|%s' % (settings.NFS_EXPORT_ROOT, settings.MNT_PT),
                        l) is not None):
                    share_name = l.split()[1].split('/')[2]
                elif (re.search(settings.SFTP_MNT_ROOT, l) is not None):
                    share_name = l.split()[1].split('/')[3]
                else:
                    continue
                if (share_name not in mount_map):
                    mount_map[share_name] = [l.split()[1], ]
                else:
                    mount_map[share_name].append(l.split()[1])
        failed_remounts = []
        try:
            pool_mnt = '/mnt2/%s' % pool.name
            remount(pool_mnt, mnt_options)
        except:
            failed_remounts.append(pool_mnt)
        for share in mount_map.keys():
            if (Share.objects.filter(pool=pool, name=share).exists()):
                for m in mount_map[share]:
                    try:
                        remount(m, mnt_options)
                    except Exception, e:
                        logger.exception(e)
                        failed_remounts.append(m)
        if (len(failed_remounts) > 0):
            e_msg = ('Failed to remount the following mounts.\n %s\n '
                     'Try again or do the following as root(may cause '
                     'downtime):\n 1. systemctl stop rockstor\n'
                     '2. unmount manually\n3. systemctl start rockstor\n.' %
                     failed_remounts)
            handle_exception(Exception(e_msg), request)
        return Response(PoolInfoSerializer(pool).data)

    @transaction.commit_on_success
    def put(self, request, pname, command):
        """
        resize a pool.
        @pname: pool's name
        @command: 'add' - add a list of disks and hence expand the pool
                  'remove' - remove a list of disks and hence shrink the pool
        """
        with self._handle_exception(request):
            try:
                pool = Pool.objects.get(name=pname)
            except:
                e_msg = ('pool: %s does not exist' % pname)
                handle_exception(Exception(e_msg), request)

            if (command == 'remount'):
                return self._remount(request, pool)

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
                resize_pool(pool, mount_disk, dnames)
            elif (command == 'remove'):
                remaining_disks = Disk.objects.filter(pool=pool).count() - len(disks)
                if (pool.raid == 'raid0' or pool.raid == 'raid1' or
                    pool.raid == 'raid10' or pool.raid == 'single'):
                    e_msg = ('Removing drives from this(%s) raid '
                             'configuration is not supported' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                if (pool.raid == 'raid5' and remaining_disks < 3):
                    e_msg = ('Resize not possible because a minimum of 3 '
                             'drives is required for this(%s) '
                             'raid configuration.' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                if (pool.raid == 'raid6' and remaining_disks < 4):
                    e_msg = ('Resize not possible because a minimum of 4 '
                             'drives is required for this(%s) raid '
                             'configuration' % pool.raid)
                    handle_exception(Exception(e_msg), request)
                for d in disks:
                    d.pool = None
                    d.save()
                mount_disk = Disk.objects.filter(pool=pool)[0].name
                resize_pool(pool, mount_disk, dnames, add=False)
            else:
                msg = ('unknown command: %s' % command)
                raise Exception(msg)
            usage = pool_usage(mount_disk)
            pool.size = usage[0]
            pool.save()
            return Response(PoolInfoSerializer(pool).data)

    @transaction.commit_on_success
    def delete(self, request, pname):
        with self._handle_exception(request):
            pool = Pool.objects.get(name=pname)
            if (Share.objects.filter(pool=pool).exists()):
                e_msg = ('Pool: %s is not empty. Cannot delete until all '
                         'shares in the pool are deleted' % (pname))
                handle_exception(Exception(e_msg), request)
            pool_path = ('%s%s' % (settings.MNT_PT, pname))
            umount_root(pool_path)
            pool.delete()
            return Response()
