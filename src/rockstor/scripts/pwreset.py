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
import pwd
from django.db import transaction
from django.contrib.auth.models import User as DjangoUser
from storageadmin.models import User
from system import users


@transaction.atomic
def change_password(username, password):
    try:
        duser = DjangoUser.objects.get(username=username)
        duser.set_password(password)
        duser.save()
    except:
        sys.exit("username: %s does not exist in the admin database" % username)
    try:
        User.objects.get(username=username)
    except:
        sys.exit("username: %s does not exist in the database" % username)

    try:
        pwd.getpwnam(username)
    except KeyError:
        sys.exit("username: %s does not exist in the system" % username)

    try:
        users.usermod(username, password)
        users.smbpasswd(username, password)
    except:
        sys.exit(
            "Low level error occured while changing password of user: %s" % username
        )


def main():
    if len(sys.argv) < 3 or (len(sys.argv) > 1 and sys.argv[1] == "-h"):
        sys.exit("Usage: pwreset <username> <new_password>")

    try:
        change_password(sys.argv[1], sys.argv[2])
    except:
        sys.exit(
            "Error changing password for user: %s. Check the username "
            "and try again." % sys.argv[1]
        )
