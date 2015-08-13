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
                      btrfs_uuid, pool_usage, mount_root, get_pool_info,
                      pool_raid)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
from system import smart
import logging
logger = logging.getLogger(__name__)


class DiskListView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get_queryset(self, *args, **kwargs):
        #do rescan on get.
        with self._handle_exception(self.request):
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
            if (d.fstype is not None and d.fstype != 'btrfs'):
                dob.btrfs_uuid = None
                dob.parted = True
            if (Pool.objects.filter(name=d.label).exists()):
                dob.pool = Pool.objects.get(name=d.label)
            else:
                dob.pool = None
            if (dob.pool is None and d.root is True):
                p = self._create_root_pool(d)
                p.disk_set.add(dob)
                p.save()
                dob.pool = p
            dob.save()
        for do in Disk.objects.all():
            if (do.name not in [d.name for d in disks]):
                do.offline = True
            else:
                try:
                    # for non ata/sata drives
                    do.smart_available, do.smart_enabled = smart.available(do.name)
                except Exception, e:
                    logger.exception(e)
                    do.smart_available = do.smart_enabled = False
            do.save()
        ds = DiskInfoSerializer(Disk.objects.all().order_by('name'), many=True)
        return Response(ds.data)

    def _create_root_pool(self, d):
        p = Pool(name=settings.ROOT_POOL, raid='single')
        p.size = pool_usage(mount_root(p))[0]
        enable_quota(p)
        p.uuid = btrfs_uuid(d.name)
        return p

    def post(self, request, command, dname=None):
        with self._handle_exception(request):
            if (command == 'scan'):
                return self._scan()

        e_msg = ('Unsupported command(%s).' % command)
        handle_exception(Exception(e_msg), request)


class DiskDetailView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    @staticmethod
    def _validate_disk(dname, request):
        try:
            return Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk(%s) does not exist' % dname)
            handle_exception(Exception(e_msg), request)

    def get(self, *args, **kwargs):
        if 'dname' in self.kwargs:
            try:
                data = Disk.objects.get(name=self.kwargs['dname'])
                serialized_data = DiskInfoSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()

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

    def post(self, request, command, dname):
        with self._handle_exception(request):
            if (command == 'wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs-wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs-disk-import'):
                return self._btrfs_disk_import(dname, request)
            if (command == 'blink-drive'):
                return self._blink_drive(dname, request)
            if (command == 'enable-smart'):
                return self._toggle_smart(dname, request, enable=True)
            if (command == 'disable-smart'):
                return self._toggle_smart(dname, request)

        e_msg = ('Unsupported command(%s). Valid commands are wipe, btrfs-wipe,'
                 ' btrfs-disk-import, blink-drive, enable-smart, disable-smart' % command)
        handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def _wipe(self, dname, request):
        disk = self._validate_disk(dname, request)
        wipe_disk(disk.name)
        disk.parted = False
        disk.btrfs_uuid = None
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.atomic
    def _btrfs_disk_import(self, dname, request):
        try:
            disk = self._validate_disk(dname, request)
            p_info = get_pool_info(dname)
            #get some options from saved config?
            po = Pool(name=p_info['label'], raid="unknown")
            #need to save it so disk objects get updated properly in the for
            #loop below.
            po.save()
            for d in p_info['disks']:
                do = Disk.objects.get(name=d)
                do.pool = po
                do.parted = False
                do.save()
                mount_root(po)
            po.raid = pool_raid('%s%s' % (settings.MNT_PT, po.name))['data']
            po.size = pool_usage('%s%s' % (settings.MNT_PT, po.name))[0]
            po.save()
            return Response(DiskInfoSerializer(disk).data)
        except Exception, e:
            e_msg = ('Failed to import any pool on this device(%s). Error: %s'
                     % (dname, e.__str__()))
            handle_exception(Exception(e_msg), request)

    @classmethod
    @transaction.atomic
    def _toggle_smart(cls, dname, request, enable=False):
        disk = cls._validate_disk(dname, request)
        if (not disk.smart_available):
            e_msg = ('S.M.A.R.T support is not available on this Disk(%s)' % dname)
            handle_exception(Exception(e_msg), request)
        smart.toggle_smart(disk.name, enable)
        disk.smart_enabled = enable
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @classmethod
    def _blink_drive(cls, dname, request):
        disk = cls._validate_disk(dname, request)
        total_time = int(request.data.get('total_time', 90))
        blink_time = int(request.data.get('blink_time', 15))
        sleep_time = int(request.data.get('sleep_time', 5))
        blink_disk(disk.name, total_time, blink_time, sleep_time)
        return Response()
