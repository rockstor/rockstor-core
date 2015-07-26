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
from datetime import datetime
from rest_framework.parsers import FileUploadParser, MultiPartParser
from rest_framework import status

import logging
logger = logging.getLogger(__name__)

from django_ztask.decorators import task
@task()
def restore_config(cbid):
    cbo = ConfigBackup.objects.get(id=cbid)
    fp = os.path.join(settings.STATIC_ROOT, 'config-backups', cbo.filename)
    import gzip
    import json
    from cli.rest_util import api_call
    gfo = gzip.open(fp)
    ml = json.load(gfo)
    gfo.close()
    base_url = 'https://localhost/api'
    for i in ml:
        if (i['model'] == 'storageadmin.user'):
            ufields = i['fields']
            url = ('%s/users' % base_url)
            ufields['password'] = 'rockstor'
            api_call(url, data=ufields, calltype='post', save_error=False)


class ConfigBackupMixin(object):
    serializer_class = ConfigBackupSerializer
    cb_dir = os.path.join(settings.STATIC_ROOT, 'config-backups')

    @staticmethod
    def _md5sum(fp):
        return run_command(['/usr/bin/md5sum', fp])[0][0].split()[0]


class ConfigBackupListView(ConfigBackupMixin, rfc.GenericView):

    def get_queryset(self, *args, **kwargs):
        for cbo in ConfigBackup.objects.all():
            fp = os.path.join(self.cb_dir, cbo.filename)
            if (not os.path.isfile(fp)):
                cbo.delete()
            md5sum = self._md5sum(fp)
            if (md5sum != cbo.md5sum):
                logger.error('md5sum mismatch for %s. cbo: %s file: %s. '
                             'Deleting dbo' %
                             (cbo.filename, cbo.md5sum, md5sum))
                cbo.delete()
        return ConfigBackup.objects.filter().order_by('-id')

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            filename = ('backup-%s.json' % datetime.now().strftime('%Y-%m-%d-%H%M%S'))
            if (not os.path.isdir(self.cb_dir)):
                os.mkdir(self.cb_dir)
            fp = os.path.join(self.cb_dir, filename)
            with open(fp, 'w') as dfo:
                call_command('dumpdata', 'storageadmin', stdout=dfo)
            run_command(['/usr/bin/gzip', fp])
            gz_name = ('%s.gz' % filename)
            fp = os.path.join(self.cb_dir, gz_name)
            md5sum = self._md5sum(fp)
            size = os.stat(fp).st_size
            cbo = ConfigBackup(filename=gz_name, md5sum=md5sum, size=size)
            cbo.save()
            return Response(ConfigBackupSerializer(cbo).data)


class ConfigBackupDetailView(ConfigBackupMixin, rfc.GenericView):

    @transaction.atomic
    def delete(self, request, backup_id):
        with self._handle_exception(request):
            cbo = self._validate_input(backup_id)
            fp = os.path.join(self.cb_dir, cbo.filename)
            if (os.path.isfile(fp)):
                os.remove(fp)
            cbo.delete()
            return Response()

    @transaction.atomic
    def post(self, request, backup_id):
        with self._handle_exception(request):
            command = request.data.get('command', 'restore')
            if (command == 'restore'):
                cbo = self._validate_input(backup_id)
                # models that need to be restored.
                #1. User, Group, Accesskeys?
                #2. SambaShare
                #3. NFSExport, NFSExportGroup
                #4. Service configs
                #5. Appliances?
                #6. Scheduled Tasks
                #7. SFTP, AFP
                logger.debug('restore starting...')
                restore_config.async(cbo.id)
                logger.debug('restore submitted...')
        return Response()

    @staticmethod
    def _validate_input(backup_id):
        try:
            return ConfigBackup.objects.get(id=backup_id)
        except ConfigBackup.DoesNotExist:
            e_msg = ('Contif backup for the id(%s) does not exist' % backup_id)
            handle_exception(Exception(e_msg), request)


class ConfigBackupUpload(ConfigBackupMixin, rfc.GenericView):
    parser_classes = (FileUploadParser, MultiPartParser)

    def get_queryset(self, *args, **kwargs):
        for cbo in ConfigBackup.objects.all():
            fp = os.path.join(self.cb_dir, cbo.filename)
            if (not os.path.isfile(fp)):
                cbo.delete()
            md5sum = self._md5sum(fp)
            if (md5sum != cbo.md5sum):
                logger.error('md5sum mismatch for %s. cbo: %s file: %s. '
                             'Deleting dbo' %
                             (cbo.filename, cbo.md5sum, md5sum))
                cbo.delete()
        return ConfigBackup.objects.filter().order_by('-id')



    def post(self, request, format=None):
        with self._handle_exception(request):
            filename = request.data['file-name']
            fp = ''
            if (not os.path.isdir(self.cb_dir)):
                os.mkdir(self.cb_dir)
                fp = os.path.join(self.cb_dir, filename)
            else:
                fp = os.path.join(self.cb_dir, filename)
            md5sum = self._md5sum(fp)
            size = os.stat(fp).st_size
            file_obj = request.data['file']
            cbo = ConfigBackup(filename=filename, md5sum=md5sum, size=size, config_backup=file_obj)
            cbo.save()
            return Response(ConfigBackupSerializer(cbo).data)
