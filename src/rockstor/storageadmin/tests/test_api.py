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
from rest_framework.test import APITestCase, APIClient
import mock
from mock import patch

# functionality for all API tests.

class APITestMixin(APITestCase):

    @classmethod
    def setUpClass(cls):
        # error handling run_command mocks
        cls.patch_run_command = patch('storageadmin.util.run_command')
        cls.mock_run_command = cls.patch_run_command.start()
        cls.mock_run_command.return_value = True

    @classmethod
    def tearDownClass(cls):
        patch.stopall()

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def tearDown(self):
        self.client.logout()

    # TODO way to make this test not run on base class?
    def test_get_base(self):
        """
        get on the base url.
        """
        response1 = self.client.get(self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)

        # TODO Could test get nonexistant item for each
        # e_msg = ('Not found')
        # response3 = self.client.get('%s/raid0pool' % self.BASE_URL)
        # self.assertEqual(response3.status_code,
        #                  status.HTTP_404_NOT_FOUND, msg=response3.data)
        # self.assertEqual(response3.data['detail'], e_msg)
