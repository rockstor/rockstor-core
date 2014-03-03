"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

from cli.rest_util import api_call
from storageadmin.exceptions import RockStorAPIException


BASE_URL = 'https://localhost/api/'

def create_trail(pid, logger):
    try:
        url = ('%splugin/backup/trail/policy/%d' % (BASE_URL, pid))
        td = api_call(url, calltype='post', save_error=False)
        logger.info('new policy trail created for policy(%d)' % pid)
        return td
    except Exception,  e:
        logger.error('Failed to create new policy trail for policy(%d)' % pid)
        raise e

def update_trail(tid, data, logger):
    try:
        url = ('%splugin/backup/trail/%d' % (BASE_URL, tid))
        api_call(url, data=data, calltype='put', save_error=False)
        return logger.info('policy trail(%s) status updated to %s' %
                           (url, data['status']))
    except Exception, e:
        logger.error('Failed to update policy trail(%s) status to %s' %
                     (url, data['status']))
        raise e

from system.osi import (is_mounted, run_command)
import os
MOUNT = '/bin/mount'
def mount_source(source_ip, source_share):
    mnt_pt = ('/mnt/backup/%s_%s' % (source_ip, source_share))
    if (is_mounted(mnt_pt)):
        return True
    if (not os.path.isdir(mnt_pt)):
        os.makedirs(mnt_pt)
    cmd = [MOUNT, '%s:%s' % (source_ip, source_share), mnt_pt]
    return run_command(cmd)

def create_snapshot(sname, snap_name, logger):
    try:
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        snap_details = api_call(url, calltype='post', save_error=False)
        return logger.debug('created snapshot. url: %s. details = %s' %
                           (url, snap_details))
    except RockStorAPIException, e:
        return logger.debug('Failed to create snapshot: %s. It may already '
                            'exist. error: %s' % (url, e.detail))
    except Exception:
        raise

def delete_old_snapshots(sname, num_retain, logger):
    url = ('%sshares/%s/snapshots' % (BASE_URL, sname))
    snap_details = api_call(url, save_error=False)
    if (snap_details['count'] > num_retain):
        extra = snap_details['count'] - num_retain
        for i in range(extra):
            if (i >= len(snap_details['results'])):
                return delete_old_snapshots(sname, num_retain, logger)
            snap_name = snap_details['results'][i]['name']
            api_call('%s/%s' % (url, snap_name), calltype='delete',
                     save_error=False)
            logger.debug('deleted snap: %s' % snap_name)
