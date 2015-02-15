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

from django.db import transaction
from django.utils.timezone import utc
from rest_framework.response import Response
from smart_manager.models import (Replica, ReplicaTrail)
from smart_manager.serializers import (ReplicaTrailSerializer)
from datetime import (datetime, timedelta)
import rest_framework_custom as rfc


class ReplicaTrailView(rfc.GenericView):
    serializer_class = ReplicaTrailSerializer

    def get_queryset(self, *args, **kwargs):
        if ('rtid' in kwargs):
            self.pagninate_by = 0
            try:
                return ReplicaTrail.objects.get(id=kwargs['rtid'])
            except:
                return []

        if ('rid' in kwargs):
            replica = Replica.objects.get(id=kwargs['rid'])
            if ('limit' in self.request.QUERY_PARAMS):
                limit = int(self.request.QUERY_PARAMS.get('limit', 2))
                return ReplicaTrail.objects.filter(
                    replica=replica).order_by('-id')[0:limit]
            return ReplicaTrail.objects.filter(replica=replica).order_by('-id')
        return ReplicaTrail.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request, rid):
        replica = Replica.objects.get(id=rid)
        snap_name = request.DATA['snap_name']
        ts = datetime.utcnow().replace(tzinfo=utc)
        rt = ReplicaTrail(replica=replica, snap_name=snap_name,
                          status='pending', snapshot_created=ts)
        rt.save()
        return Response(ReplicaTrailSerializer(rt).data)

    @transaction.commit_on_success
    def put(self, request, rtid):
        rt = ReplicaTrail.objects.get(id=rtid)
        new_status = request.DATA['status']
        if ('error' in request.DATA):
            rt.error = request.DATA['error']
        if ('kb_sent' in request.DATA):
            rt.kb_sent = request.DATA['kb_sent']
        if ('end_ts' in request.DATA):
            rt.end_ts = request.DATA['end_ts']
        rt.status = new_status
        rt.save()
        return Response(ReplicaTrailSerializer(rt).data)

    @transaction.commit_on_success
    def delete(self, request, rid):
        with self._handle_exception(request):
            days = int(request.DATA.get('days', 30))
            replica = Replica.objects.get(id=rid)
            ts = datetime.utcnow().replace(tzinfo=utc)
            ts0 = ts - timedelta(days=days)
            if (ReplicaTrail.objects.filter(replica=replica).count() > 100):
                ReplicaTrail.objects.filter(replica=replica,
                                            end_ts__lt=ts0).delete()
            return Response()
