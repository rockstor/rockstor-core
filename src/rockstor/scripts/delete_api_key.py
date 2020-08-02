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
from django.db import transaction
from storageadmin.models import OauthApp


@transaction.atomic
def main():
    if len(sys.argv) < 2 or (len(sys.argv) > 1 and sys.argv[1] == "-h"):
        sys.exit("Usage: delete-api-key <name>")
    name = sys.argv[1]
    try:
        app = OauthApp.objects.get(name=name)
    except OauthApp.DoesNotExist:
        e_msg = "api-key(%s) does not exist" % name
        sys.exit(e_msg)

    app.application.delete()
    app.delete()
    print("api-key(%s) successfully deleted." % name)


if __name__ == "__main__":
    main()
