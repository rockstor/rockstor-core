"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from rest_framework import status
from rest_framework.test import APITestCase
from mock import patch
from storageadmin.tests.test_api import APITestMixin


class AppliancesTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/appliances'

    @classmethod
    def setUpClass(cls):
        super(AppliancesTests, cls).setUpClass()

        # post mocks
        cls.patch_set_token = patch('storageadmin.views.appliances.set_token')
        cls.mock_set_token = cls.patch_set_token.start()
        cls.mock_set_token.return_value = {}

        cls.patch_api_call = patch('storageadmin.views.appliances.api_call')
        cls.mock_api_call = cls.patch_api_call.start()
        cls.mock_api_call.return_value = {'uuid': '01'}

    @classmethod
    def tearDownClass(cls):
        super(AppliancesTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):
        # failed set_token
        data = {'ip': '1.1.1.1', 'mgmt_port': '443', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        self.mock_set_token.side_effect = Exception()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Failed to authenticate on remote appliance. Verify port '
                 'number, id and secret are correct and try again.')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_set_token.side_effect = None

        # failed api_call
        data = {'ip': '1.1.1.1', 'mgmt_port': '443', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        self.mock_api_call.side_effect = Exception()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Failed to get remote appliance information. Verify all '
                 'inputs and try again.')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_api_call.side_effect = None

        # ip already exists
        data = {'ip': '192.168.56.101', 'mgmt_port': '443', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('The appliance with ip = 192.168.56.101 already exists '
                 'and cannot be added again')
        self.assertEqual(response.data['detail'], e_msg)

        # invalid management port
        data = {'ip': '1.1.1.1', 'mgmt_port': 'invalid', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Invalid management port(invalid) supplied. Try again')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'ip': '1.1.1.1', 'mgmt_port': '443', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        # add appliance
        data = {'ip': '1.1.1.1', 'mgmt_port': '443', 'client_id': '',
                'client_secret': '', 'current_appliance': False}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # delete appliance that does not exists
        app_id = 11
        response = self.client.delete('%s/%d' % (self.BASE_URL, app_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Appliance(11) does not exist')
        self.assertEqual(response.data['detail'], e_msg)
