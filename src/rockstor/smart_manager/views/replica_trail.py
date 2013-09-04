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
from generic_view import GenericView
import logging
logger = logging.getLogger(__name__)
from datetime import datetime


class ReplicaTrailView(GenericView):
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
            return ReplicaTrail.objects.filter(replica=replica)

        return ReplicaTrail.objects.all()

    @transaction.commit_on_success
    def post(self, request, rid):
        replica = Replica.objects.get(id=rid)
        snap_name = request.DATA['snap_name']
        ts = datetime.utcnow().replace(tzinfo=utc)
        rt = ReplicaTrail(replica=replica, snap_name=snap_name,
                          status='snap_created', state_ts=ts)
        rt.save()
        return Response(ReplicaTrailSerializer(rt).data)

    @transaction.commit_on_success
    def put(self, request, rtid):
        rt = ReplicaTrail.objects.get(id=rtid)
        new_status = request.DATA['status']
        rt.status = new_status
        rt.save()
        return Response(ReplicaTrailSerializer(rt).data)
