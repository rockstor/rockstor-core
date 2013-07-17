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

from rest_framework import generics
from smart_manager.models import MemInfo
from smart_manager.serializers import (MemInfoSerializer)
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated


class MemInfoView(generics.ListAPIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = MemInfoSerializer
    paginate_by = 5000

    def get_queryset(self):
        limit = self.request.QUERY_PARAMS.get('limit', 10000)
        limit = int(limit)
        t1 = self.request.QUERY_PARAMS.get('t1', None)
        t2 = self.request.QUERY_PARAMS.get('t2', None)
        if (t1 is not None and t2 is not None):
            return MemInfo.objects.filter(ts__gt=t1, ts__lte=t2)
        return MemInfo.objects.all().order_by('-ts')[0:limit]

