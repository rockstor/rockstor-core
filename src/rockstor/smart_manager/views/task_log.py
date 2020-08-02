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

from smart_manager.models import Task, TaskDefinition
from smart_manager.serializers import TaskSerializer
from django.conf import settings
from django.db import transaction
from rest_framework.response import Response
import rest_framework_custom as rfc


class TaskLogView(rfc.GenericView):
    serializer_class = TaskSerializer
    valid_tasks = (
        "snapshot",
        "scrub",
    )

    def get_queryset(self, *args, **kwargs):
        if "tid" in self.kwargs:
            self.paginate_by = 0
            try:
                return Task.objects.get(id=self.kwargs["tid"])
            except:
                return []
        if "tdid" in self.kwargs:
            td = TaskDefinition.objects.get(id=self.kwargs["tdid"])
            return Task.objects.filter(task_def=td).order_by("-id")
        return Task.objects.filter().order_by("-id")

    def get_paginate_by(self, foo):
        if self.paginate_by is None:
            return None
        return settings.PAGINATION["page_size"]

    @transaction.atomic
    def post(self, request, command):
        with self._handle_exception(request):
            if command == "prune":
                max_log = settings.TASK_SCHEDULER.get("max_log")
                for td in TaskDefinition.objects.all():
                    if Task.objects.filter(task_def=td).count() > max_log:
                        start_cutoff = (
                            Task.objects.filter(task_def=td)
                            .order_by("-start")[max_log]
                            .start
                        )
                        Task.objects.filter(
                            task_def=td, start__lte=start_cutoff
                        ).delete()
            return Response()
