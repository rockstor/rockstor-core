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
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Disk, Pool, Share)
from fs.btrfs import (scan_disks, wipe_disk, blink_disk, enable_quota,
                      btrfs_uuid, pool_usage, mount_root, get_pool_info,
                      pool_raid, enable_quota)
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from share_helpers import (import_shares, import_snapshots)
from django.conf import settings
import rest_framework_custom as rfc
from system import smart
import logging
logger = logging.getLogger(__name__)


class DiskMixin(object):
    serializer_class = DiskInfoSerializer

    @staticmethod
    @transaction.atomic
    def _update_disk_state():
        # todo shorten / simplify by sub-dividing
        # todo sort out rogue serial and size details from removed devices
        # Acquire a list (namedtupil collection) of attached drives > min size
        disks = scan_disks(settings.MIN_DISK_SIZE)
        # Build a list of the missing devices by serial number comparison.
        # Ie stored device serial numbers vs attached device serial numbers
        # This way we can preserve removed device info prior to overwrite.
        offline_disks = []
        for do in Disk.objects.all():
            # look for devices that are in the db but not in our disk_scan
            # use serial num as dev names may have changed
            if (do.serial not in [d.serial for d in disks]):
                do.offline = True  # to inform us later if need be
                offline_disks.append(do)
            do.save()
        # Iterate over the attached drives to update the db's knowledge.
        # N.B. Disk model has name (dev name) as unique to reflect kernel dev
        # Also note that this involves a whole sale overwrite of dev db slots
        for d in disks:
            # start with an empty disk object
            dob = None
            # If the db has an exiting entry with this disk's name then
            # copy this entire entry and then update the serial number.
            if (Disk.objects.filter(name=d.name).exists()):
                dob = Disk.objects.get(name=d.name)
                dob.serial = d.serial
            # If the db has existing entry with this disk's serial number and
            # there was no prior match by name (last conditional) then
            # copy this entire entry and update the device name (ie the dev)
            elif (Disk.objects.filter(serial=d.serial).exists()):
                dob = Disk.objects.get(serial=d.serial)
                dob.name = d.name
            # we have an assumed new disk entry as no dev name or serial match
            # with db stored results. Build a new entry for this disk.
            else:
                dob = Disk(name=d.name, size=d.size, parted=d.parted,
                           btrfs_uuid=d.btrfs_uuid, model=d.model,
                           serial=d.serial, transport=d.transport,
                           vendor=d.vendor)
            # Update the chosen disk object (existing or new)
            # todo examine if wholesale overwrite is correct here
            dob.size = d.size
            dob.parted = d.parted
            dob.offline = False  # as we are iterating over attached devices
            dob.model = d.model
            dob.transport = d.transport
            dob.vendor = d.vendor
            dob.btrfs_uuid = d.btrfs_uuid
            # If attached disk has an fs and it isn't btrfs
            if (d.fstype is not None and d.fstype != 'btrfs'):
                dob.btrfs_uuid = None
                dob.parted = True
            # If our existing Pool db knows of this disk's label then
            if (Pool.objects.filter(name=d.label).exists()):
                # update the disk object's pool attribute as we know it already
                dob.pool = Pool.objects.get(name=d.label)
            else:  # this disk is not known to exist in any pool via it's label
                dob.pool = None
            # if the disk object is not a member of a pool and
            # the attached disk we are examining is our root disk
            if (dob.pool is None and d.root is True):
                # setup our special root disk db entry
                p = Pool(name=settings.ROOT_POOL, raid='single')
                p.disk_set.add(dob)
                p.save()
                dob.pool = p
                dob.save()
                p.size = pool_usage(mount_root(p))[0]
                enable_quota(p)
                p.uuid = btrfs_uuid(dob.name)
                p.save()
            dob.save()
        # Now do a final pass over all database Disk.objects to
        # 1) update offline status after db re-writes above
        # 2) insert the missing / offline disk info into the remaining dev slots
        # 3) update smart (available, enabled) properties
        # todo do we need to cope with more missing disk than db entries
        # todo how would they be missing if we didn't first know of them
        # todo and to know of them their must be a db slot. caution with unique
        for do in Disk.objects.all():
            if (do.serial in [entry.serial for entry in offline_disks]):
                # db entry whose serial number isn't in our last disk_scan
                do.offline = True
                do.smart_available = do.smart_enabled = False
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


class DiskListView(DiskMixin, rfc.GenericView):
    serializer_class = DiskInfoSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            return Disk.objects.all().order_by('name')

    def post(self, request, command, dname=None):
        with self._handle_exception(request):
            if (command == 'scan'):
                return self._update_disk_state()

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
            enable_quota(po)
            import_shares(po, request)
            for share in Share.objects.filter(pool=po):
                import_snapshots(share)
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
