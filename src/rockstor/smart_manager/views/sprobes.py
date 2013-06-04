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
from smart_manager.serializers import SProbeSerializer
import os
import zmq

import logging
logger = logging.getLogger(__name__)

class SProbeView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    tap_map = settings.TAP_MAP
    ctx = zmq.Context()
    task_socket = ctx.socket(zmq.PUSH)
    task_socket.connect('tcp://%s:%d' % settings.TAP_SERVER)

    def get(self, request, pname=None):
        """
        return the latest tap module
        """
        if (pname is not None and pname not in self.tap_map.keys()):
            e_msg = ('Unknown tap: %s requested' % pname)
            handle_exception(Exception(e_msg), request)

        if (pname is None):
            return Response(self.tap_map.keys())

        ros = SProbe.objects.filter(name=pname).order_by('-ts')
        return Response(SProbeSerializer(ros).data)

    @transaction.commit_on_success
    def post(self, request, pname):
        """
        start a new tap
        """
        if (pname not in self.tap_map.keys()):
            e_msg = ('Unknown tap: %s requested' % pname)
            handle_exception(Exception(e_msg), request)

        #if there's a recipe already running, throw error
        if (SProbe.objects.filter(name=pname,
                                  state__regex=r'(created|running)').exists()):
            e_msg = ('Smart probe: %s already running' % pname)
            handle_exception(Exception(e_msg), request)

        #get last id
        cur_id = 0
        try:
            cur_id = SProbe.objects.all().order_by('-ts')[0].id
        except:
            logger.info('no previous probe ids found for: %s' % pname)

        ro = SProbe(name=pname, smart=True, state='created')
        kernel_module = os.path.join(settings.TAP_DIR,
                                     settings.TAP_MAP[pname] + '.ko')
        task = {
            'module': kernel_module,
            'tap': pname,
            'action': 'start',
            'roid': cur_id + 1,
            }
        ro.save()
        self.task_socket.send_json(task)
        return Response(SProbeSerializer(ro).data)
