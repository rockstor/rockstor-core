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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Share
from backup.models import BackupPolicy
from backup.serializers import BackupPolicySerializer
from storageadmin.util import handle_exception
from generic_view import GenericView
from datetime import datetime
from django.utils.timezone import utc

class BackupPolicyView(GenericView):
    serializer_class = BackupPolicySerializer

    def get_queryset(self, *args, **kwargs):
        self.paginate_by = 0
        try:
            return BackupPolicy.objects.get(**kwargs)
        except:
            return []
        return BackupPolicy.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        name = request.DATA['name']
        source_ip = request.DATA['source_ip']
        source_path = request.DATA['source_path']
        dest_share = request.DATA['dest_share']
        notify_email = request.DATA['notify_email']
        frequency = None
        if ('frequency' in request.DATA):
            frequency = int(request.DATA['frequency'])
            if (frequency < 60):
                frequency = 60
            else:
                frequency = frequency - (frequency % 60)
        ts = int(float(request.DATA['ts']))
        ts_dto = datetime.utcfromtimestamp(float(ts)).replace(second=0,
                                                              microsecond=0,
                                                              tzinfo=utc)
        num_retain = request.DATA['num_retain']
        if (not Share.objects.filter(name=dest_share).exists()):
            e_msg = ('Destination share(%s) does not exist. Check and try'
                     ' again' % (dest_share))
            handle_exception(Exception(e_msg), request)

        bp = BackupPolicy(name=name, source_ip=source_ip,
                          source_path=source_path, dest_share=dest_share,
                          notify_email=notify_email, start=ts,
                          frequency=frequency, num_retain=num_retain)
        bp.save()
        return Response(BackupPolicySerializer(bp).data)

    def _validate_policy(self, id, request):
        try:
            return BackupPolicy.objects.get(id=id)
        except:
            e_msg = ('Backup policy(%s) does not exist' % id)
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def put(self, request, id):
        policy = self._validate_policy(id, request)
        enabled = request.DATA['enabled']
        policy.enabled = enabled
        policy.save()
        return Response(BackupPolicySerializer(policy).data)

    @transaction.commit_on_success
    def delete(self, request, id):
        bp = self._validate_policy(id, request)
        bp.delete()
        return Response()

