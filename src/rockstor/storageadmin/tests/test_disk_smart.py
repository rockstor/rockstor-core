"""
Copyright (c) 2012-2023 RockStor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from unittest.mock import patch
from rest_framework import status

from storageadmin.tests.test_api import APITestMixin


class DiskSmartTests(APITestMixin):
    # Fixture requires a single unpartitioned disk with id 2 of type supported by smart.
    # No pool association means we can keep our fixture to a minimum.
    # The required tables are created/populated upon smart "Refresh" button use.
    # Fixture model content:
    # - storageadmin.disk (disk to which storageadmin.smartinfo is linked)
    # - storageadmin.smartcapability
    # - storageadmin.smartattribute
    # - storageadmin.smarterrorlog
    # - storageadmin.smarttestlogdetail
    # - storageadmin.smartidentity
    # - storageadmin.smartinfo (links storageadmin.smart*.info to storageadmin.disk.id)
    # Note storageadmin.smartinfo.pk is associated with storageadmin.smart*.info
    #
    # bin/django dumpdata storageadmin.disk storageadmin.smartcapability
    # storageadmin.smartattribute storageadmin.smarterrorlog
    # storageadmin.smarttestlogdetail storageadmin.smartidentity storageadmin.smartinfo
    # --natural-foreign --indent 4 >
    # src/rockstor/storageadmin/fixtures/test_disk_smart.json
    #
    # Proposed fixture = "test_disk_smart.json" was "fix1.json"
    # ./bin/test -v 2 -p test_disk_smart.py

    fixtures = ["test_api.json", "test_disk_smart.json"]
    BASE_URL = "/api/disks/smart"

    @classmethod
    def setUpClass(cls):
        super(DiskSmartTests, cls).setUpClass()

        # Contextual mock of run_command to return nothing.
        # Here we test our API end points against our existing fixture info.
        # TODO Create system.test.test_smart for lower level smartctl output parsing.
        cls.patch_run_test = patch("system.smart.run_command")
        cls.mock_run_test = cls.patch_run_test.start()
        cls.mock_run_test.return_value = [""], [""], 0

    @classmethod
    def tearDownClass(cls):
        super(DiskSmartTests, cls).tearDownClass()

    def test_get(self):

        # get with disk id
        response = self.client.get("{}/info/2".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_reqeusts_1(self):

        # # invalid disk id
        diskId = 99999
        response = self.client.post("{}/info/{}".format(self.BASE_URL, diskId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Disk id ({}) does not exist.".format(diskId)
        self.assertEqual(response.data[0], e_msg)

    def test_post_requests_2(self):

        # invalid command
        diskId = 2
        response = self.client.post("{}/invalid/{}".format(self.BASE_URL, diskId))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Unknown command: (invalid). The only valid commands are " "info and test."
        )
        self.assertEqual(response.data[0], e_msg)

        # unsupported self test
        data = {"test_type": "invalid"}
        response = self.client.post(
            "{}/test/{}".format(self.BASE_URL, diskId), data=data
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Unsupported Self-Test: (invalid)."
        self.assertEqual(response.data[0], e_msg)

        # test command
        data = {"test_type": "short"}
        response = self.client.post(
            "{}/test/{}".format(self.BASE_URL, diskId), data=data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # happy path
        response = self.client.post("{}/info/{}".format(self.BASE_URL, diskId))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
