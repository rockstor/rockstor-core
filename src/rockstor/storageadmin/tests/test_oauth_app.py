"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import patch
from rest_framework import status
from storageadmin.tests.test_api import APITestMixin


class OauthAppTests(APITestMixin):
    # Proposed fixture "test_oauth_app.json" was "fix1.json"
    fixtures = ["test_api.json"]
    BASE_URL = "/api/oauth_app"

    @classmethod
    def setUpClass(cls):
        super(OauthAppTests, cls).setUpClass()

        # post mocks
        cls.patch_set_token = patch("storageadmin.views.appliances.set_token")
        cls.mock_set_token = cls.patch_set_token.start()
        cls.mock_set_token.return_value = {}

    @classmethod
    def tearDownClass(cls):
        super(OauthAppTests, cls).tearDownClass()

    def test_get(self):

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    # def test_post_requests(self):
    #
    #     # # TODO: Attempt to mock User and create an 'admin' instance.
    #     # # mock user 'admin' as that is the logged in test user.
    #     # temp_d_user = DjangoUser(username='test')
    #     # temp_user = User(id=1, username='admin', user=temp_d_user)
    #     # mock_user.objects.get.return_value = temp_user
    #
    #     # # TODO: "Existing application name" and "happy path" fail with:
    #     # # 'User with name (admin) does not exist.'
    #     #
    #     # # Existing application name
    #     # data = {'name': 'cliapp'}
    #     # response = self.client.post(self.BASE_URL, data=data)
    #     # self.assertEqual(response.status_code,
    #     #                  status.HTTP_500_INTERNAL_SERVER_ERROR,
    #     #                  msg=response.data)
    #     # e_msg = ('Application with name (cliapp) already exists. Choose a '
    #     #          'different name.')
    #     # self.assertEqual(response.data[0], e_msg)
    #
    #     # # happy path
    #     # data = {'name': 'AccessKey1'}
    #     # response = self.client.post(self.BASE_URL, data=data)
    #     # self.assertEqual(response.status_code,
    #     #                  status.HTTP_200_OK, msg=response.data)
    # TODO: ERROR AttributeError: 'HttpResponseNotFound' object has no attribute 'data'
    # def test_delete_requests(self):
    #
    #     # delete application that does not exist
    #     access_key = 'invalid'
    #     response = self.client.delete('{}/{}'.format(self.BASE_URL,
    #                                                  access_key))
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = 'Application with id ({}) does not exist.'.format(access_key)
    #     self.assertEqual(response.data[0], e_msg)
    #
    #     # invalid delete operation
    #     access_key = 'cliapp'
    #     response = self.client.delete('{}/{}'.format(self.BASE_URL,
    #                                                  access_key))
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = ('Application with id ({}) cannot be deleted because '
    #              'it is '
    #              'used internally by Rockstor. If you really need to '
    #              'delete it, login as root and use '
    #              '/opt/rock-dep/delete-api-key command. If you do delete it, '
    #              'please create another one with the same name as it '
    #              'is required by Rockstor '
    #              'internally.').format(access_key)
    #     self.assertEqual(response.data[0], e_msg)
    #
    #     # happy path
    #     # create before you delete
    #     data = {'name': 'AccessKey2'}
    #     response = self.client.post(self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #
    #     access_key = 'AccessKey2'
    #     response = self.client.delete('{}/{}'.format(self.BASE_URL,
    #                                                  access_key))
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
