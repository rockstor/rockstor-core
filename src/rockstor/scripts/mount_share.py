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
from django.conf import settings
from storageadmin.models import Share
from fs import btrfs


def mount_share():
    try:
        name = sys.argv[1]
    except IndexError:
        sys.exit("%s <share_name>" % sys.argv[0])

    try:
        so = Share.objects.get(name=name)
    except Share.DoesNotExist:
        sys.exit("Share(%s) does not exist" % name)

    mnt_pt = "%s%s" % (settings.MNT_PT, so.name)
    btrfs.mount_share(so, mnt_pt)
