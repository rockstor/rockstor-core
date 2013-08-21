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

from smart_manager.models import Task
from smart_manager.serializers import TaskSerializer
from django.conf import settings
from task_scheduler import TaskSchedulerView
from storageadmin.util import handle_exception
from storageadmin.models import Share
from rest_framework.response import Response


class SnapSchedulerView(TaskSchedulerView):
    serializer_class = TaskSerializer

    def _validate_share(self, request):
        try:
            sname = request.QUERY_PARAMS.get('share', None)
            return Share.objects.get(name=sname)
        except:
            e_msg = ('Share: %s does not exist' % sname)
            handle_exception(Exception(e_msg), request)

    def post(self, request):

        share = self._validate_share(request)
        return Response()
