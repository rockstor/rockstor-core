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
from renderers import IgnoreClient
from django.conf import settings
from django.db.models import Count


class GenericSProbeView(generics.ListCreateAPIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    content_negotiation_class = IgnoreClient

    def get_queryset(self):
        limit = self.request.QUERY_PARAMS.get('limit',
                                              settings.PAGINATION['max_limit'])
        limit = int(limit)
        t1 = self.request.QUERY_PARAMS.get('t1', None)
        t2 = self.request.QUERY_PARAMS.get('t2', None)
        group_field = self.request.QUERY_PARAMS.get('group', None)
        if (group_field is not None):
            qs = []
            distinct_fields = self.model_obj.objects.values(group_field).annotate(c=Count(group_field))
            filter_field = ('%s__exact' % group_field)
            for d in distinct_fields:
                qs.extend(self.model_obj.objects.filter(**{filter_field : d[group_field]}).order_by('-ts')[0:limit])
            return qs
        if (t1 is not None and t2 is not None):
            return self.model_obj.objects.filter(ts__gt=t1, ts__lte=t2)
        return self.model_obj.objects.all().order_by('-ts')[0:limit]

    def get_paginate_by(self, foo):
        download = self.request.QUERY_PARAMS.get('download', None)
        if (download is not None):
            return None
        if (self.paginate_by is not None and self.paginate_by == 0):
            return None
        return settings.PAGINATION['page_size']

    def get_allow_empty(self):
        if (self.paginate_by is None):
            return True
        return False

    def post(self, request, *args, **kwargs):
        pass
