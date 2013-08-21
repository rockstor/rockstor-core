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
from advanced_sprobe import AdvancedSProbeView


class TaskSchedulerView(AdvancedSProbeView):
    serializer_class = TaskSerializer

    def get_queryset(self, *args, **kwargs):
        return Task.objects.all()

    def get_paginate_by(self, foo):
        download = self.request.QUERY_PARAMS.get('download', None)
        if (download is not None):
            return None
        if (self.paginate_by is None):
            return None
        return settings.PAGINATION['page_size']

    def post(self, request, *args, **kwargs):
        pass
