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

from smart_manager.models import SProbe
from smart_manager.serializers import SProbeSerializer
from rest_framework.response import Response
from django.conf import settings
from advanced_sprobe import AdvancedSProbeView


class SProbeMetadataView(AdvancedSProbeView):
    serializer_class = SProbeSerializer

    def get_queryset(self, *args, **kwargs):

        limit = self.request.query_params.get(
            "limit", settings.REST_FRAMEWORK["MAX_LIMIT"]
        )
        limit = int(limit)
        start_t1 = self.request.query_params.get("start_t1", None)
        start_t2 = self.request.query_params.get("start_t2", None)
        end_t1 = self.request.query_params.get("end_t1", None)
        end_t2 = self.request.query_params.get("end_t2", None)
        name_regex = self.request.query_params.get("name_regex", None)
        name_exact = self.request.query_params.get("name", None)
        state = self.request.query_params.get("state", None)
        filter_params = {}
        if name_regex is not None:
            filter_params["name__regex"] = name_regex
        if name_exact is not None:
            filter_params["name"] = name_exact
        if start_t1 is not None and start_t2 is not None:
            filter_params["start__gt"] = start_t1
            filter_params["start__lte"] = start_t2
        if end_t1 is not None and end_t2 is not None:
            filter_params["end__gt"] = end_t1
            filter_params["end__lte"] = end_t2
        if state is not None:
            filter_params["state"] = state
        return SProbe.objects.filter(**filter_params).order_by("-start")[0:limit]

    def get_paginate_by(self, foo):
        download = self.request.query_params.get("download", None)
        if download is not None:
            return None
        if self.paginate_by is not None and self.paginate_by == 0:
            return None
        return settings.PAGINATION["page_size"]

    def post(self, request, *args, **kwargs):
        pass


class SProbeMetadataDetailView(AdvancedSProbeView):
    serializer_class = SProbeSerializer

    def get(self, *args, **kwargs):
        if "pid" in self.kwargs:
            try:
                data = SProbe.objects.get(id=kwargs["pid"])
                serialized_data = SProbeSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()
