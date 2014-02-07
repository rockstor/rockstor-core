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

def get_sender_ip(uuid, logger):
    try:
        url = ('%sappliances' % BASE_URL)
        ad = api_call(url, save_error=False)
        logger.debug('ad: %s' % ad)
        for a in ad['results']:
            if (a['uuid'] == uuid):
                return a['ip']
    except Exception, e:
        logger.error('Failed to get sender ip address')
        raise e

def update_replica_status(rid, data, logger):
    try:
        url = ('%ssm/replicas/trail/%d' % (BASE_URL, rid))
        api_call(url, data=data, calltype='put', save_error=False)
        return logger.info('replica(%s) status updated to %s' %
                           (url, data['status']))
    except Exception, e:
        logger.error('Failed to update replica(%s) status to: %s'
                     % (url, data['status']))
        raise e

def disable_replica(rid, logger):
    try:
        url = ('%s/sm/replicas/%d' % (BASE_URL, rid))
        api_call(url, data={'enabled': False,}, calltype='put',
                 save_error=False)
        return logger.info('Replica(%s) is disabled' % url)
    except Exception, e:
        logger.error('Failed to disable replica(%s)' % url)
        raise e

def create_replica_trail(rid, snap_name, logger):
    url = ('%ssm/replicas/trail/replica/%d' % (BASE_URL, rid))
    try:
        rt = api_call(url, data={'snap_name': snap_name,},
                      calltype='post', save_error=False)
        logger.debug('Created replica trail: %s' % url)
        return rt
    except Exception, e:
        logger.error('Failed to create replica trail: %s' % url)
        raise e

def rshare_id(sname, logger):
    try:
        url = ('%ssm/replicas/rshare/%s' % (BASE_URL, sname))
        rshare = api_call(url, save_error=False)
        logger.debug('rshare exists: %s' % rshare)
        return rshare['id']
    except Exception:
        raise

def create_rshare(data, logger):
    try:
        url = ('%ssm/replicas/rshare' % BASE_URL)
        rshare = api_call(url, data=data, calltype='post', save_error=False)
        logger.debug('ReplicaShare: %s created.' % rshare)
        return rshare['id']
    except RockStorAPIException, e:
        return logger.debug('Failed to create rshare: %s. It may already'
                            ' exists. error: %s' % (url, e.detail))
    except Exception:
        logger.error('Failed to create Replicashare: %s' % data)
        raise

def create_receive_trail(rid, data, logger):
    url = ('%s/sm/replicas/rtrail/rshare/%d' % (BASE_URL, rid))
    try:
        rt = api_call(url, data=data, calltype='post', save_error=False)
        logger.debug('Created receive trail: %s' % rt)
        return rt['id']
    except Exception:
        logger.error('Failed to create receive trail: %s' % url)
        raise

def update_receive_trail(rtid, data, logger):
    url = ('%s/sm/replicas/rtrail/%d' % (BASE_URL, rtid))
    try:
        rt = api_call(url, data=data, calltype='put', save_error=False)
        return logger.debug('Updated receive trail: %s' % rt)
    except Exception:
        logger.error('Failed to update receive trail: %s' % url)
        raise

def is_snapshot(sname, snap_name, logger):
    try:
        #do a get and see if the snapshot is already created
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        snap_details = api_call(url, save_error=False)
        logger.info('previous snapshot found. details: %s' % snap_details)
        return True
    except RockStorAPIException, e:
        if (re.match('Invalid api end point', e.detail) is not None):
            #it's 404.
            return False
        raise e
    except Exception:
        logger.error('exception while looking up if snapshot exists at: '
                    '%s' % url)
        raise

def create_snapshot(sname, snap_name, logger, snap_type='replication'):
    try:
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        snap_details = api_call(url, data={'snap_type': snap_type,},
                                calltype='post', save_error=False)
        return logger.debug('created snapshot. url: %s. details = %s' %
                           (url, snap_details))
    except RockStorAPIException, e:
        return logger.debug('Failed to create snapshot: %s. It may already '
                            'exist. error: %s' % (url, e.detail))
    except Exception:
        raise

def is_share(sname, logger):
    try:
        url = ('%s/shares/%s' % (BASE_URL, sname))
        share_details = api_call(url, save_error=False)
        logger.debug('Share exists: %s' % share_details)
        return True
    except Exception, e:
        logger.error('Exception while looking up if share exists at: %s'
                     % url)
        logger.exception(e)
        return False

def create_share(sname, pool, logger):
    try:
        url = ('%sshares' % BASE_URL)
        #@todo: make share size same as pool size
        #make it default = 2TB = 2147483648KB
        data = {'pool': pool,
                'size': 2147483648,
                'replica': True,
                'sname': sname,}
        headers = {'content-type': 'application/json',}
        res = api_call(url, data=data, calltype='post', headers=headers)
        return logger.debug('Created share: %s' % res)
    except RockStorAPIException, e:
        return logger.debug('Failed to create share: %s. It may already '
                            'exist. error: %s' % (sname, e.detail))
    except Exception:
        raise
