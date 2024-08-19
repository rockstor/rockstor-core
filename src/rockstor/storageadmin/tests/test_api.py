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
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


# functionality for all API tests.
class APITestMixin(APITestCase):
    # Models to have in fixture:
    # auth.user
    # bin/django dumpdata --natural-foreign --indent 4 auth.user > src/rockstor/storageadmin/fixtures/test_api.json

    @classmethod
    def setUpClass(cls):
        super(APITestMixin, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        patch.stopall()
        super(APITestMixin, cls).tearDownClass()

    def setUp(self):
        self.user = User.objects.get(username='admin')
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        # self.client.logout()
        self.client.force_authenticate(user=None)

    def get_base(self, baseurl, name=True):
        """
        Test GET request
        1. Get base URL
        2. Pass URL params
        3. Get nonexistant object
        """
        response = self.client.get(baseurl)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)

        # get object that doesn't exist
        if (name):
            response1 = self.client.get('%s/invalid' % baseurl)
        else:
            response1 = self.client.get('%s/1234567' % baseurl)
        self.assertEqual(response1.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response1)
