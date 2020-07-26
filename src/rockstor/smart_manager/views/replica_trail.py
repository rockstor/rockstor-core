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

from django.db import transaction
from django.utils.timezone import utc
from rest_framework.response import Response
from smart_manager.models import Replica, ReplicaTrail
from smart_manager.serializers import ReplicaTrailSerializer
from datetime import datetime, timedelta
import rest_framework_custom as rfc


class ReplicaTrailListView(rfc.GenericView):
    serializer_class = ReplicaTrailSerializer

    def get_queryset(self, *args, **kwargs):
        if "rid" in self.kwargs:
            replica = Replica.objects.get(id=self.kwargs["rid"])
            if "limit" in self.request.query_params:
                limit = int(self.request.query_params.get("limit", 2))
                return ReplicaTrail.objects.filter(replica=replica).order_by("-id")[
                    0:limit
                ]
            return ReplicaTrail.objects.filter(replica=replica).order_by("-id")
        return ReplicaTrail.objects.filter().order_by("-id")

    @transaction.atomic
    def post(self, request, rid):
        with self._handle_exception(request):
            replica = Replica.objects.get(id=rid)
            snap_name = request.data["snap_name"]
            ts = datetime.utcnow().replace(tzinfo=utc)
            rt = ReplicaTrail(
                replica=replica,
                snap_name=snap_name,
                status="pending",
                snapshot_created=ts,
            )
            rt.save()
            return Response(ReplicaTrailSerializer(rt).data)

    @transaction.atomic
    def delete(self, request, rid):
        with self._handle_exception(request):
            days = int(request.data.get("days", 30))
            replica = Replica.objects.get(id=rid)
            ts = datetime.utcnow().replace(tzinfo=utc)
            ts0 = ts - timedelta(days=days)
            if ReplicaTrail.objects.filter(replica=replica).count() > 100:
                ReplicaTrail.objects.filter(replica=replica, end_ts__lt=ts0).delete()
            return Response()


class ReplicaTrailDetailView(rfc.GenericView):
    serializer_class = ReplicaTrailSerializer

    def get(self, *args, **kwargs):
        if "rtid" in self.kwargs:
            try:
                data = ReplicaTrail.objects.get(id=self.kwargs["rtid"])
                serialized_data = ReplicaTrailSerializer(data)
                return Response(serialized_data.data)
            except:
                return Response()

    @transaction.atomic
    def put(self, request, rtid):
        with self._handle_exception(request):
            rt = ReplicaTrail.objects.get(id=rtid)
            rt.status = request.data["status"]
            if "error" in request.data:
                rt.error = request.data["error"]
            if "kb_sent" in request.data:
                rt.kb_sent = request.data["kb_sent"]
            if rt.status in ("failed", "succeeded",):
                ts = datetime.utcnow().replace(tzinfo=utc)
                rt.end_ts = ts
                if rt.status == "failed":
                    rt.send_failed = ts
            rt.save()
            return Response(ReplicaTrailSerializer(rt).data)
