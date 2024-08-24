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

from system.constants import SYSTEMCTL
from system.services import tailscale_service_status, init_service_op


class ServicesTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    export DJANGO_SETTINGS_MODULE=settings
    poetry run django-admin test -p test_services.py -v 2
    """

    def test_init_service_op_unsupported_service(self):
        service_name = "unsupported_service"
        command = "status"
        expected_msg = f"unknown service: {service_name}"

        with self.assertRaises(Exception) as cm:
            # Set throw to False as otherwise an Exception would be raised
            # due to a problem unrelated to a supported/unsupported service name
            # (which is the focus for this test)
            init_service_op(service_name, command, throw=False)

        # Verify the message returned by the Exception
        returned_msg = str(cm.exception)
        self.assertEqual(
            returned_msg,
            expected_msg,
            msg="Un-expected exception message returned:\n "
            f"returned = {returned_msg}.\n "
            f"expected = {expected_msg}.",
        )

    def test_init_service_op_valid(self):
        """test final command returned"""
        supported_services = (
            "nfs-server",
            "nmb",
            "smb",
            "sshd",
            "ypbind",
            "rpcbind",
            "ntpd",
            "snmpd",
            "docker",
            "smartd",
            "shellinaboxd",
            "sssd",
            "nut-server",
            "rockstor-bootstrap",
            "rockstor",
            "systemd-shutdownd",
            "tailscaled",
        )
        cmds = [
            "start",
            "stop",
            "restart",
            "enable",
            "disable",
            "status",
        ]
        self.patch_run_command = patch("system.services.run_command")
        # Test that run_command was called as expected
        for s in supported_services:
            for c in cmds:
                self.mock_run_command = self.patch_run_command.start()
                init_service_op(service_name=s, command=c)
                if c == "status":
                    self.mock_run_command.assert_called_once_with(
                        [SYSTEMCTL, c, s, "--lines=0"], throw=True
                    )
                else:
                    self.mock_run_command.assert_called_once_with(
                        [SYSTEMCTL, c, s], throw=True
                    )
                self.patch_run_command.stop()

    def test_tailscale_service_status(self):
        """
        Returns specific integers based on get_tailscale_status() output.
        We thus need to test each to catch any change in syntax/naming.
        """
        # Should return 1 if tailscaled systemd service is inactive
        self.patch_is_systemd_service_active = patch(
            "system.services.is_systemd_service_active"
        )
        self.mock_is_systemd_service_active = (
            self.patch_is_systemd_service_active.start()
        )
        self.mock_is_systemd_service_active.return_value = False
        expected = 1
        returned = tailscale_service_status()
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_service_status() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

        # Mock tailscaled systemd service as active
        # and test various status outputs
        self.mock_is_systemd_service_active.return_value = True
        ts_status_out = []
        expected = []

        # NOTE: the real ts_status_outputs can be very large so
        # the expected ts_status_out below are shortened and anonymized
        # for convenience and clarity. We only need one key in all of that.

        # Tailscaled ON, not logged in
        ts_status_out.append(
            {
                "Version": "1.50.0-ta920f0231-geb5b0beea",
                "TUN": True,
                "BackendState": "NeedsLogin",
                "AuthURL": "",
                "TailscaleIPs": None,
                "Self": {},
                "Health": ["state=NeedsLogin, wantRunning=false"],
                "MagicDNSSuffix": "",
                "CurrentTailnet": None,
                "CertDomains": None,
                "Peer": None,
                "User": None,
                "ClientVersion": None,
            }
        )
        expected.append(5)

        # Tailscaled ON, AuthURL created
        ts_status_out.append(
            {
                "Version": "1.50.0-ta920f0231-geb5b0beea",
                "TUN": True,
                "BackendState": "NeedsLogin",
                "AuthURL": "https://login.tailscale.com/a/1223456abc",
                "TailscaleIPs": None,
                "Self": {},
                "Health": ["not in map poll"],
                "MagicDNSSuffix": "",
                "CurrentTailnet": None,
                "CertDomains": None,
                "Peer": None,
                "User": None,
                "ClientVersion": None,
            }
        )
        expected.append(5)

        # Tailscaled ON, logged in
        ts_status_out.append(
            {
                "Version": "1.50.0-ta920f0231-geb5b0beea",
                "TUN": True,
                "BackendState": "Running",
                "AuthURL": "",
                "TailscaleIPs": [
                    "100.100.100.100",
                    "a1b1:a2b2:a3b3:a4b4:a5b5:a6b6:a7b7:a8b8",
                ],
                "Self": {},
                "Health": None,
                "MagicDNSSuffix": "tailXXXXX.ts.net",
                "CurrentTailnet": {
                    "Name": "email@address.com",
                    "MagicDNSSuffix": "tailXXXXX.ts.net",
                    "MagicDNSEnabled": True,
                },
                "CertDomains": None,
                "Peer": {},
                "User": {},
                "ClientVersion": None,
            }
        )
        expected.append(0)

        # Tailscaled ON, down
        ts_status_out.append(
            {
                "Version": "1.50.0-ta920f0231-geb5b0beea",
                "TUN": True,
                "BackendState": "Stopped",
                "AuthURL": "",
                "TailscaleIPs": [
                    "100.100.100.100",
                    "a1b1:a2b2:a3b3:a4b4:a5b5:a6b6:a7b7:a8b8",
                ],
                "Self": {},
                "Health": ["state=Stopped, wantRunning=false"],
                "MagicDNSSuffix": "tailXXXXX.ts.net",
                "CurrentTailnet": {
                    "Name": "email@address.com",
                    "MagicDNSSuffix": "tailXXXXX.ts.net",
                    "MagicDNSEnabled": True,
                },
                "CertDomains": None,
                "Peer": {},
                "User": {},
                "ClientVersion": None,
            }
        )
        expected.append(1)

        # Need to mock get_tailscale_status
        self.patch_get_tailscale_status = patch("system.services.get_tailscale_status")
        self.mock_get_tailscale_status = self.patch_get_tailscale_status.start()

        for (ts_out, exp) in zip(ts_status_out, expected):
            self.mock_get_tailscale_status.return_value = ts_out
            returned = tailscale_service_status()
            self.assertEqual(
                returned,
                exp,
                msg="Un-expected tailscale_service_status() result:\n "
                f"returned = ({returned}).\n "
                f"expected = ({exp}).",
            )
