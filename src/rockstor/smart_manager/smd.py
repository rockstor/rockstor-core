"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
import time
import sys
from django.conf import settings
from stap_dispatcher import Stap
from cli.rest_util import (api_call, set_token)
from fs.btrfs import device_scan

import logging
logger = logging.getLogger(__name__)


def clean_exit(children):
    logger.error('clean exiting smd')

    for p in children:
        if (not p.is_alive()):
            logger.error('child process: %s not alive. no need to terminate' %
                         p.name)
            continue

        logger.error('terminating the child process: %s' % p.name)
        p.terminate()
        logger.error('waiting for child process: %s to exit' % p.name)
        p.join()
        logger.error('child process: %s terminated successfully' % p.name)
    logger.error('smd out!')
    sys.exit(0)


def main():
    try:
        device_scan()
    except Exception, e:
        e_msg = ('Exception while btrfs device scan: %s. This is a critical '
                 'error. Rockstor cannot be bootstrapped. ' % e.__str__())
        logger.error(e_msg)
        clean_exit([])

    #sometimes the db system takes several seconds to start up.
    #generously retry every 5 seconds, for 120 times, i.e., 10 minutes
    #before giving up.
    num_attempts = 0
    while True:
        try:
            set_token()
            logger.debug('API token set. Moving on to boostrapping...')
            break
        except Exception, e:
            e_msg = ('Exception while setting token: %s' % e.__str__())
            if (num_attempts > 120):
                e_msg = ('Too many retries. Giving up. Rockstor cannot be '
                         'bootstrapped, this is a critical error. %s' % e_msg)
                logger.error(e_msg)
                clean_exit([])

            logger.error(e_msg)
            num_attempts += 1
            time.sleep(5)

    api_url = 'https://localhost/api'
    bootstrap_url = ('%s/commands/bootstrap' % api_url)
    netscan_url = ('%s/network' % api_url)
    try:
        api_call(netscan_url, calltype='get')
        api_call(bootstrap_url, calltype='post')
    except Exception, e:
        logger.error('Unable to bootstrap the machine. Moving on..')
        logger.exception(e)

    live_procs = [Stap(settings.TAP_SERVER), ]
    for p in live_procs:
        p.start()

    while (True):
        for p in live_procs:
            if (not p.is_alive()):
                msg = ('%s is dead. exitcode: %d' % (p.name, p.exitcode))
                logger.error(msg)
                clean_exit(live_procs)
        if (len(live_procs) == 0):
            logger.error('All child processes have exited. I am returning.')
            clean_exit([])
        time.sleep(.5)
