"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

# This file enables auto-discovery of Huey tasks.
# https://huey.readthedocs.io/en/latest/django.html?highlight=auto#django
# All Huey decorated functions should either be in this file or included by this file.
from huey.contrib.djhuey import HUEY
from django.utils import timezone
from huey.signals import (
    SIGNAL_EXECUTING,
    SIGNAL_COMPLETE,
    SIGNAL_ERROR,
    SIGNAL_REVOKED,
    SIGNAL_LOCKED,
)
from storageadmin.models import PoolBalance

# An alternative import method:
# from huey.contrib import djhuey as huey

# N.B. these imports are required for task auto-discovery, even if not used here-in.
from fs.btrfs import start_resize_pool, start_balance
from smart_manager.views.scheduling_helpers import restart_rockstor
from storageadmin.views.rockon_helpers import start, stop, update, install, uninstall
from storageadmin.views.config_backup import restore_config, restore_rockons
from storageadmin.views.pool_balance import update_end_time
from storageadmin.views.share_acl import clear_taskid

import logging

logger = logging.getLogger(__name__)

# HUEY SIGNAL CALLBACKS
# Executed upon the indicated signal.
# See: https://huey.readthedocs.io/en/latest/signals.html#signals


@HUEY.signal(SIGNAL_EXECUTING)
def task_signal_executing(signal, task):
    # global huey
    # HUEY.storage.put_data("executing-{}".format(task.name), 1)
    logger.info(f"-STARTING Huey task: [{task.name}], id: {task.id}.")



@HUEY.signal(SIGNAL_COMPLETE)
def task_completed(signal, task):
    # Task completed OK.
    # Could do clean if task name begins with rockon_helper:
    # removing all key,value pairs where value = task.id
    logger.info(f"COMPLETED Huey task: [{task.name}], id: {task.id}.")
    time_now = timezone.now()
    match task.name:
        case "start_balance" | "start_resize_pool":
            logger.info(f"Updating end_time accordingly to {time_now}")
            # We now abstract db end_time update to an appropriately decorated task.
            try:
                task_result_handle = update_end_time(task.id, time_now)
                db_update_end_time_task_id = task_result_handle.id
                logger.debug(
                    f"Initiated Huey db_task id ({db_update_end_time_task_id}) to update end_time from task_completed() id ({task.id})"
                )
            except Exception as e:
                logger.error(
                    f"Exception while updating PoolBalance end_time from Huey.signal: {e.__str__()}"
                )
        case "chown":
            pass
        case "chmod":
            pass
        case "acl_change_manager":
            logger.info(f"--- Initiating task to clear DB Share.taskid = {task.id}.")
            clear_taskid(task.id)
        case "clear_taskid":
            pass
        case _:
            logger.error(f"No known task_completed jobs to execute for {task.name}.")


@HUEY.signal(SIGNAL_ERROR, SIGNAL_LOCKED)
def task_failed(signal, task, exc=None):
    # FROM: https://huey.readthedocs.io/en/latest/api.html#Huey.signal
    # Do something in response to the "ERROR" OR "SIGNAL_LOCKED" signals.
    # Note that the "ERROR" signal includes a third parameter,
    # which is the unhandled exception that was raised by the task.
    # Since this parameter is not sent with the "LOCKED" signal, we
    # provide a default of ``exc=None``.
    #
    # Possibly stash error message if it exists.
    # Only log the final failure, once all retries are exhausted.
    if task.retries > 0:
        return
    message = f"Task [{task.name}], id: {task.id} failed, Args: {task.args}, Kwargs: {task.kwargs}, Exception{exc}"
    logger.error(message)
    # mail_admins(subject, message)
    if task.name == "start_balance" or task.name == "start_resize_pool":
        logger.info("Updating status accordingly")
        PoolBalance.objects.filter(tid=task.id).latest().update(status="failed")
    if task.name == "acl_change_manager":
        logger.info(f"--- Initiating task to clear DB Share.taskid = {task.id}.")
        clear_taskid(task.id)
