"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from storageadmin.util import handle_exception
from storageadmin.models import DashboardConfig
from storageadmin.serializers import DashboardConfigSerializer

import logging

logger = logging.getLogger(__name__)


class DashboardConfigView(APIView):
    authentication_classes = (
        DigestAuthentication,
        SessionAuthentication,
        BasicAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            current_user = request.user
            dcs = DashboardConfig.objects.filter(user__pk=current_user.id)
            if len(dcs) > 0:
                dc = dcs[0]
                return Response(DashboardConfigSerializer(dc).data)
            else:
                return Response()
        except Exception as e:
            handle_exception(e, request)

    def post(self, request):
        try:
            current_user = request.user
            widgets = request.data["widgets"]
            dcs = DashboardConfig.objects.filter(user__pk=current_user.id)
            if len(dcs) > 0:
                dc = dcs[0]
                dc.widgets = widgets
            else:
                dc = DashboardConfig(widgets=widgets)
                dc.user_id = current_user.id
            dc.save()
            return Response(DashboardConfigSerializer(dc).data)
        except Exception as e:
            handle_exception(e, request)

    def put(self, request):
        try:
            current_user = request.user
            widgets = request.data["widgets"]
            dcs = DashboardConfig.objects.filter(user__pk=current_user.id)
            if len(dcs) > 0:
                dc = dcs[0]
                dc.widgets = widgets
            else:
                dc = DashboardConfig(widgets=widgets)
                dc.user_id = current_user.id
            dc.save()
            return Response(DashboardConfigSerializer(dc).data)
        except Exception as e:
            handle_exception(e, request)
