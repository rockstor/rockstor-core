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
from django_ztask.decorators import task
from cli.rest_util import api_call
import gzip
import json
import logging
logger = logging.getLogger(__name__)
BASE_URL = 'https://localhost/api'

def generic_post(url, payload):
    headers = {'content-type': 'application/json', }
    try:
        api_call(url, data=payload, calltype='post', headers=headers,
                 save_error=False)
        logger.debug('Successfully created resource: %s. payload: %s' %
                     (url, payload))
    except Exception, e:
        logger.error('Exception occured while creating resource: %s. '
                     'payload: %s. exception: %s. Moving on.' %
                     (url, payload, e.__str__()))


def restore_users_groups(ml):
    logger.debug('Started restoring users and groups.')
    users = []
    groups = []
    for m in ml:
        if (m['model'] == 'storageadmin.user'):
            users.append(m['fields'])
        if (m['model'] == 'storageadmin.group'):
            groups.append(m['fields'])

    #order is important, first create all the groups and then users.
    for g in groups:
        generic_post('%s/groups' % BASE_URL, g)
    for u in users:
        #users are created with default(rockstor) password
        u['password'] = 'rockstor'
        generic_post('%s/users' % BASE_URL, u)
    logger.debug('Finished restoring users and groups.')


def restore_samba_exports(ml):
    logger.debug('Started restoring Samba exports.')
    exports = []
    for m in ml:
        if (m['model'] == 'storageadmin.sambashare'):
            exports.append(m['fields'])
    for e in exports:
        e['shares'] = [e['path'].split('/')[-1],]
        generic_post('%s/samba' % BASE_URL, e)
    logger.debug('Finished restoring Samba exports.')


def restore_afp_exports(ml):
    logger.debug('Started restoring AFP exports.')
    exports = []
    for m in ml:
        if (m['model'] == 'storageadmin.netatalkshare'):
            exports.append(m['fields'])
    if (len(exports) > 0):
        logger.debug('Starting Netatalk service')
        generic_post('%s/sm/services/netatalk/start' % BASE_URL, {})
    for e in exports:
        e['shares'] = [e['path'].split('/')[-1],]
        generic_post('%s/netatalk' % BASE_URL, e)
    logger.debug('Finished restoring AFP exports.')


def restore_nfs_exports(ml):
    logger.debug('Started restoring NFS exports.')
    exports = []
    export_groups = {}
    adv_exports = {'entries': [], }
    for m in ml:
        if (m['model'] == 'storageadmin.nfsexport'):
            exports.append(m['fields'])
        elif (m['model'] == 'storageadmin.nfsexportgroup'):
            m['fields']['pk'] = m['pk']
            export_groups[m['pk']] = m['fields']
        elif (m['model'] == 'storageadmin.advancednfsexport'):
            adv_exports['entries'].append(m['fields']['export_str'])
    for e in exports:
        if (len(e['mount'].split('/')) != 3):
            logger.debug('skipping nfs export with mount: %s' % e['mount'])
            continue
        e['shares'] = [e['mount'].split('/')[2],]
        payload = dict(export_groups[e['export_group']], **e)
        generic_post('%s/nfs-exports' % BASE_URL, payload)
    generic_post('%s/adv-nfs-exports' % BASE_URL, adv_exports)
    logger.debug('Finished restoring NFS exports.')


def restore_services(ml):
    logger.debug('Started restoring services.')
    services = {}
    for m in ml:
        if (m['model'] == 'smart_manager.service'):
            name = m['fields']['name']
            config = m['fields']['config']
            if (config is not None):
                config = json.loads(config)
                services[name] = {'config': config, }
    logger.debug('services = %s' % services)
    for s in services:
        generic_post('%s/sm/services/%s/config' % (BASE_URL, s), services[s])
    logger.debug('Finished restoring services.')


@task()
def restore_config(cbid):
    cbo = ConfigBackup.objects.get(id=cbid)
    fp = os.path.join(settings.MEDIA_ROOT, 'config-backups', cbo.filename)
    gfo = gzip.open(fp)
    lines = gfo.readlines()
    sa_ml = json.loads(lines[0])
    sm_ml = json.loads(lines[1])
    gfo.close()
    restore_users_groups(sa_ml)
    restore_samba_exports(sa_ml)
    restore_nfs_exports(sa_ml)
    restore_afp_exports(sa_ml)
    restore_services(sm_ml)
    #restore_dashboard(ml)
    #restore_appliances(ml)
    #restore_network(sa_ml)
    #restore_scheduled_tasks(ml)
    #restore_rockons(ml)

class ConfigBackupMixin(object):
    serializer_class = ConfigBackupSerializer
    cb_dir = os.path.join(settings.MEDIA_ROOT, 'config-backups')

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
        models = {'storageadmin':
                  ['user', 'group', 'sambashare', 'netatalkshare', 'nfsexport',
                   'nfsexportgroup', 'advancednfsexport', ],
                  'smart_manager':
                  ['service', ], }
        model_list = []
        for a in models:
            for m in models[a]:
                model_list.append('%s.%s' % (a, m))
        logger.debug('model list = %s' % model_list)
        with self._handle_exception(request):
            filename = ('backup-%s.json' % datetime.now().strftime('%Y-%m-%d-%H%M%S'))
            if (not os.path.isdir(self.cb_dir)):
                os.mkdir(self.cb_dir)
            fp = os.path.join(self.cb_dir, filename)
            with open(fp, 'w') as dfo:
                call_command('dumpdata', *model_list, stdout=dfo)
                dfo.write('\n')
                call_command('dumpdata', database='smart_manager', *model_list, stdout=dfo)
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
            e_msg = ('Config backup for the id(%s) does not exist' % backup_id)
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
            file_obj = request.data['file']
            if (ConfigBackup.objects.filter(filename=filename).exists()):
                msg = ('Config backup(%s) already exists. Uploading a '
                       'duplicate is not allowed.' % filename)
                handle_exception(Exception(msg), request)
            cbo = ConfigBackup.objects.create(
                filename=filename, config_backup=file_obj
            )
            if (not os.path.isdir(self.cb_dir)):
                os.mkdir(self.cb_dir)
            fp = os.path.join(self.cb_dir, filename)

            cbo.md5sum = self._md5sum(fp)
            cbo.size = os.stat(fp).st_size
            cbo.save()
            return Response(ConfigBackupSerializer(cbo).data)
