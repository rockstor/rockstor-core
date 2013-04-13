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
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from storageadmin.auth import DigestAuthentication
from smart_manager.models import (CPUMetric, LoadAvg, MemInfo)
from smart_manager.serializers import (CPUMetricSerializer, LoadAvgSerializer,
                                       MemInfoSerializer)

import logging
logger = logging.getLogger(__name__)


class SmartManagerView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, mname):
        if (mname == 'cpumetric'):
            cms = CPUMetricSerializer(CPUMetric.objects.all()).data
            return Response(cms)
        elif (mname == 'loadavg'):
            ls = LoadAvgSerializer(LoadAvg.objects.all()).data
            return Response(ls)
        elif (mname == 'meminfo'):
            ms = MemInfoSerializer(MemInfo.objects.all()).data
            return Response(ms)
        else:
            msg = ('Invalid smart manager resource. request data: %s mname: %s'
                   % (request.DATA, mname))
            logger.error(msg)
            raise Exception(msg)

    def post(self, request):
        return Response()

    def put(self, request):
        return Response()

    def delete(self, request):
        return Response()



