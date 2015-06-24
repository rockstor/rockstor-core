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
        cls.mock_add_ssh_key.return_value = 'key'

        cls.patch_update_shell = patch('storageadmin.views.user.update_shell')
        cls.mock_update_shell = cls.patch_update_shell.start()
        cls.mock_update_shell.return_value = True
        
        cls.patch_is_pub_key = patch('storageadmin.views.user.is_pub_key')
        cls.mock_is_pub_key = cls.patch_is_pub_key.start()
        cls.mock_is_pub_key.return_value = False
        

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
        
        #?????? post not considering email
        # create user with invalid email
        data = {'username': 'user1','password': 'pwuser1','email':'...'}
        #response = self.client.post(self.BASE_URL, data=data)
        #self.assertEqual(response.status_code,
        #                 status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)   
           
        # create user with existing username
        data = {'username': 'admin','password': 'pwadmin',}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR, msg=response.data)
        e_msg = ("user: admin already exists. Please choose a different username")                 
        self.assertEqual(response.data['detail'], e_msg)       

       
        # happy path
        data = {'username': 'newUser','password': 'pwuser2', 'group': 'admin', 'pubic_key':'xxx'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['username'], 'newUser')                 
        
        data = {'username': 'newUser2','password': 'pwuser2', 'uid':'5001'}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['username'], 'newUser2')
        
        
    def test_put_requests(self):   
        
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
                         
                  
       
          