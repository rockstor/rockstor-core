"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
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
from storageadmin.models import Setup, OauthApp


BASE_DIR = settings.ROOT_DIR
BASE_BIN = "{}.venv/bin".format(BASE_DIR)
QGROUP_CLEAN = "{}/qgroup-clean".format(BASE_BIN)
QGROUP_MAXOUT_LIMIT = "{}/qgroup-maxout-limit".format(BASE_BIN)


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

    try:
        print("Refreshing client_secret for oauth2_provider app from settings")
        app = OauthApp.objects.get(name=settings.OAUTH_INTERNAL_APP)
        app.application.client_secret = settings.CLIENT_SECRET
        app.application.save()
        app.save()
    except Exception as e:
        print(
            f"Failed client_secret update. Oauth internal App ({settings.OAUTH_INTERNAL_APP})"
            f"Exception: {e.__str__()}"
        )
    print("Oauth internal App client_secret updated.")

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
            if num_attempts > 10:
                print(
                    "Max attempts(10) reached. Connection errors persist. "
                    "Failed to bootstrap. Error: %s" % e.__str__()
                )
                sys.exit(1)
            print(
                "Exception occurred while bootstrapping. This could be "
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
