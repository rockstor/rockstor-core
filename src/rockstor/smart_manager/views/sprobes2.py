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
from rest_framework.permissions import IsAuthenticated
from system.services import init_service_op
from smart_manager.models import (Service, ServiceStatus, SProbe)
from django.conf import settings
from django.db import transaction
from smart_manager import serializers
from smart_manager.serializers import (SProbeSerializer,
                                       NFSDCallDistributionSerializer)
from smart_manager.models import NFSDCallDistribution
import os
import zmq

import logging
logger = logging.getLogger(__name__)

class SProbeView2(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    tap_map = settings.TAP_MAP
    ctx = zmq.Context()
    task_socket = ctx.socket(zmq.PUSH)
    task_socket.connect('tcp://%s:%d' % settings.TAP_SERVER)

    def _validate_probe(self, pname, pid, request):
        try:
            return SProbe.objects.get(name=pname, id=pid)
        except:
            e_msg = ('Probe: %s with id: %s does not exist' % (pname, pid))
            handle_exception(Exception(e_msg), request)

    def get(self, request, pname, pid):
        """
        return all ts data for the given pname and pid
        """
        ro = self._validate_probe(pname, pid, request)
        if (pname == 'nfs-distrib'):
            dos = NFSDCallDistribution.objects.filter(rid=ro).order_by('ts')
            return Response(NFSDCallDistributionSerializer(dos).data)

    @transaction.commit_on_success
    def post(self, request, pname, pid, command):
        """
        start a new tap
        """
        ro = self._validate_probe(pname, pid, request)

        if (command not in ('stop', 'status',)):
            e_msg = ('command: %s not supported.' % command)
            handle_exception(Exception(e_msg), request)

        if (command == 'status'):
            return Response(SProbeSerializer(ro).data)

        else:
            if (ro.state == 'stopped' or ro.state == 'error'):
                e_msg = ('Probe: %s with id: %s already in state: %s. It '
                         'cannot be stopped.' % (pname, pid, ro.state))
                handle_exception(Exception(e_msg), request)

            ro.state = 'stopped'
            ro.save()
            task = {
                'tap': pname,
                'action': 'stop',
                'roid': ro.id,
                }
            self.task_socket.send_json(task)
            return Response(SProbeSerializer(ro).data)
