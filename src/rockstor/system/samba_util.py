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
import re
import shutil
from tempfile import mkstemp

from system.constants import SMB_CONFIG, RS_SHARES_HEADER, RS_SHARES_FOOTER
from system.osi import run_command

"""
This file is to contain intentionally low-level facilities.
Some may be directly involved in Django model definitions.
It is therefor imperative/required that no related Django
model be import as this creates a circular dependency:
I.e.:
- Model requires this file's contents to initialise.
- This file requires related model to be initialised.
"""

TESTPARM = "/usr/bin/testparm"


def test_parm(config=SMB_CONFIG):
    cmd = [TESTPARM, "-s", config]
    o, e, rc = run_command(cmd, throw=False)
    if rc != 0:
        raise Exception("Syntax error while checking the temporary samba config file")
    return True


def remove_smb_export(share_name_list: list[str]) -> bool:
    """
    Primarily required by SambaShare.delete() override post_delete action.
    Simply removes named Share entries within RS_SHARES_HEADER section of
    the SMB_CONFIG file. Intended as a low-level approach to bring existing
    SMB config in-line with a single SambaShare delete during, for example a
    larger (Pool delete) atomic transaction. So we cannot use existing
    whole-sale config re-writes as that would be unnecessary heavy weight.
    Also note that as we are intra-model we must be simple and predictable.
    :param share_name_list: list of stings from SambaShare.share.name
    :return: True if file was modified, False otherwise.
    """
    if not os.path.exists(SMB_CONFIG) or share_name_list == []:
        return False
    fh, npath = mkstemp()
    with open(SMB_CONFIG, "r") as smb_conf, open(npath, "w") as temp_file:
        rockstor_section: bool = False
        share_entry: bool = False
        modified: bool = False
        for line in smb_conf:
            # Establish if we are between Rockstor Share headers:
            if re.match(RS_SHARES_HEADER, line) is not None:
                rockstor_section = True
            elif re.match(RS_SHARES_FOOTER, line) is not None:
                rockstor_section = False
            # Establish if we are in one of the specific share_entries:
            if any(
                line.startswith(f"[{share_name}]") for share_name in share_name_list
            ):
                share_entry = True
            elif line.startswith(r"["):
                share_entry = False
            # Skip copying the share_name section.
            if rockstor_section and share_entry:
                modified = True
                continue
            else:
                temp_file.write(line)
    if modified:
        # Avoid writing invalid changes at the cost of spurious share entries.
        try:
            test_parm(npath)
        except:
            os.remove(npath)
            return not modified
        shutil.move(npath, SMB_CONFIG)
    else:
        os.remove(npath)
    return modified
