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


from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Share, Appliance
from smart_manager.models import ReplicaShare, ReceiveTrail
from smart_manager.serializers import ReplicaShareSerializer
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc
import rest_framework_custom as rfc


class ReplicaShareListView(rfc.GenericView):
    serializer_class = ReplicaShareSerializer

    def get_queryset(self, *args, **kwargs):
        return ReplicaShare.objects.filter().order_by("-id")

    @transaction.atomic
    def post(self, request):
        sname = request.data["share"]
        if ReplicaShare.objects.filter(share=sname).exists():
            # Note e_msg is consumed by replication/util.py create_rshare()
            e_msg = "Replicashare(%s) already exists." % sname
            handle_exception(Exception(e_msg), request)

        share = self._validate_share(sname, request)
        aip = request.data["appliance"]
        self._validate_appliance(aip, request)
        src_share = request.data["src_share"]
        ts = datetime.utcnow().replace(tzinfo=utc)
        r = ReplicaShare(
            share=sname, appliance=aip, pool=share.pool.name, src_share=src_share, ts=ts
        )
        r.save()
        return Response(ReplicaShareSerializer(r).data)

    @staticmethod
    def _validate_share(sname, request):
        try:
            return Share.objects.get(name=sname)
        except:
            e_msg = "Share: %s does not exist" % sname
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_appliance(ip, request):
        try:
            return Appliance.objects.get(ip=ip)
        except:
            e_msg = "Appliance with ip: %s is not recognized." % ip
            handle_exception(Exception(e_msg), request)


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

    @transaction.atomic
    def delete(self, request, rid):
        with self._handle_exception(request):
            try:
                rs = ReplicaShare.objects.get(id=rid)
            except:
                e_msg = "ReplicaShare(%d) does not exist." % rid
                handle_exception(Exception(e_msg), request)

            if Share.objects.filter(name=rs.share).exists():
                e_msg = (
                    "To delete this, you need to first delete this "
                    "Share: %s. If you are sure, try again after "
                    "deleting it." % rs.share
                )
                handle_exception(Exception(e_msg), request)

            ReceiveTrail.objects.filter(rshare=rs).delete()
            rs.delete()
            return Response()
