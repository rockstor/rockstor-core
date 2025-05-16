"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

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

import typing
import unittest
from unittest.mock import patch

from system.pkg_mgmt import (
    rpm_build_info,
    current_version,
)


class SystemPackageTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    poetry run django-admin test -p test_pkg_mgmt.py -v 2
    """

    def setUp(self):
        # Avoid default of first Docstring in verbose mode
        unittest.TestCase.shortDescription = lambda x: None
        self.patch_run_command = patch("system.pkg_mgmt.run_command")
        self.mock_run_command = self.patch_run_command.start()

        # We need to test the conditions of distro.id() returning one of:
        # rockstor, opensuse, (was opensuse-leap), opensuse-tumbleweed
        self.patch_distro = patch("system.pkg_mgmt.distro")
        self.mock_distro = self.patch_distro.start()

    def tearDown(self):
        patch.stopall()

    # @patch("system.pkg_mgmt.subprocess.run")
    # def test_pkg_updates_info(self, mock_subproc_run):
    # No updates available:
    #         run_out = [
    #             """<?xml version='1.0'?>
    # <stream>
    # <message type="info">Loading repository data...</message>
    # <message type="info">Reading installed packages...</message>
    # <update-status version="0.6">
    # <update-list>
    # </update-list>
    # </update-status>
    # </stream>"""
    #         ]
    #
    #         # Need mocking setup for subprocess.run
    #         returned = pkg_updates_info()

    def test_current_version(self):
        """
        current_version() wraps `rpm -q --queryformat ... rockstor` and returns version-release,
        and optionally Build Date from 2 lines indicating the same.
        N.B. There is overlap here with test_rpm_build_info() concerning the
        non-legacy code path as it calls current_version also.
        But rpm_build_info(), while it exists, performs additional translation of version.
        :return:
        """
        # version & date function - rpm installed
        out = [["5.0.15-2981", "Thu May 01 2025"]]
        err = [[""]]
        rc = [0]
        get_build_date = [True]
        expected_results: typing.List[(str, str | None)] = [
            ("5.0.15-2981", "2025-May-01")
        ]
        # version only - rpm installed
        out.append(["5.0.15-111.1", "Thu May 01 2025"])
        err.append([""])
        rc.append(0)
        get_build_date.append(False)
        expected_results.append(("5.0.15-111.1", None))
        # version & date function - no rpm installed
        out.append(["package rockstor is not installed"])
        err.append([""])
        rc.append(1)
        get_build_date.append(True)
        expected_results.append(("0.0.0-0", None))
        # version only - no rpm installed
        out.append(["package rockstor is not installed"])
        err.append([""])
        rc.append(1)
        get_build_date.append(False)
        expected_results.append(("0.0.0-0", None))
        # Need more test data sets.
        for o, e, r, get_date, expected in zip(
            out, err, rc, get_build_date, expected_results
        ):
            self.mock_run_command.return_value = (o, e, r)
            returned = current_version(get_build_date=get_date)
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected zypper_repos_list() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_rpm_build_info(self):
        """
        rpm_build_info strips out and concatenates Version and Release info for the
        rockstor package. This is returned along with a standardised date format for
        the Buildtime which is also parse out.
        """
        # Tumbleweed using rpm -q --query-format
        out = [
            [
                "3.9.2-50.2093",
                "Fri Nov 29 2019",
            ]
        ]
        err = [[""]]
        rc = [0]
        # N.B. we no longer add a day to work around yum/dnf 'changelog --since' issues.
        expected_results = [("3.9.2-50.2093", "2019-Nov-29")]
        # Slowroll using rpm -q --query-format
        out.append(
            [
                "5.0.15-2969",
                "Fri Mar 07 2025",
            ]
        )
        err.append([""])
        rc.append(0)
        # N.B. we no longer add a day to work around yum/dnf 'changelog --since' issues.
        expected_results.append(("5.0.15-2969", "2025-Mar-07"))
        # Tumbleweed using rpm -q --query-format for a source install, we key from rc=1
        out.append(
            [
                "package rockstor is not installed",
            ]
        )
        err.append([""])
        rc.append(1)
        expected_results.append(("Unknown Version", None))

        for o, e, r, expected in zip(out, err, rc, expected_results):
            self.mock_run_command.return_value = (o, e, r)
            returned = rpm_build_info("rockstor")
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected rpm_build_info() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    # TODO: Add test for zypper auto update functionality post transition from currently
    #  legacy yum based system which was previously lightly tested to exist only via
    #  API level unit test src/rockstor/storageadmin/tests/test_commands.py
    #  Suggested name:
    #  test_auto_update(self)
    #  Related additional low level test:
    #  test_auto_update_status(self)
    #  Add test for rockstor_pkg_update_check()
