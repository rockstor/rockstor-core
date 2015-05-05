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
from backup.models import (BackupPolicy, PolicyTrail)
from backup.serializers import PolicyTrailSerializer
from generic_view import GenericView
import logging
logger = logging.getLogger(__name__)
from datetime import datetime


class PolicyTrailView(GenericView):
    serializer_class = PolicyTrailSerializer

    def get_queryset(self, *args, **kwargs):
        if ('tid' in self.kwargs):
            self.pagninate_by = 0
            try:
                return PolicyTrail.objects.get(id=self.kwargs['tid'])
            except:
                return []

        if ('pid' in self.kwargs):
            bp = BackupPolicy.objects.get(id=self.kwargs['pid'])
            return PolicyTrail.objects.filter(policy=bp).order_by('-id')
        return PolicyTrail.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request, pid):
        policy = BackupPolicy.objects.get(id=pid)
        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        pt = PolicyTrail(policy=policy, status='start', start=now,
                         status_ts=now)
        pt.save()
        return Response(PolicyTrailSerializer(pt).data)

    @transaction.commit_on_success
    def put(self, request, tid):
        pt = PolicyTrail.objects.get(id=tid)
        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        pt.status = request.DATA['status']
        pt.status_ts = now
        if ('error' in request.DATA):
            pt.error = request.DATA['error']
        if (pt.status == 'snapshot created'):
            pt.snap_created = now
        if (pt.status == 'sync started'):
            pt.sync_started = now
        pt.save()
        return Response(PolicyTrailSerializer(pt).data)

