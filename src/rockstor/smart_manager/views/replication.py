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
import logging
logger = logging.getLogger(__name__)


class ReplicaView(rfc.GenericView):
    serializer_class = ReplicaSerializer

    def get_queryset(self, *args, **kwargs):
        status = self.request.query_params.get('status', None)
        if (status is not None):
            enabled = None
            if (status == 'enabled'):
                enabled = True
            elif (status == 'disabled'):
                enabled = False
            if (enabled is not None):
                return Replica.objects.filter(enabled=enabled)

        return Replica.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request):
        with self._handle_exception(request):
            sname = request.DATA.get('share')
            if (Replica.objects.filter(share=sname).exists()):
                e_msg = ('Another replication task already exists for this '
                         'share(%s). Only 1-1 replication is supported '
                         'currently.' % sname)
                handle_exception(Exception(e_msg), request)
            share = self._validate_share(sname, request)
            appliance = self._validate_appliance(request)
            dpool = request.DATA.get('pool')
            frequency = self._validate_frequency(request)
            task_name = request.DATA.get('task_name')
            try:
                data_port = int(request.DATA.get('data_port'))
                meta_port = int(request.DATA.get('meta_port'))
            except:
                e_msg = ('data and meta ports must be valid port '
                         'numbers(1-65535).')
                handle_exception(Exception(e_msg), request)
            data_port = self._validate_port(data_port, request)
            meta_port = self._validate_port(meta_port, request)
            ts = datetime.utcnow().replace(tzinfo=utc)
            r = Replica(task_name=task_name, share=sname,
                        appliance=appliance.uuid, pool=share.pool.name,
                        dpool=dpool, enabled=True, frequency=frequency,
                        data_port=data_port, meta_port=meta_port, ts=ts)
            r.save()
            return Response(ReplicaSerializer(r).data)

    @transaction.commit_on_success
    def put(self, request, rid):
        with self._handle_exception(request):
            try:
                r = Replica.objects.get(id=rid)
            except:
                e_msg = ('Replica(%s) does not exist' % rid)
                handle_exception(Exception(e_msg), request)

            r.frequency = self._validate_frequency(request, r.frequency)
            enabled = request.DATA.get('enabled', r.enabled)
            if (type(enabled) != bool):
                e_msg = ('enabled switch must be a boolean, not %s' %
                         type(enabled))
                handle_exception(Exception(e_msg), request)
            r.enabled = enabled
            ts = datetime.utcnow().replace(tzinfo=utc)
            r.ts = ts
            r.save()
            return Response(ReplicaSerializer(r).data)

    def _validate_share(self, sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def _validate_appliance(self, request):
        try:
            ip = request.DATA.get('appliance', None)
            return Appliance.objects.get(ip=ip)
        except:
            e_msg = ('Appliance with ip(%s) is not recognized.' % ip)
            handle_exception(Exception(e_msg), request)

    def _validate_port(self, port, request):
        if (port < 1 or port > 65535):
            e_msg = ('Valid port numbers are between 1-65535')
            handle_exception(Exception(e_msg), request)
        return port

    def _validate_frequency(self, request, default=1):
        e_msg = ('frequency must be a positive integer')
        try:
            frequency = int(request.DATA.get('frequency', default))
        except:
            handle_exception(Exception(e_msg), request)
        if (frequency < 1):
            handle_exception(Exception(e_msg), request)
        return frequency

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
