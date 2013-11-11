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

from smart_manager.models import (Task, TaskDefinition)
from smart_manager.serializers import TaskSerializer
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


class TaskLogView(AdvancedSProbeView):
    serializer_class = TaskSerializer
    valid_tasks = ('snapshot', 'scrub',)

    def get_queryset(self, *args, **kwargs):
        if ('tid' in kwargs):
            self.paginate_by = 0
            try:
                return Task.objects.get(id=kwargs['tid'])
            except:
                return []
        if ('tdid' in kwargs):
            td = TaskDefinition.objects.get(id=kwargs['tdid'])
            return Task.objects.filter(task_def=td).order_by('-id')
        return Task.objects.filter().order_by('-id')

    def get_paginate_by(self, foo):
        if (self.paginate_by is None):
            return None
        return settings.PAGINATION['page_size']
