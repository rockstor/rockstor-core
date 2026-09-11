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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

import os
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch

from system.constants import SMB_CONFIG
from system.samba_util import remove_smb_export

INITIAL_SMB_CONFIG = r"""
[global]
    log file = /var/log/samba/log.%m
    log level = 3
    load printers = no
    cups options = raw
    printcap name = /dev/null
    map to guest = Bad User

####BEGIN: Rockstor SAMBA GLOBAL CUSTOM####
    workgroup = ROCKSTOR
####END: Rockstor SAMBA GLOBAL CUSTOM####

####BEGIN: Rockstor SAMBA CONFIG####
[share1]
    root preexec = sh -c "cd /opt/rockstor/ && poetry run mnt-share share1"
    root preexec close = yes
    comment = b'Samba-Export'
    path = /mnt2/share1
    browseable = yes
    read only = no
    guest ok = no
[share3]
    root preexec = sh -c "cd /opt/rockstor/ && poetry run mnt-share share3"
    root preexec close = yes
    comment = b'Samba-Export'
    path = /mnt2/share3
    browseable = yes
    read only = no
    guest ok = no
[share2]
    root preexec = sh -c "cd /opt/rockstor/ && poetry run mnt-share share2"
    root preexec close = yes
    comment = b'Samba-Export'
    path = /mnt2/share2
    browseable = yes
    read only = no
    guest ok = no
####END: Rockstor SAMBA CONFIG####
"""

ONE_EXPORT_REMOVED_SMB_CONFIG = r"""
[global]
    log file = /var/log/samba/log.%m
    log level = 3
    load printers = no
    cups options = raw
    printcap name = /dev/null
    map to guest = Bad User

####BEGIN: Rockstor SAMBA GLOBAL CUSTOM####
    workgroup = ROCKSTOR
####END: Rockstor SAMBA GLOBAL CUSTOM####

####BEGIN: Rockstor SAMBA CONFIG####
[share1]
    root preexec = sh -c "cd /opt/rockstor/ && poetry run mnt-share share1"
    root preexec close = yes
    comment = b'Samba-Export'
    path = /mnt2/share1
    browseable = yes
    read only = no
    guest ok = no
[share2]
    root preexec = sh -c "cd /opt/rockstor/ && poetry run mnt-share share2"
    root preexec close = yes
    comment = b'Samba-Export'
    path = /mnt2/share2
    browseable = yes
    read only = no
    guest ok = no
####END: Rockstor SAMBA CONFIG####
"""

ALL_EXPORTS_REMOVED_SMB_CONFIG = r"""
[global]
    log file = /var/log/samba/log.%m
    log level = 3
    load printers = no
    cups options = raw
    printcap name = /dev/null
    map to guest = Bad User

####BEGIN: Rockstor SAMBA GLOBAL CUSTOM####
    workgroup = ROCKSTOR
####END: Rockstor SAMBA GLOBAL CUSTOM####

####BEGIN: Rockstor SAMBA CONFIG####
####END: Rockstor SAMBA CONFIG####
"""


class SystemSambaUtilTests(TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    poetry run django-admin test -p test_system_samba_util.py -v 2
    ...
    For SAMBA API tests see: storageadmin/tests/test_samba.py
    """

    @classmethod
    def setUpClass(cls):
        cls.setUpClassPyfakefs()
        # Re-establish the start-state of the filesystem before every test.
        cls.fake_fs().create_file(SMB_CONFIG, contents=INITIAL_SMB_CONFIG)

    def setUp(self):
        # patch our samba util 'testparm' wrapper:
        self.patch_testparm = patch("system.samba_util.test_parm")
        self.mock_testparm = self.patch_testparm.start()

    def tearDown(self):
        # No necessity for self.tearDownPyfakefs()
        patch.stopall()

    def test_remove_smb_export(self):
        self.assertTrue(os.path.exists(SMB_CONFIG))
        self.mock_testparm.return_value = True
        self.assertTrue(remove_smb_export(["share3"]))
        self.mock_testparm.assert_called_once()
        self.assertFalse(remove_smb_export(["non-existent-share"]))
        # Check that we did not call testparm again:
        self.mock_testparm.assert_called_once()
        # with open(SMB_CONFIG) as written_content:
        #     print(written_content.read())
        with open(SMB_CONFIG) as written_content:
            self.assertEqual(written_content.read(), ONE_EXPORT_REMOVED_SMB_CONFIG)
        # Check response to our testparm wrapper raising an Exception:
        self.mock_testparm.side_effect = Exception(
            "Syntax error while checking the temporary samba config file"
        )
        self.assertFalse(remove_smb_export(["share1"]))
        # Reset testparm to have not side_effect:
        self.mock_testparm.side_effect = None
        self.assertTrue(remove_smb_export(["share1", "share2"]))
        # with open(SMB_CONFIG) as written_content:
        #     print(written_content.read())
        with open(SMB_CONFIG) as written_content:
            self.assertEqual(written_content.read(), ALL_EXPORTS_REMOVED_SMB_CONFIG)
        self.assertFalse(remove_smb_export([]))
        self.assertFalse(remove_smb_export(["", ""]))
        os.remove(SMB_CONFIG)
        self.assertFalse(os.path.exists(SMB_CONFIG))
        # Ensure robustness to no smb.conf file existing.
        self.assertFalse(remove_smb_export(["some-share"]))
