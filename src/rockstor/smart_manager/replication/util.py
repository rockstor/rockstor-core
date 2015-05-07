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
from datetime import datetime
from django.utils.timezone import utc
from cli.rest_util import api_call
from storageadmin.exceptions import RockStorAPIException

BASE_URL = 'https://localhost/api/'


class Bunch(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def get_sender_ip(uuid, logger):
    try:
        url = ('%sappliances' % BASE_URL)
        ad = api_call(url, save_error=False)
        for a in ad['results']:
            if (a['uuid'] == uuid):
                return a['ip']
    except Exception, e:
        logger.error('Failed to get sender ip address')
        raise e


def update_replica_status(rtid, data, logger):
    try:
        url = ('%ssm/replicas/trail/%d' % (BASE_URL, rtid))
        return api_call(url, data=data, calltype='put')
    except Exception, e:
        logger.error('Failed to update replica(%s) status to: %s'
                     % (url, data['status']))
        raise e


def convert_ts(ts):
    if (ts is not None):
        tformat = '%Y-%m-%dT%H:%M:%SZ'
        if (len(ts) > 20):
            tformat = '%Y-%m-%dT%H:%M:%S.%fZ'
        return datetime.strptime(
            ts, tformat).replace(tzinfo=utc)


def get_replicas(logger, enabled=True):
    try:
        query_str = 'page_size=1000'
        if (enabled is True):
            query_str = ('%s&status=enabled' % query_str)
        else:
            query_str = ('%s&status=disabled' % query_str)
        url = ('%ssm/replicas?%s' % (BASE_URL, query_str))
        replicas = api_call(url, save_error=False)
        r = []
        for replica in replicas['results']:
            replica['ts'] = convert_ts(replica['ts'])
            r.append(Bunch(**replica))
        return r
    except Exception, e:
        logger.exception(e)
        raise e


def disable_replica(rid, logger):
    try:
        url = ('%ssm/replicas/%d' % (BASE_URL, rid))
        headers = {'content-type': 'application/json', }
        return api_call(url, data={'enabled': False, }, calltype='put',
                        save_error=False, headers=headers)
    except Exception, e:
        logger.error('Failed to disable replica(%s)' % url)
        raise e


def create_replica_trail(rid, snap_name, logger):
    url = ('%ssm/replicas/trail/replica/%d' % (BASE_URL, rid))
    try:
        rt = api_call(url, data={'snap_name': snap_name, },
                      calltype='post', save_error=False)
        return rt
    except Exception, e:
        logger.error('Failed to create replica trail: %s' % url)
        raise e


def get_replica_trail(rid, logger, limit=2):
    url = ('%ssm/replicas/trail/replica/%d?limit=%d' % (BASE_URL, rid, limit))
    try:
        rt = api_call(url, save_error=False)
        res = []
        for r in rt['results']:
            r['snapshot_created'] = convert_ts(r['snapshot_created'])
            r['snapshot_failed'] = convert_ts(r['snapshot_failed'])
            r['send_pending'] = convert_ts(r['send_pending'])
            r['send_succeeded'] = convert_ts(r['send_succeeded'])
            r['send_failed'] = convert_ts(r['send_failed'])
            r['end_ts'] = convert_ts(r['end_ts'])
            res.append(Bunch(**r))
        return res
    except Exception, e:
        logger.exception(e)
        raise e


def rshare_id(sname, logger):
    try:
        url = ('%ssm/replicas/rshare/%s' % (BASE_URL, sname))
        rshare = api_call(url, save_error=False)
        return rshare['id']
    except Exception:
        raise


def create_rshare(data, logger):
    try:
        url = ('%ssm/replicas/rshare' % BASE_URL)
        rshare = api_call(url, data=data, calltype='post', save_error=False)
        return rshare['id']
    except RockStorAPIException, e:
        if (e.detail == 'Replicashare(%s) already exists.' % data['share']):
            logger.debug(e.detail)
            return rshare_id(data['share'], logger)
        raise e


def create_receive_trail(rid, data, logger):
    url = ('%ssm/replicas/rtrail/rshare/%d' % (BASE_URL, rid))
    try:
        rt = api_call(url, data=data, calltype='post', save_error=False)
        return rt['id']
    except Exception:
        raise


def update_receive_trail(rtid, data, logger):
    url = ('%ssm/replicas/rtrail/%d' % (BASE_URL, rtid))
    try:
        return api_call(url, data=data, calltype='put', save_error=False)
    except Exception:
        logger.error('Failed to update receive trail: %s' % url)
        raise


def prune_trail(url, logger, days=7):
    try:
        data = {'days': days, }
        return api_call(url, data=data, calltype='delete', save_error=False)
    except Exception, e:
        logger.debug('Failed to prune trail for url(%s)' % url)
        logger.exception(e)


def prune_receive_trail(rid, logger):
    url = ('%ssm/replicas/rtrail/rshare/%d' % (BASE_URL, rid))
    return prune_trail(url, logger)


def prune_replica_trail(rid, logger):
    url = ('%ssm/replicas/trail/replica/%d' % (BASE_URL, rid))
    return prune_trail(url, logger)


def is_snapshot(sname, snap_name, logger):
    try:
        #  do a get and see if the snapshot is already created
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        api_call(url, save_error=False)
        return True
    except RockStorAPIException, e:
        if (re.match('Invalid api end point', e.detail) is not None):
            #  it's 404.
            return False
        raise e
    except Exception:
        logger.error('exception while looking up if snapshot exists at: '
                     '%s' % url)
        raise


def create_snapshot(sname, snap_name, logger, snap_type='replication'):
    try:
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        return api_call(url, data={'snap_type': snap_type, }, calltype='post',
                        save_error=False)
    except RockStorAPIException, e:
        if (e.detail == ('Snapshot(%s) already exists for the Share(%s).' %
                         (snap_name, sname))):
            return logger.debug(e.detail)
        raise e


def delete_snapshot(sname, snap_name, logger):
    try:
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        return api_call(url, calltype='delete', save_error=False)
    except RockStorAPIException, e:
        if (e.detail == 'Snapshot(%s) does not exist.' % snap_name):
            return logger.debug(e.detail)
        raise e


def is_share(sname, logger):
    try:
        url = ('%sshares/%s' % (BASE_URL, sname))
        api_call(url, save_error=False)
        return True
    except Exception, e:
        logger.error('Exception while looking up if share exists at: %s'
                     % url)
        logger.exception(e)
        return False


def create_share(sname, pool, logger):
    try:
        url = ('%sshares' % BASE_URL)
        data = {'pool': pool,
                'replica': True,
                'sname': sname, }
        headers = {'content-type': 'application/json', }
        return api_call(url, data=data, calltype='post', headers=headers,
                        save_error=False)
    except RockStorAPIException, e:
        if (e.detail == 'Share(%s) already exists.' % sname):
            return logger.debug(e.detail)
        raise e
