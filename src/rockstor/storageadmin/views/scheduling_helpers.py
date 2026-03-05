"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import logging

logger = logging.getLogger(__name__)


def is_pending_task(huey_handler, taskid: str, task_name: list[str] | None = None):
    """
    Boolean indicator of task id pending status.
    Returns true if the taskid is pending.
    :param huey_handler:
    :param taskid: Huey task id.
    :param task_name: Optional, helps with logging and filtering.
    :return: boolean
    """
    if task_name is None:
        pending_task_ids = [t.id for t in huey_handler.pending()]
    else:
        logger.debug(f"Searching for pending task name {task_name}.")
        pending_task_ids = [t.id for t in huey_handler.pending() if t.name in task_name]
    if taskid in pending_task_ids:
        logger.debug(f"Pending task id found: id ({taskid}).")
        return True
    logger.debug(f"Pending task id NOT found: id ({taskid}).")
    return False

# Potentially a is_scheduled_task() via huey_handler.scheduled().
# https://huey.readthedocs.io/en/latest/api.html#Huey.scheduled