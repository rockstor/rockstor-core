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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from system.services import init_service_op

import logging
logger = logging.getLogger(__name__)


class ServiceView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    service_list = ('nfs', 'samba', 'sftp', 'ldap', 'ad',)
    command_list = ('start', 'stop', 'restart', 'reload',)

    def get(self, request, sname):
        """
        return current status of the service
        """
        if (sname not in self.service_list):
            msg = ('Unknown service: %s requested' % sname)
            logger.error(msg)
            raise Exception(msg)
        out, err, rc = init_service_op(sname, 'status')


    def post(self, request):
        pass

    def put(self, request, sname):
        """
        execute a command on the service
        """
        if (sname not in self.service_list):
            msg = ('Unknown service: %s requested' % sname)
            logger.error(msg)
            raise Exception(msg)

        command = request.DATA['command']
        if (command not in self.command_list):
            msg = ('Unknown command: %s for service: %s' % (command, sname))
            logger.error(msg)
            raise Exception(msg)
        init_service_op()
