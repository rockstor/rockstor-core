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
from smart_manager.models import (Service, ServiceStatus, STap)
from django.conf import settings
from smart_manager import models
from smart_manager import serializers
import os
import zmq

import logging
logger = logging.getLogger(__name__)

class StapView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    tap_map = settings.TAP_MAP
    ctx = zmq.Context()
    task_socket = ctx.socket(zmq.PUSH)
    task_socket.connect('tcp://127.0.0.1:10000')

    def get(self, request, tname=None):
        """
        return the latest tap module
        """
        if (tname is not None and tname not in self.tap_map.keys()):
            msg = ('Unknown tap: %s requested' % tname)
            logger.error(msg)
            raise Exception(msg)

        return self._get_helper(tname)

    def _get_helper(self, tname=None):
        if (tname is None):
            logger.info('tname is None')
            return Response()

        model = getattr(models, self.tap_map[tname])
        if (model.objects.exists()):
            tos = model.objects.order_by('-ts')[0]
            serializer_name = self.tap_map[tname] + 'Serializer'
            o_s = getattr(serializers, serializer_name)
            res = o_s(tos).data
            logger.info('returning response: %s' % res)
            return Response(res)
        logger.info('model: %s does not exist' % self.tap_map[tname])
        return Response()

    def post(self, request, tname):
        """
        start a new tap
        """
        if (tname not in self.tap_map.keys()):
            msg = ('Unknown tap: %s requested' % tname)
            logger.error(msg)
            raise Exception(msg)

        kernel_module = os.path.join(settings.TAP_DIR, tname + '.ko')
        task = {
            'module': kernel_module,
            'tap': tname,
            'tap_class': self.tap_map[tname],
            }
        self.task_socket.send_json(task)
        return self._get_helper(tname)

