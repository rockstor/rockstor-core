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


class SambaTests(APITestCase):
    fixtures = ['samba.json']
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

    def switch_samba(self, switch):
        systemctl('smb', switch)
        systemctl('nmb', switch)

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
        self.switch_samba('start')
        response = self.client.post(self.BASE_URL, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
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
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['browsable'], 'no')
        self.assertEqual(response.data['guest_ok'], 'no')
        self.assertEqual(response.data['read_only'], 'no')

    def test_samba_3(self):
        """
        happy path, multiple admin users
        """
        data = self.data.copy()
        data['admin_users'] = ('smbuser', 'user1', 'user2', 'user3',)
        self.session_login()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(len(response.data['admin_users']), 4)

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
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['admin_users']), 0)

    def test_samba_5(self):
        """
        non existant admin user
        """
        data = self.data.copy()
        data['admin_users'] = ('suman',)
        self.session_login()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'],
                         'User matching query does not exist.')

    def test_samba_6(self):
        """
        non existant share
        """
        data = self.data.copy()
        data['shares'] = ('share10',)
        self.session_login()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'],
                         'Share with name: share10 does not exist')

    def test_samba_7(self):
        """
        happy path, multiple shares
        """
        data = self.data.copy()
        data['shares'] = ('share1', 'share2', 'share3',)
        self.session_login()
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertTrue(response.data['share'] in data['shares'])

    def test_samba_8(self):
        """
        add export while samba service is off
        """
        self.session_login()
        self.switch_samba('stop')
        response = self.client.post(self.BASE_URL, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)

    def test_samba_8_1(self):
        """
        delete export, happy path
        """
        self.session_login()
        self.switch_samba('start')
        self._create_and_delete()

    def _create_and_delete(self):
        response = self.client.post(self.BASE_URL, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        smb_id = response.data['id']
        response2 = self.client.delete('%s/%d' % (self.BASE_URL, smb_id))
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response2.data)

    def test_samba_9(self):
        """
        delete export while samba service is off
        """
        self.session_login()
        self.switch_samba('stop')
        self._create_and_delete()

    def create_and_update(self):
        self.session_login()
        response = self.client.post(self.BASE_URL, data=self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        smb_id = response.data['id']
        data = self.data.copy()
        data['browsable'] = 'no'
        data['guest_ok'] = 'no'
        data['read_only'] = 'no'
        response2 = self.client.put('%s/%d' % (self.BASE_URL, smb_id),
                                    data=data)
        self.assertEqual(response2.status_code, status.HTTP_200_OK,
                         msg=response.data)
        self.assertEqual(response2.data['browsable'], 'no', msg=response2.data)
        self.assertEqual(response2.data['guest_ok'], 'no', msg=response2.data)
        self.assertEqual(response2.data['read_only'], 'no', msg=response2.data)

    def test_samba_10(self):
        """
        export edit happy path
        """
        self.switch_samba('start')
        self.create_and_update()

    def test_samba_11(self):
        """
        export edit while samba service is off
        """
        self.switch_samba('stop')
        self.create_and_update()

    def test_samba_12(self):
        """
        export edit on an non-existant export
        """
        self.session_login()
        response = self.client.put('%s/%d' % (self.BASE_URL, 10000),
                                   data=self.data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'],
                         'Samba export for the id(10000) does not exist')
