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
from mock import patch
from storageadmin.tests.test_api import APITestMixin


class GroupTests(APITestMixin, APITestCase):
    fixtures = ['fix3.json']
    BASE_URL = '/api/groups'

    @classmethod
    def setUpClass(cls):
        super(GroupTests, cls).setUpClass()

        # post mocks
        cls.patch_groupadd = patch('storageadmin.views.group.groupadd')
        cls.mock_groupadd = cls.patch_groupadd.start()
        cls.mock_groupadd.return_value = [''], [''], 0

        cls.patch_groupdel = patch('storageadmin.views.group.groupdel')
        cls.mock_groupdel = cls.patch_groupdel.start()
        cls.mock_groupdel.return_value = [''], [''], 0

        cls.patch_getgrnam = patch('grp.getgrnam')
        cls.mock_getgrnam = cls.patch_getgrnam.start()
        cls.mock_getgrnam.return_value = 'grname', '2', '001'

    @classmethod
    def tearDownClass(cls):
        super(GroupTests, cls).tearDownClass()

    def test_get_requests(self):
        # self.get_base(self.BASE_URL)
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # get with groupname
        response = self.client.get('{}/admin2'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):
        # invalid username
        data = {'groupname': 'root', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         msg=response.content)
        self.assertEqual(response.data[0], 'Group (root) already exists. '
                                           'Choose a different one.')

        # invalid group names
        invalid_groupnames = ('rocky.rocky', '1234group', '-1234', 'rocky$',)
        for g in invalid_groupnames:
            data['groupname'] = g
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_400_BAD_REQUEST,
                             msg=response.data)
            err_msg = ('Groupname is invalid. It must conform to the regex: '
                       '([A-Za-z][-a-zA-Z0-9_]*$).')
            self.assertEqual(response.data[0], err_msg)

        # invalid groupname with more than 31 characters
        data['groupname'] = 'r' * 31
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         msg=response.content)
        err_msg = 'Groupname cannot be more than 30 characters long.'
        self.assertEqual(response.data[0], err_msg)

        # invalid gid
        data = {'groupname': 'ngroup2',
                'gid': 1001, }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         msg=response.data)
        err_msg = 'GID (1001) already exists. Choose a different one.'
        self.assertEqual(response.data[0], err_msg)

        # happy path
        data = {'groupname': 'newgroup', }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)

    def test_delete_requests(self):
        # delete group that doesn't exist
        response = self.client.delete('{}/foobargroup'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        err_msg = 'Group (foobargroup) does not exist.'
        self.assertEqual(response.data[0], err_msg)

        # delete a restricted group
        response = self.client.delete('{}/root'.format(self.BASE_URL))
        self.assertEqual(response.status_code,
                         status.HTTP_400_BAD_REQUEST,
                         msg=response.data)
        err_msg = 'Delete of restricted group (root) is not supported.'
        self.assertEqual(response.data[0], err_msg)

        # # TODO: FAIL AssertionError: ['Group (admin2) does not exist.', 'None\n']
        # # happy path
        # response = self.client.delete('{}/admin2'.format(self.BASE_URL))
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)
