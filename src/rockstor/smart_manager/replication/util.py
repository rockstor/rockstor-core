
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
