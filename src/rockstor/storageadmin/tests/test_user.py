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
import mock
from mock import patch
from storageadmin.tests.test_api import APITestMixin

class UserTests(APITestMixin, APITestCase):
    fixtures = ['fix3.json']
    BASE_URL = '/api/users'
    valid_pubkey = 'ssh-dss AAAAB3NzaC1kc3MAAACBAIo+KNTMOS6H9slesrwgSsqp+hxJUDxTT3uy5/LLBDPHRxUz+OR5jcbk/CvgbZsDE3Q7iAIlN8w2bM/L/CG4AwT90f4vFf783QJK9gRxqZmgrPb7Ey88EIeb7UN3+nhc754IEl28y82Rqnq/gtQveSB3aQIWdEIdw17ToLsN5dDPAAAAFQDQ+005d8pBpJSuwH5T7n/xhI6s5wAAAIBJP0okYMbFrYWBfPJvi+WsLHw1tqRerX7bteVmN4IcIlDDtSTaQV7DOAl5B+iMPciRGaixtParUPk8oTew/MY1rECfIBs5wt+3hns4XDcsrXDTNyFDx9qYDtI3Fxt0+2f8k58Ym622Pqq1TZ09IBX7hEZH2EB0dUvxsUOf/4cUNAAAAIEAh3IpPoHWodVQpCalZ0AJXub9hJtOWWke4v4l8JL5w5hNlJwUmAPGuJHZq5GC511hg/7r9PqOk3KnSVp9Jsya6DrtJAxr/8JjAd0fqQjDsWXQRLONgcMfH24ciuFLyIWgDprTWmEWekyFF68vEwd4Jpnd4CiDbZjxc44xBnlbPEI= suman@Learnix'

    @classmethod
    def setUpClass(cls):
        super(UserTests, cls).setUpClass()

        # post mocks

        cls.patch_getpwnam = patch('pwd.getpwnam')
        cls.mock_getpwnam = cls.patch_getpwnam.start()
        cls.mock_getpwnam.return_value = 1,2,3,4

        cls.patch_useradd = patch('storageadmin.views.user.useradd')
        cls.mock_useradd = cls.patch_useradd.start()
        cls.mock_useradd.return_value = ([''], [''], 0)

        cls.patch_usermod = patch('storageadmin.views.user.usermod')
        cls.mock_usermod = cls.patch_usermod.start()
        cls.mock_usermod.return_value = 'out', 'err', 0

        cls.patch_userdel = patch('storageadmin.views.user.userdel')
        cls.mock_userdel = cls.patch_userdel.start()
        cls.mock_userdel.return_value = True

        cls.patch_smbpasswd = patch('storageadmin.views.user.smbpasswd')
        cls.mock_smbpasswd = cls.patch_smbpasswd.start()
        cls.mock_smbpasswd.return_value = 'out', 'err', 0

        cls.patch_add_ssh_key = patch('storageadmin.views.user.add_ssh_key')
        cls.mock_add_ssh_key = cls.patch_add_ssh_key.start()
        cls.mock_add_ssh_key.return_value = True

        cls.patch_update_shell = patch('storageadmin.views.user.update_shell')
        cls.mock_update_shell = cls.patch_update_shell.start()
        cls.mock_update_shell.return_value = True


    @classmethod
    def tearDownClass(cls):
        super(UserTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
         """
        # get base URL
        self.get_base(self.BASE_URL)

        # get user with username admin2
        response = self.client.get('%s/admin2' % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    def test_post_requests(self):

        data = {'username': 'user1','password': 'pwuser1',}
        invalid_user_names = ('User $', '-user', '.user', '', ' ',)
        for uname in invalid_user_names:
            data['username'] = uname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
            e_msg = ("Username is invalid. It must confirm to the regex: [A-Za-z][-a-zA-Z0-9_]*$")
            self.assertEqual(response.data['detail'], e_msg)


        # username with more than 30 characters
        invalid_user_name = 'user'*11
        data = {'username': invalid_user_name,'password': 'pwadmin',}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Username cannot be more than 30 characters long")
        self.assertEqual(response.data['detail'], e_msg)

        # create user with no password
        data = {'username': 'user1'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Password must be a valid string")
        self.assertEqual(response.data['detail'], e_msg)

        # create user with invalid admin(not boolean)
        data = {'username': 'user1','password': 'pwuser1','admin':'Y'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Admin(user type) must be a boolean")
        self.assertEqual(response.data['detail'], e_msg)

        # create user with invalid shell
        data = {'username': 'user1','password': 'pwuser1','shell':'Y'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("shell(Y) is not valid. Valid shells are ('/opt/rock-dep/bin/rcli', '/bin/bash', '/sbin/nologin')")
        self.assertEqual(response.data['detail'], e_msg)

        # create user with existing username
        data = {'username': 'admin','password': 'pwadmin',}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(admin) already exists. Please choose a different username")
        self.assertEqual(response.data['detail'], e_msg)

        # create user with existing username admin2 and uid
        data = {'username': 'admin2', 'password': 'pwadmin2', 'uid':'0000'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(admin2) already exists. Please choose a different username")
        self.assertEqual(response.data['detail'], e_msg)

        # create a user with existing uid (admin2 has uid 1001)
        data = {'username': 'newUser','password': 'pwuser2', 'group': 'admin', 'uid':'1001','pubic_key':'xxx'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("uid: 1001 already exists. Please choose a different one.")
        self.assertEqual(response.data['detail'], e_msg)

        # create a user that is already a system user(eg: root)
        data = {'username': 'root', 'password': 'rootpw'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(root) already exists. Please choose a different username")
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'username': 'newUser','password': 'pwuser2', 'group': 'admin', 'pubic_key':'xxx'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['username'], 'newUser')

        data = {'username': 'newUser2','password': 'pwuser2', 'uid':'5001', 'user':'newuser'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['username'], 'newUser2')

    def test_invalid_UID(self):     
        # Create username with non int UID
        data = {'username': 'newUser','password': 'pwuser2', 'group': 'admin', 'uid':'string'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("UID must be an integer")
        self.assertEqual(response.data['detail'], e_msg)

    def test_duplicate_name2(self):

        # create user with existing user with name exists in system user
        data = {'username': 'chrony','password': 'pwadmin2',}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(chrony) already exists. Please choose a different username")
        self.assertEqual(response.data['detail'], e_msg)

    def test_duplicate_name1(self):

        # create user with existing username admin2 (throwing appropriate error if uid sent in data)
        data = {'username': 'admin2','password': 'pwadmin2'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(admin2) already exists. Please choose a different username")
        self.assertEqual(response.data['detail'], e_msg)


    def test_email_validation(self):

        # create user with invalid email
        data = {'username': 'user1','password': 'pwuser1','email':'123'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        self.assertEqual(response.data['detail'], "{'email': [u'Enter a valid email address.']}")

    def test_pubkey_validation(self):
        data = {'username': 'user1', 'password': 'pwuser1', 'email': 'test@test.com',
                'public_key': 'foobar'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        self.assertEqual(response.data['detail'], 'Public key is invalid')
        data['public_key'] = self.valid_pubkey
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['public_key'], data['public_key'])

    def test_put_requests(self):

        # Edit user that does not exists
        data = {'group':'admin'}
        response = self.client.put('%s/admin5' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(admin5) does not exist")
        self.assertEqual(response.data['detail'], e_msg)

        data = {'password': 'admin2','group':'admin'}
        response = self.client.put('%s/bin' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Editing restricted user(bin) is not supported.")
        self.assertEqual(response.data['detail'], e_msg)

        data = {'admin': True, 'group':'admin'}
        response = self.client.put('%s/admin2' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("password reset is required to enable admin access. please provide a new password")
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'password': 'admin2','group':'admin', 'admin': True}
        response = self.client.put('%s/admin2' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        data = {'password': 'admin2','group':'admin', 'admin': True, 'user':'uadmin2', 'public_key': self.valid_pubkey}
        response = self.client.put('%s/admin2' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        data = {'password': 'admin2','group':'admin', 'user':'uadmin2','shell':'/bin/xyz', 'email':'admin2@xyz.com'}
        response = self.client.put('%s/admin2' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)


    def test_delete_requests(self):

        # delete user that does not exists
        username = 'admin5'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("User(admin5) does not exist")
        self.assertEqual(response.data['detail'], e_msg)


        # delete user that does not exists
        username = 'bin'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Delete of restricted user(bin) is not supported.")
        self.assertEqual(response.data['detail'], e_msg)


        username = 'admin2'
        self.mock_userdel.side_effect = KeyError('error')
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("A low level error occured while deleting the user: admin2")
        self.assertEqual(response.data['detail'], e_msg)

        # delete currently logged in user
        self.mock_userdel.side_effect = None
        username = 'admin'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("Cannot delete the currently logged in user")
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        # delete user
        username = 'admin2'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        username = 'admin3'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        username = 'games'
        response = self.client.delete('%s/%s' % (self.BASE_URL,username))
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
