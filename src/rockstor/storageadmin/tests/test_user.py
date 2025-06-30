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
along with this program. If not, see <https://www.gnu.org/licenses/>
"""

from rest_framework import status
from unittest.mock import patch

from django.conf import settings
from storageadmin.tests.test_api import APITestMixin


"""
Fixture creation instructions:

We have need for a created "testuser" (uid 1004) see also: 
exclude_list within src/rockstor/storageadmin/views/user.py

cd /opt/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin dumpdata storageadmin.user storageadmin.group
--natural-foreign --indent 4 >
src/rockstor/storageadmin/fixtures/test_user.json

To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_user.py
"""


class UserTests(APITestMixin):
    # multi_db = True
    fixtures = ["test_api.json", "test_user.json"]
    BASE_URL = "/api/users"
    # Slowroll `ssh-keygen`:
    # openssh-common (Version-Release Buildtime): 10.0p2-2.0.2.1.sr20250501 May 13 2025
    valid_pubkey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIKKFqyt41xjfic1gPx49ByHwDYrlPTD+zI4LWgn7emyv test@rslowroll"

    @classmethod
    def setUpClass(cls):
        super(UserTests, cls).setUpClass()

        # post mocks

        cls.patch_getpwnam = patch("pwd.getpwnam")
        cls.mock_getpwnam = cls.patch_getpwnam.start()
        cls.mock_getpwnam.return_value = 1, 2, 3, 5

        # Mock out username_to_uid to return None for now to avoid triggering
        # issues in that code, N.B. it also calls getpwnam (see last mock).
        # TODO: Add specific tests for pincode generation and delete.
        cls.patch_username_to_uid = patch("system.pinmanager.username_to_uid")
        cls.mock_username_to_uid = cls.patch_username_to_uid.start()
        cls.mock_username_to_uid.return_value = None

        cls.patch_useradd = patch("storageadmin.views.user.useradd")
        cls.mock_useradd = cls.patch_useradd.start()
        cls.mock_useradd.return_value = ([""], [""], 0)

        cls.patch_usermod = patch("storageadmin.views.user.usermod")
        cls.mock_usermod = cls.patch_usermod.start()
        cls.mock_usermod.return_value = "out", "err", 0

        cls.patch_userdel = patch("storageadmin.views.user.userdel")
        cls.mock_userdel = cls.patch_userdel.start()
        cls.mock_userdel.return_value = True

        cls.patch_smbpasswd = patch("storageadmin.views.user.smbpasswd")
        cls.mock_smbpasswd = cls.patch_smbpasswd.start()
        cls.mock_smbpasswd.return_value = "out", "err", 0

        cls.patch_add_ssh_key = patch("storageadmin.views.user.add_ssh_key")
        cls.mock_add_ssh_key = cls.patch_add_ssh_key.start()
        cls.mock_add_ssh_key.return_value = True

        cls.patch_update_shell = patch("storageadmin.views.user.update_shell")
        cls.mock_update_shell = cls.patch_update_shell.start()
        cls.mock_update_shell.return_value = True

    @classmethod
    def tearDownClass(cls):
        super(UserTests, cls).tearDownClass()

    def test_get(self):
        """
        Test GET request
        1. Get base URL
        """
        # get base URL
        self.get_base(self.BASE_URL)

        # get list of all users:
        response = self.client.get(f"{self.BASE_URL}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_post_requests(self):

        data = {"username": "user1", "password": "pwuser1"}
        invalid_user_names = ("User $", "-user", ".user", "", " ")
        for uname in invalid_user_names:
            data["username"] = uname
            response = self.client.post(self.BASE_URL, data=data)
            self.assertEqual(
                response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
            )
            e_msg = (
                "Username is invalid. It must conform to the regex: "
                "([A-Za-z][-a-zA-Z0-9_]*$)."
            )
            self.assertEqual(response.data[0], e_msg)

        # username with more than 30 characters
        invalid_user_name = "user" * 11
        data = {"username": invalid_user_name, "password": "pwadmin"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = "Username cannot be more than 30 characters long."
        self.assertEqual(response.data[0], e_msg)

        # create user with no password
        data = {"username": "user1"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = "Password must be a valid string."
        self.assertEqual(response.data[0], e_msg)

        # create user with invalid admin(not boolean)
        data = {"username": "user1", "password": "pwuser1", "admin": "Y"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = 'Element "admin" (user type) must be a boolean.'
        self.assertEqual(response.data[0], e_msg)

        # create user with invalid shell
        data = {"username": "user1", "password": "pwuser1", "shell": "Y"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = (
            f"Element shell (Y) is not valid. Valid shells are {settings.VALID_SHELLS}."
        )
        self.assertEqual(response.data[0], e_msg)

        # TODO: create user with existing username
        # Tricky as if we pass a password then it's interpreted as a pw change
        # and if not then we trigger:
        # "Password must be a valid string."
        # data = {'username': 'admin', 'password': 'string'}
        # response = self.client.post(self.BASE_URL, data=data)
        # self.assertEqual(response.status_code,
        #                  status.HTTP_200_OK,
        #                  msg=response.data)
        # e_msg = ("User (admin) already exists. Please choose a different "
        #          "username.")
        # self.assertEqual(response.data, e_msg)

        # Create user with existing username and uid (in fixture).
        data = {"username": "testuser", "password": "fakepassword", "uid": "1004"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = f"User ({data['username']}) already exists. Please choose a different username."
        self.assertEqual(response.data[0], e_msg)

        # create a user with existing uid ('testuser' in fixture has a uid 1004)
        # TODO: We are not limiting user id to >= 1000.
        data = {
            "username": "newUser",
            "password": "pwuser2",
            "group": "users",
            "uid": "1004",
            "pubic_key": "xxx",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"UID ({data['uid']}) already exists. Please choose a different one."
        self.assertEqual(response.data[0], e_msg)

        # happy path create user: "newUser" with explicit group & public key.
        data = {
            "username": "newUser",
            "password": "pwuser2",
            "group": "admin",
            "pubic_key": "xxx",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["username"], "newUser")

        # happy path create another user "newUser2" with explicit uid and user
        data = {
            "username": "newUser2",
            "password": "pwuser2",
            "uid": "5001",
            "user": "newuser",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["username"], "newUser2")

    def test_invalid_UID(self):
        # Create username with non int UID
        data = {
            "username": "newUser",
            "password": "pwuser2",
            "group": "admin",
            "uid": "string",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = (
            "UID must be an integer, try again. Exception: (invalid "
            "literal for int() with base 10: 'string')."
        )
        self.assertEqual(response.data[0], e_msg)

    def test_duplicate_system_username(self):

        # create a user that is already a system user(eg: root)
        data = {"username": "root", "password": "rootpw"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = f"User ({data['username']}) already exists. Please choose a different username."
        self.assertEqual(response.data[0], e_msg)

    def test_duplicate_managed_username(self):

        # create user with existing rockstor username ("testuser" in fixtures).
        # N.B. no uid specified.
        data = {"username": "testuser", "password": "pwadmin2"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = f"User ({data['username']}) already exists. Please choose a different username."
        self.assertEqual(response.data[0], e_msg)

    def test_email_validation(self):

        # create user with invalid email
        data = {"username": "user99", "password": "pwuser1", "email": "123"}
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        # N.B. in the above we are expecting 500 currently.
        self.assertEqual(
            response.data[0], "{'email': ['Enter a valid email address.']}"
        )

    def test_pubkey_validation(self):
        data = {
            "username": "user1",
            "password": "pwuser1",
            "email": "test@test.com",
            "public_key": "foobar",
        }
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        self.assertEqual(response.data[0], "Public key is invalid.")

        # TODO: Look closer as the above, as it seems we may be creating a user
        # TODO: with an invalid public_key

        # Change our user to avoid triggering User ... already exists error
        # if the above user creation succeeded.
        data["username"] = "user22"
        # And switch our key to a valid one:
        data["public_key"] = self.valid_pubkey
        response = self.client.post(self.BASE_URL, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data["public_key"], data["public_key"])

    def test_put_requests(self):

        # Edit user that does not exist
        data = {"group": "admin"}
        response = self.client.put(f"{self.BASE_URL}/admin99", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "User (admin99) does not exist."
        self.assertEqual(response.data[0], e_msg)

        data = {"password": "admin2", "group": "admin"}
        response = self.client.put(f"{self.BASE_URL}/bin", data=data)
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        # for restricted users see exclude_list in src/rockstor/storageadmin/views/user.py
        e_msg = "Editing restricted user (bin) is not supported."
        self.assertEqual(response.data[0], e_msg)

    def test_enable_admin_without_pw_change(self):
        # Edit existing user to enable admin: check pw reset prompt
        data = {"admin": True}
        response = self.client.put(f"{self.BASE_URL}/testuser", data=data)
        self.assertEqual(
            response.status_code, status.HTTP_400_BAD_REQUEST, msg=response.data
        )
        e_msg = (
            "Password reset is required to enable admin access. Please "
            "provide a new password."
        )
        self.assertEqual(response.data[0], e_msg)

    def test_enable_admin_existing_user(self):
        # happy path - enable admin on existing user with password change
        data = {"password": "admin2", "group": "users", "admin": True}
        response = self.client.put(f"{self.BASE_URL}/testuser", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_enable_admin_plus_public_key(self):
        data = {
            "password": "admin2",
            "group": "users",
            "admin": True,
            "user": "testuser",
            "public_key": self.valid_pubkey,
        }
        response = self.client.put(f"{self.BASE_URL}/testuser", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_change_existing_user_various(self):
        # change password, group, shell, and email.
        data = {
            "password": "newpass",
            "group": "newgroup",
            "user": "testuser",
            "shell": "/bin/xyz",
            "email": "admin2@xyz.com",
        }
        response = self.client.put(f"{self.BASE_URL}/testuser", data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    def test_delete_nonexistent_user(self):

        # As we now have a pincard mechanism which will attempt to flush
        # pincards of non existent users we mock it's output to avoid
        # real system calls to the passwd db.

        # delete user that does not exists
        username = "non-existent"
        response = self.client.delete(f"{self.BASE_URL}/{username}")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"User ({username}) does not exist."
        self.assertEqual(response.data[0], e_msg)

    def test_delete_system_user(self):
        # delete preexisting restricted system user
        username = "bin"
        response = self.client.delete(f"{self.BASE_URL}/{username}")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"Delete of restricted user ({username}) is not supported."
        self.assertEqual(response.data[0], e_msg)

    def test_low_level_error_on_delete(self):
        username = "testuser"
        self.mock_userdel.side_effect = KeyError("error")
        response = self.client.delete(f"{self.BASE_URL}/{username}")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = f"A low level error occurred while deleting the user ({username})."
        self.assertEqual(response.data[0], e_msg)

    def test_logged_in_user_delete(self):
        # delete currently logged in user (admin) from APITestMixin
        self.mock_userdel.side_effect = None
        username = "admin"
        response = self.client.delete(f"{self.BASE_URL}/{username}")
        self.assertEqual(
            response.status_code,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            msg=response.data,
        )
        e_msg = "Cannot delete the currently logged in user."
        self.assertEqual(response.data[0], e_msg)

    def test_delete_existing_user(self):
        # Happy path of deleting an in-fixture, Web-UI created user "testuser".
        username = "testuser"
        response = self.client.delete(f"{self.BASE_URL}/{username}")
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)
