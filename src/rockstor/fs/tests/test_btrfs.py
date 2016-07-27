"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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

import unittest
from fs.btrfs import add_pool, pool_raid, is_subvol
import mock
from mock import patch


class Pool(object):
    def __init__(self, raid, name):
        self.raid = raid
        self.name = name


class BTRFSTests(unittest.TestCase):
    def setUp(self):
        self.patch_run_command = patch('fs.btrfs.run_command')
        self.mock_run_command = self.patch_run_command.start()

    def tearDown(self):
        patch.stopall()

    # sample test
    def test_add_pool_mkfs_fail(self):
        pool = Pool(raid='raid0', name='mypool')
        disks = ('sdb', 'sdc')
        self.mock_run_command.side_effect = Exception('mkfs error')
        self.assertEqual(add_pool(pool, disks), 1)

    def test_get_pool_raid_levels_identification(self):
        """
        Presents the raid identification function with example data and compares
        it's return dict to that expected for the given input.
        :return: 'ok' if all is as expected or a message indicating which raid
        level was incorrectly identified given the test data.
        N.B. Only the first raid level fail is indicated, however all are
        expected to pass anyway so we will have to tend to each failure in turn
        until all pass.
        """
        # setup fake mount point
        mount_point = '/mnt2/fake-pool'
        cmd_rc = 0
        cmd_e = ['']
        # setup example btrfs fi df mount_point outputs for given inputs.
        # Outputs are simple lists of whole lines output from btrfs fi df
        single_fi_df = ['Data, single: total=8.00MiB, used=64.00KiB',
                        'System, single: total=4.00MiB, used=16.00KiB',
                        'Metadata, single: total=216.00MiB, used=128.00KiB',
                        'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        # Expected return is a dict of extracted info from above command output.
        single_return = {'data': 'single', 'system': 'single',
                         'globalreserve': 'single', 'metadata': 'single'}
        raid0_fi_df = ['Data, RAID0: total=512.00MiB, used=256.00KiB',
                       'System, RAID0: total=16.00MiB, used=16.00KiB',
                       'Metadata, RAID0: total=512.00MiB, used=128.00KiB',
                       'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid0_return = {'data': 'raid0', 'system': 'raid0',
                        'globalreserve': 'single', 'metadata': 'raid0'}
        raid1_fi_df = ['Data, RAID1: total=512.00MiB, used=192.00KiB',
                       'System, RAID1: total=32.00MiB, used=16.00KiB',
                       'Metadata, RAID1: total=256.00MiB, used=128.00KiB',
                       'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid1_return = {'data': 'raid1', 'system': 'raid1',
                        'globalreserve': 'single', 'metadata': 'raid1'}
        # Thanks to @grebnek in forum and GitHub for spotting this:
        # https://btrfs.wiki.kernel.org/index.php/FAQ#Why_do_I_have_.22single.22_chunks_in_my_RAID_filesystem.3F
        # When converting from single to another raid level it is normal for
        # a few chunks to remain in single until the next balance operation.
        raid1_fi_df_some_single_chunks = [
            'Data, RAID1: total=416.00MiB, used=128.00KiB',
            'Data, single: total=416.00MiB, used=0.00B',
            'System, RAID1: total=32.00MiB, used=16.00KiB',
            'Metadata, RAID1: total=512.00MiB, used=128.00KiB',
            'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        # for a time we incorrectly parsed the last btrfs fi df mount_point as
        # the following:
        raid1_some_single_chunks_return_broken = {'data': 'single',
                                                  'system': 'raid1',
                                                  'globalreserve': 'single',
                                                  'metadata': 'raid1'}
        # but the expected result should be the same as "raid1_return" above
        # ie data raid1 not single.
        raid10_fi_df = ['Data, RAID10: total=419.75MiB, used=128.00KiB',
                        'System, RAID10: total=16.00MiB, used=16.00KiB',
                        'Metadata, RAID10: total=419.75MiB, used=128.00KiB',
                        'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid10_return = {'data': 'raid10', 'system': 'raid10',
                         'globalreserve': 'single', 'metadata': 'raid10'}
        raid5_fi_df = ['Data, RAID5: total=215.00MiB, used=128.00KiB',
                       'System, RAID5: total=8.00MiB, used=16.00KiB',
                       'Metadata, RAID5: total=215.00MiB, used=128.00KiB',
                       'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid5_return = {'data': 'raid5', 'system': 'raid5',
                        'globalreserve': 'single', 'metadata': 'raid5'}
        raid6_fi_df = ['Data, RAID6: total=211.62MiB, used=128.00KiB',
                       'System, RAID6: total=8.00MiB, used=16.00KiB',
                       'Metadata, RAID6: total=211.62MiB, used=128.00KiB',
                       'GlobalReserve, single: total=16.00MiB, used=0.00B', '']
        raid6_return = {'data': 'raid6', 'system': 'raid6',
                        'globalreserve': 'single', 'metadata': 'raid6'}
        # Data to test for correct recognition of the default rockstor_rockstor
        # pool ie:
        default_sys_fi_df = ['Data, single: total=3.37GiB, used=2.71GiB',
                             'System, DUP: total=8.00MiB, used=16.00KiB',
                             'System, single: total=4.00MiB, used=0.00B',
                             'Metadata, DUP: total=471.50MiB, used=165.80MiB',
                             'Metadata, single: total=8.00MiB, used=0.00B',
                             'GlobalReserve, single: total=64.00MiB, used=0.00B',
                             '']
        default_sys_return = {'data': 'single', 'system': 'dup',
                              'globalreserve': 'single', 'metadata': 'dup'}
        # N.B. prior to pr #1408 as of writing this unit test we had a
        # default_sys_return of which was correct for data but not system
        default_sys_return_broken = {'data': 'single', 'system': 'single',
                            'globalreserve': 'single', 'metadata': 'single'}
        # list used to report what raid level is currently under test.
        raid_levels_tested = ['single', 'raid0', 'raid1', 'raid10', 'raid5',
                              'raid6', 'raid1_some_single_chunks',
                              'default_sys_pool']
        # list of example fi_df outputs in raid_levels_tested order
        btrfs_fi_di = [single_fi_df, raid0_fi_df, raid1_fi_df, raid10_fi_df,
                       raid5_fi_df, raid6_fi_df, raid1_fi_df_some_single_chunks,
                       default_sys_fi_df]
        # list of correctly parsed return dictionaries
        return_dict = [single_return, raid0_return, raid1_return, raid10_return,
                       raid5_return, raid6_return, raid1_return,
                       default_sys_return]
        # simple iteration over above example inputs to expected outputs.
        for raid_level, fi_df, expected_result in map(None, raid_levels_tested,
                                                      btrfs_fi_di, return_dict):
            # mock example command output with no error and rc=0
            self.mock_run_command.return_value = (fi_df, cmd_e, cmd_rc)
            # assert get_pool_raid_level returns what we expect.
            self.assertEqual(pool_raid(mount_point), expected_result,
                             msg='get_pool_raid_level() miss identified raid '
                                 'level %s' % raid_level)

    def test_is_subvol_exists(self):
        mount_point = '/mnt2/test-pool/test-share'
        o = ['/mnt2/test-pool/test-share', '\tName: \t\t\ttest-share',
             '\tUUID: \t\t\t80c240a2-c353-7540-bb5e-b6a71a50a02e',
             '\tParent UUID: \t\t-', '\tReceived UUID: \t\t-',
             '\tCreation time: \t\t2016-07-27 17:01:09 +0100',
             '\tSubvolume ID: \t\t258', '\tGeneration: \t\t13',
             '\tGen at creation: \t13', '\tParent ID: \t\t5',
             '\tTop level ID: \t\t5', '\tFlags: \t\t\t-', '\tSnapshot(s):', '']
        e = ['']
        rc = 0
        # btrfs subvol show has return code of 0 (no errors) when subvol exists
        self.mock_run_command.return_value = (o, e, rc)
        self.assertEqual(is_subvol(mount_point), True,
                         msg='Did NOT return True for existing subvol')

    def test_is_subvol_nonexistent(self):
        mount_point = '/mnt2/test-pool/test-share'
        o = ['']
        e = ["ERROR: cannot find real path for '/mnt2/test-pool/test-share': No such file or directory", '']
        rc = 1
        # btrfs subvol show has return code of 1 when subvol doesn't exist.
        self.mock_run_command.return_value = (o, e, rc)
        self.assertEqual(is_subvol(mount_point), False,
                         msg='Did NOT return False for nonexistent subvol')
