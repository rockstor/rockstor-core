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
from contextlib import contextmanager
from storageadmin.exceptions import RockStorAPIException

"""
Disk view, for anything at the disk level
"""

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Disk, Pool)
from fs.btrfs import (scan_disks, wipe_disk, blink_disk, enable_quota,
                      btrfs_uuid, pool_usage, mount_root)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
from rest_framework.generics import RetrieveAPIView
import logging
logger = logging.getLogger(__name__)


class DiskDetailView(RetrieveAPIView, rfc.GenericView):
    """Return a single Disk object"""
    def get(self, *args, **kwargs):
        if 'dname' in self.kwargs:
            self.paginate_by_param = None
            try:
                data = Disk.objects.get(name=self.kwargs['dname'])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return []


class DiskView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def _validate_disk(self, dname, request):
        try:
            return Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk: %s does not exist' % dname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        #do rescan on get.
        with self._handle_exception(self.request):
            self._scan()
        if ('dname' in self.kwargs):
            self.paginate_by_param = None
            try:
                return Disk.objects.get(name=kwargs['dname'])
            except:
                return []
        return Disk.objects.all().order_by('name')

    @transaction.atomic
    def _scan(self):
        disks = scan_disks(settings.MIN_DISK_SIZE)
        for d in disks:
            dob = None
            if (Disk.objects.filter(name=d.name).exists()):
                dob = Disk.objects.get(name=d.name)
                dob.serial = d.serial
            elif (Disk.objects.filter(serial=d.serial).exists()):
                dob = Disk.objects.get(serial=d.serial)
                dob.name = d.name
            else:
                dob = Disk(name=d.name, size=d.size, parted=d.parted,
                           btrfs_uuid=d.btrfs_uuid, model=d.model,
                           serial=d.serial, transport=d.transport,
                           vendor=d.vendor)
            dob.size = d.size
            dob.parted = d.parted
            dob.offline = False
            dob.model = d.model
            dob.transport = d.transport
            dob.vendor = d.vendor
            dob.btrfs_uuid = d.btrfs_uuid
            if (Pool.objects.filter(name=d.label).exists()):
                dob.pool = Pool.objects.get(name=d.label)
            if (dob.pool is None and d.root is True):
                p = self._create_root_pool(d)
                p.disk_set.add(dob)
                p.save()
                dob.pool = p
            dob.save()
        for do in Disk.objects.all():
            if (do.name not in [d.name for d in disks]):
                do.offline = True
                do.save()
        ds = DiskInfoSerializer(Disk.objects.all().order_by('name'), many=True)
        return Response(ds.data)

    def _create_root_pool(self, d):
        p = Pool(name=settings.ROOT_POOL, raid='single')
        p.size = pool_usage(mount_root(p, d.name))[0]
        enable_quota(p, '/dev/%s' % d.name)
        p.uuid = btrfs_uuid(d.name)
        return p

    @transaction.atomic
    def _wipe(self, dname, request):
        disk = self._validate_disk(dname, request)
        try:
            wipe_disk(disk.name)
        except Exception, e:
            logger.exception(e)
            e_msg = ('Failed to wipe the disk due to a system error.')
            handle_exception(Exception(e_msg), request)

        disk.parted = False
        disk.btrfs_uuid = None
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    def _btrfs_disk_import(self, dname, request):
        """stub method for now"""
        e_msg = ('Failed to import any pools, shares and snapshots that '
                 'may be on the disk: %s. Import or backup manually' % dname)
        handle_exception(Exception(e_msg), request)

    def _blink_drive(self, dname, request):
        disk = self._validate_disk(dname, request)
        total_time = int(request.DATA.get('total_time', 90))
        blink_time = int(request.DATA.get('blink_time', 15))
        sleep_time = int(request.DATA.get('sleep_time', 5))
        blink_disk(disk.name, total_time, blink_time, sleep_time)
        return Response()

    def post(self, request, command, dname=None):
        with self._handle_exception(request):
            if (command == 'scan'):
                return self._scan()
            if (command == 'wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs-wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs-disk-import'):
                return self._btrfs_disk_import(dname, request)
            if (command == 'blink-drive'):
                return self._blink_drive(dname, request)

            e_msg = ('Unknown command: %s. Only valid commands are scan, '
                     'wipe' % command)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def delete(self, request, dname):
        try:
            disk = Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk: %s does not exist' % dname)
            handle_exception(Exception(e_msg), request)

        if (disk.offline is not True):
            e_msg = ('Disk: %s is not offline. Cannot delete' % dname)
            handle_exception(Exception(e_msg), request)

        try:
            disk.delete()
            return Response()
        except Exception, e:
            e_msg = ('Could not remove disk(%s) due to system error' % dname)
            logger.exception(e)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    @contextmanager
    def _handle_exception(request, msg=None):
        try:
            yield
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request, msg)
