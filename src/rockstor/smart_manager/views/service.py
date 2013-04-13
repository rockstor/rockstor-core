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
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from rest_framework.permissions import IsAuthenticated
from system.services import init_service_op
from smart_manager.models import (Service, ServiceStatus)
from smart_manager.serializers import (ServiceStatusSerializer)


import logging
logger = logging.getLogger(__name__)


class ServiceView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    service_list = ('nfs', 'samba', 'sftp', 'ldap', 'ad', 'iscsi')
    command_list = ('start', 'stop', 'restart', 'reload',)

    def get(self, request, sname=None):
        """
        return current status of the service
        """
        try:
            if (sname is None):
                return self.get_helper()

            if (sname not in self.service_list):
                msg = ('Unknown service: %s requested' % sname)
                handle_exception(Exception(msg), request)

            return self.get_helper(sname)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def get_helper(self, sname=None):
        if (sname is None):
            sos = []
            for s in Service.objects.filter(registered=True):
                if (ServiceStatus.objects.filter(service=s).exists()):
                    so = ServiceStatus.objects.filter(service=s).order_by('-ts')[0]
                    sos.append(so)
            return Response(ServiceStatusSerializer(sos).data)

        s = Service.objects.get(name=sname)
        if (ServiceStatus.objects.filter(service=s).exists()):
            so = ServiceStatus.objects.filter(service=s).order_by('-ts')[0]
            ns = ServiceStatusSerializer(so).data
            logger.info('returning response: %s' % ns)
            return Response(ns)

        return Response()

    def post(self, request):
        pass

    def put(self, request, sname):
        """
        execute a command on the service
        """
        try:
            if (sname not in self.service_list):
                msg = ('Unknown service: %s requested' % sname)
                handle_exception(Exception(msg, request))

            command = request.DATA['command']
            if (command not in self.command_list):
                msg = ('Unknown command: %s for service: %s' % (command,
                                                                sname))
                handle_exception(Exception(msg, request))

            if (sname == 'ldap' or sname == 'ad' or sname == 'iscsi'):
                return Response()
            else:
                logger.info('sname: %s command: %s' % (sname, command))
                out, err, rc = init_service_op(sname, command)
                logger.info('out: %s err: %s rc: %s' % (out, err, rc))
                return self.get_helper(sname)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
