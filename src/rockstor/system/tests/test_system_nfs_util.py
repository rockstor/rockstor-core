"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import os
import unittest
from pyfakefs.fake_filesystem_unittest import TestCase
from unittest.mock import patch

from system.constants import NFS_CONFIG
from system.nfs_util import remove_nfs_export, refresh_nfs_exports, EXPORTFS

# N.B. Bar remove_nfs_update(), every NFS_CONFIG update;
# i.e. calls to refresh_nfs_exports(), carries all existing config from DB,
# including any changes requested.
# Calling refresh_nfs_exports({}) requests removing all entries in NFS_CONFIG.
# E.g.: storageadmin/views/nfs_exports.py refresh_nfs_exports() called with:

INITIAL_NFS_DICT = {
    "/export/nfs_export1": [
        {
            "client_str": "*",
            "option_list": "rw,async,insecure",
            "mnt_pt": "/mnt2/nfs_export1",
        }
    ],
    "/export/nfs_export2": [
        {
            "client_str": "192.168.2.2",
            "option_list": "rw,async,insecure",
            "mnt_pt": "/mnt2/nfs_export2",
        },
        {
            "client_str": "192.168.4.4",
            "option_list": "ro,sync,insecure",
            "mnt_pt": "/mnt2/nfs_export2",
        },
    ],
    "/export/nfs_export3": [
        {
            "client_str": "192.168.2.4",
            "option_list": "ro,sync,insecure",
            "mnt_pt": "/mnt2/nfs_export3",
            "admin_host": "adminhost.lan",
        }
    ],
}

# Currently creates the following NFS_CONFIG:

INITIAL_NFS_CONFIG = r"""/export/nfs_export1 *(rw,async,insecure)
/export/nfs_export2 192.168.2.2(rw,async,insecure) 192.168.4.4(ro,sync,insecure)
/export/nfs_export3 192.168.2.4(ro,sync,insecure) adminhost.lan(rw,no_root_squash)
"""

ONE_EXPORT_REMOVED_NFS_CONFIG = r"""/export/nfs_export1 *(rw,async,insecure)
/export/nfs_export3 192.168.2.4(ro,sync,insecure) adminhost.lan(rw,no_root_squash)
"""

ALL_EXPORTS_REMOVED_NFS_CONFIG = r""""""


