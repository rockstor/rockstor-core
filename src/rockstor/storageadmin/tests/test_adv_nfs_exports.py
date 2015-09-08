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
from system.services import systemctl
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

class AdvNFSExportTests(APITestMixin, APITestCase):
    fixtures = ['fix4.json']
    BASE_URL = '/api/adv-nfs-exports'

    @classmethod
    def setUpClass(cls):
        super(AdvNFSExportTests, cls).setUpClass()

        # post mocks
        cls.patch_refresh_wrapper = patch('storageadmin.views.nfs_exports.refresh_wrapper')
        cls.mock_refresh_wrapper = cls.patch_refresh_wrapper.start()
        cls.mock_refresh_wrapper.return_value = False

       

    @classmethod
    def tearDownClass(cls):
        super(AdvNFSExportTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

  
    def test_post_requests(self):
        
        
        # without specifying entries
        data = { }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Cannot export without specifying entries')
        self.assertEqual(response.data['detail'], e_msg)
        
        # happy path
        data = {'entries':["/export/share2 *.edu(rw,async,insecure)"] }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
                         
        # Invalid entries
        data = {'entries':['invalid'] }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ('Invalid exports input -- invalid')
        self.assertEqual(response.data['detail'], e_msg)             
            