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
from smart_manager.models import ReplicaShare
from smart_manager.serializers import ReplicaShareSerializer
from storageadmin.util import handle_exception
from generic_view import GenericView
from datetime import datetime
from django.utils.timezone import utc

import logging
logger = logging.getLogger(__name__)


class ReplicaShareView(GenericView):
    serializer_class = ReplicaShareSerializer

    def get_queryset(self, *args, **kwargs):
        if ('sname' in kwargs):
            self.paginate_by = 0
            try:
                return ReplicaShare.objects.get(share=kwargs['sname'])
            except:
                return []
        return ReplicaShare.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request):
        sname = request.DATA['share']
        if (ReplicaShare.objects.filter(share=sname).exists()):
            e_msg = ('Replicashare(%s) already exists.' % sname)
            handle_exception(Exception(e_msg), request)

        share = self._validate_share(sname, request)
        aip = request.DATA['appliance']
        self._validate_appliance(aip, request)
        src_share = request.DATA['src_share']
        data_port = int(request.DATA['data_port'])
        meta_port = int(request.DATA['meta_port'])
        ts = datetime.utcnow().replace(tzinfo=utc)
        r = ReplicaShare(share=sname, appliance=aip,
                         pool=share.pool.name, src_share=src_share,
                         data_port=data_port,
                         meta_port=meta_port, ts=ts)
        r.save()
        return Response(ReplicaShareSerializer(r).data)

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

