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
import time
from cli.rest_util import api_call
from fs.btrfs import device_scan
from system.osi import run_command
import requests
from django.conf import settings

BASE_DIR = settings.ROOT_DIR
BASE_BIN = '%sbin' % BASE_DIR
QGROUP_CLEAN = '%s/qgroup-clean' % BASE_BIN
QGROUP_MAXOUT_LIMIT = '%s/qgroup-maxout-limit' % BASE_BIN


def main():
    baseurl = 'https://localhost/api'
    bootstrap_url = ('%s/commands/bootstrap' % baseurl)
    netscan_url = ('%s/network' % baseurl)
    device_scan()
    print('BTRFS device scan complete')

    num_attempts = 0
    while True:
        try:
            api_call(netscan_url, calltype='get')
            api_call(bootstrap_url, calltype='post')
            break
        except requests.exceptions.ConnectionError, e:
            if (num_attempts > 15):
                print('Max attempts(15) reached. Connection errors persist. '
                      'Failed to bootstrap. Error: %s' % e.__str__())
                sys.exit(1)
            print('Connection error while bootstrapping. This could be because '
                  'rockstor.service is still starting up. will wait 2 seconds '
                  'and try again.')
            time.sleep(2)
            num_attempts += 1
    print('Bootstrapping complete')

    try:
        print('Running qgroup cleanup. %s' % QGROUP_CLEAN)
        run_command([QGROUP_CLEAN])
    except Exception, e:
        print('Exception while running %s: %s' % (QGROUP_CLEAN, e.__str__()))

    try:
        print('Running qgroup limit maxout. %s' % QGROUP_MAXOUT_LIMIT)
        run_command([QGROUP_MAXOUT_LIMIT])
    except Exception, e:
        print('Exception while running %s: %s' % (QGROUP_MAXOUT_LIMIT, e.__str__()))


if __name__ == '__main__':
    main()
