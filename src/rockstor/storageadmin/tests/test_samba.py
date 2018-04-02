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
import mock
from rest_framework import status
from rest_framework.test import APITestCase
from mock import patch

from storageadmin.models import Pool, Share, SambaCustomConfig, SambaShare
from storageadmin.tests.test_api import APITestMixin


class SambaTests(APITestMixin, APITestCase):
    # fixture with:
    # share-smb - SMB exported with defaults: (comment "Samba-Export")
    # {'browsable': 'yes', 'guest_ok': 'no', 'read_only': 'no'}
    # share2 - no SMB export
    # fixtures = ['fix3.json']
    fixtures = ['test_smb.json']
    BASE_URL = '/api/samba'

    @classmethod
    def setUpClass(cls):
        super(SambaTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch('storageadmin.views.samba.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()

        # mock Share model's mount_status utility
        # True = Share is mounted, False = Share unmounted
        cls.patch_mount_status = patch('system.osi.mount_status')
        cls.mock_mount_status = cls.patch_mount_status.start()
        cls.mock_mount_status.return_value = True

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

        # all values as per fixture
        cls.temp_pool = Pool(id=11, name='rock-pool', size=5242880)
        cls.temp_share_smb = Share(id=23, name='share-smb', pool=cls.temp_pool)
        cls.temp_sambashare = SambaShare(id=1, share=cls.temp_share_smb)
        # cls.temp_smb_custom_config = \
        #     SambaCustomConfig(id=1, smb_share=cls.temp_sambashare)

        cls.temp_share2 = Share(id=24, name='share2', pool=cls.temp_pool)

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

        # # get sambashare with id
        # response = self.client.get('{}/1'.format(self.BASE_URL))
        # self.assertEqual(response.status_code, status.HTTP_200_OK,
        #                  msg=response)

        # get sambashare with non-existant id
        response = self.client.get('{}/5'.format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND,
                         msg=response)

    def test_post_requests_1(self):
        """
        invalid samba api operations
        . Create a samba without providing share id
        """

        # create samba export with no share names
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Must provide share names.'
        self.assertEqual(response.data[0], e_msg)

    def test_post_requests_2(self):
        """
         . Create a samba export for the share that has already been exported
        """

        # create samba with invalid browsable, guest_ok, read_only choices
        data = {'shares': (24,), 'browsable': 'Y', 'guest_ok': 'yes',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for browsable. Possible choices '
                 'are yes or no.')
        self.assertEqual(response.data[0], e_msg)

        data = {'shares': (24,), 'browsable': 'yes', 'guest_ok': 'Y',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for guest_ok. Possible options are '
                 'yes or no.')
        self.assertEqual(response.data[0], e_msg)

        data = {'shares': (24,), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'Y'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Invalid choice for read_only. Possible options '
                 'are yes or no.')
        self.assertEqual(response.data[0], e_msg)

        # create samba export
        # we use share id 24 (share2) as not yet smb exported.
        data = {'shares': (24, ), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'yes', 'admin_users': ('admin', ),
                'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        smb_id = response.data['id']

        # test get of detailed view for the smb_id
        response = self.client.get('{}/{}'.format(self.BASE_URL, smb_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response.data['id'], smb_id)

        # # TODO: Needs multiple share instances mocked
        # # create samba exports for multiple(3) shares at once
        # data = {'shares': ('share2', 'share3', 'share4'), 'browsable': 'yes',
        #         'guest_ok': 'yes', 'read_only': 'yes',
        #         'admin_users': ('admin', )}
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        # create samba export with no admin users
        data = {'shares': ('share5', ), 'browsable': 'yes', 'guest_ok': 'yes',
                'read_only': 'yes', 'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # create samba export with the share that has already been exported
        # above
        data = {'shares': (24, ), 'browsable': 'no', 'guest_ok': 'yes',
                'read_only': 'yes'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Share (share2) is already exported via Samba.'
        self.assertEqual(response.data[0], e_msg)

    def test_put_requests_1(self):
        """
        . Edit samba that does not exists
        """

        # edit samba that does not exist
        smb_id = 99999
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': 'usr'}
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Samba export for the id ({}) does not exist.'.format(smb_id)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.samba.SambaShare')

    def test_put_requests_2(self, mock_sambashare):
        """
        1. Edit samba that does not exists
        2. Edit samba
        """

        mock_sambashare.objects.get.return_value = self.temp_sambashare

        # edit samba with invalid custom config
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'custom_config': 'CONFIGXYZ'}
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Custom config must be a list of strings.'
        self.assertEqual(response.data[0], e_msg)

        # test mount_share exception case
        # TODO: Fails on first assert
        # Note as mount isn't called unless the share is found not to be
        # mounted we indicate this via our mock of the share utility.

        self.mock_mount_status.return_value = False

        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes', }
        self.mock_mount_share.side_effect = KeyError('error')
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Failed to mount share (share-smb) due to a low level error.'
        self.assertEqual(response.data[0], e_msg)
        # Return share mock mounted_state to mounted
        self.mock_mount_status.return_value = True

        # happy path
        smb_id = 1
        self.mock_mount_share.side_effect = None
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': ('admin', ), 'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # edit samba export with admin user other than admin
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'admin_users': ('admin2', ), 'custom_config': ('CONFIG',
                                                               'XYZ')}
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # edit samba export passing no admin users
        smb_id = 1
        data = {'browsable': 'yes', 'guest_ok': 'yes', 'read_only': 'yes',
                'custom_config': ('CONFIG', 'XYZ')}
        response = self.client.put('{}/{}'.format(self.BASE_URL, smb_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests_1(self):
        """
        . Delete samba that does not exist
        """
        # Delete samba that does nor exists
        smb_id = 99999
        response = self.client.delete('{}/{}'.format(self.BASE_URL, smb_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Samba export for the id ({}) does not exist.'.format(smb_id)
        self.assertEqual(response.data[0], e_msg)

    @mock.patch('storageadmin.views.samba.SambaShare')
    def test_delete_requests_2(self, mock_sambashare):
        """
        . Delete samba

        """

        mock_sambashare.objects.get.return_value = self.temp_sambashare

        # happy path
        smb_id = 1
        response = self.client.delete('{}/{}'.format(self.BASE_URL, smb_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
