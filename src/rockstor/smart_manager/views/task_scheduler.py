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

from smart_manager.models import TaskDefinition
from smart_manager.serializers import TaskDefinitionSerializer
from django.db import transaction
import json
from rest_framework.response import Response
from django.utils.timezone import utc
from datetime import datetime
from storageadmin.util import handle_exception
import rest_framework_custom as rfc


class TaskSchedulerView(rfc.GenericView):
    serializer_class = TaskDefinitionSerializer
    valid_tasks = ('snapshot', 'scrub',)

    def get_queryset(self, *args, **kwargs):
        if ('tdid' in kwargs):
            self.paginate_by = 0
            try:
                return TaskDefinition.objects.get(id=kwargs['tdid'])
            except:
                return []
        return TaskDefinition.objects.filter().order_by('-id')

    def _validate_input(self, request):
        frequency = None
        meta = {}
        try:
            frequency = int(float(request.DATA.get('frequency')))
            if (frequency < 1):
                frequency = 1
        except:
            e_msg = ('frequency is in minutes and hence must be a positive '
                     'integer')
            handle_exception(Exception(e_msg), request)

        meta = request.DATA.get('meta', {})
        if (type(meta) != dict):
            e_msg = ('meta must be a dictionary, not %s' % type(meta))
            handle_exception(Exception(e_msg), request)
        return frequency, meta

    @transaction.commit_on_success
    def post(self, request):
        with self._handle_exception(request):
            name = request.DATA['name']
            if (TaskDefinition.objects.filter(name=name).exists()):
                msg = ('Another task exists with the same name(%s). Choose '
                       'a different name' % name)
                handle_exception(Exception(msg), request)

            task_type = request.DATA['task_type']
            if (task_type not in self.valid_tasks):
                e_msg = ('Unknown task type: %s cannot be scheduled' % name)
                handle_exception(Exception(e_msg), request)

            frequency, meta = self._validate_input(request)
            json_meta = json.dumps(meta)

            ts = int(float(request.DATA['ts']))
            ts_dto = datetime.utcfromtimestamp(
                float(ts)).replace(second=0, microsecond=0, tzinfo=utc)
            td = TaskDefinition(name=name, task_type=task_type, ts=ts_dto,
                                frequency=frequency, json_meta=json_meta)
            td.save()
            return Response(TaskDefinitionSerializer(td).data)

    def _task_def(self, request, tdid):
        try:
            return TaskDefinition.objects.get(id=tdid)
        except:
            e_msg = ('Event with id: %s does not exist' % tdid)
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def put(self, request, tdid):
        with self._handle_exception(request):
            tdo = self._task_def(request, tdid)
            enabled = request.DATA.get('enabled', True)
            if (type(enabled) != bool):
                e_msg = ('enabled flag must be a boolean and not %s' %
                         type(enabled))
                handle_exception(Exception(e_msg), request)
            tdo.enabled = enabled
            tdo.frequency, new_meta = self._validate_input(request)
            meta = json.loads(tdo.json_meta)
            meta.update(new_meta)
            tdo.json_meta = json.dumps(meta)
            tdo.save()
            return Response(TaskDefinitionSerializer(tdo).data)

    @transaction.commit_on_success
    def delete(self, request, tdid):
        tdo = self._task_def(request, tdid)
        tdo.delete()
        return Response()
