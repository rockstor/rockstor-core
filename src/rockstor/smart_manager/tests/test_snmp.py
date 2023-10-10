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
from rest_framework.test import APITestCase


"""
To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_snmp.py
"""


class SNMPTests(APITestCase):
    databases = '__all__'
    # TODO Requires command to reproduce minimal fixture:
    #  "services.json" fixture requires only the smart_manager.service model.
    fixtures = ["test_api.json", "services.json"]
    BASE_URL = "/api/sm/services/snmpd"

    def session_login(self):
        self.client.login(username="admin", password="admin")

    def test_snmp_0(self):
        """
        unauthorized access
        """
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_snmp_0_1(self):
        """
        config happy path
        """
        self.patch_configure_snmp = patch(
            "smart_manager.views.snmp_service.configure_snmp"
        )
        self.mock_configure_snmp = self.patch_configure_snmp.start()

        config = {
            "syslocation": "Rockstor Labs",
            "syscontact": "rocky@rockstor.com",
            "rocommunity": "public",
            "aux": (),
        }
        data = {"config": config}
        self.session_login()
        response = self.client.post("%s/config" % self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)

    def test_snmp_1(self):
        """
        config without input
        """
        self.session_login()
        response = self.client.post("%s/config" % self.BASE_URL)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_2(self):
        """
        config without syslocation
        """
        config = {
            "syscontact": "rocky@rockstor.com",
            "rocommunity": "public",
            "aux": (),
        }
        data = {"config": config}
        self.session_login()
        response = self.client.post("%s/config" % self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_3(self):
        """
        config without syscontact
        """
        config = {"syslocation": "Rockstor Labs", "rocommunity": "public", "aux": ()}
        self.session_login()
        response = self.client.post(
            "%s/config" % self.BASE_URL, data={"config": config}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_4(self):
        """
        config without rocommunity
        """
        config = {
            "syslocation": "Rockstor Labs",
            "syscontact": "rocky@rockstor.com",
            "aux": (),
        }
        self.session_login()
        response = self.client.post(
            "%s/config" % self.BASE_URL, data={"config": config}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_5(self):
        """
        config without aux
        """
        config = {
            "syslocation": "Rockstor Labs",
            "syscontact": "rocky@rockstor.com",
            "rocommunity": "public",
        }
        self.session_login()
        response = self.client.post(
            "%s/config" % self.BASE_URL, data={"config": config}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_6(self):
        """
        config with wrong aux type
        """
        config = {
            "syslocation": "Rockstor Labs",
            "syscontact": "rocky@rockstor.com",
            "rocommunity": "public",
            "aux": "foo",
        }
        self.session_login()
        response = self.client.post(
            "%s/config" % self.BASE_URL, data={"config": config}
        )
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.content,
        )

    def test_snmp_7(self):
        """
        start/stop tests
        """
        self.patch_systemctl = patch("smart_manager.views.snmp_service.systemctl")
        self.mock_systemctl = self.patch_systemctl.start()
        self.mock_systemctl.return_value = [""], [""], 0

        self.session_login()
        response = self.client.post("%s/start" % self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.content)
        response2 = self.client.post("%s/stop" % self.BASE_URL)
        self.assertEqual(
            response2.status_code, status.HTTP_200_OK, msg=response.content
        )
