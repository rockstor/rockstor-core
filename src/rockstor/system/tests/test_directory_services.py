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
import unittest
from unittest.mock import patch

from system.exceptions import CommandException
from system.directory_services import domain_workgroup


class SystemDirectoryServicesTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    export DJANGO_SETTINGS_MODULE=settings
    poetry run django-admin test -p test_directory_services.py -v 2
    """

    def setUp(self):
        self.patch_run_command = patch("system.directory_services.run_command")
        self.mock_run_command = self.patch_run_command.start()

    def tearDown(self):
        patch.stopall()

    def test_domain_workgroup(self):
        """
        This tests for the correct return of WORKGROUP from the AD server
        as fetched by NET
        """
        domain = "samdom.example.com"
        o = ["Workgroup: SAMDOM", ""]
        e = [""]
        r = 0
        self.mock_run_command.return_value = (o, e, r)
        expected = "SAMDOM"

        returned = domain_workgroup(domain)
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected domain_workgroup() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

    def test_domain_workgroup_invalid(self):
        """
        Test domain_workgroup() if AD domain can't be reached.
        It should raise a CommandException.
        """
        domain = "bogusad.bogusdomain.com"
        self.mock_run_command.side_effect = CommandException(
            err=["Didn't find the cldap server!", ""],
            cmd=["/usr/bin/net", "ads", "workgroup", f"--realm={domain.upper()}"],
            out=[""],
            rc=255,
        )
        with self.assertRaises(CommandException):
            domain_workgroup(domain)

    def test_domain_workgroup_missing(self):
        """
        Test domain_workgroup() if AD domain can be reached but does
        not return the Workgroup information.
        It should raise an Exception
        """
        domain = "samdom.example.com"
        o = [""]
        e = [""]
        r = 0
        self.mock_run_command.return_value = (o, e, r)

        with self.assertRaises(Exception):
            domain_workgroup(domain)
