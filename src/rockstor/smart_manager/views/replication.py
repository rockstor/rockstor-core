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

"""
View for things at snapshot level
"""

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Share, Appliance)
from smart_manager.models import (Replica, ReplicaTrail)
from smart_manager.serializers import ReplicaSerializer
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc
import rest_framework_custom as rfc


class ReplicaView(rfc.GenericView):
    serializer_class = ReplicaSerializer

    def get_queryset(self, *args, **kwargs):
        if ('sname' in kwargs):
            return Replica.objects.filter(share=kwargs['sname'])
        if ('rid' in kwargs):
            self.paginate_by = 0
            try:
                return Replica.objects.get(id=kwargs['rid'])
            except:
                return []
        return Replica.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request):
        sname = request.DATA['share']
        if (Replica.objects.filter(share=sname).exists()):
            e_msg = ('Another replication task already exists for this '
                     'share(%s). Only 1-1 replication is supported currently.'
                     % sname)
            handle_exception(Exception(e_msg), request)
        share = self._validate_share(sname, request)
        aip = request.DATA['appliance']
        self._validate_appliance(aip, request)
        dpool = request.DATA['pool']
        frequency = int(request.DATA['frequency'])
        task_name = request.DATA['task_name']
        data_port = int(request.DATA['data_port'])
        meta_port = int(request.DATA['meta_port'])
        ts = datetime.utcnow().replace(tzinfo=utc)
        r = Replica(task_name=task_name, share=sname, appliance=aip,
                    pool=share.pool.name, dpool=dpool, enabled=True,
                    frequency=frequency, data_port=data_port,
                    meta_port=meta_port, ts=ts)
        r.save()
        return Response(ReplicaSerializer(r).data)

    @transaction.commit_on_success
    def put(self, request, rid):
        ts = datetime.utcnow().replace(tzinfo=utc)
        try:
            r = Replica.objects.get(id=rid)
        except:
            e_msg = ('Replica(%s) does not exist' % rid)
            handle_exception(Exception(e_msg), request)

        enabled = request.DATA['enabled']
        if (enabled == 'False'):
            enabled = False
        else:
            enabled = True
        r.enabled = enabled
        r.ts = ts
        r.save()
        return Response(ReplicaSerializer(r).data)

    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def _validate_appliance(self, ip, request):
        try:
            return Appliance.objects.get(ip=ip)
        except:
            e_msg = ('Appliance with ip: %s is not recognized.' % ip)
            handle_exception(Exception(e_msg), request)

    def delete(self, request, rid):
        with self._handle_exception(request):
            try:
                r = Replica.objects.get(id=rid)
            except:
                e_msg = ('Replica(%s) does not exist' % rid)
                handle_exception(Exception(e_msg), request)

            if (r.enabled is True):
                e_msg = ('Replica(%s) is still enabled. Disable it and '
                         'retry.' % rid)
                handle_exception(Exception(e_msg), request)

            ReplicaTrail.objects.filter(replica=r).delete()
            r.delete()
            return Response()
