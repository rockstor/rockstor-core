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


class NFSExportTests(APITestMixin, APITestCase):
    fixtures = ['fix4.json']
    BASE_URL = '/api/nfs-exports'

    @classmethod
    def setUpClass(cls):
        super(NFSExportTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.nfs_exports.'
                                      'mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = 'out', 'err', 0

        cls.patch_is_share_mounted = patch('storageadmin.views.nfs_exports.'
                                           'is_share_mounted')
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = False

        cls.patch_refresh_nfs_exports = patch('storageadmin.views.nfs_exports.'
                                              'refresh_nfs_exports')
        cls.mock_refresh_nfs_exports = cls.patch_refresh_nfs_exports.start()
        cls.mock_refresh_nfs_exports.return_value = 'out', 'err', 0

    @classmethod
    def tearDownClass(cls):
        super(NFSExportTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get nfs-export with id
        response = self.client.get('%s/11' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

    def test_invalid_get(self):
        # get nfs-export with invalid id
        response = self.client.get('%s/12' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response)

    def test_post_requests(self):
        """
        invalid nfs-export api operations
        1. Add nfs-export without providing share names
        2  Add nfs-export
        3. Add nfs-export for the share that is already been exported

        """
        # Add nfs-export without providing share names
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = 'out', 'err', 0

        data = {'host_str': '*', 'mod_choice': 'rw', 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Cannot export without specifying shares')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data1 = {'shares': ('share2',), 'host_str': '*.edu',
                 'mod_choice': 'rw', 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Add nfs-export for the share that is already been exported
        data1 = {'shares': ('share1',), 'host_str': '*', 'mod_choice': 'rw',
                 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('An export already exists for the host string: *')
        self.assertEqual(response.data['detail'], e_msg)

        # Add nfs-export with invalid nfs-client
        data1 = {'shares': ('share1',), 'host_str': '*', 'mod_choice': 'rw',
                 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('An export already exists for the host string: *')
        self.assertEqual(response.data['detail'], e_msg)

    def test_no_nfs_client(self):
        # Add nfs-export without specifying nfs-clients(host string). The
        # server side defaults the host string to *

        self.mock_refresh_nfs_exports.side_effect = None
        data1 = {'shares': ('clone1',), 'mod_choice': 'rw',
                 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['host_str'], '*')

    def test_invalid_nfs_client2(self):

        # invalid post request
        # Add nfs-export providing invalid nfs client
        self.mock_refresh_nfs_exports.side_effect = Exception()

        data1 = {'shares': ('clone1',), 'host_str': 'host%%%edu',
                 'mod_choice': 'rw', 'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Invalid Hostname or IP: host%%%edu')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    def test_invalid_nfs_client3(self):

        # invalid put request
        # edit nfs-export providing invalid nfs-client
        self.mock_refresh_nfs_exports.side_effect = Exception()
        nfs_id = 11
        data = {'shares': ('share2',), 'host_str': 'host%%%edu',
                'admin_host': ' ', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid Hostname or IP: host%%%edu')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    def test_invalid_admin_host1(self):

        # invalid post request
        # Add nfs-export providing invalid admin host
        self.mock_refresh_nfs_exports.side_effect = Exception()
        data = {'shares': ('clone1',), 'host_str': '*.edu',
                'admin_host': 'admin%host', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid admin host: admin%host')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    def test_invalid_admin_host2(self):
        # invalid put request
        # edit nfs-export providing invalid admin host
        self.mock_refresh_nfs_exports.side_effect = Exception()
        nfs_id = 11
        data = {'shares': ('share2',), 'host_str': '*.edu',
                'admin_host': 'admin%host', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid admin host: admin%host')
        self.assertEqual(response.data['detail'], e_msg)
        self.mock_refresh_nfs_exports.side_effect = None

    def test_put_requests(self):
        """
        1. Edit nfs-export
        2. Edit nfs-export with no shares
        3. Edit nfs-export that does not exists
        """

        # Edit nfs-export with no shares
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = 'out', 'err', 0

        nfs_id = 11
        data = {'host_str': '*.edu', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Cannot export without specifying shares')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        nfs_id = 11
        data = {'shares': ('share2',), 'host_str': '*.edu', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # happy path2 with admin host
        nfs_id = 11
        data = {'shares': ('share2',), 'host_str': '*.edu',
                'admin_host': 'host', 'mod_choice': 'rw',
                'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # edit nfs-export that does not exist
        nfs_id = 5
        data = {'shares': ('share2',), 'host_str': '*.edu',
                'mod_choice': 'rw', 'sync_choice': 'async', }
        response = self.client.put('%s/%d' % (self.BASE_URL, nfs_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('NFS export with id: 5 does not exist')
        self.assertEqual(response.data['detail'], e_msg)

    def test_delete_requests(self):

        """
        1. Delete nfs-export
        2. Delete nfs-export that does not exist
        """

        # happy path
        nfs_id = 11
        response = self.client.delete('%s/%d' % (self.BASE_URL, nfs_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Delete nfs-export that does nor exists
        nfs_id = 5
        response = self.client.delete('%s/%d' % (self.BASE_URL, nfs_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('NFS export with id: 5 does not exist')
        self.assertEqual(response.data['detail'], e_msg)

    def test_adv_nfs_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base('/api/adv-nfs-exports')

    def test_adv_nfs_post_requests(self):
        # without specifying entries
        data = {}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Cannot export without specifying entries')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'entries': ["/export/share2 *.edu(rw,async,insecure)"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # Invalid entries
        data = {'entries': ["/export/share2"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid exports input -- /export/share2')
        self.assertEqual(response.data['detail'], e_msg)

        # Invalid entries
        data = {'entries': ["/export/share2 *.edu(rw,async,insecure"]}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid exports input -- /export/share2 *.edu(rw,async,'
                 'insecure. offending section: *.edu(rw,async,insecure')
        self.assertEqual(response.data['detail'], e_msg)

        # Invalid entries
        data = {'entries': ['invalid']}
        response = self.client.post('/api/adv-nfs-exports', data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid exports input -- invalid')
        self.assertEqual(response.data['detail'], e_msg)
