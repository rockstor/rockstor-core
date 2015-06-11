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
from rest_framework.response import Response
from rest_framework.test import APITestCase
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin
from storageadmin.models import Share, Snapshot

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
        
        cls.patch_create_clone = patch('storageadmin.views.share_command.create_clone')
        cls.mock_create_clone = cls.patch_create_clone.start()
        cls.mock_create_clone.return_value = Response('{"message": "ok!"}')
        

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
        2. Rollback a share that has no snapshots
        """
        # Clone a share that does not exist
        
        data = {'name':'cshare1'}
        shareName = 'invalidshare'
        e_msg = ('Share(invalidshare) does not exist')
        response = self.client.post('%s/%s/clone' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
        
        # Rollback a share that has no snapshots
        
        # create share
        data = {'sname': 'rshare1', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'rshare1')
        
        e_msg = ('Snapshot(rsnap1) does not exist for this Share(rshare1)')
        shareName = 'rshare1'
        data = {'name':'rsnap1'}
        response = self.client.post('%s/%s/rollback' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
                         
       
    
    def test_clone_command(self):
        """         
        1. Clone a share 
        """
        # create share
        data = {'sname': 'cshare2', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, 
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'cshare2')
    
        # clone a share
        data = {'name':'clone'}
        shareName = 'cshare2'
        response = self.client.post('%s/%s/clone' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
    
    @mock.patch('storageadmin.views.share.SambaShare')
    @mock.patch('storageadmin.views.share.NFSExport')
    @mock.patch('storageadmin.views.share.Snapshot')   
    def test_rollback_command(self, mock_snapshot, mock_nfs, mock_samba):                     
        """                 
        1. Rollback a share 
        """
        # create share
        data = {'sname': 'rshare2', 'pool': 'rockstor_rockstor', 'size': 100}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, 
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['name'], 'rshare2')
        share = Share.objects.get(name='rshare2')
        
        # create mock snapshot and rollback share
        shareName = 'rshare2'
        data = {'name':'rsnap2'}
        mock_snapshot.objects.get(share=share, name='rsnap2').return_value = {'snapshot_name':'rsnap2'}
        response = self.client.post('%s/%s/rollback' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)   
        mock_snapshot.objects.get(share=share, name='rsnap2').return_value = null
        
        # Rollback share with NFS export
        mock_nfs.objects.filter(share=share).exists.return_value = True
        e_msg = ('Share(rshare2) cannot be rolled back as it is '
                 'exported via nfs. Delete nfs exports and '
                 'try again')
        response = self.client.post('%s/%s/rollback' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)   
        self.assertEqual(response.data['detail'], e_msg)
        mock_nfs.objects.filter(share=share).exists.return_value = False

        # Rollback share that is shared via Samba
        mock_samba.objects.filter(share=share).exists.return_value = True
        e_msg = ('Share(rshare2) cannot be rolled back as it is shared'
                 ' via Samba. Unshare and try again')
        response = self.client.post('%s/%s/rollback' % (self.BASE_URL, shareName), data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], e_msg)
        mock_samba.objects.filter(share=share).exists.return_value = False