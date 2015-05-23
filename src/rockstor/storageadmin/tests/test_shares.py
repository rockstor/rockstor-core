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

    @classmethod
    def setUpClass(self):

    # static mocks
    # update quota -- return true
    # share id -- ?

    # get mocks

        # post mocks
        self.patch_add_share = patch('storageadmin.views.share.add_share')
        self.mock_add_share = self.patch_add_share.start()
        self.mock_add_share.return_value = True

        self.patch_share_id = patch('storageadmin.views.share.share_id')
        self.mock_share_id = self.patch_share_id.start()
        self.mock_share_id.return_value = 'derp'

        self.patch_update_quota = patch('storageadmin.views.share.update_quota')
        self.mock_update_quota = self.patch_update_quota.start()
        self.mock_update_quota.return_value = True

        self.patch_is_share_mounted = patch('storageadmin.views.share.is_share_mounted')
        self.mock_is_share_mounted = self.patch_is_share_mounted.start()
        self.mock_is_share_mounted.return_value = True

        self.patch_set_property = patch('storageadmin.views.share.set_property')
        self.mock_set_property = self.patch_set_property.start()
        self.mock_set_property.return_value = True

    # put mocks

    # delete mocks

    @classmethod
    def tearDownClass(self):
        patch.stopall()

    def setUp(self):
        self.client.login(username='admin', password='admin')

    def tearDown(self):
        self.client.logout()

    def test_auth(self):
        """
        unauthorized api access
        """
        self.client.logout()
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_base(self):
        """
        get on the base url.
        """
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
        # will need to create a pool first (or use root pool)

        # create a share on a pool that does not exist
        data = {'sname': 'rootshare', 'pool': 'does_not_exist', 'size': 1048576}
        e_msg = ('Pool(does_not_exist) does not exist.')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)

        # create a share on root pool
        data['pool'] = 'rockstor_rockstor'
        response2 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK, msg=response2.data)
        self.assertEqual(response2.data['name'], 'rootshare')

        # test share with invalid compression
        data['compression'] = 'invalid'
        e_msg2 = ("Unsupported compression algorithm(invalid). Use one of ('lzo', 'zlib', 'no')")
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg2)

        # create a share with invalid size (too small)
        data2 = {'sname': 'too_small', 'pool': 'rockstor_rockstor', 'size': 0}
        e_msg3 = ('Share size should atleast be 100KB. Given size is 0KB')
        response3 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response3.data)
        self.assertEqual(response3.data['detail'], e_msg3)

        # create a share with invalid size (non integer)
        data2['size'] = 'non int'
        e_msg3 = ('Share size must be an integer')
        response4 = self.client.post(self.BASE_URL, data=data2)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response4.data)
        self.assertEqual(response4.data['detail'], e_msg3)
        # TODO find out how it converts GB vs TB
            # Share size should atleast be 100KB
            # Accepted formats: GB & TB... try KB
            # what is size converted to? request for 1GB is 1048576. response
                # 1GB = 1048576
                # 4GB = 4194304

        # test share with invalid name
            # share with that name already exists
            # pool with that name already exists

        # test share with a pool that has no disks

        # test replica?




        # compression here? or seperate method?

    def test_delete_share(self):
        self.assertEqual(1,2)

    def test_resize_share(self):
        self.assertEqual(1,2)
        # PUT operation
        # test valid / invalid sizes
        # appears to accept invalid high size & reassigns max available


