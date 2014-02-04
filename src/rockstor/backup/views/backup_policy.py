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
Disk view, for anything at the disk level
"""

from rest_framework.response import Response
from django.db import transaction
from backup.models import BackupPolicy
from backup.serializers import BackupPolicySerializer
from storageadmin.util import handle_exception
from django.conf import settings
from generic_view import GenericView

class BackupPolicyView(GenericView):
    serializer_class = BackupPolicySerializer

    def get_queryset(self, *args, **kwargs):
        if ('pname' in kwargs):
            self.paginate_by = 0
            try:
                return BackupPolicy.objects.get(name=kwargs['pname'])
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
        start = int(float(request.DATA['start']))
        frequency = None
        if ('frequency' in request.DATA):
            frequency = int(request.DATA['frequency'])
            if (frequency < 60):
                frequency = None
            else:
                frequency = frequency - (frequency % 60)
        num_retain = request.DATA['num_retain']
        bp = BackupPolicy(name=name, source_ip=source_ip, 
                source_path=source_path, dest_share=dest_share,
                notify_email=notify_email, start=start,
                frequency=frequency, num_retain=num_retain)
        bp.save()
        return Response(BackupPolicySerializer(bp).data)


