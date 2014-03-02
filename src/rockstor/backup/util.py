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

import re
from cli.rest_util import api_call
from storageadmin.exceptions import RockStorAPIException

BASE_URL = 'https://localhost/api/'

def create_trail(pid, logger):
    try:
        url = ('%splugin/backup/trail/policy/%d' % (BASE_URL, pid))
        td = api_call(url, calltype='post', save_error=False)
        logger.info('new policy trail created for policy(%d)' % pid)
        return td['id']
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

