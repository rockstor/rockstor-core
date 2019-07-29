"""
Copyright (c) 2012-2019 RockStor, Inc. <http://rockstor.com>
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


class TaskSchedulerTests(APITestCase):
    multi_db = True
    fixtures = ["scheduled_tasks.json"]
    BASE_URL = "/api/sm/tasks"

    def session_login(self):
        self.client.login(username='admin', password='admin')

    def test_get(self):
        """
        Test GET request
        """
        # get scheduled task with valid id
        self.session_login()
        response = self.client.get('{}/10'.format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

        # get scheduled task with invalid id
        self.session_login()
        response = self.client.get('{}/100'.format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK,
                         msg=response)

