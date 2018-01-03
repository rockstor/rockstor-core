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


class PoolBalanceTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/pools'

    @classmethod
    def setUpClass(cls):
        super(PoolBalanceTests, cls).setUpClass()

        # post mocks

        cls.patch_balance_status = patch('storageadmin.views.pool_balance.'
                                         'balance_status')
        cls.mock_balance_status = cls.patch_balance_status.start()
        cls.mock_balance_status.return_value = {'status': 'finished',
                                                'percent_done': '100'}

    @classmethod
    def tearDownClass(cls):
        super(PoolBalanceTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        # 'pool1' is the pool already created and exits in fix1.json
        response = self.client.get('%s/pool1/balance' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):

        # invalid pool
        data = {'force': 'true'}
        response = self.client.post('%s/invalid/balance' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Pool (invalid) does not exist.'
        self.assertEqual(response.data['detail'], e_msg)

        # Invalid scrub command
        data = {'force': 'true'}
        response = self.client.post('%s/pool1/balance/invalid' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Unknown balance command (invalid).'
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'force': 'true'}
        response = self.client.post('%s/pool1/balance' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # happy path
        data = {'force': 'true'}
        response = self.client.post('%s/pool1/balance/status' % self.BASE_URL,
                                    data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
