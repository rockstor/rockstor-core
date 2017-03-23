"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
from datetime import (datetime, timedelta)
import crontabwindow  # load crontabwindow module
from smart_manager.models import (Task, TaskDefinition)
from cli.api_wrapper import APIWrapper
from django.utils.timezone import utc
import logging
logger = logging.getLogger(__name__)


def validate_shutdown_meta(meta):
    if (type(meta) != dict):
        raise Exception('meta must be a dictionary, not %s' % type(meta))
    return meta


def main():
    tid = int(sys.argv[1])
    cwindow = sys.argv[2] if len(sys.argv) > 2 else '*-*-*-*-*-*'
    if (crontabwindow.crontab_range(cwindow)):
        # Performance note: immediately check task execution time/day window
        # range to avoid other calls
        tdo = TaskDefinition.objects.get(id=tid)
        aw = APIWrapper()
        if (tdo.task_type not in ['reboot', 'shutdown', 'suspend']):
            logger.error('task_type(%s) is not a system reboot, '
                         'shutdown or suspend.' % tdo.task_type)
            return
        meta = json.loads(tdo.json_meta)
        validate_shutdown_meta(meta)

        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        schedule = now + timedelta(minutes=3)
        t = Task(task_def=tdo, state='scheduled', start=now, end=schedule)

        try:
            # set default command url before checking if it's a shutdown
            # and if we have an rtc wake up
            url = ('commands/%s' % tdo.task_type)

            # if task_type is shutdown and rtc wake up true
            # parse crontab hour & minute vs rtc hour & minute to state
            # if wake will occur same day or next day, finally update
            # command url adding wake up epoch time
            if (tdo.task_type in ['shutdown', 'suspend'] and meta['wakeup']):
                crontab_fields = tdo.crontab.split()
                crontab_time = (int(crontab_fields[1]) * 60 +
                                int(crontab_fields[0]))
                wakeup_time = meta['rtc_hour'] * 60 + meta['rtc_minute']
                # rtc wake up requires UTC epoch, but users on WebUI set time
                # thinking to localtime, so first we set wake up time,
                # update it if wake up is on next day, finally move it to UTC
                # and get its epoch
                epoch = datetime.now().replace(hour=int(meta['rtc_hour']),
                                               minute=int(meta['rtc_minute']),
                                               second=0, microsecond=0)
                # if wake up < crontab time wake up will run next day
                if (crontab_time > wakeup_time):
                    epoch += timedelta(days=1)

                epoch = epoch.strftime('%s')
                url = ('%s/%s' % (url, epoch))

            aw.api_call(url, data=None, calltype='post', save_error=False)
            logger.debug('System %s scheduled' % tdo.task_type)
            t.state = 'finished'

        except Exception as e:
            t.state = 'failed'
            logger.error('Failed to schedule system %s' % tdo.task_type)
            logger.exception(e)

        finally:
            # t.end = datetime.utcnow().replace(tzinfo=utc)
            t.save()

    else:
        logger.debug('Cron scheduled task not executed because outside '
                     'time/day window ranges')


if __name__ == '__main__':
    # takes two arguments. taskdef object id and crontabwindow.
    main()
