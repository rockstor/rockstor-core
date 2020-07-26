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


from smart_manager.models import (
    ReplicaShare,
    ReplicaTrail,
    Replica,
    ReceiveTrail,
)
from smart_manager.serializers import (
    ReplicaShareSerializer,
    ReplicaTrailSerializer,
    ReplicaSerializer,
    ReceiveTrailSerializer,
)

import rest_framework_custom as rfc
from rest_framework.response import Response


class ReplicaShareDetailView(rfc.GenericView):
    serializer_class = ReplicaShareSerializer

    def get(self, *args, **kwargs):
        try:
            if "sname" in self.kwargs:
                data = ReplicaShare.objects.get(share=self.kwargs["sname"])
            else:
                data = ReplicaShare.objects.get(id=self.kwargs["rid"])
            serialized_data = ReplicaShareSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()


class ReplicaTrailDetailView(rfc.GenericView):
    serializer_class = ReplicaTrailSerializer

    def get(self, *args, **kwargs):
        if "rtid" in self.kwargs:
            try:
                return ReplicaTrail.objects.get(id=self.kwargs["rtid"])
            except:
                return Response()


class ReplicaDetailView(rfc.GenericView):
    serializer_class = ReplicaSerializer

    def get(self, *args, **kwargs):
        if "sname" in self.kwargs:
            try:
                data = Replica.objects.get(share=self.kwargs["sname"])
                serialized_data = ReplicaSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()
        elif "rid" in self.kwargs:
            try:
                data = Replica.objects.get(id=self.kwargs["rid"])
                serialized_data = ReplicaSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()


class ReceiveTrailDetailView(rfc.GenericView):
    serializer_class = ReceiveTrailSerializer

    def get(self, request, *args, **kwargs):
        if "rtid" in self.kwargs:
            with self._handle_exception(request):
                return ReceiveTrail.objects.get(id=self.kwargs["rtid"])
