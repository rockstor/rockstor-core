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
import stat
from stat import S_IMODE

from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch

from system.constants import SYSTEMCTL
from system.ssh import (
    init_sftp_config,
    SSHD_HEADER,
    INTERNAL_SFTP_STR,
    toggle_sftp_service,
    update_sftp_user_share_config,
    remove_sftp_server_subsystem,
)
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
        self.patch_run_command = patch("system.ssh.run_command")
        self.mock_run_command = self.patch_run_command.start()
        self.patch_is_sftp_running = patch("system.ssh.is_sftp_running")
        self.mock_is_sftp_running = self.patch_is_sftp_running.start()

    def tearDown(self):
        # No necessity for self.tearDownPyfakefs()
        patch.stopall()

    def test_init_sftp_config_and_toggle_sftp_service(self):
        self.mock_distro.id.return_value = "opensuse"
        self.mock_distro.version.return_value = "15.6"
        # - Created if non-existent for overlay compatibility.
        # N.B. init code only appends if no SSHD_HEADER line found.
        sshd_conf_files_sftp = "/etc/ssh/sshd_config"  # 15.6 expected file
        self.assertFalse(os.path.exists(sshd_conf_files_sftp))
        # Create flag file to add "AllowUsers root" line to sshd_conf_files_sftp.
        self.fs.create_file(f"{CONFROOT}/PermitRootLogin")
        # Establish parent directory in fakefs
        self.fs.create_dir("/etc/ssh")
        # Run from initrock during rockstor-pre.service. True is change made:
        self.assertTrue(init_sftp_config())
        # Check sshd_conf_files_sftp created:
        self.assertTrue(os.path.exists(sshd_conf_files_sftp))
        expected = [
            f"{SSHD_HEADER}\n",
            f"{INTERNAL_SFTP_STR}\n",
            "AllowUsers root\n",
        ]
        with open(sshd_conf_files_sftp) as written_content:
            self.assertEqual(written_content.readlines(), expected)
        # Test return False when existing config found.
        self.assertFalse(init_sftp_config())
        with open(sshd_conf_files_sftp) as written_content:
            self.assertEqual(written_content.readlines(), expected)
        # TEST DISABLE SFTP - removing INTERNAL_SFTP_STR line from config
        toggle_sftp_service(switch=False)
        expected_sftp_disabled = [
            f"{SSHD_HEADER}\n",
            "AllowUsers root\n",
        ]
        with open(sshd_conf_files_sftp) as written_content:
            self.assertEqual(written_content.readlines(), expected_sftp_disabled)
        # See also: system/tests/test_services.py for sshd run_command calls.
        self.mock_run_command.assert_called_once_with(
            [SYSTEMCTL, "reload", "sshd"], log=True
        )

    def test_update_sftp_user_share_config(self):
        self.mock_distro.id.return_value = "opensuse"
        self.mock_distro.version.return_value = "16.0"
        self.mock_is_sftp_running.return_value = True

        sshd_conf_files_sftp = "/etc/ssh/sshd_config.d/rockstor-sftp.conf"
        # Create file, as per initrock, as 600: "-rw-------" with contents for when
        # NO "/opt/rockstor/CONF/PermitRootLogin" flag file exists:
        file_mode = stat.S_IRUSR | stat.S_IWUSR
        self.fs.create_file(
            sshd_conf_files_sftp,
            st_mode=file_mode,
            contents=f"{SSHD_HEADER}\n{INTERNAL_SFTP_STR}\n",  # No "AllowUsers root\n",
        )
        input_map = {"radmin": "/mnt3/radmin"}  # user radmin creates a SFTP share.
        update_sftp_user_share_config(input_map)
        expected = [
            f"{SSHD_HEADER}\n",
            f"{INTERNAL_SFTP_STR}\n",
            "AllowUsers radmin\n",  # no /opt/rockstor/CONF/PermitRootLogin so no `root`
            "Match User radmin\n",
            "\tForceCommand internal-sftp\n",
            "\tChrootDirectory /mnt3/radmin\n",
            "\tX11Forwarding no\n",
            "\tAllowTcpForwarding no\n",
        ]
        with open(sshd_conf_files_sftp) as written_content:
            self.assertEqual(written_content.readlines(), expected)
        self.mock_run_command.assert_called_once_with(
            [SYSTEMCTL, "reload", "sshd"], log=True
        )
        # Check original file permissions were preserved.
        self.assertEqual(S_IMODE(os.stat(sshd_conf_files_sftp).st_mode), file_mode)

    def test_remove_sftp_server_subsystem(self):
        self.mock_distro.id.return_value = "opensuse-tumbleweed"
        self.mock_distro.version.return_value = "20260806"
        # OS SSH config file to edit for TW:
        sshd_conf_files_sshd_os = "/usr/etc/ssh/sshd_config"
        file_mode = stat.S_IRUSR | stat.S_IWUSR
        self.fs.create_file(
            sshd_conf_files_sshd_os,
            st_mode=file_mode,
            contents="# override default of no subsystems\n"
            "Subsystem       sftp    /usr/libexec/ssh/sftp-server\n",
        )
        # TEST RC when change is applied:
        self.assertTrue(remove_sftp_server_subsystem())
        # Potential anomaly re "\n" last line in output file.
        expected = [
            "# override default of no subsystems\n",
            "#Subsystem       sftp    /usr/libexec/ssh/sftp-server\n",
            "\n",
        ]
        with open(sshd_conf_files_sshd_os) as written_content:
            self.assertEqual(written_content.readlines(), expected)
        # Check original file permissions were preserved.
        self.assertEqual(S_IMODE(os.stat(sshd_conf_files_sshd_os).st_mode), file_mode)
        # TEST RC when no changes are made: i.e. line already remarked out:
        self.assertFalse(remove_sftp_server_subsystem())
        # TEST rc when no file exists:
        self.fs.remove(sshd_conf_files_sshd_os)
        self.assertFalse(remove_sftp_server_subsystem())
