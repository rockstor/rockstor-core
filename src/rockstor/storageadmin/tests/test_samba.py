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


class SambaTests(APITestMixin, APITestCase):
    fixtures = ['fix3.json']
    BASE_URL = '/api/samba'

    @classmethod
    def setUpClass(cls):
        super(SambaTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.samba.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()

        cls.patch_is_share_mounted = patch('storageadmin.views.samba.'
                                           'is_share_mounted')
        cls.mock_is_share_mounted = cls.patch_is_share_mounted.start()
        cls.mock_is_share_mounted.return_value = False

        cls.patch_status = patch('storageadmin.views.samba.status')
        cls.mock_status = cls.patch_status.start()
        cls.mock_status.return_value = 'out', 'err', 0

        cls.patch_restart_samba = patch('storageadmin.views.samba.'
                                        'restart_samba')
        cls.mock_status = cls.patch_restart_samba.start()

        cls.patch_refresh_smb_config = patch('storageadmin.views.samba.'
                                             'refresh_smb_config')
        cls.mock_refresh_smb_config = cls.patch_refresh_smb_config.start()
        cls.mock_refresh_smb_config.return_value = 'smbconfig'

    @classmethod
    def tearDownClass(cls):
        super(SambaTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get sambashare with id
        response = self.client.get('%s/1' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

        # get sambashare with non-existant id
        response = self.client.get('%s/5' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response)

    def test_post_requests(self):
        """
        invalid samba api operations
        1. Create a samba without providing share names
        2. Create a samba export for the share that is already been exported
        """

        # create samba export with no share names
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = ('Must provide share names')
        self.assertEqual(response.data['detail'], e_msg)

        # create samba with invalid browsable, guest_ok, read_only choices
        data = {'shares': ('share1',), 'browsable': 'Y', 'guest_ok': 'yes',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for browsable. Possible choices '
                 'are yes or no.')
        self.assertEqual(response.data['detail'], e_msg)

        data = {'shares': ('share1',), 'browsable': 'yes', 'guest_ok': 'Y',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for guest_ok. Possible options are '
                 'yes or no.')
        self.assertEqual(response.data['detail'], e_msg)

        data = {'shares': ('share1',), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'Y'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for read_only. Possible options '
                 'are yes or no.')
        self.assertEqual(response.data['detail'], e_msg)

        # create samba export
        # we use 'share1' which is available from the fixture, fix3.json
        data = {'shares': ('share1', ), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'yes', 'admin_users': ('admin', ),
                'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        smb_id = response.data['id']

        # test get of detailed view for the smb_id
        response = self.client.get('%s/%d' % (self.BASE_URL, smb_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['id'], smb_id)

        # create samba exports for multiple(3) shares at once
        data = {'shares': ('share2', 'share3', 'share4'), 'browsable': 'yes',
                'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': ('admin', )}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # create samba export with no admin users
        data = {'shares': ('share5', ), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'yes', 'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # create samba export with the share that is already been exported
        # above
        data = {'shares': ('share1', ), 'browsable': 'no', 'guest_ok': 'yes',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Share(share1) is already exported via Samba')
        self.assertEqual(response.data['detail'], e_msg)

    def test_put_requests(self):
        """
        1. Edit samba that does not exists
        2. Edit samba
        """
        # edit samba that does not exist
        smb_id = 12
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': 'usr'}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Samba export for the id(12) does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # edit samba with invalid custom config
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'custom_config': 'CONFIGXYZ'}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('custom config must be a list of strings')
        self.assertEqual(response.data['detail'], e_msg)

        # test mount_share exception case
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', }
        self.mock_mount_share.side_effect = KeyError('error')
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Failed to mount share(share6) due to a low level error.')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        smb_id = 1
        self.mock_mount_share.side_effect = None
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': ('admin', ), 'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # edit samba export with admin user other than admin
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': ('admin2', ), 'custom_config': ('CONFIG',
                                                               'XYZ')}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # edit samba export passing no admin users
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        """
        1. Delete samba that does not exist
        2. Delete samba
        """
        # Delete samba that does nor exists
        smb_id = 12
        response = self.client.delete('%s/%d' % (self.BASE_URL, smb_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Samba export for the id(12) does not exist')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        smb_id = 1
        response = self.client.delete('%s/%d' % (self.BASE_URL, smb_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
