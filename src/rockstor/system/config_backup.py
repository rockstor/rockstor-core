"""
Copyright (c) 2012-2019 RockStor, Inc. <http://rockstor.com>
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

import logging
import os
from datetime import datetime
from django.core.management import call_command
from storageadmin.models import ConfigBackup
from system.osi import run_command, md5sum

logger = logging.getLogger(__name__)


def backup_config():
    models = {
        "storageadmin": [
            "user",
            "group",
            "sambashare",
            "sambacustomconfig",
            "netatalkshare",
            "nfsexport",
            "nfsexportgroup",
            "advancednfsexport",
        ],
        "smart_manager": ["service"],
    }
    model_list = []
    for a in models:
        for m in models[a]:
            model_list.append("{}.{}".format(a, m))

    filename = "backup-{}.json".format(datetime.now().strftime("%Y-%m-%d-%H%M%S"))
    cb_dir = ConfigBackup.cb_dir()

    if not os.path.isdir(cb_dir):
        os.mkdir(cb_dir)
    fp = os.path.join(cb_dir, filename)
    with open(fp, "w") as dfo:
        call_command("dumpdata", *model_list, stdout=dfo)
        dfo.write("\n")
        call_command("dumpdata", database="smart_manager", *model_list, stdout=dfo)
    run_command(["/usr/bin/gzip", fp])
    gz_name = "{}.gz".format(filename)
    fp = os.path.join(cb_dir, gz_name)
    size = os.stat(fp).st_size
    cbo = ConfigBackup(filename=gz_name, md5sum=md5sum(fp), size=size)
    cbo.save()
    return cbo
