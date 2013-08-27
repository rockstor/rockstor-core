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
from advanced_sprobe import AdvancedSProbeView
from rest_framework.response import Response
from django.utils.timezone import utc
from datetime import datetime
from storageadmin.util import handle_exception
import logging
logger = logging.getLogger(__name__)


class TaskSchedulerView(AdvancedSProbeView):
    serializer_class = TaskDefinitionSerializer
    valid_tasks = ('snapshot', 'scrub',)

    def get_queryset(self, *args, **kwargs):
        return TaskDefinition.objects.all()

    def get_paginate_by(self, foo):
        download = self.request.QUERY_PARAMS.get('download', None)
        if (download is not None):
            return None
        if (self.paginate_by is None):
            return None
        return settings.PAGINATION['page_size']

    @transaction.commit_on_success
    def post(self, request):
        name = request.DATA['name']
        if (name not in self.valid_tasks):
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
        td = TaskDefinition(name=name, ts=ts_dto, frequency=frequency,
                            json_meta=json_meta)
        td.save()
        return Response()

    @transaction.commit_on_success
    def delete(self, request):
        event_id = request.DATA['id']
        try:
            TaskDefinition.objects.get(id=event_id).delete()
            return Response()
        except Exception, e:
            logger.exception(e)
            e_msg = ('Event with id: %s does not exist' % event_id)
            handle_exception(Exception(e_msg), request)
