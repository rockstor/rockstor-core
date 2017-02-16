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
from django.conf import settings
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
        if (tdo.task_type not in ['reboot', 'shutdown']):
            logger.error('task_type(%s) is not a system reboot '
                         'or shutdown.' % tdo.task_type)
            return
        meta = json.loads(tdo.json_meta)
        validate_shutdown_meta(meta)

        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        schedule = now + timedelta(minutes = 2)
        t = Task(task_def=tdo, state='scheduled', start=now, end=schedule)
        try:
            url = ('commands/%s/2' % tdo.task_type)
            aw.api_call(url, data=None, calltype='post', save_error=False)
            logger.debug('System %s in 2 minutes' % tdo.task_type)
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
