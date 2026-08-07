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
from pathlib import Path

from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch

from system.ssh import init_sftp_config, SSHD_HEADER, INTERNAL_SFTP_STR
from settings import CONFROOT


class SshTests(TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    poetry run django-admin test -p test_ssh.py -v 2
    """
    def setUp(self):
        self.setUpPyfakefs()
        self.patch_distro = patch("system.ssh.distro")
        self.mock_distro = self.patch_distro.start()


    def tearDown(self):
        # No necessity for self.tearDownPyfakefs()
        patch.stopall()

    def test_init_sftp_config_no_config(self):
        self.mock_distro.id.return_value = "opensuse"
        self.mock_distro.version.return_value = "15.6"
        sshd_conf_files_sftp = "/etc/ssh/sshd_config"  # 15.6 expected file
        # - Created if non-existent to account for overlay locations.
        # Otherwise, the tested code only appends if no SSHD_HEADER line in file.
        self.assertFalse(os.path.exists(sshd_conf_files_sftp))
        # Create flag file to add "AllowUsers root" line to sshd_conf_files_sftp.
        self.fs.create_file(f"{CONFROOT}/PermitRootLogin")
        # Establish parent directory in fakefs
        path = Path("/etc/ssh")
        path.mkdir(parents=True)
        # Run from initrock during rockstor-pre.service.
        self.assertTrue(init_sftp_config())
        # Check sshd_conf_files_sftp created:
        self.assertTrue(os.path.exists(sshd_conf_files_sftp))
        expected_contents =[f"{SSHD_HEADER}\n",f"{INTERNAL_SFTP_STR}\n","AllowUsers root\n"]
        with open(sshd_conf_files_sftp) as written_content:
            self.assertEqual(written_content.readlines(), expected_contents)

