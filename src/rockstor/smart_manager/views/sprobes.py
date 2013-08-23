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
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from smart_manager.serializers import SProbeConfigSerializer
from smart_manager.taplib.probe_config import (TapConfig, TAP_MAP)


class SProbeView(generics.ListAPIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = SProbeConfigSerializer

    def get_queryset(self):
        config_list = []
        for pid in TAP_MAP.keys():
            config_list.append(TapConfig(uuid=pid,
                                         location=TAP_MAP[pid]['location'],
                                         sdetail=TAP_MAP[pid]['sdetail']))
        return config_list
