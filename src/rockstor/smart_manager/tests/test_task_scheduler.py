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
        self.client.login(username="admin", password="admin")

    def test_get(self):
        """
        Test GET request
        """
        # get scheduled task with valid id
        self.session_login()
        response = self.client.get("{}/10".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

        # get scheduled task with invalid id
        self.session_login()
        response = self.client.get("{}/100".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    def test_post_valid(self):
        """
        Test valid POST request
        """
        datalist = [
            {
                "task_type": "scrub",
                "name": "scrubtest",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {"pool": "3"},
                "crontabwindow": "*-*-*-*-*-*",
            },
            {
                "task_type": "snapshot",
                "name": "snapshot_test",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {
                    "writable": True,
                    "visible": True,
                    "prefix": "snaptest",
                    "share": "4",
                    "max_count": "4",
                },
                "crontabwindow": "*-*-*-*-*-*",
            },
            {
                "task_type": "reboot",
                "name": "sys_reboot_test",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {},
                "crontabwindow": "*-*-*-*-*-*",
            },
            {
                "task_type": "shutdown",
                "name": "sys_shutdown_test",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {"wakeup": False, "rtc_hour": "0", "rtc_minute": "0"},
                "crontabwindow": "*-*-*-*-*-*",
            },
            {
                "task_type": "suspend",
                "name": "sys_suspend_test",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {"wakeup": True, "rtc_hour": "0", "rtc_minute": "0"},
                "crontabwindow": "*-*-*-*-*-*",
            },
        ]
        self.session_login()
        for data in datalist:
            response = self.client.post("{}/".format(self.BASE_URL), data=data)
            self.assertEqual(
                response.status_code, status.HTTP_200_OK, msg=response.content
            )

    def test_post_name_exists(self):
        """
        Test invalid POST request when a task with the same name already exists.
        It should return an exception.
        """
        data = {
            "task_type": "scrub",
            "name": "scurb-testpool01",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {"pool": "3"},
            "crontabwindow": "*-*-*-*-*-*",
        }

        self.session_login()
        response = self.client.post("{}/".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_post_invalid_type(self):
        """
        Test invalid POST request when a task type is incorrect.
        It should return an exception.
        """
        data = {
            "task_type": "unsupported_type",
            "name": "test_scrub",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {"pool": "3"},
            "crontabwindow": "*-*-*-*-*-*",
        }

        self.session_login()
        response = self.client.post("{}/".format(self.BASE_URL), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_put_valid(self):
        """
        Test PUT request with valid tdid
        """
        data = {
            "task_type": "snapshot",
            "name": "snapshot_test",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {
                "writable": True,
                "visible": True,
                "prefix": "snaptest",
                "share": "4",
                "max_count": "4",
            },
            "crontabwindow": "*-*-*-*-*-*",
        }
        tdid = 15
        self.session_login()
        response = self.client.put("{}/{}".format(self.BASE_URL, tdid), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

    def test_put_invalid(self):
        """
        Test PUT request with invalid tdid
        """
        data = {
            "task_type": "snapshot",
            "name": "snapshot_test",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {
                "writable": True,
                "visible": True,
                "prefix": "snaptest",
                "share": "4",
                "max_count": "4",
            },
            "crontabwindow": "*-*-*-*-*-*",
        }
        tdid = 150
        self.session_login()
        response = self.client.put("{}/{}".format(self.BASE_URL, tdid), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_delete_valid(self):
        """
        Test delete request with valid tdid
        """
        data = {
            "task_type": "snapshot",
            "name": "snapshot_test",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {
                "writable": True,
                "visible": True,
                "prefix": "snaptest",
                "share": "4",
                "max_count": "4",
            },
            "crontabwindow": "*-*-*-*-*-*",
        }
        tdid = 15
        self.session_login()
        response = self.client.delete("{}/{}".format(self.BASE_URL, tdid), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

    def test_delete_invalid(self):
        """
        Test delete request with invalid tdid
        """
        data = {
            "task_type": "snapshot",
            "name": "snapshot_test",
            "enabled": False,
            "crontab": "42 3 * * 5",
            "meta": {
                "writable": True,
                "visible": True,
                "prefix": "snaptest",
                "share": "4",
                "max_count": "4",
            },
            "crontabwindow": "*-*-*-*-*-*",
        }
        tdid = 150
        self.session_login()
        response = self.client.delete("{}/{}".format(self.BASE_URL, tdid), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )
