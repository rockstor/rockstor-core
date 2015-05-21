__author__ = 'samrichards'

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

from storageadmin.models import Pool

# TODO inheritance structure... tests/test_api.py
# 1. determine all mocks needed for share views
# 2. overlapping mocks for pools & shares? place in parent class
# 3.


class ShareTests(APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/shares'

    # @classmethod
    # def setUpClass(self):

    # static mocks
    # update quota -- return true
    # share id -- ?

    # get mocks

    # post mocks

    # put mocks

    # delete mocks

    # @classmethod
    # def tearDownClass(self):
    #     patch.stopall()

    # def setUp(self):
    #     self.client.login(username='admin', password='admin')

    def test_auth(self):
        """
        unauthorized api access
        """
        # self.client.logout()
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_base(self):
        """
        get on the base url.
        """
        self.client.login(username='admin', password='admin')
        response1 = self.client.get(self.BASE_URL)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)

    def test_name_regex(self):
        self.assertEqual(1,2)

    def test_invalid_api_requests(self):
        self.assertEqual(1,2)

    def test_compression(self):
        self.assertEqual(1,2)
        # diff compressions on creation
        # edit compression post creation... this is a POST w/ compress command in URL

    def test_create_share(self):
        self.assertEqual(1,2)
        # test valid / invalide share sizes
        # valid / invalid pools
        # compression here? or seperate method?

    def test_delete_share(self):
        self.assertEqual(1,2)

    def test_resize_share(self):
        self.assertEqual(1,2)
        # PUT operation
        # test valid / invalid sizes
        # appears to accept invalid high size & reassigns max available


