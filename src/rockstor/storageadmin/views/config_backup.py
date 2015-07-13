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

import logging
logger = logging.getLogger(__name__)

class ConfigBackupMixin(object):
    serializer_class = ConfigBackupSerializer

    @staticmethod
    def _restart_samba():
        out = status()
        if (out[2] == 0):
            restart_samba()

    @classmethod
    def _validate_input(cls, request, smbo=None):
        options = {}
        def_opts = cls.DEF_OPTS
        if (smbo is not None):
            def_opts = cls.DEF_OPTS.copy()
            def_opts['comment'] = smbo.comment
            def_opts['browsable'] = smbo.browsable
            def_opts['guest_ok'] = smbo.guest_ok
            def_opts['read_only'] = smbo.read_only

        options['comment'] = request.data.get('comment', def_opts['comment'])
        options['browsable'] = request.data.get('browsable',
                                                def_opts['browsable'])

        options['custom_config'] = request.data.get('custom_config', [])
        if (type(options['custom_config']) != list):
            e_msg = ('custom config must be a list of strings')
            handle_exception(Exception(e_msg), request)
        if (options['browsable'] not in cls.BOOL_OPTS):
            e_msg = ('Invalid choice for browsable. Possible '
                     'choices are yes or no.')
            handle_exception(Exception(e_msg), request)
        options['guest_ok'] = request.data.get('guest_ok',
                                               def_opts['guest_ok'])
        if (options['guest_ok'] not in cls.BOOL_OPTS):
            e_msg = ('Invalid choice for guest_ok. Possible '
                     'options are yes or no.')
            handle_exception(Exception(e_msg), request)
        options['read_only'] = request.data.get('read_only',
                                                def_opts['read_only'])
        if (options['read_only'] not in cls.BOOL_OPTS):
            e_msg = ('Invalid choice for read_only. Possible '
                     'options are yes or no.')
            handle_exception(Exception(e_msg), request)
        return options


class ConfigBackupListView(ConfigBackupMixin, rfc.GenericView):
    queryset = ConfigBackup.objects.all()

    @transaction.atomic
    def post(self, request):
        from datetime import datetime
        filename = ('backup-%s.tgz' % datetime.now().strftime('%Y-%m-%d-%H%M%S'))
        cbo = ConfigBackup(filename=filename)
        cbo.save()
        logger.debug('filename = %s' % filename)
        logger.debug('cbo filename = %s' % cbo.filename)
        cb_dir = os.path.join(settings.STATIC_ROOT, 'config_backups')
        if (not os.path.isdir(cb_dir)):
            os.mkdir(cb_dir)
        fp = os.path.join(cb_dir, filename)
        with open(fp, 'w') as dfo:
            call_command('dumpdata', 'storageadmin', stdout=dfo)
        return Response(ConfigBackupSerializer(cbo).data)


class ConfigBackupDetailView(ConfigBackupMixin, rfc.GenericView):

    @transaction.atomic
    def delete(self, request, backup_id):
        logger.debug('in config backup delete')
        try:
            ConfigBackup.objects.get(id=backup_id).delete()
            return Response()
        except:
            e_msg = ('Config backup for the id(%s) does not exist' % smb_id)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, backup_id, command):
        return Response()
