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

import sys
from system.osi import (run_command, is_mounted)

DOCKER = '/usr/bin/docker'


def main():
    mnt_pt = sys.argv[1]
    if (not is_mounted(mnt_pt)):
        sys.exit('Docker root(%s) not mounted.' % mnt_pt)
    run_command([DOCKER, '-d', '-s', 'btrfs', '-g', mnt_pt])
