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
from huey.exceptions import TaskException
from rest_framework.response import Response
from django.db import transaction
from huey.contrib.djhuey import HUEY
from storageadmin.util import handle_exception
from storageadmin.serializers import PoolBalanceSerializer
from storageadmin.models import Pool, PoolBalance
import rest_framework_custom as rfc
from fs.btrfs import balance_status, balance_status_internal
from pool import PoolMixin

import logging

logger = logging.getLogger(__name__)


class PoolBalanceView(PoolMixin, rfc.GenericView):
    serializer_class = PoolBalanceSerializer

    @staticmethod
    def _validate_pool(pid, request):
        try:
            return Pool.objects.get(id=pid)
        except:
            e_msg = "Pool ({}) does not exist.".format(pid)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            pool = self._validate_pool(self.kwargs["pid"], self.request)
            self._balance_status(pool)
            return PoolBalance.objects.filter(pool=pool).order_by("-id")

    @staticmethod
    @transaction.atomic
    def _balance_status(pool):
        try:
            # acquire a handle on the last pool balance status db entry
            ps = PoolBalance.objects.filter(pool=pool).order_by("-id")[0]
        except:
            # return empty handed if we have no 'last entry' to update
            return Response()
        # Check if we have a pending task which matches our tid.
        logger.debug("POOLS BALANCE MODEL PS.TID = {}".format(ps.tid))
        hi = HUEY
        logger.debug("HUEY.pending() {}".format(hi.pending()))
        # Pending balance tasks. N.B. Executing tasks are no longer pending.
        # There is a 1 to 3 second 'pending" status for Huey tasks.
        pending_task_ids = [
            task.id
            for task in hi.pending()
            if task.name in ["start_balance", "start_resize_pool"]
        ]
        logger.debug("Pending balance task.ids = {}".format(pending_task_ids))
        try:
            # https://huey.readthedocs.io/en/latest/api.html#Huey.get
            # The following does a destructive read unless preserve=True.
            # This read will also throw the TaskException which is our interest here.
            # https://huey.readthedocs.io/en/latest/api.html#Huey.result
            # https://github.com/coleifer/huey/issues/449#issuecomment-535028271
            # Syntax requires huey 2.1.3
            hi.result(ps.tid)
        except TaskException as e:
            ps.status = "failed"
            # N.B. metadata indexes: retries, traceback, task_id, error
            ps.message = e.metadata.get("traceback", "missing 'traceback' key")
            # TODO: Consider a huey signal to triggered the addition of end time
            #  currently no SIGNAL_ERROR is seen to be active (see task.py)
            # ps.end_time = to.failed  # defaults to Null in model.
            # https://docs.djangoproject.com/en/1.8/ref/models/instances
            #  /#specifying-which-fields-to-save
            ps.save(update_fields=["status", "message"])
            return ps
        if ps.status == u"started" and ps.tid in pending_task_ids:
            # Model default (i.e. a new balance) defaults to status "started".
            # Preserve this state while we await our pending task (1 to 3 seconds).
            logger.debug("WE CAN LEAVE OUR MODEL AS IS SO RETURN WITH IT")
            return ps
        # Get the current status of balance on this pool, irrespective of
        # a running balance task, ie command line intervention.
        if ps.internal:
            cur_status = balance_status_internal(pool)
        else:
            cur_status = balance_status(pool)
        previous_status = {"status": ps.status, "percent_done": ps.percent_done}
        logger.debug("PREVIOUS_STATUS = {}".format(previous_status))
        logger.debug("CURRENT STATUS = {}".format(cur_status))
        # TODO: future "Balance Cancel" button should call us to have these
        #  values updated in the db table ready for display later.
        # Update cur_state to become preferred proposed state.
        if (
            previous_status["status"] == u"cancelling"
            and cur_status["status"] == u"finished"
        ):
            # override current status as 'cancelled'
            cur_status["status"] = u"cancelled"
            cur_status["message"] = u"cancelled at {}% complete".format(ps.percent_done)
            # and retain prior percent finished value
            cur_status["percent_done"] = ps.percent_done
        elif (
            previous_status["status"] == u"failed"
            and cur_status["status"] == u"finished"
        ):
            # override current status as 'failed'
            cur_status["status"] = u"failed"
            # and retain prior percent finished value
            cur_status["percent_done"] = ps.percent_done
        logger.debug("PROPOSED STATUS = {}".format(cur_status))
        if cur_status == previous_status:
            logger.debug("PROPOSED STATUS = MODEL STATUS: NO UPDATE REQUIRED")
            return ps
        if (
            previous_status["status"] != u"finished"
            and previous_status["status"] != u"cancelled"
        ):
            # update the last pool balance status with current status info.
            logger.debug(
                "UPDATING BALANCE STATUS ID {} WITH {}".format(ps.id, cur_status)
            )
            PoolBalance.objects.filter(id=ps.id).update(**cur_status)
        return ps

    @transaction.atomic
    def post(self, request, pid, command=None):
        pool = self._validate_pool(pid, request)
        if command is not None and command != "status":
            e_msg = "Unknown balance command ({}).".format(command)
            handle_exception(Exception(e_msg), request)

        with self._handle_exception(request):
            ps = self._balance_status(pool)
            if command == "status":
                return Response(PoolBalanceSerializer(ps).data)
            force = request.data.get("force", False)
            if PoolBalance.objects.filter(
                pool=pool, status__regex=r"(started|running)"
            ).exists():
                if force:
                    p = PoolBalance.objects.filter(
                        pool=pool, status__regex=r"(started|running)"
                    ).order_by("-id")[0]
                    p.status = "terminated"
                    p.save(update_fields=["status"])
                else:
                    e_msg = (
                        "A Balance process is already running for pool ({})."
                    ).format(pool.name)
                    handle_exception(Exception(e_msg), request)

            tid = self._balance_start(pool, force=force)
            ps = PoolBalance(pool=pool, tid=tid)
            ps.save()
            return Response(PoolBalanceSerializer(ps).data)
