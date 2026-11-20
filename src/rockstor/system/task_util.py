"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import os
import shutil
import stat
from tempfile import mkstemp
from smart_manager.constants import CRONTAB_FILE

"""
This file is to contain intentionally low-level facilities.
Some may be directly involved in Django model definitions.
It is therefor imperative/required that no related Django
model be import as this creates a circular dependency:
I.e.:
- Model requires this file's contents to initialise.
- This file requires related model to be initialised.
"""


def remove_crontab(script: str, task_def_id: int):
    """
    Remove all lines containing passed 'script' and 'task_def_id':
    e.g. line: "42 3 * * 5 root /opt/rockstor/.venv/bin/st-pool-scrub 35 \*-*-*-*-*-*$
    :param script: Python script we use cronttab to activate.
    :param task_def_id: ID of TaskDefinition instance describing the task.
    """
    if not os.path.exists(CRONTAB_FILE):
        return
    modified = False
    task_text = f"{script} {task_def_id}"
    file_handle, npath = mkstemp()
    # Copy all non-matching crontab lines to our secure temp file
    with open(CRONTAB_FILE, "r") as crontab_file, open(npath, "w") as temp_file:
        for line in crontab_file:
            if task_text in line:
                modified = True
                continue
            temp_file.write(line)
    if modified:
        # Set temp_file to rw- --- --- (600) via stat constants.
        os.chmod(npath, stat.S_IRUSR | stat.S_IWUSR)
        shutil.move(npath, CRONTAB_FILE)
    else:
        os.remove(npath)
