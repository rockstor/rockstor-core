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
from system.osi import run_command
from fs.btrfs import mount_share
from storageadmin.models import Share

DOCKERD = "/usr/bin/dockerd"

ROCKSTOR_DOCKER_OPTS = [
    "--log-driver=journald",
    "--storage-driver",
    "btrfs",
    "--storage-opt",
    "btrfs.min_space=1G",
]


def main():
    # We expect the last element of our argument list to be the mount point as
    # docker_service.py formats it that way.:
    mnt_pt = sys.argv[-1]
    # N.B. sys.argv[0] is name of script itself and always present.
    system_docker_opts = []
    if len(sys.argv) > 2:
        # We have at least 1 additional argument passed so extract it/them ie:
        # [script-name, additional-arg, mount-point]
        # we extract additional-arg (or it's plural counterpart) as a list.
        system_docker_opts = sys.argv[1:-1]
    sname = mnt_pt.split("/")[-1]
    try:
        so = Share.objects.get(name=sname)
        mount_share(so, mnt_pt)
    except Exception as e:
        sys.exit(
            "Failed to mount Docker root(%s). Exception: %s" % (mnt_pt, e.__str__())
        )
    cmd = (
        [DOCKERD] + ROCKSTOR_DOCKER_OPTS + system_docker_opts + ["--data-root", mnt_pt]
    )
    run_command(cmd)
