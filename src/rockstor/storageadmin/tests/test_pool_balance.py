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
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin
from storageadmin.models import Pool


class PoolBalanceTests(APITestMixin, APITestCase):
    # fixture assumed to have:
    # 1 non sys pool (id=2, name='rock-pool', raid='raid1')
    fixtures = ['test_pool_scrub_balance.json']
    BASE_URL = '/api/pools'

    @classmethod
    def setUpClass(cls):
        super(PoolBalanceTests, cls).setUpClass()

        # post mocks

        # would be better to mock out all of _balance_start() on PoolMixin ?
        # rather than mount_root and start_balance within it.
        cls.patch_mount_root = patch('storageadmin.views.pool.'
                                        'mount_root')
        cls.mock_mount_root = cls.patch_mount_root.start()
        cls.mock_mount_root.return_value = '/mnt2/mock-pool'

        cls.patch_start_balance = patch('storageadmin.views.pool.'
                                        'start_balance')
        cls.mock_start_balance = cls.patch_start_balance.start()
        cls.mock_start_balance.return_value = None

        cls.patch_balance_status = patch('storageadmin.views.pool_balance.'
                                         'balance_status')
        cls.mock_balance_status = cls.patch_balance_status.start()
        cls.mock_balance_status.return_value = {'status': 'finished',
                                                'percent_done': '100'}

    @classmethod
    def tearDownClass(cls):
        super(PoolBalanceTests, cls).tearDownClass()

    @mock.patch('storageadmin.views.pool_balance.Pool')
    def test_get(self, mock_pool):

        temp_pool = Pool(id=2, name='rock-pool', raid='raid', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        # get base URL
        # Pool id=1 already created and exits in fixtures

        pId = 2
        response = self.client.get('{}/{}/balance'.format(self.BASE_URL, pId))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests_1(self):

        # invalid pool
        data = {'force': 'true'}
        non_pId = 99999
        # mock_pool.objects.get.side_effect = Pool.DoesNotExist
        r = self.client.post('{}/{}/balance'.format(self.BASE_URL, non_pId),
                             data=data)
        self.assertEqual(r.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)

        e_msg = 'Pool ({}) does not exist.'.format(non_pId)
        self.assertEqual(r.data[0], e_msg)

    @mock.patch('storageadmin.views.pool_balance.Pool')
    def test_post_requests_2(self, mock_pool):

        temp_pool = Pool(id=2, name='rock-pool', raid='raid', size=88025459)
        mock_pool.objects.get.return_value = temp_pool

        # Invalid scrub command
        data = {'force': 'true'}
        pId = 2
        r = self.client.post('{}/{}/balance/invalid'.format(self.BASE_URL,
                                                            pId), data=data)
        self.assertEqual(r.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=r.data)

        e_msg = 'Unknown balance command (invalid).'
        self.assertEqual(r.data[0], e_msg)

        # happy path
        data = {'force': 'true'}
        r = self.client.post('{}/{}/balance'.format(self.BASE_URL, pId),
                             data=data)
        self.assertEqual(r.status_code,
                         status.HTTP_200_OK, msg=r.data)

        # TODO: add more balance_status returns akin to:
        # self.mock_balance_status.return_value = {'status': 'running',
        #                                          'percent_done': '60'}
        # with check on reading this state.
        # Also add behavioural test for {'status': 'unknown'} such as for
        # unmounted volumes.
        # Plus non force alternatives.
        # and another series where we mock PoolBalance.

        # happy path
        data = {'force': 'true'}
        r = self.client.post('{}/{}/balance/status'.format(self.BASE_URL, pId),
                             data=data)
        self.assertEqual(r.status_code,
                         status.HTTP_200_OK, msg=r.data)
