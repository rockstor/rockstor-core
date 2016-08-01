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
from fs.btrfs import add_pool, pool_raid, is_subvol, share_usage, balance_status
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
        # # setup mock patch for is_mounted() in fs.btrfs
        # self.patch_is_mounted = patch('fs.btrfs.is_mounted')
        # self.mock_is_mounted = self.patch_is_mounted.start()
        # setup mock patch for mount_root() in fs.btrfs
        self.patch_mount_root = patch('fs.btrfs.mount_root')
        self.mock_mount_root = self.patch_mount_root.start()

    def tearDown(self):
        patch.stopall()

    # # sample test
    # def test_add_pool_mkfs_fail(self):
    #     pool = Pool(raid='raid0', name='mypool')
    #     disks = ('sdb', 'sdc')
    #     self.mock_run_command.side_effect = Exception('mkfs error')
    #     self.assertEqual(add_pool(pool, disks), 1)

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
        self.assertTrue(is_subvol(mount_point),
                        msg='Did NOT return True for existing subvol')

    def test_is_subvol_nonexistent(self):
        mount_point = '/mnt2/test-pool/test-share'
        o = ['']
        e = ["ERROR: cannot find real path for '/mnt2/test-pool/test-share': No such file or directory", '']
        rc = 1
        # btrfs subvol show has return code of 1 when subvol doesn't exist.
        self.mock_run_command.return_value = (o, e, rc)
        self.assertFalse(is_subvol(mount_point),
                         msg='Did NOT return False for nonexistent subvol')


    # def test_is_subvol_exception(self):
    #     mount_point = '/mnt2/test-pool/test-share'
    #     o = ['']
    #     e = ["not important as we are throwing exception in run_command"]
    #     rc = 1
    #     # btrfs subvol show has return code of 1 when subvol doesn't exist.
    #     self.mock_run_command.side_effect = Exception('mkfs error')
    #     self.assertFalse(is_subvol(mount_point),
    #                  msg='Did NOT return False for exception')


    def test_share_usage(self):
        """
        Moc the return value of "btrfs qgroup show pool_mount_point" to assess
        test_share's parsing capabilities to extract rfer and excl subvol usage
        information.
        :return:
        """
        # share_usage() CALLED WITH pool name of=test-pool and share_id=0/285
        # mount_root(Pool object) returned /mnt2/test-pool
        # share_usage cmd=['/sbin/btrfs', 'qgroup', 'show', u'/mnt2/test-pool']
        # share_usage returning rusage=461404 and eusage=3512
        #
        # Setup our calling variables and mock the root pool as mounted.
        root_mount_point = '/mnt2/test-pool'
        o = ['qgroupid         rfer         excl ',
             '--------         ----         ---- ',
             '0/5          16.00KiB     16.00KiB ',
             '0/259         2.04MiB      2.04MiB ',
             '0/260         7.37GiB      7.37GiB ',
             '0/261        63.65MiB     63.65MiB ',
             '0/263       195.32MiB    496.00KiB ',
             '0/264       195.34MiB    112.00KiB ',
             '0/265       195.34MiB     80.00KiB ',
             '0/266       195.34MiB     80.00KiB ',
             '0/267       195.34MiB     80.00KiB ',
             '0/268       195.38MiB    152.00KiB ',
             '0/269       229.06MiB     80.00KiB ',
             '0/270       229.06MiB     80.00KiB ',
             '0/271       229.06MiB     80.00KiB ',
             '0/272       229.06MiB     96.00KiB ',
             '0/273       229.06MiB    128.00KiB ',
             '0/274       236.90MiB     80.00KiB ',
             '0/275       236.90MiB     80.00KiB ',
             '0/276       236.90MiB     80.00KiB ',
             '0/277       450.54MiB    128.00KiB ',
             '0/278       450.54MiB    112.00KiB ',
             '0/279       450.54MiB    128.00KiB ',
             '0/280       450.54MiB     80.00KiB ',
             '0/281       450.54MiB     80.00KiB ',
             '0/282       450.54MiB     80.00KiB ',
             '0/283       450.54MiB     80.00KiB ',
             '0/284       450.54MiB    176.00KiB ',
             '0/285       450.59MiB      3.43MiB ',
             '2015/1          0.00B        0.00B ',
             '2015/2        2.04MiB      2.04MiB ',
             '2015/3        7.37GiB      7.37GiB ',
             '2015/4       63.65MiB     63.65MiB ', '']
        e = ['']
        rc = 0
        # is_mounted returning True avoids mount command calls in mount_root()
        mount_point = '/mnt2/test-mount'
        self.mock_mount_root.return_value = mount_point
        # setup the return values from our run_command wrapper
        # examples of output from /mnt2/test-pool from a real system install
        self.mock_run_command.return_value = (o, e, rc)
        # create a fake pool object
        pool = Pool(raid='raid0', name='test-pool')
        # and fake share_id / qgroupid
        share_id = '0/285'
        # As share_usage uses convert_to_kib() everything is converted to KiB
        # here we convert 450.59MiB and 3.43MiB to their KiB equivalent (x1024)
        expected_results = (461404, 3512)
        self.assertEqual(share_usage(pool, share_id), expected_results,
                         msg='Failed to retrieve expected rfer and excl usage')


    # def test_balance_status_in_progress(self):
    #     """
    #     Moc return value of run_command executing btrfs balance status
    #     pool_mount_point which is invoked inside of target function.
    #     :return:
    #     """
    #     # balance_status called with pool object of name=Pool object
    #     #
    #     # typical return for no current balance operation in progress:
    #     # out=["No balance found on '/mnt2/single-to-raid1'", '']
    #     # err=['']
    #     # rc=0
    #     # example return for ongoing balance operation:
    #     pool = Pool(raid='raid0', name='test-pool')
    #     out = ["Balance on '/mnt2/rock-pool' is running",
    #            '7 out of about 114 chunks balanced (8 considered),  94% left',
    #            '']
    #     err = ['']
    #     # N.B. the return code for a in progress balance = 1
    #     rc = 1
    #     expected_results = {'status': 'running', 'percent_done': 6}
    #     # is_mounted returning True avoids mount command calls in mount_root()
    #     self.mock_is_mounted.return_value = True
    #     self.mock_run_command.return_value = (out, err, rc)
    #     self.assertEqual(balance_status(pool), expected_results,
    #                      msg="Failed to correctly identify balance running status")


    # def test_balance_status_cancel_requested(self):
    #     """
    #     As per test_balance_status_in_progress(self) but while balance is
    #     :return:
    #     """
    #
    #     # run_command moc return values.
    #     out = ["Balance on '/mnt2/rock-pool' is running, cancel requested",
    #            '15 out of about 114 chunks balanced (16 considered),  87% left',
    #            '']
    #     err=['']
    #     rc=1
    #     self.mock_is_mounted.return_value = True
    #
    #
    # def test_balance_status_pause_requested(self):
    #     """
    #     As per test_balance_status_in_progress(self) but while pause requested
    #     :return:
    #     """
    #     out = ["Balance on '/mnt2/rock-pool' is running, pause requested",
    #            '3 out of about 114 chunks balanced (4 considered),  97% left',
    #            '']
    #     err=['']
    #     rc=1
    #     self.mock_is_mounted.return_value = True
    #
    #
    # def test_balance_status_paused(self):
    #     """
    #     Test to see if balance_status() correctly identifies a Paused balance state.
    #     :return:
    #     """
    #     out = ["Balance on '/mnt2/rock-pool' is paused",
    #            '3 out of about 114 chunks balanced (4 considered),  97% left',
    #            '']
    #     err = ['']
    #     rc = 1
    #     self.mock_is_mounted.return_value = True