class SystemNfsUtilTests(TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    poetry run django-admin test -p test_system_nfs_util.py -v 2
    ...
    For NFS API tests see: storageadmin/tests/test_nfs_export.py
    """

    def setUp(self):
        self.setUpPyfakefs()
        # Re-establish the start-state of the filesystem before every test.
        self.fake_fs().create_file(NFS_CONFIG, contents=INITIAL_NFS_CONFIG)
        # Mock bind_mount(): wrapper for:
        # - `mkdir /export/share.name`
        # - `mount --bind /mnt2/share.name /export/share.name
        self.patch_bindmount = patch("system.nfs_util.bind_mount")
        self.mock_bindmount = self.patch_bindmount.start()
        # nfs4_mount_teardown() returns true if no mount and no mount point.
        # I.e. there is nothing to teardown.
        # Have is_mounted() always return False initially to narrow tested code.
        # This way bindmount is called: but we mock this above to do nothing.
        # Ergo no /export/... mount points are created and no mounts established.
        self.patch_ismounted = patch("system.nfs_util.is_mounted")
        self.mock_ismounted = self.patch_ismounted.start()
        self.mock_ismounted.return_value = False
        # Mock valid_export(): exportfs requires real OS access, and with a mock we can
        # test rejection mechanisms.
        self.patch_validexport = patch("system.nfs_util.valid_export")
        self.mock_validexport = self.patch_validexport.start()
        self.mock_validexport.return_value = True
        # Mock re_export_all() to similarly avoid a call to exportfs to reexport all.
        self.patch_reexportall = patch("system.nfs_util.reexport_all")
        self.mock_reexportall = self.patch_reexportall.start()
        self.mock_reexportall.return_value = True
        # Ensure tests run after a failed real FS test are not similarly doing so.
        self.fake_fs().resume()

    def tearDown(self):
        # No necessity for self.tearDownPyfakefs()
        patch.stopall()

    def test_remove_nfs_export(self):
        self.assertTrue(os.path.exists(NFS_CONFIG))
        with open(NFS_CONFIG) as initial_content:
            self.assertEqual(initial_content.read(), INITIAL_NFS_CONFIG)
        self.assertTrue(remove_nfs_export(["nfs_export2"]))
        self.assertFalse(remove_nfs_export(["non-existent-share"]))
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), ONE_EXPORT_REMOVED_NFS_CONFIG)
        self.assertTrue(remove_nfs_export(["nfs_export1", "nfs_export3"]))
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), ALL_EXPORTS_REMOVED_NFS_CONFIG)
        self.assertFalse(remove_nfs_export([]))
        self.assertFalse(remove_nfs_export(["", ""]))
        os.remove(NFS_CONFIG)
        self.assertFalse(os.path.exists(NFS_CONFIG))
        # Ensure robustness to no NFS_CONFIG file existing.
        self.assertFalse(remove_nfs_export(["some-share"]))

    @unittest.skip("Modifies real filesystem")
    def test_refresh_nfs_exports_real_fs(self):
        # WARNING!!!: WIPES /etc/exports & /var/lib/nfs/etab on real FS.
        # Failed attempt to establish the binary `exportfs` on our fake_fs:
        # but the c based binary call will always access the real fs!!
        # https://pytest-pyfakefs.readthedocs.io/en/latest/intro.html#limitations
        # As we use the /usr/sbin/exportfs binary, establish this in our fake fs.
        # See: https://pytest-pyfakefs.readthedocs.io/en/latest/modules.html#module-pyfakefs.helpers
        # From `ldd /usr/sbin/exportfs` we have the following dynamic dependencies:
        # self.fake_fs().add_real_file("/lib64/libc.so.6")
        # self.fake_fs().add_real_file("/lib64/ld-linux-x86-64.so.2")
        # self.fake_fs().add_real_file(EXPORTFS)
        # Fails with "[Errno 9] Bad file descriptor: '12'" from run_command().
        # Ergo we must use the real FS to establish if we are instructing the
        # OS's EXPORTFS command appropriately to construct the /etc/exports we intend.
        # TODO: requires stopping some patches to re-enable now mocked exportfs calls.
        #  Leaving as useful when making changes that depend on exportfs behaviour.
        self.fake_fs().pause()
        if os.path.exists(NFS_CONFIG):
            os.remove(NFS_CONFIG)
        refresh_nfs_exports(INITIAL_NFS_DICT)
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), INITIAL_NFS_CONFIG)
        os.remove(NFS_CONFIG)
        self.fake_fs().resume()

    def test_refresh_nfs_exports(self):
        self.assertTrue(os.path.exists(NFS_CONFIG))
        with open(NFS_CONFIG) as initial_content:
            self.assertEqual(initial_content.read(), INITIAL_NFS_CONFIG)
        # Test overwrite of the same config:
        refresh_nfs_exports(INITIAL_NFS_DICT)
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), INITIAL_NFS_CONFIG)
        # Test creation and population of /etc/exports with the same config.
        os.remove(NFS_CONFIG)
        self.assertFalse(os.path.exists(NFS_CONFIG))
        refresh_nfs_exports(INITIAL_NFS_DICT)
        self.assertTrue(os.path.exists(NFS_CONFIG))
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), INITIAL_NFS_CONFIG)
        # Test refresh_nfs_exports({})
        refresh_nfs_exports({})
        with open(NFS_CONFIG) as written_content:
            self.assertEqual(written_content.read(), ALL_EXPORTS_REMOVED_NFS_CONFIG)
