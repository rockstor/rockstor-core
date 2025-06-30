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
from unittest.mock import patch

from rest_framework import status
from rest_framework.test import APITestCase

"""
proposed fixture = "test_tailscaled.json"

cd /opt/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin dumpdata --database smart_manager smart_manager.service
--natural-foreign --indent 4 >
src/rockstor/smart_manager/fixtures/services.json

To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_tailscaled.py
"""


class TailscaledTests(APITestCase):
    databases = "__all__"
    fixtures = ["test_api.json", "services.json"]
    BASE_URL = "/api/sm/services/tailscaled"

    @classmethod
    def setUpClass(cls):
        super(TailscaledTests, cls).setUpClass()

        # POST mocks
        cls.patch_systemctl = patch("smart_manager.views.tailscaled_service.systemctl")
        cls.mock_systemctl = cls.patch_systemctl.start()
        cls.mock_systemctl.return_value = [""], [""], 0

    @classmethod
    def tearDownClass(cls):
        super(TailscaledTests, cls).tearDownClass()

    def session_login(self):
        self.client.login(username="admin", password="admin")

    def test_tailscaled_unauthorized(self):
        """
        unauthorized access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tailscaled_post_config_valid(self):
        """
        config happy path
        """
        config = {
            "accept_routes": "yes",
            "advertise_exit_node": "yes",
            "advertise_routes": "192.168.1.0/24",
            "exit_node": "100.1.1.1",
            "exit_node_allow_lan_access": "true",
            "hostname": "rockdev",
            "reset": "yes",
            "ssh": "yes",
            "custom_config": "--shields-up\n--accept-risk=all",
        }

        data = {"config": config}
        self.session_login()
        response = self.client.post(f"{self.BASE_URL}/config", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

    def test_tailscaled_post_config_no_config(self):
        """
        config without input
        """
        self.session_login()
        response = self.client.post(f"{self.BASE_URL}/config")
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=response.content,
        )

    def test_tailscaled_login_start_stop(self):
        """
        start/stop tests
        """
        # mock tailscale_up() used by LOGIN, START
        self.patch_tailscale_up = patch(
            "smart_manager.views.tailscaled_service.tailscale_up"
        )
        self.mock_tailscale_up = self.patch_tailscale_up.start()
        self.mock_tailscale_up.return_value = [""], [""], 0

        # mock tailscale_down() used by STOP
        self.patch_tailscale_down = patch(
            "smart_manager.views.tailscaled_service.tailscale_down"
        )
        self.mock_tailscale_down = self.patch_tailscale_down.start()
        self.mock_tailscale_down.return_value = [""], [""], 0

        self.session_login()

        # First, configure the service
        config = {
            "accept_routes": "yes",
            "advertise_exit_node": "yes",
            "advertise_routes": "192.168.1.0/24",
            "exit_node": "100.1.1.1",
            "exit_node_allow_lan_access": "true",
            "hostname": "rockdev",
            "reset": "yes",
            "ssh": "yes",
            "custom_config": "--shields-up\n--accept-risk=all",
        }
        data = {"config": config}
        response = self.client.post(f"{self.BASE_URL}/config", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

        # Then test login

        # we need to mock a "NeedsLogin with authURL" get_tailscale_status()
        self.patch_get_tailscale_status = patch("system.tailscale.get_tailscale_status")
        self.mock_get_tailscale_status = self.patch_get_tailscale_status.start()
        ts_status = {
            "Version": "1.50.0-ta920f0231-geb5b0beea",
            "TUN": True,
            "BackendState": "NeedsLogin",
            "AuthURL": "https://login.tailscale.com/a/1223456abc",
            "TailscaleIPs": None,
            "Self": {
                "ID": "",
                "PublicKey": "nodekey:0000000000000000000000000000000000000000000000000000000000000000",
                "HostName": "rockstortest",
                "DNSName": "",
                "OS": "linux",
                "UserID": 0,
                "TailscaleIPs": None,
                "Addrs": [],
                "CurAddr": "",
                "Relay": "",
                "RxBytes": 0,
                "TxBytes": 0,
                "Created": "0001-01-01T00:00:00Z",
                "LastWrite": "0001-01-01T00:00:00Z",
                "LastSeen": "0001-01-01T00:00:00Z",
                "LastHandshake": "0001-01-01T00:00:00Z",
                "Online": False,
                "ExitNode": False,
                "ExitNodeOption": False,
                "Active": False,
                "PeerAPIURL": None,
                "InNetworkMap": False,
                "InMagicSock": False,
                "InEngine": False,
            },
            "Health": ["not in map poll"],
            "MagicDNSSuffix": "",
            "CurrentTailnet": None,
            "CertDomains": None,
            "Peer": None,
            "User": None,
            "ClientVersion": None,
        }
        self.mock_get_tailscale_status.return_value = ts_status

        response2 = self.client.post(f"{self.BASE_URL}/config/login")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, msg=response2.content
        )

        # Then test start
        response3 = self.client.post(f"{self.BASE_URL}/start")
        self.assertEqual(
            response.status_code, status.HTTP_200_OK, msg=response3.content
        )
        # Finally, test stop
        response4 = self.client.post(f"{self.BASE_URL}/stop")
        self.assertEqual(
            response4.status_code, status.HTTP_200_OK, msg=response4.content
        )
