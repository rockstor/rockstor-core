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

class ShareIscsiTests(APITestMixin, APITestCase):
    fixtures = ['fix1.json']
    BASE_URL = '/api/shares'

    @classmethod
    def setUpClass(cls):
        super(ShareIscsiTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.share_iscsi.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = True
       
        cls.patch_export_iscsi = patch('storageadmin.views.share_iscsi.export_iscsi')
        cls.mock_export_iscsi = cls.patch_export_iscsi.start()
        cls.mock_export_iscsi.return_value = 'out', 'rc', 0
                   
    @classmethod
    def tearDownClass(cls):
        super(ShareIscsiTests, cls).tearDownClass()

    def test_get(self):
        
        # get base URL
        # 'share1' is the pool already created and exits in fix1.json 
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        response = self.client.get('%s/share1/iscsi/' %self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        
    def test_post_requests(self):
    
        # invalid share
        data = {}
        response = self.client.post('%s/invalid/iscsi/' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code, 
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        
        e_msg = ('Share matching query does not exist.')
        self.assertEqual(response.data['detail'], e_msg)
   
        # happy path
        data = {}
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
   
        # happy path
        data = {}
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        err_msg = 'Already exported via iscsi'
        self.assertEqual(response.data['detail'], err_msg)
    
    # test for share already exported via nfs     
    @mock.patch('storageadmin.views.share_iscsi.NFSExport')    
    def test_post_request2(self, mock_nfs):
          
        # Share already exported via nfs
        mock_nfs.objects.filter(share='share1').exists.return_value = True
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        err_msg = 'Already exported via nfs'
        self.assertEqual(response.data['detail'], err_msg)      
        
    
    # test for share already exported via samba     
    @mock.patch('storageadmin.views.share_iscsi.SambaShare')
    def test_post_request3(self, mock_smb):     
        # Share already exported via nfs
        mock_smb.objects.filter(share='share1').exists.return_value = True
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        err_msg = 'Already exported via Samba'
        self.assertEqual(response.data['detail'], err_msg)      
       
    def test_post_requests4(self):    
         
        # invalid tid option
        data = {'tname': 'newscsi','tid': 'invalid'}
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        err_msg = 'tid must be an integer'
        self.assertEqual(response.data['detail'], err_msg)   
        
        # happy path with options
        data = {'tname': 'newscsi','tid': -1}
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
                         
                                          
    def test_delete_requests(self):
        
        response = self.client.post('%s/share1/iscsi/' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        response = self.client.delete('%s/share1/iscsi/' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)                 