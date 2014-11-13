"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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

from storageadmin.models import (User, Group)
from system.users import (get_users, get_groups)

import logging
logger = logging.getLogger(__name__)


def combined_users():
    users = list(User.objects.all())
    sys_users = get_users(min_uid=0)
    for u in sys_users.keys():
        if (User.objects.filter(username=u).exists()):
            continue
        users.append(User(username=u, uid=sys_users[u][0],
                          gid=sys_users[u][1], admin=False))
    return users


def combined_groups():
    groups = list(Group.objects.all())
    sys_groups = get_groups()
    for g in sys_groups.keys():
        if (Group.objects.filter(groupname=g).exists()):
            continue
        groups.append(Group(groupname=g, gid=sys_groups[g]))
    return groups
