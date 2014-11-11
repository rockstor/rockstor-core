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


class UserTests(APITestCase):
    fixtures = ['samba.json']
    BASE_URL = '/api/users'

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_user_0(self):
        """
        uauthorized api access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_user_0_1(self):
        """
        get users
        """
        self.client.login(username='admin', password='admin')
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)

    def test_user_1(self):
        """
        add user happy path
        """
        pub_key = ('ssh-dss AAAAB3NzaC1kc3MAAACBAIo+KNTMOS6H9slesrwgSsqp+hxJU'
                   'DxTT3uy5/LLBDPHRxUz+OR5jcbk/CvgbZsDE3Q7iAIlN8w2bM/L/CG4Aw'
                   'T90f4vFf783QJK9gRxqZmgrPb7Ey88EIeb7UN3+nhc754IEl28y82Rqnq'
                   '/gtQveSB3aQIWdEIdw17ToLsN5dDPAAAAFQDQ+005d8pBpJSuwH5T7n/x'
                   'hI6s5wAAAIBJP0okYMbFrYWBfPJvi+WsLHw1tqRerX7bteVmN4IcIlDDt'
                   'STaQV7DOAl5B+iMPciRGaixtParUPk8oTew/MY1rECfIBs5wt+3hns4XD'
                   'csrXDTNyFDx9qYDtI3Fxt0+2f8k58Ym622Pqq1TZ09IBX7hEZH2EB0dUv'
                   'xsUOf/4cUNAAAAIEAh3IpPoHWodVQpCalZ0AJXub9hJtOWWke4v4l8JL5'
                   'w5hNlJwUmAPGuJHZq5GC511hg/7r9PqOk3KnSVp9Jsya6DrtJAxr/8JjA'
                   'd0fqQjDsWXQRLONgcMfH24ciuFLyIWgDprTWmEWekyFF68vEwd4Jpnd4C'
                   'iDbZjxc44xBnlbPEI= suman@Learnix')
        data = {'username': 'rocky',
                'public_key': pub_key,
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
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
        add an existing user
        """
        self.client.login(username='admin', password='admin')
        data = {'username': 'root',
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'user: root already exists. Please choose a '
                         'different username')

    def test_user_2_1(self):
        """
        invalid regex tests
        """
        self.client.login(username='admin', password='admin')
        data = {'username': '1234user',
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        invalid_usernames = ('rocky.rocky', '1234user', '-1234',
                             'rocky$')
        for u in invalid_usernames:
            data['username'] = u
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(response.status_code,
                             status.HTTP_500_INTERNAL_SERVER_ERROR,
                             msg=response.content)
            self.assertEqual(response.data['detail'],
                             'Username is invalid. It must confirm to the '
                             'regex: [A-Za-z][-a-zA-Z0-9_]*$')

    def test_user_2_2(self):
        """
        31 character username
        """
        self.client.login(username='admin', password='admin')
        data = {'username': 'r' * 30,
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        self.client.login(username='admin', password='admin')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)
        response2 = self.client.delete('%s/%s' %
                                       (self.BASE_URL, data['username']))
        self.assertEqual(response2.status_code,
                         status.HTTP_200_OK,
                         msg=response2.content)
        data['username'] = 'r' * 31
        response3 = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response3.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response3.content)
        self.assertEqual(response3.data['detail'],
                         'Username cannot be more than 30 characters long')

    def test_user_3(self):
        """
        invalid shell
        """
        self.client.login(username='admin', password='admin')
        data = {'username': 'root',
                'shell': '/bin/customshell',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        msg = ("shell(/bin/customshell) is not valid. Valid shells are "
               "('/opt/rock-dep/bin/rcli', '/bin/bash', '/sbin/nologin')")
        self.assertEqual(response.data['detail'], msg)

    def test_user_4(self):
        """
        user in User model but deleted manually in the system
        """
        data = {'username': 'rocky',
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        self.client.login(username='admin', password='admin')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)
        from system.users import userdel
        userdel(data['username'])
        response2 = self.client.delete('%s/rocky' % self.BASE_URL)
        self.assertEqual(response2.status_code,
                         status.HTTP_200_OK,
                         msg=response2.content)

    def test_user_5(self):
        """
        invalid public key
        """
        self.client.login(username='admin', password='admin')
        data = {'username': 'root',
                'public_key': 'foobar',
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'], 'Public key is invalid')

    def test_user_6(self):
        """
        delete user that doesn't exist
        """
        self.client.login(username='admin', password='admin')
        response = self.client.delete('%s/foobaruser' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'User(foobaruser) does not exist')

    def test_user_7(self):
        """
        delete a prohibited user
        """
        self.client.login(username='admin', password='admin')
        response = self.client.delete('%s/root' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response.data['detail'],
                         'Delete of restricted user(root) is not supported.')

    def test_user_8(self):
        """
        change user password, public key
        """
        pub_key = ('ssh-dss AAAAB3NzaC1kc3MAAACBAIo+KNTMOS6H9slesrwgSsqp+hxJU'
                   'DxTT3uy5/LLBDPHRxUz+OR5jcbk/CvgbZsDE3Q7iAIlN8w2bM/L/CG4Aw'
                   'T90f4vFf783QJK9gRxqZmgrPb7Ey88EIeb7UN3+nhc754IEl28y82Rqnq'
                   '/gtQveSB3aQIWdEIdw17ToLsN5dDPAAAAFQDQ+005d8pBpJSuwH5T7n/x'
                   'hI6s5wAAAIBJP0okYMbFrYWBfPJvi+WsLHw1tqRerX7bteVmN4IcIlDDt'
                   'STaQV7DOAl5B+iMPciRGaixtParUPk8oTew/MY1rECfIBs5wt+3hns4XD'
                   'csrXDTNyFDx9qYDtI3Fxt0+2f8k58Ym622Pqq1TZ09IBX7hEZH2EB0dUv'
                   'xsUOf/4cUNAAAAIEAh3IpPoHWodVQpCalZ0AJXub9hJtOWWke4v4l8JL5'
                   'w5hNlJwUmAPGuJHZq5GC511hg/7r9PqOk3KnSVp9Jsya6DrtJAxr/8JjA'
                   'd0fqQjDsWXQRLONgcMfH24ciuFLyIWgDprTWmEWekyFF68vEwd4Jpnd4C'
                   'iDbZjxc44xBnlbPEI= suman@Learnix')
        data = {'username': 'rocky',
                'public_key': pub_key,
                'shell': '/bin/bash',
                'password': 'wisdom',
                'email': 'rocky@rockstor.com',
                'admin': True, }
        self.client.login(username='admin', password='admin')
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.content)
        data['password'] = 'wisdom123'
        response3 = self.client.put('%s/rocky' % self.BASE_URL, data=data)
        self.assertEqual(response3.status_code, status.HTTP_200_OK,
                         msg=response.content)
        data['public_key'] = 'foobar'
        response4 = self.client.put('%s/rocky' % self.BASE_URL, data=data)
        self.assertEqual(response4.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.content)
        self.assertEqual(response4.data['detail'], 'Public key is invalid')
        response2 = self.client.delete('%s/rocky' % self.BASE_URL)
        self.assertEqual(response2.status_code,
                         status.HTTP_200_OK,
                         msg=response2.content)
