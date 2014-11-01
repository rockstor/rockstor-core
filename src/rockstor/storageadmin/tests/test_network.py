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


class NetworkTests(APITestCase):
    fixtures = ['samba.json']
    BASE_URL = '/api/network'

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_network_1(self):
        """
        unauthorized access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN,
                         msg=response.data)

    def test_network_2(self):
        """
        simple get
        """
        self.session_login()
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)
        print response.data

    def test_network_3(self):
        """
        simple post
        """
        self.session_login()
        response = self.client.post(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response.data)

    def test_network_4(self):
        """
        put, change itype
        """
        pass
