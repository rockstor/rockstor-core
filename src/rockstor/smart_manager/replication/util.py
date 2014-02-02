
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
