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
from rest_framework.test import APIClient
from storageadmin.tests.test_api import APITestMixin


class AppliancesTests(APITestMixin):
    # Fixture expected to contain appliance self reference (created during setup)
    # and a remote (replication) appliance ("current_appliance": False).
    #
    # bin/django dumpdata storageadmin.appliance --natural-foreign --indent 4 >
    # src/rockstor/storageadmin/fixtures/test_appliances.json
    #
    # ./bin/test -v 2 -p test_appliances.py
    fixtures = ["test_api.json", "test_appliances.json"]
    BASE_URL = "/api/appliances"
    client = APIClient()
    databases = '__all__'

    @classmethod
    def setUpClass(cls):
        super(AppliancesTests, cls).setUpClass()

        # post mocks
        cls.patch_set_token = patch("storageadmin.views.appliances.set_token")
        cls.mock_set_token = cls.patch_set_token.start()
        cls.mock_set_token.return_value = {}

        cls.patch_api_call = patch("storageadmin.views.appliances.api_call")
        cls.mock_api_call = cls.patch_api_call.start()
        cls.mock_api_call.return_value = {"uuid": "01"}

        # Mock gethostname() to return hostname under our control,
        # _update_hostname() uses gethostname to update the db.
        cls.patch_gethostname = patch("storageadmin.views.appliances.gethostname")
        cls.mock_gethostname = cls.patch_gethostname.start()
        cls.mock_gethostname.return_value = "test-host"

        # Mock sethostname() so we don't actually set our host's hostname.
        cls.patch_sethostname = patch("storageadmin.views.appliances.sethostname")
        cls.mock_sethostname = cls.patch_sethostname.start()
        cls.mock_sethostname.return_value = [""], [""], 0

    @classmethod
    def tearDownClass(cls):
        super(AppliancesTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_requests_1(self):

        # failed set_token
        data = {
            "ip": "1.1.1.1",
            "mgmt_port": "443",
            "client_id": "",
            "client_secret": "",
            "current_appliance": False,
        }
        self.mock_set_token.side_effect = Exception()
        response = self.client.post(self.BASE_URL, data=data, follow=True)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Failed to authenticate on remote appliance. Verify port "
            "number, id and secret are correct and try again."
        )
        self.assertEqual(response.data[0], e_msg)
        self.mock_set_token.side_effect = None

        # failed api_call
        data = {
            "ip": "1.1.1.1",
            "mgmt_port": "443",
            "client_id": "",
            "client_secret": "",
            "current_appliance": False,
        }
        self.mock_api_call.side_effect = Exception()
        response = self.client.post(self.BASE_URL, data=data, follow=True)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Failed to get remote appliance information. Verify all "
            "inputs and try again."
        )
        self.assertEqual(response.data[0], e_msg)
        self.mock_api_call.side_effect = None

    def test_post_requests_2(self):

        # ip/hostname already exists
        data = {
            "ip": "rleap15-3aarch64.lan",
            "mgmt_port": "443",
            "client_id": "",
            "client_secret": "",
            "current_appliance": False,
        }
        # N.B. if the following is set to follow=True we get infinite recursion !!
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "The appliance with ip = rleap15-3aarch64.lan already exists "
            "and cannot be added again."
        )
        self.assertEqual(response.data[0], e_msg)

        # invalid management port
        data = {
            "ip": "1.1.1.1",
            "mgmt_port": "invalid",
            "client_id": "",
            "client_secret": "",
            "current_appliance": False,
        }
        response = self.client.post(self.BASE_URL, data=data, follow=True)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid management port (invalid) supplied. Try again."
        self.assertEqual(response.data[0], e_msg)

        # happy path
        data = {
            "ip": "1.1.1.1",
            "mgmt_port": "443",
            "client_id": "",
            "client_secret": "",
            "current_appliance": False,
        }
        response = self.client.post(self.BASE_URL, data=data, follow=True)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):

        # delete appliance that does not exists
        app_id = 99999
        response = self.client.delete("{}/{}".format(self.BASE_URL, app_id))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Appliance id ({}) does not exist.".format(app_id)
        self.assertEqual(response.data[0], e_msg)
