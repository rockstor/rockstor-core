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
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from huey.contrib.djhuey import HUEY
from storageadmin.util import handle_exception
from storageadmin.serializers import PoolBalanceSerializer
from storageadmin.models import Pool, PoolBalance
import rest_framework_custom as rfc
from fs.btrfs import balance_status_all
from pool import PoolMixin

import logging

logger = logging.getLogger(__name__)


def balance_status_filter(prior_status, live_status):
    """
    Perform contextual modification on live_status given prior_status content.
    I.e. our live_status may be finished, but our prior status was failed.
    or our live_status is finished but our prior status was cancelling.
    For these examples we preserve the prior status to not lose information.
    E.g. a finished balance that was previously recorded as caneclling has its
    live_status updated to 'cancelled'.
    :param prior_status: status dict from last PoolBalance instance
    :param live_status: status dict form balance_status_internal() or balance_status()
    :return: The proposed state (edited live state).
    The proposed status is intended for Web-UI / api consumption.
    """
    logger.debug("PRIOR_STATUS = {}".format(prior_status))
    logger.debug("LIVE_STATUS = {}".format(live_status))
    if live_status["status"] == u"finished":
        if prior_status["status"] == u"cancelling":
            # Override live status as 'cancelled' and add message with prior % complete,
            logger.debug("Overide 'finished' as 'cancelled'")
            live_status["status"] = u"cancelled"
            live_status["message"] = u"cancelled at {}% complete".format(
                prior_status["percent_done"]
            )
            live_status["percent_done"] = prior_status["percent_done"]
        elif prior_status["status"] == u"failed":
            logger.debug("Overide 'finished' as 'failed'")
            # Override live status as 'failed', preserving the failed % complete.
            live_status["status"] = u"failed"
            live_status["percent_done"] = prior_status["percent_done"]
    logger.debug("PROPOSED STATUS = {}".format(live_status))
    return live_status


def is_pending_balance_task(Huey_handle, tid):
    """
    Boolean indicator of task id pending status.
    :param Huey_handle: Huey instance.
    :param tid: task_id
    :return: Boolean, true if tid is pending
    """
    pending_balance_task_ids = [
        task.id
        for task in Huey_handle.pending()
        if task.name in ["start_balance", "start_resize_pool"]
    ]
    if tid in pending_balance_task_ids:
        logger.debug("Pending task id found ({})".format(tid))
        return True
    return False


