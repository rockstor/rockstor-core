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

from smart_manager.models import SProbe
from django.conf import settings
from django.db import transaction
from storageadmin.util import handle_exception
from smart_manager.serializers import SProbeSerializer, PaginatedSProbe
from rest_framework.response import Response
import zmq
import os
import rest_framework_custom as rfc
from django.core.paginator import Paginator
from smart_manager.taplib.probe_config import TAP_MAP
import logging

logger = logging.getLogger(__name__)


class AdvancedSProbeView(rfc.GenericView):
    content_negotiation_class = rfc.IgnoreClient

    def get_queryset(self, *args, **kwargs):
        self.page_size = None
        pname = self.request.path.split("/")[4]
        limit = self.request.query_params.get(
            "limit", settings.REST_FRAMEWORK["MAX_LIMIT"]
        )
        limit = int(limit)
        t1 = self.request.query_params.get("t1", None)
        t2 = self.request.query_params.get("t2", None)
        pid = None
        if "pid" in self.kwargs:
            pid = self.kwargs["pid"]
        if pid is None:
            self.serializer_class = SProbeSerializer
            try:
                return SProbe.objects.filter(name=pname).order_by("-start")[0:limit]
            except:
                e_msg = "No smart probe instances exist for: %s" % pname
                handle_exception(Exception(e_msg), self.request)

        command = None
        if "command" in self.kwargs:
            command = self.kwargs["command"]
        if command is None:
            self.serializer_class = SProbeSerializer
            self.paginate_by = None
            return SProbe.objects.filter(name=pname, id=pid)

        if command != "data":
            e_msg = "unknown command: %s" % repr(command)
            handle_exception(Exception(e_msg), self.request)

        ro = None
        try:
            ro = SProbe.objects.get(name=pname, id=pid)
        except:
            e_msg = "Probe: %s with id: %s does not exist" % (pname, pid)
            handle_exception(Exception(e_msg), self.request)

        if t1 is not None and t2 is not None:
            return self.model_obj.objects.filter(rid=ro, ts__gt=t1, ts__lte=t2)
        return self.model_obj.objects.filter(rid=ro).order_by("-ts")[0:limit]

    def _validate_probe(self, pname, pid, request):
        try:
            return SProbe.objects.get(name=pname, id=pid)
        except:
            e_msg = "Probe: %s with id: %s does not exist" % (pname, pid)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, pid=None, command=None):
        """
        start or stop a smart probe
        """
        # get the task uuid from the url string
        pname = request.path.split("/")[4]
        task = {}
        ro = None
        if pid is None:  # start a probe
            # if there's a recipe already running, throw error
            if SProbe.objects.filter(
                name=pname, state__regex=r"(created|running)"
            ).exists():
                e_msg = "Smart probe: %s already running" % pname
                handle_exception(Exception(e_msg), request)
            # if max number of probes already running, throw error
            num_live = len(SProbe.objects.filter(state__regex=r"(created|running"))
            if num_live > settings.MAX_TAP_WORKERS:
                e_msg = (
                    "Maximum number(%d) of smart probes running. Cannot "
                    "start another one until one of them is stopped"
                    % settings.MAX_TAP_WORKERS
                )
                handle_exception(Exception(e_msg), request)

            # get last id
            cur_id = 0
            try:
                cur_id = SProbe.objects.all().order_by("-start")[0].id
            except:
                logger.info("no previous probe ids found for: %s" % pname)

            display_name = None
            if "display_name" in request.data:
                display_name = request.data["display_name"]
            ro = SProbe(
                name=pname, display_name=display_name, smart=True, state="created"
            )
            ro.save()
            kernel_module = os.path.join(
                settings.TAP_DIR, TAP_MAP[pname]["location"] + ".ko"
            )
            task = {
                "module": kernel_module,
                "tap": pname,
                "action": "start",
                "roid": cur_id + 1,
            }
        else:
            ro = self._validate_probe(pname, pid, request)
            if command not in ("stop", "status",):
                e_msg = "command: %s not supported." % command
                handle_exception(Exception(e_msg), request)
            if command == "status":
                return self._paginated_response((ro,), request)
            if ro.state == "stopped" or ro.state == "error":
                e_msg = (
                    "Probe: %s with id: %s already in state: %s. It "
                    "cannot be stopped." % (pname, pid, ro.state)
                )
                handle_exception(Exception(e_msg), request)
            task = {
                "tap": pname,
                "action": "stop",
                "roid": ro.id,
            }

        ctx = zmq.Context()
        task_socket = ctx.socket(zmq.PUSH)
        task_socket.connect("tcp://%s:%d" % settings.TAP_SERVER)
        task_socket.send_json(task)
        return self._paginated_response((ro,), request)

    def _paginated_response(self, qs, request):
        p = Paginator(qs, 100)
        data = p.page(1)
        serializer_context = {"request": request}
        serializer = PaginatedSProbe(data, context=serializer_context)
        return Response(serializer.data)
