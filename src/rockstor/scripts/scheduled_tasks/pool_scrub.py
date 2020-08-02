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

import time
import sys
import json
from datetime import datetime
import crontabwindow  # load crontabwindow module
from smart_manager.models import Task, TaskDefinition
from cli.api_wrapper import APIWrapper
from django.utils.timezone import utc
import logging

logger = logging.getLogger(__name__)

# List of scrub states considered terminal (non running):
TERMINAL_SCRUB_STATES = ["error", "finished", "halted", "cancelled", "conn-reset"]


def update_state(t, pool, aw):
    url = "pools/%s/scrub/status" % pool
    try:
        status = aw.api_call(url, data=None, calltype="post", save_error=False)
        t.state = status["status"]
    except Exception as e:
        logger.error("Failed to get scrub status at %s" % url)
        t.state = "error"
        logger.exception(e)
    finally:
        t.save()
    return t.state


def main():
    tid = int(sys.argv[1])
    cwindow = sys.argv[2] if len(sys.argv) > 2 else "*-*-*-*-*-*"
    if crontabwindow.crontab_range(cwindow):
        # Performance note: immediately check task execution time/day window
        # range to avoid other calls
        tdo = TaskDefinition.objects.get(id=tid)
        if tdo.task_type != "scrub":
            return logger.error("task_type(%s) is not scrub." % tdo.task_type)
        meta = json.loads(tdo.json_meta)
        aw = APIWrapper()

        if Task.objects.filter(task_def=tdo).exists():
            ll = Task.objects.filter(task_def=tdo).order_by("-id")[0]
            if ll.state not in TERMINAL_SCRUB_STATES:
                logger.debug(
                    "Non terminal state(%s) for task(%d). Checking "
                    "again." % (ll.state, tid)
                )
                cur_state = update_state(ll, meta["pool"], aw)
                if cur_state not in TERMINAL_SCRUB_STATES:
                    return logger.debug(
                        "Non terminal state(%s) for task(%d). "
                        "A new task will not be run." % (cur_state, tid)
                    )

        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        t = Task(task_def=tdo, state="started", start=now)
        url = "pools/%s/scrub" % meta["pool"]
        try:
            aw.api_call(url, data=None, calltype="post", save_error=False)
            logger.debug("Started scrub at %s" % url)
            t.state = "running"
        except Exception as e:
            logger.error("Failed to start scrub at %s" % url)
            t.state = "error"
            logger.exception(e)
        finally:
            t.save()

        while True:
            cur_state = update_state(t, meta["pool"], aw)
            if cur_state in TERMINAL_SCRUB_STATES:
                logger.debug("task(%d) finished with state(%s)." % (tid, cur_state))
                t.end = datetime.utcnow().replace(tzinfo=utc)
                t.save()
                break
            logger.debug(
                "pending state(%s) for scrub task(%d). Will check "
                "again in 60 seconds." % (cur_state, tid)
            )
            time.sleep(60)
    else:
        logger.debug(
            "Cron scheduled task not executed because outside time/day window ranges"
        )


if __name__ == "__main__":
    # takes two arguments. taskdef object id and crontabwindow.
    main()
