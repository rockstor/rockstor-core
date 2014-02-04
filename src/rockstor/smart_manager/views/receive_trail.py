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
from smart_manager.models import (ReplicaShare, ReceiveTrail)
from smart_manager.serializers import (ReceiveTrailSerializer)
from generic_view import GenericView
import logging
logger = logging.getLogger(__name__)
from datetime import datetime


class ReceiveTrailView(GenericView):
    serializer_class = ReceiveTrailSerializer

    def get_queryset(self, *args, **kwargs):
        if ('rtid' in kwargs):
            self.pagninate_by = 0
            try:
                return ReceiveTrail.objects.get(id=kwargs['rtid'])
            except:
                return []

        if ('rid' in kwargs):
            replica = ReplicaShare.objects.get(id=kwargs['rid'])
            return ReceiveTrail.objects.filter(replica=replica).order_by('-id')
        return ReceiveTrail.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request, rid):
        rs = ReplicaShare.objects.get(id=rid)
        snap_name = request.DATA['snap_name']
        ts = datetime.utcnow().replace(tzinfo=utc)
        rt = ReceiveTrail(rshare=rs, snap_name=snap_name,
                          status='pending', receive_pending=ts)
        rt.save()
        return Response(ReceiveTrailSerializer(rt).data)

    @transaction.commit_on_success
    def put(self, request, rtid):
        rt = ReceiveTrail.objects.get(id=rtid)
        if ('snapshot_created' in request.DATA):
            rt.snapshot_created = request.DATA['snapshot_created']
        if ('snapshot_failed' in request.DATA):
            rt.snapshot_failed = request.DATA['snapshot_failed']
        if ('receive_succeeded' in request.DATA):
            rt.receive_succeeded = request.DATA['receive_succeeded']
        if ('receive_failed' in request.DATA):
            rt.receive_failed = request.DATA['receive_failed']
        if ('status' in request.DATA):
            rt.stats = request.DATA['status']
        if ('error' in request.DATA):
            rt.error = request.DATA['error']
        if ('kb_received' in request.DATA):
            rt.kb_received = request.DATA['kb_received']
        if ('end_ts' in request.DATA):
            rt.end_ts = request.DATA['end_ts']
        rt.save()
        return Response(ReceiveTrailSerializer(rt).data)
