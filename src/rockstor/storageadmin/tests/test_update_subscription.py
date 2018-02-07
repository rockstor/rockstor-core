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


class UpdateSubscriptionTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/update-subscriptions'

    @classmethod
    def setUpClass(cls):
        super(UpdateSubscriptionTests, cls).setUpClass()

        # post mocks

        cls.patch_repo_status = patch('storageadmin.views.update_subscription'
                                      '.repo_status')
        cls.mock_repo_status = cls.patch_repo_status.start()
        cls.mock_repo_status.return_value = ('active', 'public repo')

        cls.patch_switch_repo = patch('storageadmin.views.update_subscription.'
                                      'switch_repo')
        cls.mock_switch_repo = cls.patch_switch_repo.start()

    @classmethod
    def tearDownClass(cls):
        super(UpdateSubscriptionTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):

        # happy path
        response = self.client.post('%s/activate-stable' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         msg=response.data)

        e_msg = 'Activation code is required for Stable subscription.'
        self.assertEqual(response.data[0], e_msg)

        # # repo staturn returning inactive

        # TODO: may need to mock appliance object.
        # self.mock_repo_status.return_value = ('inactive', 'public repo')
        # response = self.client.post('%s/activate-testing' % self.BASE_URL)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        # # e_msg = (
        # #         'Activation code (None) could not be authorized. Verify the '
        # #         'code and try again. If the problem persists, contact '
        # #         'support@rockstor.com')
        # # TODO Test needs updating to accommodate for newer message + app uuid.
        # appliance_uuid = '1234'
        # e_msg = (
        #         'Activation code (None) could not be authorized for your '
        #         'appliance (1234). Verify the code and try again. If the '
        #         'problem persists, email support@rockstor.com with this '
        #         'message.')
        # self.assertEqual(response.data[0], e_msg)

        self.mock_repo_status.return_value = ('active', 'public repo')

        # repo staturn returning not active
        # TODO: may need mock appliance object
        # self.mock_repo_status.return_value = ('invalid', 'public repo')
        # response = self.client.post('%s/activate-testing' % self.BASE_URL)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
        #                  msg=response.data)
        #
        # e_msg = ('Failed to activate subscription. Status code: invalid '
        #          'details: public repo')
        # self.assertEqual(response.data[0], e_msg)
        self.mock_repo_status.return_value = ('active', 'public repo')

        # happy path
        # TODO: may need mock appliance object
        # response = self.client.post('%s/activate-testing' % self.BASE_URL)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        # happy path
        data = {'activation_code': 'pass'}
        response = self.client.post('%s/activate-stable'
                                    % self.BASE_URL, data=data)
        # TODO: another "Appliance matching query does not exist"
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
        data = {'name': 'stable'}
        response = self.client.post('%s/check-status'
                                    % self.BASE_URL, data=data)
        # TODO: UpdateSubscription matching query does not exist
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
