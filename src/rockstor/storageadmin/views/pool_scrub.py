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
from storageadmin.util import handle_exception
from storageadmin.serializers import PoolScrubSerializer
from storageadmin.models import Pool, PoolScrub
import rest_framework_custom as rfc
from fs.btrfs import scrub_start, scrub_status
from datetime import timedelta

import logging

logger = logging.getLogger(__name__)


class PoolScrubView(rfc.GenericView):
    serializer_class = PoolScrubSerializer

    def _validate_pool(self, pid, request):
        try:
            return Pool.objects.get(id=pid)
        except:
            e_msg = "Pool with id ({}) does not exist.".format(pid)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            pool = self._validate_pool(self.kwargs["pid"], self.request)
            self._scrub_status(pool)
            return PoolScrub.objects.filter(pool=pool).order_by("-id")

    @transaction.atomic
    def _scrub_status(self, pool):
        try:
            ps = PoolScrub.objects.filter(pool=pool).order_by("-id")[0]
        except:
            return Response()
        if ps.status == "started" or ps.status == "running":
            cur_status = scrub_status(pool)
            if (
                cur_status["status"] == "finished"
                or cur_status["status"] == "halted"
                or cur_status["status"] == "cancelled"
            ):
                duration = int(cur_status["duration"])
                cur_status["end_time"] = ps.start_time + timedelta(seconds=duration)
                del cur_status["duration"]
            PoolScrub.objects.filter(id=ps.id).update(**cur_status)
        return ps

    @transaction.atomic
    def post(self, request, pid, command=None):
        pool = self._validate_pool(pid, request)
        if command is not None and command != "status":
            e_msg = "Unknown scrub command: ({}).".format(command)
            handle_exception(Exception(e_msg), request)

        with self._handle_exception(request):
            ps = self._scrub_status(pool)
            if command == "status":
                return Response(PoolScrubSerializer(ps).data)
            force = request.data.get("force", False)
            if PoolScrub.objects.filter(
                pool=pool, status__regex=r"(started|running)"
            ).exists():
                if force:
                    p = PoolScrub.objects.filter(
                        pool=pool, status__regex=r"(started|running)"
                    ).order_by("-id")[0]
                    p.status = "terminated"
                    p.save()
                else:
                    e_msg = (
                        "A Scrub process is already running for "
                        "pool ({}). If you really want to kill it "
                        "and start a new scrub, use the force "
                        "option."
                    ).format(pool.name)
                    handle_exception(Exception(e_msg), request)

            scrub_pid = scrub_start(pool, force=force)
            ps = PoolScrub(pool=pool, pid=scrub_pid)
            ps.save()
            return Response(PoolScrubSerializer(ps).data)
