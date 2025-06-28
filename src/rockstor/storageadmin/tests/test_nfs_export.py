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
from unittest.mock import patch

from rest_framework import status
from storageadmin.tests.test_api import APITestMixin

"""
fixture with:
Pool:
  - pk=11
  - name="rock-pool"
Share:
  - pk=21
  - name: "share-nfs"
  - pool: "rock-pool" above
  - exported with defaults:
    - (NFS Clients) host_str: "*"
    - (Admin Host) admin_host: None
    - (Access type) mod_choice: "rw"
    - (Response type) sync_choice: "async"
Share:
  - pk=22
  - name: "share2"
User:
  - pk: 1
  - name: admin
  - group: 1
Group:
  - pk: 1

proposed fixture = 'test_nfs.json'

cd /opt/rockstor
poetry run django-admin dumpdata storageadmin.pool storageadmin.share \
storageadmin.nfsexport storageadmin.nfsexportgroup \
storageadmin.user storageadmin.group \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_nfs.json

To run the tests:
cd /opt/rockstor/src/rockstor
poetry run django-admin test -v 2 -p test_nfs_export.py
"""


class NFSExportTests(APITestMixin):
    fixtures = ["test_api.json", "test_nfs.json"]
    BASE_URL = "/api/nfs-exports"

    @classmethod
    def setUpClass(cls):
        super(NFSExportTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch("storageadmin.views.nfs_exports." "mount_share")
        cls.mock_mount_share = cls.patch_mount_share.start()
        cls.mock_mount_share.return_value = ["out"], ["err"], 0

        cls.patch_refresh_nfs_exports = patch(
            "storageadmin.views.nfs_exports." "refresh_nfs_exports"
        )
        cls.mock_refresh_nfs_exports = cls.patch_refresh_nfs_exports.start()
        cls.mock_refresh_nfs_exports.return_value = ["out"], ["err"], 0

        # potential mocks for NFSExportGroup
        # validate_nfs_host_str
        # validate_nfs_modify_str
        # validate_nfs_sync_choice

    @classmethod
    def tearDownClass(cls):
        super(NFSExportTests, cls).tearDownClass()

    def test_get(self):
        # get base URL
        self.get_base(self.BASE_URL)

        # get nfs-export with id
        nfs_id = 3  # from fixture
        response = self.client.get(f"{self.BASE_URL}/{nfs_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response)

    def test_post(self):
        # Happy path - ensuring we create all that we intend.
        # Clarifies current map re field naming of API vs DB vs Web-UI.

        # API / DB / Web-UI field name map:
        data = {
            "shares": ("share2",),
            "host_str": "*.edu",  # 'host_str', "NFS Clients"
            "admin_host": "example-host",  # 'admin_host', "Admin Host"
            "mod_choice": "rw",  # 'editable', "Access type"
            "sync_choice": "sync",  # 'syncable', "Response type"
            # "mount_security": "secure",   # 'mount_security', NOT IMPLEMENTED.
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["host_str"], "*.edu")
        self.assertEqual(response.data["admin_host"], "example-host")
        self.assertEqual(response.data["editable"], "rw")
        self.assertEqual(response.data["syncable"], "sync")
        # self.assertEqual(response.data["mount_security"], "secure")

    def test_invalid_get(self):
        # get nfs-export with invalid id
        response = self.client.get(f"{self.BASE_URL}/99999")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=response)

    def test_post_requests(self):
        # Add nfs-export without providing share names
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = "out", "err", 0

        data = {"host_str": "*", "mod_choice": "rw", "sync_choice": "async"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Cannot export without specifying shares."
        self.assertEqual(response.data[0], e_msg)

        # happy path
        data1 = {
            "shares": ("share2",),
            "host_str": "*.edu",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Add NFS export - non-existent share
        fake_share_name: str = "non-existent"
        data1 = {
            "shares": (f"{fake_share_name}",),
            "host_str": "*",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data1)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"Share with name ({fake_share_name}) does not exist."
        self.assertEqual(response.data[0], e_msg)

    def test_no_nfs_client(self):
        # Add NFS export without host_str
        # The server side defaults the host string to * so test for this.

        self.mock_refresh_nfs_exports.side_effect = None

        data = {
            "shares": ("share2",),
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["host_str"], "*")

    def test_mod_choice_validator_post(self):
        # DB validator should restrict to "ro" or "rw": validate_nfs_modify_str() & model choices
        data = {
            "shares": ("share2",),
            "mod_choice": "rr",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'editable': ["Value 'rr' is not a valid choice."]}
        self.assertEqual(response.data[0], str(e_msg))

    def test_mod_choice_validator_put(self):
        # DB validator should restrict to "ro" or "rw": validate_nfs_modify_str() & model choices
        data = {
            "shares": ("share-nfs",),
            "mod_choice": "rr",
            "sync_choice": "async",
        }
        nfs_id = 3  # from fixture
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'editable': ["Value 'rr' is not a valid choice."]}
        self.assertEqual(response.data[0], str(e_msg))

    def test_sync_choice_validator_post(self):
        # DB validator should restrict to "async" or "sync": validate_nfs_sync_choice() & model choices
        data = {
            "shares": ("share2",),
            "mod_choice": "ro",
            "sync_choice": "aaaaa",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'syncable': ["Value 'aaaaa' is not a valid choice."]}
        self.assertEqual(response.data[0], str(e_msg))

    def test_sync_choice_validator_put(self):
        # DB validator should restrict to "async" or "sync": validate_nfs_sync_choice() & model choices
        data = {
            "shares": ("share-nfs",),
            "mod_choice": "ro",
            "sync_choice": "aaaaa",
        }
        nfs_id = 3  # from fixture
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'syncable': ["Value 'aaaaa' is not a valid choice."]}
        self.assertEqual(response.data[0], str(e_msg))

    def test_host_str_validator_post(self):
        # DB validator should restrict to valid entry: validate_nfs_host_str
        data = {
            "shares": ("share2",),
            "host_str": "1.!",
            "mod_choice": "ro",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'host_str': ['Invalid host string: 1.!']}
        self.assertEqual(response.data[0], str(e_msg))

    def test_host_str_validator_put(self):
        # DB validator should restrict to valid entry: validate_nfs_host_str
        data = {
            "shares": ("share-nfs",),
            "host_str": "ted fred",
            "mod_choice": "ro",
            "sync_choice": "async",
        }
        nfs_id = 3  # from fixture
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = {'host_str': ['Invalid host string: ted fred']}
        self.assertEqual(response.data[0], str(e_msg))

    def test_share_already_exported(self):
        # Add NFS export for share already exported
        data = {
            "shares": ("share-nfs",),
            "host_str": "*",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "An export already exists for the host string: (*)."
        self.assertEqual(response.data[0], e_msg)

    def test_low_level_error_post(self):
        # Invalid POST request
        # Add NFS export - invalid admin host
        ll_error: str = "post low level error"
        self.mock_refresh_nfs_exports.side_effect = Exception(ll_error)
        data = {
            "shares": ("share2",),
            "host_str": "*.edu",
            "admin_host": "admin-host",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )

        e_msg = (
            f"A lower level error occurred while refreshing NFS exports: ({ll_error})."
        )
        self.assertEqual(response.data[0], e_msg)

        self.mock_refresh_nfs_exports.side_effect = None

    def test_low_level_error_put(self):
        # Invalid PUT request
        # Edit NFS export - invalid admin host
        ll_error: str = "put low level error"
        self.mock_refresh_nfs_exports.side_effect = Exception(ll_error)

        data = {
            "shares": ("share-nfs",),
            "host_str": "*.edu",
            "admin_host": "admin-host",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        nfs_id = 3  # from fixture
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )

        e_msg = (
            f"A lower level error occurred while refreshing NFS exports: ({ll_error})."
        )
        self.assertEqual(response.data[0], e_msg)

        self.mock_refresh_nfs_exports.side_effect = None

    def test_put_requests(self):
        # Edit NFS export without specifying share.
        self.mock_refresh_nfs_exports.side_effect = None
        self.mock_refresh_nfs_exports.return_value = "out", "err", 0
        nfs_id = 3  # from fixture
        data = {"host_str": "*.edu", "mod_choice": "rw", "sync_choice": "async"}
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Cannot export without specifying shares."
        self.assertEqual(response.data[0], e_msg)

        # Happy path - editing existing NFS export.
        nfs_id = 3  # from fixture
        data = {
            "shares": ("share-nfs",),
            "host_str": "*.edu",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Happy path - editing existing NFS export re adding admin host.
        nfs_id = 3  # from fixture
        data = {
            "shares": ("share-nfs",),
            "host_str": "*.edu",
            "admin_host": "test-nfs-admin-host",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Edit non-existent NFS export, existing share in fixtures.
        nfs_id = 99999
        data = {
            "shares": ("share2",),
            "host_str": "*.edu",
            "mod_choice": "rw",
            "sync_choice": "async",
        }
        response = self.client.put(f"{self.BASE_URL}/{nfs_id}", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"NFS export with id ({nfs_id}) does not exist."
        self.assertEqual(response.data[0], e_msg)

    def test_delete_requests(self):
        # Happy path
        nfs_id = 3  # from fixture
        response = self.client.delete(f"{self.BASE_URL}/{nfs_id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Delete nfs-export that does not exist
        nfs_id = 99999
        response = self.client.delete(f"{self.BASE_URL}/{nfs_id}")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"NFS export with id ({nfs_id}) does not exist."
        self.assertEqual(response.data[0], e_msg)

    def test_adv_nfs_get(self):
        # Get advanced base URL
        self.get_base("/api/adv-nfs-exports")

    def test_adv_nfs_post_requests(self):
        # Without specifying entries
        data = {}
        response = self.client.post("/api/adv-nfs-exports", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Cannot export without specifying entries."
        self.assertEqual(response.data[0], e_msg)

        # Happy path
        data = {"entries": ["/export/share-nfs *(rw,async,insecure)"]}
        response = self.client.post("/api/adv-nfs-exports", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Invalid entries
        data = {"entries": ["/export/share2"]}
        response = self.client.post("/api/adv-nfs-exports", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid exports input -- (/export/share2)."
        self.assertEqual(response.data[0], e_msg)

        # Invalid entries
        data = {"entries": ["/export/share2 *(rw,async,insecure"]}
        response = self.client.post("/api/adv-nfs-exports", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = (
            "Invalid exports input -- (/export/share2 *(rw,async,"
            "insecure). Offending section: (*(rw,async,insecure)."
        )
        self.assertEqual(response.data[0], e_msg)

        # Invalid entries
        data = {"entries": ["invalid"]}
        response = self.client.post("/api/adv-nfs-exports", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid exports input -- (invalid)."
        self.assertEqual(response.data[0], e_msg)
