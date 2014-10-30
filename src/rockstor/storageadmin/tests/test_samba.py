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


class SambaTests(APITestCase):
    fixtures = ['storageadmin.json']
    BASE_URL = '/api/samba'
    data = {'shares': ('share1', ),
            'comment': 'samba export',
            'browsable': 'yes',
            'guest_ok': 'yes',
            'read_only': 'yes',
            'admin_users': ('smbuser', ), }
    exp_response = {'share': u'share1',
                    'admin_users': [{u'id': 2,
                                     'user': 2,
                                     'username': u'smbuser',
                                     'uid': 5002,
                                     'gid': 5002,
                                     'public_key': u'',
                                     'smb_shares': [1]}],
                    u'id': 1,
                    'path': u'/mnt2/share1',
                    'comment': u'samba export',
                    'browsable': u'yes',
                    'read_only': u'yes',
                    'guest_ok': u'yes',
                    'create_mask': u'0755'}

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_samba_0(self):
        """
        unauthorized api access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_samba_1(self):
        """
        happy path with vanilla self.data
        """
        self.session_login()

        response = self.client.post(self.BASE_URL, data=self.data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, self.exp_response)

    def test_samba_2(self):
        """
        happy path with self.data, all options no
        """
        self.session_login()
        data = self.data.copy()
        del(data['comment'])
        data['browsable'] = 'no'
        data['guest_ok'] = 'no'
        data['read_only'] = 'no'
        response = self.client.post(self.BASE_URL, data=data,
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['browsable'], 'no')
        self.assertEqual(response.data['guest_ok'], 'no')
        self.assertEqual(response.data['read_only'], 'no')

    def test_samba_3(self):
        """
        happy path, multiple admin users
        """
        self.assertEqual(1, 2)

    def test_samba_4(self):
        """
        happy path, no admin users
        """
        data = {'shares': ('share1', ),
                'comment': 'samba export',
                'browsable': 'yes',
                'guest_ok': 'yes',
                'read_only': 'yes', }
        self.session_login()
        response = self.client.post(self.BASE_URL, data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['admin_users']), 0)