class PoolBalanceView(PoolMixin, rfc.GenericView):
    serializer_class = PoolBalanceSerializer

    @staticmethod
    def _validate_pool(pid, request):
        try:
            return Pool.objects.get(id=pid)
        except ObjectDoesNotExist as e:
            e_msg = "Pool ({}) does not exist.".format(pid)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            pool = self._validate_pool(self.kwargs["pid"], self.request)
            self._balance_status(pool)
            return PoolBalance.objects.filter(pool=pool).order_by("start_time")

    @staticmethod
    @transaction.atomic
    def _balance_status(pool):
        """
        Retrieves and updates the last relevant PoolBalance entry for the given Pool.
        Assuming that entry, if it exists, has not already been marked as:
        'finished', 'cancelled', or 'failed' i.e. terminal end states.
        N.B. Works along-side Huey task events in the case of non cli initiated balance.
        Intended primarily for Web-UI (Huey task run) balance event monitoring.
        But when an ongoing balance is sensed, and there are no associated (via tid)
        pending or ongoing Huey tasks a new PoolBalance entry is created with tid=None.
        N.B. Future "Balance Cancel" button should call us to update balance status.
        :param pool: Pool db object
        :return: Empty response if no PoolBalance entry and no cli balance is detected.
        Other-wise an updated or freshly created PoolBalance is returned.
        """
        bstatus = balance_status_all(pool)
        balance_active = bstatus.active
        internal = bstatus.internal
        live_status = bstatus.status
        return_empty = False  # Default to empty response
        msg_new_cli = "Suspected cli balance detected. New entry created."
        try:
            ps = PoolBalance.objects.filter(pool=pool).latest()
        except ObjectDoesNotExist as e:
            if not balance_active:  # No past record and no ongoing balance.
                return_empty = True
                return Response()
            else:  # Active balance but no existing PoolBalance record for this Pool.
                # Web-UI initiated balances always have an existing PoolBalance record.
                ps = PoolBalance(
                    pool=pool, internal=internal, message=msg_new_cli, **live_status
                )
                ps.save()
                logger.debug(
                    "++++++ "
                    + msg_new_cli
                    + " Pool name {}, PoolBalance ID {}.".format(pool.name, ps.id)
                )
                return ps
        else:  # We have a prior entry, check for Huey task id and matching task:
            logger.debug(
                "Latest PoolBalance: TID = {} Pool ({}) End_time ({})".format(
                    ps.tid, pool.name, ps.end_time
                )
            )
            if ps.tid is not None:  # latest balance record has Huey task id (tid)
                hi = HUEY
                task_result = None
                try:
                    # https://huey.readthedocs.io/en/latest/api.html#Huey.get
                    # The following does a destructive read unless preserve=True.
                    # This read will also throw the TaskException which is our interest here.
                    # https://huey.readthedocs.io/en/latest/api.html#Huey.result
                    # https://github.com/coleifer/huey/issues/449#issuecomment-535028271
                    # Syntax requires huey 2.1.3
                    task_result = hi.result(ps.tid)
                except TaskException as e:
                    ps.status = "failed"
                    # N.B. metadata indexes: retries, traceback, task_id, error
                    ps.message = e.metadata.get("traceback", "missing 'traceback' key")
                    # TODO: Consider a huey signal to triggered the addition of end time
                    #  currently no SIGNAL_ERROR is seen to be active (see task.py)
                    ps.save(update_fields=["status", "message"])
                    return ps
                else:  # task has not failed
                    logger.debug("Matching task result={}".format(task_result))
                    if task_result is None:  # Check for pending task.
                        # Pending balance tasks. Executing tasks are no longer pending.
                        # There is a 1 to 3 second 'pending" status for Huey tasks.
                        if ps.status == u"started" and is_pending_balance_task(
                            hi, ps.tid
                        ):
                            # Model default - new balance record has status "started".
                            # Preserve pending/"started" state until we know better.
                            logger.debug(
                                "DB STATUS STARTED + PENDING HUEY TASK - RETURN DB ENTRY"
                            )
                            return ps
            else:  # Latest balance record is cli generated
                pass
            # irrespective of Huey or cli run, we update and return what we now have:
            prior_status = {"status": ps.status, "percent_done": ps.percent_done}
            if live_status == prior_status:
                logger.debug("PROPOSED STATUS = MODEL STATUS: NO UPDATE REQUIRED")
                return ps
            proposed_status = balance_status_filter(prior_status, live_status)
            # We don't want to update finished or cancelled entries.
            if prior_status["status"] in [u"finished", u"cancelled"]:
                if live_status["status"] not in [u"unknown", u"finished"]:
                    # Create new PoolBalance record:
                    ps = PoolBalance(pool=pool, message=msg_new_cli, **proposed_status)
                    ps.save()
                    logger.debug(
                        "++++++ "
                        + msg_new_cli
                        + " Pool name {}, PoolBalance ID {}.".format(pool.name, ps.id)
                    )
            else:  # prior_status is neither finished nor cancelled, so we update it.
                logger.debug(
                    "UPDATING RECORD ID {} WITH {}.".format(ps.id, proposed_status)
                )
                PoolBalance.objects.filter(id=ps.id).update(**proposed_status)
                ps.refresh_from_db()
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
                if isinstance(ps, PoolBalance):
                    logger.debug(
                        "====== Returning PoolBalance serialized - status command. ======"
                    )
                    return Response(PoolBalanceSerializer(ps).data)
                else:
                    logger.debug(
                        "====== Returning Empty as no PoolBalance - status command. ======"
                    )
                    return Response(status=status.HTTP_204_NO_CONTENT)
            force = request.data.get("force", False)
            if PoolBalance.objects.filter(
                pool=pool, status__regex=r"(started|running)"
            ).exists():
                if force:
                    p = PoolBalance.objects.filter(
                        pool=pool, status__regex=r"(started|running)"
                    ).latest()
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
