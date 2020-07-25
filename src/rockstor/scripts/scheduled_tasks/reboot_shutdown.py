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
import sys
import json
from datetime import datetime, timedelta
import crontabwindow  # load crontabwindow module
from smart_manager.models import Task, TaskDefinition
from cli.api_wrapper import APIWrapper
from django.utils.timezone import utc
from system.osi import is_network_device_responding
from csv import reader as csv_reader
import re
import time

import logging

logger = logging.getLogger(__name__)


def validate_shutdown_meta(meta):
    if type(meta) != dict:
        raise Exception("meta must be a dictionary, not %s" % type(meta))
    return meta


def all_devices_offline(addresses):
    for address in addresses:
        logger.debug("Pinging {}...".format(address))
        if is_network_device_responding(address):
            return False
    return True


def run_conditions_met(meta):
    if meta["ping_scan"]:
        address_parser = csv_reader([meta["ping_scan_addresses"]], delimiter=",")
        addresses = list(address_parser)

        if len(addresses) > 0:
            addresses = addresses[0]
            # remove all non word characters except from '.' and '-' to prevent
            # the execution of shell code when running the ping command
            addresses = [re.sub(r"[^\w\.-]", "", address) for address in addresses]
            interval = (
                float(meta["ping_scan_interval"])
                if float(meta["ping_scan_interval"]) >= 5
                else 5.0
            )
            iterations = (
                int(meta["ping_scan_iterations"])
                if int(meta["ping_scan_iterations"]) >= 1
                else 1
            )

            logger.debug("Pinging devices: {}".format(addresses))
            for i in range(iterations):
                if not all_devices_offline(addresses):
                    logger.debug("At least one pinged device is still online")
                    return False
                else:
                    # don't sleep after last scan
                    if (i + 1) >= iterations:
                        break
                    logger.debug(
                        "No device answered, trying again in {} seconds.".format(
                            interval
                        )
                    )
                    # simply sleep as done in pool_scrub.py
                    time.sleep(interval)

            logger.debug("All pinged devices are offline")

    return True


def main():
    tid = int(sys.argv[1])
    cwindow = sys.argv[2] if len(sys.argv) > 2 else "*-*-*-*-*-*"
    if crontabwindow.crontab_range(cwindow):
        # Performance note: immediately check task execution time/day window
        # range to avoid other calls
        tdo = TaskDefinition.objects.get(id=tid)
        aw = APIWrapper()
        if tdo.task_type not in ["reboot", "shutdown", "suspend"]:
            logger.error(
                "task_type(%s) is not a system reboot, "
                "shutdown or suspend." % tdo.task_type
            )
            return
        meta = json.loads(tdo.json_meta)
        validate_shutdown_meta(meta)

        if not run_conditions_met(meta):
            logger.debug(
                "Cron scheduled task not executed because the run conditions have not been met"
            )
            return

        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        schedule = now + timedelta(minutes=3)
        t = Task(task_def=tdo, state="scheduled", start=now, end=schedule)

        try:
            # set default command url before checking if it's a shutdown
            # and if we have an rtc wake up
            url = "commands/%s" % tdo.task_type

            # if task_type is shutdown and rtc wake up true
            # parse crontab hour & minute vs rtc hour & minute to state
            # if wake will occur same day or next day, finally update
            # command url adding wake up epoch time
            if tdo.task_type in ["shutdown", "suspend"] and meta["wakeup"]:
                crontab_fields = tdo.crontab.split()
                crontab_time = int(crontab_fields[1]) * 60 + int(crontab_fields[0])
                wakeup_time = meta["rtc_hour"] * 60 + meta["rtc_minute"]
                # rtc wake up requires UTC epoch, but users on WebUI set time
                # thinking to localtime, so first we set wake up time,
                # update it if wake up is on next day, finally move it to UTC
                # and get its epoch
                epoch = datetime.now().replace(
                    hour=int(meta["rtc_hour"]),
                    minute=int(meta["rtc_minute"]),
                    second=0,
                    microsecond=0,
                )
                # if wake up < crontab time wake up will run next day
                if crontab_time > wakeup_time:
                    epoch += timedelta(days=1)

                epoch = epoch.strftime("%s")
                url = "%s/%s" % (url, epoch)

            aw.api_call(url, data=None, calltype="post", save_error=False)
            logger.debug("System %s scheduled" % tdo.task_type)
            t.state = "finished"

        except Exception as e:
            t.state = "failed"
            logger.error("Failed to schedule system %s" % tdo.task_type)
            logger.exception(e)

        finally:
            # t.end = datetime.utcnow().replace(tzinfo=utc)
            t.save()

    else:
        logger.debug(
            "Cron scheduled task not executed because outside time/day window ranges"
        )


if __name__ == "__main__":
    # takes two arguments. taskdef object id and crontabwindow.
    main()
