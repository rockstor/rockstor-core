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
from django.conf import settings
from django.db import transaction
import json
from rest_framework.response import Response
from django.utils.timezone import utc
from datetime import datetime
from storageadmin.util import handle_exception
from generic_view import GenericView
import logging
logger = logging.getLogger(__name__)


class TaskSchedulerView(GenericView):
    serializer_class = TaskDefinitionSerializer
    valid_tasks = ('snapshot', 'scrub',)

    def get_queryset(self, *args, **kwargs):
        if ('tdid' in kwargs):
            self.paginate_by = 0
            try:
                logger.debug('getting task definition for %s' % kwargs['tdid'])
                return TaskDefinition.objects.get(id=kwargs['tdid'])
            except:
                logger.debug('exception')
                return []
        logger.debug('returning objects')
        return TaskDefinition.objects.filter().order_by('-id')

    @transaction.commit_on_success
    def post(self, request):
        name = request.DATA['name']
        task_type = request.DATA['task_type']
        if (task_type not in self.valid_tasks):
            e_msg = ('Unknown task type: %s cannot be scheduled' % name)
            handle_exception(Exception(e_msg), request)

        frequency = None
        if ('frequency' in request.DATA):
            frequency = int(request.DATA['frequency'])
            if (frequency < 60):
                frequency = None
            else:
                frequency = frequency - (frequency % 60)
        logger.info('meta: %s' % request.DATA['meta'])
        json_meta = json.dumps(request.DATA['meta'])
        logger.info('json_meta: %s' % json_meta)
        logger.info('request: %s' % request.DATA)

        ts = int(float(request.DATA['ts']))
        ts_dto = datetime.utcfromtimestamp(float(ts)).replace(second=0,
                                                              microsecond=0,
                                                              tzinfo=utc)
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
        tdo = self._task_def(request, tdid)
        enabled = request.DATA['enabled']
        tdo.enabled = enabled
        logger.info('enabled: %s. type: %s' % (request.DATA, type(enabled)))
        tdo.save()
        return Response(TaskDefinitionSerializer(tdo).data)

    @transaction.commit_on_success
    def delete(self, request, tdid):
        tdo = self._task_def(request, tdid)
        tdo.delete()
        return Response()
