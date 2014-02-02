
from cli.rest_util import api_call

BASE_URL = 'https://localhost/api/'


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
        logger.info('successfully created replica trail: %s' % url)
        return rt
    except Exception, e:
        logger.error('Failed to create replica trail: %s' % url)
        raise e

def is_snapshot(sname, snap_name, logger):
    try:
        #do a get and see if the snapshot is already created
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        snap_details = api_call(url, save_error=False)
        logger.info('previous snapshot found. details: %s' % snap_details)
        return True
    except Exception, e:
        logger.info('exception while lookup up if snapshot exists at: '
                    '%s' % url)
        logger.exception(e)
        return False

def create_snapshot(sname, snap_name, logger):
    try:
        url = ('%sshares/%s/snapshots/%s' % (BASE_URL, sname, snap_name))
        snap_details = api_call(url, data={'snap_type': 'replication',},
                                calltype='post', save_error=False)
        return logger.info('created snapshot. url: %s. details = %s' %
                           (url, snap_details))
    except Exception, e:
        raise e
