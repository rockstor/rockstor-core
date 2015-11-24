"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import sys
import json
from datetime import datetime
from storageadmin.models import (Share, Snapshot)
from smart_manager.models import (Task, TaskDefinition)
from cli.api_wrapper import APIWrapper
from django.utils.timezone import utc
from django.conf import settings
import logging
logger = logging.getLogger(__name__)


def validate_snap_meta(meta):
    if (type(meta) != dict):
        raise Exception('meta must be a dictionary, not %s' % type(meta))
    if ('prefix' not in meta):
        raise Exception('prefix missing from meta. %s' % meta)
    if ('share' not in meta):
        raise Exception('share missing from meta. %s' % meta)
    if (not Share.objects.filter(name=meta['share']).exists()):
        raise Exception('Non-existent Share(%s) in meta. %s' %
                        (meta['share'], meta))
    if ('max_count' not in meta):
        raise Exception('max_count missing from meta. %s' % meta)
    try:
        max_count = int(float(meta['max_count']))
    except:
        raise Exception('max_count is not an integer. %s' % meta)
    if (max_count < 1):
        raise Exception('max_count must atleast be 1, not %d' % max_count)
    if ('visible' not in meta or type(meta['visible']) != bool):
        meta['visible'] = False
    return meta

def main():
    tid = int(sys.argv[1])
    tdo = TaskDefinition.objects.get(id=tid)
    stype = 'task_scheduler'
    aw = APIWrapper()
    if (tdo.task_type != 'snapshot'):
        logger.error('task_type(%s) is not snapshot.' % tdo.task_type)
        return
    meta = json.loads(tdo.json_meta)
    validate_snap_meta(meta)

    max_count = int(float(meta['max_count']))
    share = Share.objects.get(name=meta['share'])
    prefix = ('%s_' % meta['prefix'])
    snapshots = Snapshot.objects.filter(share=share, snap_type=stype,
                                        name__startswith=prefix).order_by('-id')
    if (len(snapshots) > max_count):
        for snap in snapshots[max_count:]:
            url = ('shares/%s/snapshots/%s' % (meta['share'], snap.name))
            try:
                aw.api_call(url, data=None, calltype='delete', save_error=False)
                logger.debug('deleted old snapshot at %s' % url)
            except Exception, e:
                logger.error('Failed to delete old snapshot at %s' % url)
                logger.exception(e)
                return

    now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
    t = Task(task_def=tdo, state='started', start=now)
    try:
        name = ('%s_%s' % (meta['prefix'], datetime.now().strftime(settings.SNAP_TS_FORMAT)))
        url = ('shares/%s/snapshots/%s' % (meta['share'], name))
        data = {'snap_type': stype,
                'uvisible': meta['visible'], }
        headers = {'content-type': 'application/json'}
        aw.api_call(url, data=data, calltype='post', headers=headers, save_error=False)
        logger.debug('created snapshot at %s' % url)
        t.state = 'finished'
    except Exception, e:
        logger.error('Failed to create snapshot at %s' % url)
        t.state = 'error'
        logger.exception(e)
    finally:
        t.end = datetime.utcnow().replace(tzinfo=utc)
        t.save()

if __name__ == '__main__':
    #takes one argument. taskdef object id.
    main()
