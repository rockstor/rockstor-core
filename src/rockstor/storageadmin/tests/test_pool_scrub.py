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

# from rest_framework.test import APITestCase
from unittest.mock import patch

# from storageadmin.models import Pool
from storageadmin.tests.test_api import APITestMixin

"""
Fixture creation instructions:

System needs 1 non sys pool (id=2, name='rock-pool', raid='raid1'). Maintain system pool.

bin/django dumpdata storageadmin.pool --natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_pool_scrub.json

./bin/test -v 2 -p test_pool_scrub.py
"""

class PoolScrubTests(APITestMixin):
    fixtures = ["test_api.json", "test_pool_scrub.json"]
    BASE_URL = "/api/pools"

    @classmethod
    def setUpClass(cls):
        super(PoolScrubTests, cls).setUpClass()

        # post mocks
        cls.patch_scrub_start = patch("storageadmin.views.pool_scrub." "scrub_start")
        cls.mock_scrub_start = cls.patch_scrub_start.start()
        cls.mock_scrub_start.return_value = "001"

        cls.patch_scrub_status = patch("storageadmin.views.pool_scrub." "scrub_status")
        cls.mock_scrub_status = cls.patch_scrub_status.start()
        cls.mock_scrub_status.return_value = {"status": "finished", "duration": "20"}

    @classmethod
    def tearDownClass(cls):
        super(PoolScrubTests, cls).tearDownClass()

    # @mock.patch('storageadmin.views.pool_scrub.Pool')
    def test_get(self):

        # temp_pool = Pool(id=2, name='rock-pool', raid='raid', size=88025459)
        # mock_pool.objects.get.return_value = temp_pool

        # get base URL
        pId = 2  # already created and exists in fixture
        response = self.client.get("{}/{}/scrub".format(self.BASE_URL, pId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_requests_1(self):

        # invalid pool
        data = {"force": "true"}
        pId = 99999
        response = self.client.post("{}/{}/scrub".format(self.BASE_URL, pId), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )

        e_msg = "Pool with id ({}) does not exist.".format(pId)
        self.assertEqual(response.data[0], e_msg)

    # @mock.patch('storageadmin.views.pool_scrub.Pool')
    def test_post_requests_2(self):

        # temp_pool = Pool(id=2, name='rock-pool', raid='raid', size=88025459)
        # mock_pool.objects.get.return_value = temp_pool

        # Invalid scrub command
        data = {"force": "true"}
        pId = 2
        response = self.client.post(
            "{}/{}/scrub/invalid-scrub-command" "".format(self.BASE_URL, pId), data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Unknown scrub command: (invalid-scrub-command)."
        self.assertEqual(response.data[0], e_msg)

        # happy path
        data = {"force": "true"}
        response = self.client.post("{}/{}/scrub".format(self.BASE_URL, pId), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # happy path
        data = {"force": "true"}
        response = self.client.post(
            "{}/{}/scrub/status".format(self.BASE_URL, pId), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
