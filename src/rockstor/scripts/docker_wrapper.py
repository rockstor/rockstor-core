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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import sys
from system.osi import run_command
from fs.btrfs import (mount_share, device_scan)
from storageadmin.models import Share

DOCKER = '/usr/bin/docker'


def main():
    mnt_pt = sys.argv[1]
    sname = mnt_pt.split('/')[-1]
    try:
        so = Share.objects.get(name=sname)
        mount_share(so, mnt_pt)
    except Exception, e:
        sys.exit('Failed to mount Docker root(%s). Exception: %s' % (mnt_pt, e.__str__()))
    run_command([DOCKER, 'daemon', '--log-driver=journald', '-s', 'btrfs', '-g', mnt_pt])
