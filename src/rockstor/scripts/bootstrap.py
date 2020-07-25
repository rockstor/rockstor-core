"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

import sys
import time
from cli.api_wrapper import APIWrapper
from fs.btrfs import device_scan
from system.osi import run_command
from django.conf import settings
from storageadmin.models import Setup


BASE_DIR = settings.ROOT_DIR
BASE_BIN = "%sbin" % BASE_DIR
QGROUP_CLEAN = "%s/qgroup-clean" % BASE_BIN
QGROUP_MAXOUT_LIMIT = "%s/qgroup-maxout-limit" % BASE_BIN


def main():

    try:
        device_scan()
    except Exception as e:
        print(
            "BTRFS device scan failed due to an exception. This indicates "
            "a serious problem. Aborting. Exception: %s" % e.__str__()
        )
        sys.exit(1)
    print("BTRFS device scan complete")

    # if the appliance is not setup, there's nothing more to do beyond
    # device scan
    setup = Setup.objects.first()
    if setup is None or setup.setup_user is False:
        print("Appliance is not yet setup.")
        return

    num_attempts = 0
    while True:
        try:
            aw = APIWrapper()
            time.sleep(2)
            aw.api_call("network")
            aw.api_call("commands/bootstrap", calltype="post")
            break
        except Exception as e:
            # Retry on every exception, primarily because of django-oauth
            # related code behaving unpredictably while setting
            # tokens. Retrying is a decent workaround for now(11302015).
            if num_attempts > 15:
                print(
                    "Max attempts(15) reached. Connection errors persist. "
                    "Failed to bootstrap. Error: %s" % e.__str__()
                )
                sys.exit(1)
            print(
                "Exception occured while bootstrapping. This could be "
                "because rockstor.service is still starting up. will "
                "wait 2 seconds and try again. Exception: %s" % e.__str__()
            )
            time.sleep(2)
            num_attempts += 1
    print("Bootstrapping complete")

    try:
        print("Running qgroup cleanup. %s" % QGROUP_CLEAN)
        run_command([QGROUP_CLEAN])
    except Exception as e:
        print("Exception while running %s: %s" % (QGROUP_CLEAN, e.__str__()))

    try:
        print("Running qgroup limit maxout. %s" % QGROUP_MAXOUT_LIMIT)
        run_command([QGROUP_MAXOUT_LIMIT])
    except Exception as e:
        print("Exception while running %s: %s" % (QGROUP_MAXOUT_LIMIT, e.__str__()))


if __name__ == "__main__":
    main()
