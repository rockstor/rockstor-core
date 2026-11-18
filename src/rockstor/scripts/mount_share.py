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
from settings import MNT_PT
from storageadmin.models import Share
from fs import btrfs


def mount_share():
    try:
        name = sys.argv[1]
    except IndexError:
        sys.exit(f"{sys.argv[0]} <share_name>")

    try:
        so = Share.objects.get(name=name)
    except Share.DoesNotExist:
        sys.exit(f"Share({name}) does not exist")

    mnt_pt = f"{MNT_PT}{so.name}"
    btrfs.mount_share(so, mnt_pt)
