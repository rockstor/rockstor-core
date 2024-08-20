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


from rest_framework import status
from storageadmin.tests.test_api import APITestMixin


class DashboardConfigTests(APITestMixin):
    # Proposed fixture "test_dashboardconfig.json" was "fix2.json"
    fixtures = ["test_api.json"]
    BASE_URL = "/api/dashboardconfig"

    @classmethod
    def setUpClass(cls):
        super(DashboardConfigTests, cls).setUpClass()

    @classmethod
    def tearDownClass(cls):
        super(DashboardConfigTests, cls).tearDownClass()

    def test_get_requests(self):
        # happy path
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):
        # happy path
        data = {"widgets": ""}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_put_requests(self):
        # happy path
        data = {"widgets": ""}
        response = self.client.put(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
