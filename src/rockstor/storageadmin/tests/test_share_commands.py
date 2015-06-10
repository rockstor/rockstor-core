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
from storageadmin.models import Share

class ShareCommandTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/shares'
    
    @classmethod
    def setUpClass(cls):
        super(ShareCommandTests, cls).setUpClass()

        # post mocks
        cls.patch_update_quota = patch('storageadmin.views.share_command.update_quota')
        cls.mock_update_quota = cls.patch_update_quota.start()
        cls.mock_update_quota.return_value = 'foo'

        cls.patch_rollback_snap = patch('storageadmin.views.share_command.rollback_snap')
        cls.mock_rollback_snap = cls.patch_rollback_snap.start()
        cls.mock_rollback_snap.return_value = True

        


    @classmethod
    def tearDownClass(cls):
        super(ShareCommandTests, cls).tearDownClass() 
        
    def test_get(self):
        """
        Test GET request
        1. Get base URL
        """
        self.get_base(self.BASE_URL) 
    
    def test_invalid_requests(self):
    
        """
        Test  invalid Post request
        1. Clone a share that does not exist
        """
        # Clone a share that does not exist
        
        data = {'name':'clone_share1'}
        shareName = 'newshare'
        e_msg = ('Share(newshare) does not exist')
        response = self.client.post('%s/%s/clone' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
                         
        # invalid clone names
        
        # create share
        data1 = {'sname': 'share1', 'pool': 'rockstor_rockstor', 'size': 100}
        response1 = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response1.status_code, status.HTTP_200_OK, msg=response1.data)
        self.assertEqual(response1.data['name'], 'share1')
        
        invalid_clone_names = ('clone $','-clone', '.clone', '', ' ',)
        e_msg = ('Clone name is invalid. It must start with a letter and can contain letters, digits, _, . and - characters')
        for cname in invalid_clone_names:
           data['name'] = cname
           response2 = self.client.post('%s/share1/clone' % self.BASE_URL, data=data)
           self.assertEqual(response2.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response2.data)
           self.assertEqual(response2.data['detail'], e_msg)
                           
