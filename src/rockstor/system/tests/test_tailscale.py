"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import unittest
from unittest.mock import patch

from system.constants import TAILSCALE
from system.tailscale import (
    extract_param,
    validate_ts_custom_config,
    construct_tailscale_up_command,
    tailscale_up,
    validate_ts_hostname,
    tailscale_down,
    tailscale_not_found,
)


class TailscaleTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    poetry run django-admin test -p test_tailscale.py -v 2
    """

    def test_tailscale_extract_param(self):
        """Test get params name from dict
        These would return, for instance:
          - "--accept-risk=all" -> "accept_risk"
          - "--shields-up" -> "shields_up"
        """
        params = []
        expected = []

        params.append("--accept-risk=all")
        expected.append("accept_risk")

        params.append("--shields-up")
        expected.append("shields_up")

        for param, exp in zip(params, expected):
            returned = extract_param(param)
            self.assertEqual(
                returned,
                exp,
                msg="Un-expected extract_param() result:\n "
                f"returned = {returned}.\n "
                f"expected = {exp}.",
            )

    def test_tailscale_validate_hostname(self):
        """Ensure alphanumeric, no underscore, and no unicode in hostname"""
        test_config = {
            "accept_routes": "yes",
            "advertise_exit_node": "yes",
            "advertise_routes": "192.168.1.0/24",
            "exit_node": "100.1.1.1",
            "exit_node_allow_lan_access": "true",
            "hostname": "rock-dev_@#~!$%^&*()+123ü",
            "reset": "yes",
            "ssh": "yes",
            "custom_config": "--shields-up\n--accept-risk=all",
        }
        expected = {
            "accept_routes": "yes",
            "advertise_exit_node": "yes",
            "advertise_routes": "192.168.1.0/24",
            "exit_node": "100.1.1.1",
            "exit_node_allow_lan_access": "true",
            "hostname": "rock-dev-123",
            "reset": "yes",
            "ssh": "yes",
            "custom_config": "--shields-up\n--accept-risk=all",
        }
        returned = validate_ts_hostname(test_config)
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected validate_ts_hostname() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

    def test_tailscale_validate_ts_custom_config(self):
        """
        Should return only elements of custom configs:
          - starting with '--'
          - not in TS_UI_SETTINGS
          - not in TS_UI_SETTINGS
        """
        test_custom_config = [
            "--accept-risk=all",
            "--shields-up",
            "no-heading-hyphens",
            "--accept-routes",
            "--ssh",
        ]
        expected = [
            "--accept-risk=all",
            "--shields-up",
        ]
        returned = validate_ts_custom_config(test_custom_config)
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected validate_ts_custom_config() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

    def test_tailscale_construct_tailscale_up_command(self):
        """Builds the tailscale up command from config"""
        test_config = {
            "accept_routes": "yes",
            "advertise_exit_node": "yes",
            "advertise_routes": "192.168.1.0/24",
            "exit_node": "100.1.1.1",
            "exit_node_allow_lan_access": "true",
            "hostname": "rockdev",
            "reset": "yes",
            "ssh": "yes",
            "auth_url": "https://login.tailscale.com/a/s123456df123",
            "custom_config": ["--accept-risk=all", "--shields-up"],
        }
        expected = [
            "/usr/bin/tailscale",
            "up",
            "--accept-routes",
            "--advertise-exit-node",
            "--advertise-routes=192.168.1.0/24",
            "--exit-node=100.1.1.1",
            "--exit-node-allow-lan-access",
            "--hostname=rockdev",
            "--reset",
            "--ssh",
            "--accept-risk=all",
            "--shields-up",
        ]
        returned = construct_tailscale_up_command(test_config)
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected construct_tailscale_up_command() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

    def test_tailscale_up(self):
        """Test enabling or not of ip forwarding
        If the following two keys are found in the config dict,
        then enable_ip_forwarding should be triggered. Test that.
        """
        # mock enable_ip_forwarding()
        self.patch_enable_ip_forwarding = patch("system.tailscale.enable_ip_forwarding")
        self.mock_enable_ip_forwarding = self.patch_enable_ip_forwarding.start()
        self.mock_enable_ip_forwarding.return_value = [""], [""], 0
        # mock run_command()
        self.patch_run_command = patch("system.tailscale.run_command")
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = [""], [""], 0
        # mock tailscale_not_found()
        self.patch_tailscale_not_found = patch("system.tailscale.tailscale_not_found")
        self.mock_tailscale_not_found = self.patch_tailscale_not_found.start()
        self.mock_tailscale_not_found.return_value = None

        # enable_ip_forwarding() should not be called
        config = {"hostname": "rockdevtest", "reset": "yes", "ssh": "yes"}
        expected_cmd = [TAILSCALE, "up", "--hostname=rockdevtest", "--reset", "--ssh"]
        self.mock_enable_ip_forwarding.assert_not_called()
        returned = tailscale_up(config=config)
        self.mock_run_command.assert_called_once_with(
            expected_cmd, log=True, throw=False
        )
        expected = [""], [""], 0
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_up() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

        # enable_ip_forwarding() should be called
        config = {
            "hostname": "rockdevtest",
            "reset": "yes",
            "ssh": "yes",
            "advertise_exit_node": "yes",
        }
        expected_cmd = [
            TAILSCALE,
            "up",
            "--hostname=rockdevtest",
            "--reset",
            "--ssh",
            "--advertise-exit-node",
        ]
        self.patch_run_command.stop()
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = [""], [""], 0
        self.patch_enable_ip_forwarding.stop()
        self.mock_enable_ip_forwarding = self.patch_enable_ip_forwarding.start()
        returned = tailscale_up(config=config)
        self.mock_enable_ip_forwarding.assert_called_once_with(
            name="tailscale", priority=99
        )
        self.mock_run_command.assert_called_once_with(
            expected_cmd, log=True, throw=False
        )
        expected = [""], [""], 0
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_up() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

        # enable_ip_forwarding() should be called
        # '--timeout' should be added
        config = {
            "hostname": "rockdevtest",
            "reset": "yes",
            "ssh": "yes",
            "advertise_exit_node": "yes",
        }
        expected_cmd = [
            TAILSCALE,
            "up",
            "--hostname=rockdevtest",
            "--reset",
            "--ssh",
            "--advertise-exit-node",
            "--timeout=10s",
        ]
        self.patch_run_command.stop()
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = [""], [""], 0
        self.patch_enable_ip_forwarding.stop()
        self.mock_enable_ip_forwarding = self.patch_enable_ip_forwarding.start()
        returned = tailscale_up(config=config, timeout=10)
        self.mock_enable_ip_forwarding.assert_called_once_with(
            name="tailscale", priority=99
        )
        self.mock_run_command.assert_called_once_with(
            expected_cmd, log=True, throw=False
        )
        expected = [""], [""], 0
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_up() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

    def test_tailscale_down(self):
        """Test disabling or not of ip forwarding
        If the following two keys are found in the config dict,
        then disable_ip_forwarding should be triggered. Test that.
        """
        # mock disable_ip_forwarding()
        self.patch_disable_ip_forwarding = patch(
            "system.tailscale.disable_ip_forwarding"
        )
        self.mock_disable_ip_forwarding = self.patch_disable_ip_forwarding.start()
        self.mock_disable_ip_forwarding.return_value = [""], [""], 0
        # mock run_command()
        self.patch_run_command = patch("system.tailscale.run_command")
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = [""], [""], 0

        # disable_ip_forwarding() should not be called
        config = {"hostname": "rockdevtest", "reset": "yes", "ssh": "yes"}
        expected_cmd = [TAILSCALE, "down"]
        self.mock_disable_ip_forwarding.assert_not_called()
        returned = tailscale_down(config=config)
        self.mock_run_command.assert_called_once_with(
            expected_cmd, log=True, throw=False
        )
        expected = [""], [""], 0
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_down() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )

        # disable_ip_forwarding() should be called
        config = {
            "hostname": "rockdevtest",
            "reset": "yes",
            "ssh": "yes",
            "advertise_exit_node": "yes",
        }
        self.patch_run_command.stop()
        self.mock_run_command = self.patch_run_command.start()
        self.mock_run_command.return_value = [""], [""], 0
        self.patch_disable_ip_forwarding.stop()
        self.mock_disable_ip_forwarding = self.patch_disable_ip_forwarding.start()
        returned = tailscale_down(config=config)
        self.mock_disable_ip_forwarding.assert_called_once_with(name="tailscale")
        self.mock_run_command.assert_called_once_with(
            expected_cmd, log=True, throw=False
        )
        expected = [""], [""], 0
        self.assertEqual(
            returned,
            expected,
            msg="Un-expected tailscale_down() result:\n "
            f"returned = {returned}.\n "
            f"expected = {expected}.",
        )
