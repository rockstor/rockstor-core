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


import subprocess


def add_zpool(disks):
    p = subprocess.Popen(
        ["zpool", "destroy", "pool1"], shell=False, stdout=subprocess.PIPE
    )
    p.communicate()
    p = subprocess.Popen(
        ["zpool", "create", "-f", "pool1"] + disks, shell=False, stdout=subprocess.PIPE
    )
    p.communicate()
    return True


def add_zfs_share(pool, share):
    share_fullname = pool + "/" + share
    p = subprocess.Popen(
        ["zfs", "create", share_fullname], shell=False, stdout=subprocess.PIPE
    )
    p.communicate()
    return True
