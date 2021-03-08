"""
Copyright (c) 2012-2021 RockStor, Inc. <http://rockstor.com>
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
from smart_manager.views.ztask_helpers import restart_rockstor
from storageadmin.views.rockon_helpers import start, stop, update, install, uninstall
from storageadmin.views.config_backup import restore_config, restore_rockons

import logging

logger = logging.getLogger(__name__)

# HUEY SIGNAL CALLBACKS
# Executed upon the indicated signal.
# See: https://huey.readthedocs.io/en/latest/signals.html#signals


@HUEY.signal(SIGNAL_EXECUTING)
def task_signal_executing(signal, task):
    # global huey
    # HUEY.storage.put_data("executing-{}".format(task.name), 1)
    logger.info("Now executing Huey task [{}], id: {}.".format(task.name, task.id))


@HUEY.signal(SIGNAL_COMPLETE)
def task_completed(signal, task):
    # Task completed OK.
    # Could do clean if task name begins with rockon_helper:
    # removing all key,value pairs where value = task.id
    logger.info("Task [{}] completed OK".format(task.name))
    if task.name == "start_balance" or task.name == "start_resize_pool":
        logger.info("Updating end_time accordingly")
        PoolBalance.objects.filter(tid=task.id).update(end_time=timezone.now())


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
    message = "Task [{}] failed, Task ID: {} Args: {}, Kwargs: {}, Exception{}".format(
        task.name, task.id, task.args, task.kwargs, exc
    )
    logger.error(message)
    # mail_admins(subject, message)
