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

import os.path as path
import re
import shutil
import sys


from django.conf import settings
from tempfile import mkstemp

from system.osi import run_command


SETTINGS_FILE = path.join(settings.ROOT_DIR, "src/rockstor/settings.py")
SUPERCTL_BIN = path.join(settings.ROOT_DIR, "bin/supervisorctl")


def update_settings(debug_flag):
    fh, npath = mkstemp()
    with open(SETTINGS_FILE) as sfo, open(npath, "w") as tfo:
        for line in sfo.readlines():
            if re.match("DEBUG = ", line):
                line = "DEBUG = %s\n" % debug_flag
            tfo.write(line)
    shutil.move(npath, SETTINGS_FILE)


def display_current():
    print("currently debug flag is %s" % settings.DEBUG)


def main():
    hmsg = "Usage: %s [-h] [ON|OFF]" % sys.argv[0]
    if len(sys.argv) > 1:
        log_level = sys.argv[1].upper()
        if log_level not in ("ON", "OFF"):
            sys.exit(hmsg)

        debug_flag = False
        if log_level == "ON":
            debug_flag = True

        if debug_flag == settings.DEBUG:
            print("DEBUG flag already set to %s" % debug_flag)
        else:
            update_settings(debug_flag)
            run_command([SUPERCTL_BIN, "restart", "gunicorn"])
            print("DEBUG flag is now set to %s" % debug_flag)
    else:
        display_current()
        sys.exit(hmsg)
