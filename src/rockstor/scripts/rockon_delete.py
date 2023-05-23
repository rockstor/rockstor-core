#!/usr/bin/python

"""
Copyright (c) 2012-2023 RockStor, Inc. <http://rockstor.com>
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

from storageadmin.models import RockOn, DContainer
from system.osi import run_command

DOCKER = "/usr/bin/docker"


# Console script to delete containers, images and rockstor-db metadata of a Rock-on.
def delete_rockon():
    try:
        name = sys.argv[1]
    except IndexError:
        sys.exit(
            "Delete metadata, containers and images of a Rock-On"
            "\n\tUsage: {} <Rock-On name>"
            "\n"
            "\nNOTE: the Rock-On name is case sensitive; use quotes if it includes spaces."
            '\nexample: {} "Rock-On Name"'.format(sys.argv[0], sys.argv[0])
        )

    ros = RockOn.objects.filter(name=name)
    if len(ros) > 0:
        for ro in ros:
            ro_id = ro.id
            for c in DContainer.objects.filter(rockon=ro).order_by("-launch_order"):
                # We don't throw any exceptions because we want to ensure metadata is
                # deleted for sure. It would be nice to fully delete containers and
                # images, but that's not a hard requirement.
                run_command([DOCKER, "stop", c.name], throw=False, log=True)
                run_command([DOCKER, "rm", c.name], throw=False, log=True)
                # Get image name with tag information
                img_plus_tag = "{}:{}".format(c.dimage.name, c.dimage.tag)
                run_command([DOCKER, "rmi", img_plus_tag], throw=False, log=True)

            ro.delete()
            print(
                "The metadata for the Rock-On named {} (id: {}) has been deleted from the database".format(
                    name, ro_id
                )
            )
    else:
        sys.exit("No Rock-On named {} was found in the database".format(name))


if __name__ == "__main__":
    delete_rockon()
