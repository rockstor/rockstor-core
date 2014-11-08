"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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
along with this program. If not, see <http://www.gnu.org/licenses/>
"""


from rest_framework import status
from rest_framework.test import APITestCase


class GroupTests(APITestCase):
    fixtures = ['samba.json']
    BASE_URL = '/api/groups'

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_group_0(self):
        """
        uauthorized api access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_group_0_1(self):
        """
        get groups
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)

    def test_group_1(self):
        """
        add group happy path
        """
        data = {'groupname': 'rocky', }
        self.client.login(username='admin', password='admin')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)
        response2 = self.client.delete('%s/rocky' % self.BASE_URL)
        self.assertEqual(response2.status_code,
                         status.HTTP_200_OK,
                         msg=response2.content)

    def test_user_2(self):
        """
        invalid username
        """
        self.client.login(username='admin', password='admin')
        data = {'groupname': 'root', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'Group(root) already exists. Choose a different one')

    def test_user_3(self):
        """
        invalid gid
        """
        self.client.login(username='admin', password='admin')
        data = {'groupname': 'rocky',
                'gid': 0, }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'GID(0) already exists. Choose a different one')

    def test_user_4(self):
        """
        group in db but deleted manually in the system
        """
        data = {'groupname': 'rocky', }
        self.client.login(username='admin', password='admin')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)
        from system.users import groupdel
        groupdel(data['groupname'])
        response2 = self.client.delete('%s/rocky' % self.BASE_URL)
        self.assertEqual(response2.status_code,
                         status.HTTP_200_OK,
                         msg=response2.content)

    def test_user_6(self):
        """
        delete group that doesn't exist
        """
        self.client.login(username='admin', password='admin')
        response = self.client.delete('%s/foobargroup' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'Group(foobargroup) does not exist')

    def test_user_7(self):
        """
        delete a restricted group
        """
        self.client.login(username='admin', password='admin')
        response = self.client.delete('%s/root' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'Delete of restricted group(root) is not supported.')
