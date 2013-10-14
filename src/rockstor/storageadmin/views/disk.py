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
from system.osi import scan_disks
from storageadmin.serializers import DiskInfoSerializer
from storageadmin.util import handle_exception
from django.conf import settings
from generic_view import GenericView

import logging
logger = logging.getLogger(__name__)


class DiskView(GenericView):
    serializer_class = DiskInfoSerializer

    def get_queryset(self, *args, **kwargs):
        if ('dname' in kwargs):
            self.paginate_by = 0
            try:
                return Disk.objects.get(name=kwargs['dname'])
            except:
                return []
        return Disk.objects.all()

    @transaction.commit_on_success
    def post(self, request, command):
        if (command != 'scan'):
            e_msg = ('Unknown command: %s. Only valid command is: scan' %
                     command)
            handle_exception(Exception(e_msg), request)

        disks = scan_disks(settings.MIN_DISK_SIZE)
        for k,v in disks.items():
            if (Disk.objects.filter(name=v['name']).exists()):
                continue
            new_disk = Disk(name=v['name'], size=v['size'], parted=v['parted'])
            new_disk.save()
        for d in Disk.objects.all():
            if (d.name not in disks.keys()):
                d.offline = True
                d.save()
        disks = Disk.objects.all()
        ds = DiskInfoSerializer(disks)
        return Response(ds.data)

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
