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

from rest_framework.response import Response
from storageadmin.util import handle_exception
from system.services import init_service_op, chkconfig
from system.osi import run_command
from django.db import transaction
from base_service import BaseServiceView
from smart_manager.models import Service
from storageadmin.models import Appliance
from django.conf import settings
from contextlib import contextmanager
from storageadmin.exceptions import RockStorAPIException
import re

import logging
logger = logging.getLogger(__name__)


class NTPServiceView(BaseServiceView):

    @staticmethod
    @contextmanager
    def _handle_exception(request, msg):
        try:
            yield
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request, msg)

    @transaction.commit_on_success
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name='ntpd')
        if (command == 'config'):
            e_msg = ('Invalid input for time servers. It must be '
                     'comma separated string of hostnames or IPs.')
            with self._handle_exception(request, e_msg):
                config = request.DATA['config']
                servers = [s.strip() for s in config['server'].split(',')]

            e_msg = ('Error while saving saving configuration(%s) to the '
                     'database' % config)
            with self._handle_exception(request, e_msg):
                self._save_config(service, config)

            e_msg = ('Error while validating time servers(%s). Check your '
                     'input and try again.' % config['server'])
            with self._handle_exception(request, e_msg):
                run_command([settings.COMMANDS['systemctl'], 'stop', 'ntpd'])
                cmd = [settings.COMMANDS['ntpdate']] + servers
                out, err, rc = run_command(cmd)
                if (rc != 0):
                    e_msg = ('Unable to sync time with given servers(%s)' %
                             config['server'])
                    handle_exception(Exception(e_msg), request)

            e_msg = ('Error while saving time server(%s) configuration. Try'
                     ' again' % servers)
            with self._handle_exception(request, e_msg):
                self._update_ntp_conf(servers)
                run_command([settings.COMMANDS['systemctl'], 'restart',
                             'ntpd'])
        else:
            e_msg = ('Failed to %s NTP service due to system error.' %
                     command)
            with self._handle_exception(request, e_msg):
                run_command([settings.COMMANDS['systemctl'], command, 'ntpd'])
                if (command == 'start'):
                    run_command([settings.COMMANDS['systemctl'], 'enable',
                                 'ntpd'])

        return Response()

    @staticmethod
    def _update_ntp_conf(servers):
        conf_data = []
        conf_file = settings.SYSCONFIG['ntp']
        with open(conf_file) as nfo:
            conf_data = nfo.readlines()
        with open(conf_file, 'w') as nfo:
            for l in conf_data:
                if (re.match('server ', l) is None):
                    nfo.write(l)
            for s in servers:
                nfo.write('server %s iburst\n' % s)
