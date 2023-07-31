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
from unittest import mock
from unittest.mock import patch

from rest_framework import status

from storageadmin.exceptions import RockStorAPIException
from storageadmin.models import Pool, Share, SambaShare, User
from storageadmin.tests.test_api import APITestMixin
from storageadmin.views.samba import SambaListView

"""
fixture with:
1 pool:
  - id=11
  - name="rock-pool"
1 share:
  - pool: "rock-pool" above
  - name: share-smb
  - exported with defaults:
      - comment: "Samba-Export"
      - admin_users: None
      - browsable: 'yes'
      - guest_ok: 'no'
      - read_only: 'no'
1 share:
  - name: share2 - no SMB export
1 User:
  - id: 1
  - name: admin
  - group: 1
1 Group:
  - pk: 1

proposed fixture = "test_smb.json"

cd /opt/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin dumpdata storageadmin.pool storageadmin.share
storageadmin.sambashare storageadmin.user storageadmin.group
--natural-foreign --indent 4 >
src/rockstor/storageadmin/fixtures/test_smb.json

To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_samba.py
"""


class SambaTests(APITestMixin, SambaListView):
    fixtures = ["test_api.json", "test_smb.json"]
    BASE_URL = "/api/samba"

    @classmethod
    def setUpClass(cls):
        super(SambaTests, cls).setUpClass()

        # post mocks
        cls.patch_mount_share = patch("storageadmin.views.samba.mount_share")
        cls.mock_mount_share = cls.patch_mount_share.start()

        # mock Share model's mount_status utility
        # True = Share is mounted, False = Share unmounted
        cls.patch_mount_status = patch("system.osi.mount_status")
        cls.mock_mount_status = cls.patch_mount_status.start()
        cls.mock_mount_status.return_value = True

        cls.patch_status = patch("storageadmin.views.samba.status")
        cls.mock_status = cls.patch_status.start()
        cls.mock_status.return_value = "out", "err", 0

        cls.patch_restart_samba = patch("storageadmin.views.samba.restart_samba")
        cls.mock_status = cls.patch_restart_samba.start()

        cls.patch_refresh_smb_config = patch(
            "storageadmin.views.samba.refresh_smb_config"
        )
        cls.mock_refresh_smb_config = cls.patch_refresh_smb_config.start()
        cls.mock_refresh_smb_config.return_value = "smbconfig"

        cls.patch_refresh_smb_discovery = patch(
            "storageadmin.views.samba.refresh_smb_discovery"
        )
        cls.mock_refresh_smb_discovery = cls.patch_refresh_smb_discovery.start()

    @classmethod
    def tearDownClass(cls):
        super(SambaTests, cls).tearDownClass()

    def test_validate_input(self):
        """
        Test that _validate_input() returns a valid dict when:
        1. all input data are filled and valid
        2. no input data are specified (should return default options)
        """
        # 1. all input data are filled and valid
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": False,
            "time_machine": True,
            "guest_ok": "no",
        }
        expected_result = {
            "comment": "Samba-Export",
            "read_only": "no",
            "browsable": "yes",
            "time_machine": True,
            "custom_config": [],
            "guest_ok": "no",
            "shadow_copy": False,
        }
        returned = self._validate_input(rdata=data)
        self.assertEqual(
            returned,
            expected_result,
            msg="Un-expected _validate_input() result:\n "
            "returned = ({}).\n "
            "expected = ({}).".format(returned, expected_result),
        )

        # 2. no input data are specified (should return default options)
        data = {}
        expected_result = {
            "comment": "samba export",
            "read_only": "no",
            "browsable": "yes",
            "time_machine": False,
            "custom_config": [],
            "guest_ok": "no",
            "shadow_copy": False,
        }
        returned = self._validate_input(rdata=data)
        self.assertEqual(
            returned,
            expected_result,
            msg="Un-expected _validate_input() result:\n "
            "returned = ({}).\n "
            "expected = ({}).".format(returned, expected_result),
        )

    def test_validate_input_error(self):
        """
        Test that _validate_input raises Exceptions when input data contain error(s).
        The following cases are tested below:
        1. invalid 'custom_config' information
        2. invalid 'browsable' information
        3. invalid 'guest_ok' information
        4. invalid 'read_only' information
        5. invalid 'shadow_copy' information
        """
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "yes",
            "custom_config": "not-a-list",
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        with self.assertRaises(RockStorAPIException):
            self._validate_input(rdata=data)
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "maybe",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        with self.assertRaises(RockStorAPIException):
            self._validate_input(rdata=data)
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": False,
            "guest_ok": "maybe",
        }
        with self.assertRaises(RockStorAPIException):
            self._validate_input(rdata=data)
        data = {
            "read_only": "maybe",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        with self.assertRaises(RockStorAPIException):
            self._validate_input(rdata=data)
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": ["test"],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["9", "10"],
            "shadow_copy": True,
            "guest_ok": "no",
        }
        with self.assertRaises(RockStorAPIException):
            self._validate_input(rdata=data)

    def test_create_samba_share(self):
        """
        Test that create_samba_share() returns a correct SambaShare object
        when all conditions are valid.
        """
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": [],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["2"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        expected_result = SambaShare.objects.get(pk=1)
        returned = self.create_samba_share(data)
        self.assertEqual(
            returned,
            expected_result,
            msg="Un-expected create_samba_share() result:\n "
            "returned = ({} with id {}).\n "
            "expected = ({} with id {}).".format(
                returned, returned.id, expected_result, expected_result.id
            ),
        )

    def test_create_samba_share_incorrect_share(self):
        """
        Test that create_samba_share() raises an exception
        when a non-existing share is provided.
        """
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": [],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["32"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        with self.assertRaises(RockStorAPIException):
            self.create_samba_share(rdata=data)

    @mock.patch("storageadmin.views.samba.logger")
    def test_create_samba_share_existing_export(self, mock_logger):
        """
        Test that create_samba_share() logs the appropriate error
        when the given share is already exported via Samba.
        """
        data = {
            "read_only": "no",
            "comment": "Samba-Export",
            "admin_users": [],
            "browsable": "yes",
            "custom_config": [],
            "snapshot_prefix": "",
            "shares": ["2"],
            "shadow_copy": False,
            "guest_ok": "no",
        }
        # e_msg = ("Share ({}) is already exported via Samba.").format(
        #     self.temp_share_smb.name
        # )
        self.create_samba_share(rdata=data)
        mock_logger.error.assert_called()
        # mock_logger.error.assert_called_with(e_msg)

    # TODO: ERROR: ValueError: "<SambaShare:
    #  SambaShare object>" needs to have a value for field "sambashare" before this
    #  many-to-many relationship can be used.
    # @mock.patch("storageadmin.views.samba.SambaShare")
    # def test_get(self, mock_sambashare):
    #     """
    #     Test GET request
    #     1. Get base URL
    #     2. Get request with valid id
    #     """
    #     self.get_base(self.BASE_URL)
    #
    #     # Create mock SambaShare
    #     # smb_id = self.temp_sambashare.id
    #     # Some conflict exists from a previous mock_sambashare, so set smb_id manually
    #     smb_id = 1
    #     # print("smb_id is {}".format(smb_id))
    #     mock_sambashare.objects.get.return_value = self.temp_sambashare
    #
    #     # test get of detailed view for a valid smb_id
    #     response = self.client.get("{}/{}".format(self.BASE_URL, smb_id))
    #     self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
    #     self.assertEqual(response.data["id"], smb_id)

    def test_get_non_existent(self):
        """
        Test GET request
        1. Get base URL
        2. Get request with invalid id
        """
        # get base URL
        self.get_base(self.BASE_URL)
        # # get sambashare with id
        # response = self.client.get('{}/1'.format(self.BASE_URL))
        # self.assertEqual(response.status_code, status.HTTP_200_OK,
        #                  msg=response)
        # get sambashare with non-existent id
        response = self.client.get("{}/5".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND, msg=response)

    def test_post_requests_1(self):
        """
        invalid samba api operations
        . Create a samba without providing share id
        """

        # create samba export with no share names
        data = {"browsable": "yes", "guest_ok": "yes", "read_only": "yes"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Must provide share names."
        self.assertEqual(response.data[0], e_msg)

    def test_post_requests_2(self):
        """
        . Create a samba export for the share that has already been exported
        """
        # create samba with invalid browsable, guest_ok, read_only choices
        data = {
            "shares": ["3"],
            "browsable": "Y",
            "guest_ok": "yes",
            "read_only": "yes",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid choice for browsable. Possible choices are yes or no."
        self.assertEqual(response.data[0], e_msg)

        data = {
            "shares": ["3"],
            "browsable": "yes",
            "guest_ok": "Y",
            "read_only": "yes",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid choice for guest_ok. Possible options are yes or no."
        self.assertEqual(response.data[0], e_msg)

        data = {
            "shares": ["3"],
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "Y",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Invalid choice for read_only. Possible options are yes or no."
        self.assertEqual(response.data[0], e_msg)

        # create samba export
        # we use share id 3 (share2) as not yet smb exported.
        data = {
            "shares": ["3"],
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "yes",
            "admin_users": ("admin",),
            "custom_config": ("CONFIG", "XYZ"),
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        ## The test below may better belong to test_get() above, so move it there.
        # smb_id = response.data["id"]
        # print("response.data is {}".format(response.data))
        #
        # # test get of detailed view for the smb_id
        # # First, save the SambaShare as created above (with id = 1)
        # mock_sambashare.objects.get.return_value = self.temp_sambashare
        # response = self.client.get("{}/{}".format(self.BASE_URL, smb_id))
        # self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        # self.assertEqual(response.data["id"], smb_id)

        # # TODO: Needs multiple share instances mocked
        # # create samba exports for multiple(3) shares at once
        # data = {'shares': ('share2', 'share3', 'share4'), 'browsable': 'yes',
        #         'guest_ok': 'yes', 'read_only': 'yes',
        #         'admin_users': ('admin', )}
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK, msg=response.data)

        ## post() does not raise exception in this condition anymore, but rather
        ## logs an error as "Share (share.name) is already exported via Samba".
        # # create samba export with the share that has already been exported above
        # data = {
        #     "shares": ["24"],
        #     "browsable": "no",
        #     "guest_ok": "yes",
        #     "read_only": "yes",
        # }
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     msg=response.data,
        # )
        # e_msg = "Share (share2) is already exported via Samba."
        # self.assertEqual(response.data[0], e_msg)

    def test_post_requests_no_admin(self):
        """
        Test a valid post request creating a samba export
        when no admin user is specified
        """
        # create samba export with no admin users
        data = {
            "shares": ["3"],
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "yes",
            "custom_config": ("CONFIG", "XYZ"),
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_put_requests_1(self):
        """
        . Edit samba that does not exists
        """
        # edit samba that does not exist
        smb_id = 99999
        data = {
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "yes",
            "admin_users": "usr",
        }
        response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Samba export for the id ({}) does not exist.".format(smb_id)
        self.assertEqual(response.data[0], e_msg)

    def test_put_requests_2(self):
        """
        1. Edit samba that does not exists
        2. Edit samba
        """
        # edit samba with invalid custom config
        smb_id = 1
        data = {
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "yes",
            "custom_config": "CONFIGXYZ",
        }
        response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Custom config must be a list of strings."
        self.assertEqual(response.data[0], e_msg)

        # test mount_share exception case
        # TODO: Fails on first assert
        # Note as mount isn't called unless the share is found not to be
        # mounted we indicate this via our mock of the share utility.

        self.mock_mount_status.return_value = False

        # # TODO: mocking issue as associated share is not found to be unmounted.
        # smb_id = 1
        # data = {"browsable": "yes", "guest_ok": "yes", "read_only": "yes"}
        # self.mock_mount_share.side_effect = KeyError("error")
        # response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        # self.assertEqual(
        #     response.status_code,
        #     status.HTTP_500_INTERNAL_SERVER_ERROR,
        #     msg=response.data,
        # )
        # e_msg = "Failed to mount share (share-smb) due to a low level error."
        # self.assertEqual(response.data[0], e_msg)

        # Return share mock mounted_state to mounted
        self.mock_mount_status.return_value = True

        # # TODO: AssertionError: ["local variable 'auo' referenced before assignment" ...
        # #  storageadmin/views/samba.py", line 139, in _set_admin_users\n
        # #  auo.smb_shares.add(smb_share)\nUnboundLocalError: local variable \'auo\'
        # #  referenced before assignment\n']
        # # happy path
        # smb_id = 1
        # self.mock_mount_share.side_effect = None
        # data = {
        #     "browsable": "yes",
        #     "guest_ok": "yes",
        #     "read_only": "yes",
        #     "admin_users": ("admin",),
        #     "custom_config": ("CONFIG", "XYZ"),
        # }
        # response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # # edit samba export with admin user other than admin
        # smb_id = 1
        # data = {
        #     "browsable": "yes",
        #     "guest_ok": "yes",
        #     "read_only": "yes",
        #     "admin_users": ("admin2",),
        #     "custom_config": ("CONFIG", "XYZ"),
        # }
        # response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # edit samba export passing no admin users
        smb_id = 1
        data = {
            "browsable": "yes",
            "guest_ok": "yes",
            "read_only": "yes",
            "custom_config": ("CONFIG", "XYZ"),
        }
        response = self.client.put("{}/{}".format(self.BASE_URL, smb_id), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_delete_requests_1(self):
        """
        . Delete samba that does not exist
        """
        # Delete samba that does nor exists
        smb_id = 99999
        response = self.client.delete("{}/{}".format(self.BASE_URL, smb_id))
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Samba export for the id ({}) does not exist.".format(smb_id)
        self.assertEqual(response.data[0], e_msg)

    def test_delete_requests_2(self):
        """
        . Delete samba
        """
        # happy path
        smb_id = 1
        response = self.client.delete("{}/{}".format(self.BASE_URL, smb_id))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
