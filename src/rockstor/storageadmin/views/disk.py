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
Disk view, for anything at the disk level
"""

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Disk
from fs.btrfs import (scan_disks, wipe_disk, btrfs_wipe_disk)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)


class DiskView(rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def _validate_disk(self, dname, request):
        try:
            return Disk.objects.get(name=dname)
        except:
            e_msg = ('Disk: %s does not exist' % dname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        if ('dname' in kwargs):
            self.paginate_by = 0
            try:
                return Disk.objects.get(name=kwargs['dname'])
            except:
                return []
        return Disk.objects.all()

    @transaction.commit_on_success
    def _scan(self):
        disks = scan_disks(settings.MIN_DISK_SIZE)
        for k,v in disks.items():
            if (Disk.objects.filter(name=v['name']).exists()):
                d = Disk.objects.get(name=v['name'])
                if (d.size != v['size'] or d.parted != v['parted'] or
                    d.btrfs_uuid != v['btrfs_uuid']):
                    d.size = v['size']
                    d.parted = v['parted']
                    d.btrfs_uuid = v['btrfs_uuid']
                    d.save()
                continue
            new_disk = Disk(name=v['name'], size=v['size'], parted=v['parted'],
                            btrfs_uuid=v['btrfs_uuid'])
            new_disk.save()
        for d in Disk.objects.all():
            if (d.name not in disks.keys()):
                d.offline = True
                d.save()
        disks = Disk.objects.all()
        ds = DiskInfoSerializer(disks)
        return Response(ds.data)

    @transaction.commit_on_success
    def _wipe(self, dname, request):
        disk = self._validate_disk(dname, request)
        try:
            wipe_disk(disk.name)
        except Exception, e:
            logger.exception(e)
            e_msg = ('Failed to wipe the disk due to a system error.')
            handle_exception(Exception(e_msg))

        disk.parted = False
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    @transaction.commit_on_success
    def _btrfs_wipe(self, dname, request):
        disk = self._validate_disk(dname, request)
        try:
            btrfs_wipe_disk('/dev/%s' % disk.name)
        except Exception, e:
            logger.exception(e)
            e_msg = ('Failed to wipe btrfs metadata due to a system error.')
            handle_exception(Exception(e_msg))

        disk.btrfs_uuid = None
        disk.save()
        return Response(DiskInfoSerializer(disk).data)

    def post(self, request, command, dname=None):
        try:
            if (command == 'scan'):
                return self._scan()
            if (command == 'wipe'):
                return self._wipe(dname, request)
            if (command == 'btrfs_wipe'):
                return self._btrfs_wipe(dname, request)
        except Exception, e:
            handle_exception(e, request)

        e_msg = ('Unknown command: %s. Only valid commands are scan, wipe' %
                 command)
        handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
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
