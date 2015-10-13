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
from system.services import (toggle_auth_service, systemctl)
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from system.osi import run_command

import logging
logger = logging.getLogger(__name__)


class ActiveDirectoryServiceView(BaseServiceDetailView):

    def _ntp_check(self, request):
        ntpo = Service.objects.get(name='ntpd')
        if (not self._get_status(ntpo)):
            e_msg = ('NTP must be configured and running first before Rockstor'
                     ' can join AD. Configure NTP service first '
                     'and try again.')
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _resolve_check(domain, request):
        import socket
        try:
            res = socket.gethostbyname(domain)
        except Exception, e:
            e_msg = ('Domain/Realm(%s) could not be resolved. Check '
                     'your DNS configuration and try again. '
                     'Lower level error: %s' % (domain, e.__str__()))
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_config(config, request):
        e_msg = None
        if ('domain' not in config):
            e_msg = ('Domain/Realm is required but missing in the input.')
        elif ('username' not in config):
            e_msg = ('Administrator username is required but missing in the '
                     'input')
        elif ('password' not in config):
            e_msg = ('Administrator password is required but missing in the '
                     'input')
        if (e_msg is not None):
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _join_domain(config):
        import subprocess
        domain = config.get('domain')
        cmd = ['realm', 'join', domain]
        p = subprocess.Popen(cmd, shell=False,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        pstr = ('%s\n' % config.get('password'))
        out, err = p.communicate(input=pstr)
        rc = p.returncode
        if (rc != 0):
            e_msg = ('Return code: %s. stdout: %s. stderr: %s.' %
                     (rc, out, err))
            raise Exception(e_msg)

    @staticmethod
    def _leave_domain(config):
        domain = config.get('domain')
        cmd = ['realm', 'leave', domain]
        return run_command(cmd)

    def _config(self, service, request):
        try:
            return self._get_config(service)
        except Exception, e:
            e_msg = ('Missing configuration. Please configure the '
                     'service and try again. Exception: %s' % e.__str__())
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):

        with self._handle_exception(request):
            service = Service.objects.get(name='active-directory')
            if (command == 'config'):
                config = request.data.get('config')
                self._validate_config(config, request)

                #1. Name resolution check
                self._resolve_check(config.get('domain'), request)

                #2. ntp check
                self._ntp_check(request)

                #3. realm discover check?
                domain = config.get('domain')
                try:
                    cmd = ['realm', 'discover', '--name-only', domain]
                    o, e, rc = run_command(cmd)
                except Exception, e:
                    e_msg = ('Failed to discover the given(%s) AD domain. '
                             'Error: %s' % (domain, e.__str__()))
                    handle_exception(Exception(e_msg), request)

                self._save_config(service, config)

            elif (command == 'start'):
                config = self._config(service, request)
                #1. make sure ntpd is running, or else, don't start.
                self._ntp_check(request)
                #2. Name resolution check?
                self._resolve_check(config.get('domain'), request)

                try:
                    #4. realmd stuff
                    self._join_domain(config)
                except Exception, e:
                    e_msg = ('Failed to join AD domain(%s). Error: %s' %
                             (config.get('domain'), e.__str__()))
                    handle_exception(Exception(e_msg), request)

            elif (command == 'stop'):
                config = self._config(service, request)
                try:
                    self._leave_domain(config)
                except Exception, e:
                    e_msg = ('Failed to leave AD domain(%s). Error: %s' %
                             (config.get('domain'), e.__str__()))
                    handle_exception(Exception(e_msg), request)


            return Response()
