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
from unittest import mock
from unittest.mock import patch

from rest_framework import status
from storageadmin.tests.test_api import APITestMixin
from storageadmin.models import NetworkConnection, NetworkDevice


"""
To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_network.py
"""

class NetworkTests(APITestMixin):
    # TODO Move as many by-hand mocks to now functional fixture setup.
    # TODO Provide command to create fixture
    # Fixture from single ethernet KVM instance for now to start off new
    # mocking required after recent api change.
    # Proposed fixture = "test_network.json"
    # TODO: Needs changing as API url different ie connection|devices|refresh
    # see referenced pr in setUpClass
    fixtures = ["test_api.json"]
    BASE_URL = "/api/network"

    @classmethod
    def setUpClass(cls):
        super(NetworkTests, cls).setUpClass()

        # N.B. major changes were made to network functionality via pr:
        # https://github.com/rockstor/rockstor-core/pull/1253
        # which added new network primitives via system/network.py

        # TODO: Needs a few mock changes, adding starters.

        # post mocks

        # devices map dictionary
        cls.patch_devices = patch("system.network.get_dev_config")
        cls.mock_devices = cls.patch_devices.start()
        cls.mock_devices.return_value = {
            "lo": {
                "dtype": "loopback",
                "mac": "00:00:00:00:00:00",
                "state": "10 (unmanaged)",
                "mtu": "65536",
            },
            "eth0": {
                "dtype": "ethernet",
                "mac": "52:54:00:58:5D:66",
                "connection": "eth0",
                "state": "100 (connected)",
                "mtu": "1500",
            },
        }

        # connections map dictionary
        cls.patch_connections = patch("system.network.get_con_config")
        cls.mock_connections = cls.patch_connections.start()
        cls.mock_connections.return_value = {
            "8dca3630-8c54-4ad7-8421-327cc2d3d14a": {
                "ctype": "802-3-ethernet",
                "ipv6_addresses": None,
                "ipv4_method": "auto",
                "ipv6_method": None,
                "ipv6_dns": None,
                "name": "eth0",
                "ipv4_addresses": "192.168.124.235/24",
                "ipv6_gw": None,
                "ipv4_dns": "192.168.124.1",
                "state": "activated",
                "ipv6_dns_search": None,
                "802-3-ethernet": {
                    "mac": "52:54:00:58:5D:66",
                    "mtu": "auto",
                    "cloned_mac": None,
                },
                "ipv4_gw": "192.168.124.1",
                "ipv4_dns_search": None,
            }
        }

        # system.network.get_con_list()
        cls.patch_get_con_list = patch("system.network.get_con_list")
        cls.mock_get_con_list = cls.patch_get_con_list.start()
        cls.mock_get_con_list.return_value = []

        # valid_connection
        cls.patch_valid_connection = patch("system.network.valid_connection")
        cls.mock_valid_connection = cls.patch_valid_connection.start()
        cls.mock_valid_connection.return_value = True

        # toggle_connection
        cls.patch_toggle_connection = patch("system.network.toggle_connection")
        cls.mock_toggle_connection = cls.patch_toggle_connection.start()
        cls.mock_toggle_connection.return_value = [""], [""], 0

        # delete_connection
        cls.patch_delete_connection = patch("system.network.delete_connection")
        cls.mock_delete_connection = cls.patch_delete_connection.start()
        cls.mock_delete_connection.return_value = [""], [""], 0

        # reload_connection
        cls.patch_reload_connection = patch("system.network.reload_connection")
        cls.mock_reload_connection = cls.patch_reload_connection.start()
        cls.mock_reload_connection.return_value = [""], [""], 0

        # new_connection_helper
        cls.patch_new_con_helper = patch("system.network.new_connection_helper")
        cls.mock_new_con_helper = cls.patch_new_con_helper.start()
        cls.mock_new_con_helper.return_value = [""], [""], 0

        # new_ethernet_connection
        cls.patch_new_eth_conn = patch("system.network.new_ethernet_connection")
        cls.mock_new_eth_conn = cls.patch_new_eth_conn.start()
        cls.mock_new_eth_conn.return_value = [""], [""], 0

        # new_member_helper
        cls.patch_new_mem_helper = patch("system.network.new_member_helper")
        cls.mock_new_mem_helper = cls.patch_new_mem_helper.start()
        cls.mock_new_mem_helper.return_value = [""], [""], 0

        # TODO: Also need to mock
        # system.network.new_team_connection
        # and
        # system.network.new_bond_connection

        # Set temp models entries as per fixtures
        cls.temp_ethernet = NetworkConnection(id=1, name="Wired connection 1")
        cls.temp_device_eth0 = NetworkDevice(id=2, name="eth0")
        cls.temp_rocknet = NetworkConnection(id=17, name="br-6088a34098e0")
        cls.temp_device = NetworkDevice(id=12, name="br-6088a34098e0")

    @classmethod
    def tearDownClass(cls):
        super(NetworkTests, cls).tearDownClass()

    # N.B. There are working and current system level unit tests in:
    # src/rockstor/system/tests/test_system_network.py
    # Added via pr: "Add unit testing for core network functions" #2045 on GitHub

    # Fixture fix1.json has the test data. networks already exits in data are
    # 'enp0s3' and 'enp0s8'

    # def session_login(self):
    #     self.client.login(username='admin', password='admin')

    def test_get_base(self):
        """
        unauthorized access
        """
        # get base URL
        response = self.client.get("{}/connections".format(self.BASE_URL))
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg="Un-expected get() result:\n"
            "response.status_code = ({}).\n "
            "response.data = ({}).\n ".format(response.status_code, response.data),
        )

    def test_put_invalid_id(self):
        """
        test with invalid connection id
        :return:
        """
        data = {"id": 99}
        response = self.client.put("{}/connections/99".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Network connection (99) does not exist."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

    @mock.patch("storageadmin.views.network.NetworkConnectionDetailView._nco")
    def test_put(self, mock_nco):
        """
        test put with valid connection id
        """
        mock_nco.return_value = self.temp_rocknet

        # Valid rocknet edit
        data = {"id": 17}
        response = self.client.put("{}/connections/17".format(self.BASE_URL), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Invalid MTU
        data = {"id": 17, "mtu": 10000}
        response = self.client.put("{}/connections/17".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.status_code returned was {}".format(response.status_code),
        )
        e_msg = "The mtu must be an integer in 1500 - 9000 range."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        data = {"id": 17, "mtu": 100}
        response = self.client.put("{}/connections/17".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.status_code returned was {}".format(response.status_code),
        )
        e_msg = "The mtu must be an integer in 1500 - 9000 range."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

    @mock.patch("storageadmin.views.network.NetworkConnectionDetailView._nco")
    def test_delete(self, mock_nco):
        """
        test put with valid connection id
        """
        mock_nco.return_value = self.temp_rocknet

        data = {"id": 17}
        response = self.client.put("{}/connections/17".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
            msg="response.data = {}\n"
            "reponse.status_code = {}".format(response.data, response.status_code),
        )

    @mock.patch("storageadmin.views.network.NetworkConnection.objects")
    def test_nclistview_post_invalid(self, mock_networkconnection):
        """
        test NetworkConnectionListView.post with invalid settings
        :return:
        """
        # A NetworkConnection object with the same name already exists
        mock_networkconnection.filter.return_value = mock_networkconnection
        mock_networkconnection.exists.return_value = True

        data = {"id": 17, "name": "br-6088a34098e0"}
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Connection name (br-6088a34098e0) is already in use. Choose a different name."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # No method is defined
        mock_networkconnection.filter.return_value = mock_networkconnection
        mock_networkconnection.exists.return_value = False

        data = {"id": 17, "name": "br-6088a34098e0"}
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Unsupported config method (None). Supported ones include: (('auto', 'manual'))."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # Invalid connection type
        mock_networkconnection.filter.return_value = mock_networkconnection
        mock_networkconnection.exists.return_value = False

        data = {
            "id": 17,
            "name": "br-6088a34098e0",
            "method": "auto",
            "ctype": "invalid_ctype",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Unsupported connection type (invalid_ctype). Supported ones include: (('ethernet', 'team', 'bond', 'docker'))."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # Invalid team profile
        mock_networkconnection.filter.return_value = mock_networkconnection
        mock_networkconnection.exists.return_value = False

        data = {
            "id": 17,
            "name": "br-6088a34098e0",
            "method": "auto",
            "ctype": "team",
            "team_profile": "invalid_profile",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Unsupported team profile (invalid_profile). Supported ones include: (('broadcast', 'roundrobin', 'activebackup', 'loadbalance', 'lacp'))."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # Invalid bond profile
        mock_networkconnection.filter.return_value = mock_networkconnection
        mock_networkconnection.exists.return_value = False

        data = {
            "id": 17,
            "name": "br-6088a34098e0",
            "method": "auto",
            "ctype": "bond",
            "bond_profile": "invalid_profile",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Unsupported bond profile (invalid_profile). Supported ones include: (('balance-rr', 'active-backup', 'balance-xor', 'broadcast', '802.3ad', 'balance-tlb', 'balance-alb'))."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

    # TODO: write test for NetworkConnectionListView._validate_devices

    def test_nclistview_post_devices(self):
        """
        test NetworkConnectionListView.post devices combinations
        :return:
        """
        # Unknown device for ethernet connection
        data = {
            "id": 99,
            "name": "Wired connection 99",
            "device": "eth0",
            "method": "auto",
            "ctype": "ethernet",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "Unknown network device (eth0)."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

    @mock.patch("storageadmin.views.network.NetworkDevice.objects")
    def test_nclistview_post_devices_not_list(self, mock_networkdevice):

        mock_networkdevice.get.return_value = self.temp_device_eth0
        ## Team
        # Devices not a list for team connection
        data = {
            "id": 99,
            "name": "Wired connection 99",
            "devices": "eth0",
            "method": "auto",
            "ctype": "team",
            "team_profile": "broadcast",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "devices must be a list"
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # Not enough devices for team connection
        data = {
            "id": 99,
            "name": "Wired connection 99",
            "devices": ["eth0",],
            "method": "auto",
            "ctype": "team",
            "team_profile": "broadcast",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "A minimum of 2 devices are required."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        ## Bond
        # Devices not a list for team connection
        data = {
            "id": 99,
            "name": "Wired connection 99",
            "devices": "eth0",
            "method": "auto",
            "ctype": "bond",
            "bond_profile": "balance-rr",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "devices must be a list"
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )

        # Not enough devices for team connection
        data = {
            "id": 99,
            "name": "Wired connection 99",
            "devices": ["eth0",],
            "method": "auto",
            "ctype": "bond",
            "bond_profile": "balance-rr",
        }
        response = self.client.post("{}/connections".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg="response.data = {}\n"
            "response.status_code = {}".format(response.data, response.status_code),
        )
        e_msg = "A minimum of 2 devices are required."
        self.assertEqual(
            response.data[0],
            e_msg,
            msg="response.data[0] = {}".format(response.data[0]),
        )
