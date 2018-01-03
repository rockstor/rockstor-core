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


class AFPTests(APITestMixin, APITestCase):
    fixtures = ['fix4.json']
    BASE_URL = '/api/netatalk'

    @classmethod
    def setUpClass(cls):
        super(AFPTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch(
            'storageadmin.views.netatalk.mount_share')
        cls.mock_mount_share = cls.patch_mount_share.start()

        cls.patch_refresh_afp_config = patch(
            'storageadmin.views.netatalk.refresh_afp_config')
        cls.mock_refresh_afp_config = cls.patch_refresh_afp_config.start()

        cls.patch_systemctl = patch('storageadmin.views.netatalk.systemctl')
        cls.mock_systemctl = cls.patch_systemctl.start()

    @classmethod
    def tearDownClass(cls):
        super(AFPTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with id
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get afp-export with id
        response = self.client.get('%s/2' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

    def test_post_requests(self):
        """
        invalid afp export operations
        1. Create afp export without providing share names
        2. Create a afp export for the share that is already been exported
        """

        # create afp export with no share names
        data = {'time_machine': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Must provide share names.'
        self.assertEqual(response.data['detail'], e_msg)

        # create afp export with invalid time machine value
        data = {'shares': ('share2',), 'time_machine': 'invalid', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Time_machine must be yes or no. Not (invalid).'
        self.assertEqual(response.data['detail'], e_msg)

        # create afp export with already existing share
        data = {'shares': ('share1',), 'time_machine': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Share (share1) is already exported via AFP.'
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'shares': ('share3',), 'time_machine': 'yes', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_put_requests(self):
        """
        1. Edit afp export that does not exists
        2. Edit afp export
        """
        # edit afp export that does not exist
        afp_id = 1
        data = {'shares': ('share1',), 'time_machine': 'yes', }
        response = self.client.put('%s/%d' % (self.BASE_URL, afp_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'AFP export for the id (1) does not exist.'
        self.assertEqual(response.data['detail'], e_msg)

        # edit afp export with invalid time machine value
        afp_id = 8
        data = {'shares': ('share1',), 'time_machine': 'invalid', }
        response = self.client.put('%s/%d' % (self.BASE_URL, afp_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)

        e_msg = 'Time_machine must be yes or no. Not (invalid).'
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        afp_id = 8
        data = {'shares': ('share2',), 'time_machine': 'yes', }
        response = self.client.put('%s/%d' % (self.BASE_URL, afp_id),
                                   data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_delete_requests(self):
        """
        1. Delete afp export that does not exist
        2. Delete afp export
        """
        # Delete samba that does nor exists
        afp_id = 12
        response = self.client.delete('%s/%d' % (self.BASE_URL, afp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'AFP export for the id (12) does not exist.'
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        afp_id = 8
        response = self.client.delete('%s/%d' % (self.BASE_URL, afp_id))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
