"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

import os
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from django.db import transaction
from django.conf import settings
from storageadmin.models import ConfigBackup
from storageadmin.serializers import ConfigBackupSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from django.core.management import call_command
from system.osi import run_command

import logging
logger = logging.getLogger(__name__)

class ConfigBackupMixin(object):
    serializer_class = ConfigBackupSerializer
    cb_dir = os.path.join(settings.STATIC_ROOT, 'config-backups')

class ConfigBackupListView(ConfigBackupMixin, rfc.GenericView):
    queryset = ConfigBackup.objects.all()

    @transaction.atomic
    def post(self, request):
        from datetime import datetime
        filename = ('backup-%s.json' % datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        if (not os.path.isdir(self.cb_dir)):
            os.mkdir(self.cb_dir)
        fp = os.path.join(self.cb_dir, filename)
        with open(fp, 'w') as dfo:
            call_command('dumpdata', 'storageadmin', stdout=dfo)
        run_command(['/usr/bin/gzip', fp])
        gz_name = ('%s.gz' % filename)
        size = os.stat(os.join(self.cb_dir, gz_name)).st_size
        cbo = ConfigBackup(filename=filename, size=size)
        cbo.save()
        return Response(ConfigBackupSerializer(cbo).data)


class ConfigBackupDetailView(ConfigBackupMixin, rfc.GenericView):

    @transaction.atomic
    def delete(self, request, backup_id):
        try:
            cbo = ConfigBackup.objects.get(id=backup_id)
            fp = os.path.join(self.cb_dir, cbo.filename)
            if (os.path.isfile(fp)):
                os.remove(fp)
            cbo.delete()
            return Response()
        except:
            e_msg = ('Config backup for the id(%s) does not exist' % backup_id)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, backup_id):
        command = request.data.get('command', 'restore')
        if (command == 'restore'):
            logger.debug('restored!!!')
        return Response()
