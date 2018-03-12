"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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
from fs.btrfs import (pool_raid, is_subvol, volume_usage, balance_status,
                      share_id, device_scan, scrub_status,
                      degraded_pools_found)
from mock import patch


class Pool(object):
    def __init__(self, raid, name):
        self.raid = raid
        self.name = name


class BTRFSTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd <root dir of rockstor ie /opt/rockstor>
    ./bin/test --settings=test-settings -v 3 -p test_btrfs*
    """
    def setUp(self):
        self.patch_run_command = patch('fs.btrfs.run_command')
        self.mock_run_command = self.patch_run_command.start()
        # # setup mock patch for is_mounted() in fs.btrfs
        # self.patch_is_mounted = patch('fs.btrfs.is_mounted')
        # self.mock_is_mounted = self.patch_is_mounted.start()
        # setup mock patch for mount_root() in fs.btrfs
        self.patch_mount_root = patch('fs.btrfs.mount_root')
        self.mock_mount_root = self.patch_mount_root.start()
        # some procedures use os.path.exists so setup mock
        self.patch_os_path_exists = patch('os.path.exists')
        self.mock_os_path_exists = self.patch_os_path_exists.start()

    def tearDown(self):
        patch.stopall()

    # # sample test
    # def test_add_pool_mkfs_fail(self):
    #     pool = Pool(raid='raid0', name='mypool')
    #     disks = ('sdb', 'sdc')
    #     self.mock_run_command.side_effect = Exception('mkfs error')
    #     self.assertEqual(add_pool(pool, disks), 1)

    def test_get_pool_raid_levels_identification(self):
        """Presents the raid identification function with example data and compares
        it's return dict to that expected for the given input.  :return: 'ok'
        if all is as expected or a message indicating which raid level was
        incorrectly identified given the test data.  N.B. Only the first raid
        level fail is indicated, however all are expected to pass anyway so we
        will have to tend to each failure in turn until all pass.

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
                        'GlobalReserve, single: total=16.00MiB, used=0.00B',
                        '']
        # Expected return is a dict of extracted info from above command
        # output.
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
        # but the expected result should be the same as "raid1_return" above
        # ie data raid1 not single.
        raid10_fi_df = ['Data, RAID10: total=419.75MiB, used=128.00KiB',
                        'System, RAID10: total=16.00MiB, used=16.00KiB',
                        'Metadata, RAID10: total=419.75MiB, used=128.00KiB',
                        'GlobalReserve, single: total=16.00MiB, used=0.00B',
                        '']
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
                             ('GlobalReserve, single: total=64.00MiB, '
                              'used=0.00B'),
                             '']
        default_sys_return = {'data': 'single', 'system': 'dup',
                              'globalreserve': 'single', 'metadata': 'dup'}
        # list used to report what raid level is currently under test.
        raid_levels_tested = ['single', 'raid0', 'raid1', 'raid10', 'raid5',
                              'raid6', 'raid1_some_single_chunks',
                              'default_sys_pool']
        # list of example fi_df outputs in raid_levels_tested order
        btrfs_fi_di = [single_fi_df, raid0_fi_df, raid1_fi_df, raid10_fi_df,
                       raid5_fi_df, raid6_fi_df,
                       raid1_fi_df_some_single_chunks, default_sys_fi_df]
        # list of correctly parsed return dictionaries
        return_dict = [single_return, raid0_return, raid1_return,
                       raid10_return, raid5_return, raid6_return, raid1_return,
                       default_sys_return]
        # simple iteration over above example inputs to expected outputs.
        for raid_level, fi_df, expected_result in map(None, raid_levels_tested,
                                                      btrfs_fi_di,
                                                      return_dict):
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
        e = [("ERROR: cannot find real path for '/mnt2/test-pool/test-share': "
              "No such file or directory"), '']
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

    def test_volume_usage(self):
        """
        Moc the return value of "btrfs qgroup show share_mount_pt" to assess
        to extract rfer and excl usage for original 0/* qgroup and Rockstor
        ad hoc 2015/* qgroup.
        :return:
        """
        # volume_usage() called with pool name of=test-pool volume_id=0/261
        # and new Rockstor qgroup pvolume_id=2015/4
        # mount_root(Pool object) returned /mnt2/test-pool
        # cmd=['/sbin/btrfs', 'qgroup', 'show', u'/mnt2/test-pool']
        #
        # Setup our calling variables and mock the root pool as mounted.
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
             '2015/4       63.00MiB     63.00MiB ', '']
        # the following is an example of fresh clone of a snapshot post import.
        o2 = ['qgroupid         rfer         excl ',
              '--------         ----         ---- ',
              '0/5          16.00KiB     16.00KiB ',
              '0/258        16.00KiB     16.00KiB ',
              '0/261        16.00KiB     16.00KiB ',
              '0/262        16.00KiB     16.00KiB ',
              '0/263        16.00KiB     16.00KiB ',
              '2015/1          0.00B        0.00B ',
              '2015/2          0.00B        0.00B ',
              '2015/3          0.00B        0.00B ',
              '2015/4          0.00B        0.00B ',
              '2015/5          0.00B        0.00B ',
              '2015/6          0.00B        0.00B ',
              '2015/7          0.00B        0.00B ',
              '2015/8          0.00B        0.00B ',
              '2015/9          0.00B        0.00B ',
              '2015/10         0.00B        0.00B ',
              '2015/11         0.00B        0.00B ',
              '2015/12         0.00B        0.00B ',
              '2015/13         0.00B        0.00B ',
              '2015/14         0.00B        0.00B ',
              '2015/15         0.00B        0.00B ',
              '2015/16         0.00B        0.00B ',
              '2015/17         0.00B        0.00B ',
              '2015/18         0.00B        0.00B ',
              '2015/19      16.00KiB     16.00KiB ',
              '2015/20         0.00B        0.00B ',
              '2015/21      16.00KiB     16.00KiB ',
              '2015/22      16.00KiB     16.00KiB ',
              '']
        e = ['']
        rc = 0
        # is_mounted returning True avoids mount command calls in mount_root()
        mount_point = '/mnt2/test-pool'
        self.mock_mount_root.return_value = mount_point
        # setup the return values from our run_command wrapper
        # examples of output from /mnt2/test-pool from a real system install
        self.mock_run_command.return_value = (o, e, rc)
        # create a fake pool object
        pool = Pool(raid='raid0', name='test-pool')
        # fake volume_id / qgroupid
        volume_id = '0/261'
        # and fake pvolume_id
        pvolume_id = '2015/4'
        # As volume_usage uses convert_to_kib() everything is converted to KiB
        # here we convert 450.59MiB and 3.43MiB to their KiB equivalent (x1024)
        expected_results_share = [65177, 65177, 64512, 64512]
        self.assertEqual(volume_usage(pool, volume_id, pvolume_id),
                         expected_results_share,
                         msg='Failed to retrieve share rfer and excl usage')
        # We perform a test with snapshots volumes to, having pqgroup None
        pvolume_id2 = None
        expected_results_snapshot = [65177, 65177]
        self.assertEqual(volume_usage(pool, volume_id, pvolume_id2),
                         expected_results_snapshot,
                         msg='Failed to retrieve snapshot rfer and excl usage')
        # As we have now observed a rogue db field entry for pvolume_id of
        # -1/-1 which in turn caused our subject "volume_usage" to return only
        # 2 values when callers using 3 actual parameters expect 4 values, we
        # should test to ensure dependable parameter count to return value
        # count behaviour when the 3rd parameter is not None.
        # In the above test involving 3 actual parameters where the last is
        # not None ie pvolume_id = '-1/-1' we prove 4 return values.
        self.mock_run_command.return_value = (o2, e, rc)
        pvolume_id3 = '-1/-1'
        expected_results_rogue_pvolume_id = [16, 16, 0, 0]
        # here we choose to return 0, 0 in place of the
        self.assertEqual(volume_usage(pool, volume_id, pvolume_id3),
                         expected_results_rogue_pvolume_id,
                         msg='Failed to handle bogus pvolume_id')


# TODO: add test_balance_status_finished

    def test_balance_status_in_progress(self):
        """
        Moc return value of run_command executing btrfs balance status
        pool_mount_point which is invoked inside of target function.
        :return:
        """
        # balance_status called with pool object of name=Pool object
        #
        # typical return for no current balance operation in progress:
        # out=["No balance found on '/mnt2/single-to-raid1'", '']
        # err=['']
        # rc=0
        # example return for ongoing balance operation:
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Balance on '/mnt2/rock-pool' is running",
               '7 out of about 114 chunks balanced (8 considered),  94% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'running', 'percent_done': 6}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify "
                              "balance running status"))

    def test_balance_status_cancel_requested(self):
        """
        As per test_balance_status_in_progress(self) but while balance is
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        # run_command moc return values.
        out = ["Balance on '/mnt2/rock-pool' is running, cancel requested",
               ('15 out of about 114 chunks balanced (16 considered),  '
                '87% left'),
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'cancelling', 'percent_done': 13}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance cancel "
                              "requested status"))

    def test_balance_status_pause_requested(self):
        """
        As per test_balance_status_in_progress(self) but while pause requested
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Balance on '/mnt2/rock-pool' is running, pause requested",
               '3 out of about 114 chunks balanced (4 considered),  97% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'pausing', 'percent_done': 3}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance pause "
                              "requested status"))

    def test_balance_status_paused(self):
        """Test to see if balance_status() correctly identifies a Paused balance
        state.  :return:

        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Balance on '/mnt2/rock-pool' is paused",
               '3 out of about 114 chunks balanced (4 considered),  97% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'paused', 'percent_done': 3}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance "
                              "paused status"))

    def test_scrub_status_running(self):
        """
        Test to see if scrub_status correctly identifies running status
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ['scrub status for 030baa1c-faab-4599-baa4-6077f7f6451b',
               '\tscrub started at Sun Aug  6 15:08:37 2017, running for 00:00:05',  # noqa E501
               '\tdata_extents_scrubbed: 26409',
               '\ttree_extents_scrubbed: 4495',
               '\tdata_bytes_scrubbed: 832385024',
               '\ttree_bytes_scrubbed: 73646080', '\tread_errors: 0',
               '\tcsum_errors: 0', '\tverify_errors: 0', '\tno_csum: 272',
               '\tcsum_discards: 0', '\tsuper_errors: 0',
               '\tmalloc_errors: 0',
               '\tuncorrectable_errors: 0', '\tunverified_errors: 0',
               '\tcorrected_errors: 0', '\tlast_physical: 1392836608', '']
        err = ['']
        rc = 0
        expected_results = {'status': 'running', 'csum_discards': 0,
                            'super_errors': 0,
                            'data_extents_scrubbed': 26409,
                            'last_physical': 1392836608,
                            'tree_bytes_scrubbed': 73646080,
                            'no_csum': 272,
                            'read_errors': 0, 'verify_errors': 0,
                            'uncorrectable_errors': 0, 'malloc_errors': 0,
                            'unverified_errors': 0,
                            'tree_extents_scrubbed': 4495,
                            'kb_scrubbed': 812876, 'csum_errors': 0,
                            'corrected_errors': 0}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(scrub_status(pool), expected_results,
                         msg=("Failed to identify scrub running state."))

    def test_scrub_status_finished(self):
        """
        Test to see if scrub_status correctly identifies finished status
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ['scrub status for 030baa1c-faab-4599-baa4-6077f7f6451b',
               '\tscrub started at Sun Aug  6 16:39:43 2017 and finished after 00:00:16',  # noqa E501
               '\tdata_extents_scrubbed: 81795',
               '\ttree_extents_scrubbed: 5264',
               '\tdata_bytes_scrubbed: 2881429504',
               '\ttree_bytes_scrubbed: 86245376', '\tread_errors: 0',
               '\tcsum_errors: 0', '\tverify_errors: 0', '\tno_csum: 272',
               '\tcsum_discards: 0', '\tsuper_errors: 0', '\tmalloc_errors: 0',
               '\tuncorrectable_errors: 0', '\tunverified_errors: 0',
               '\tcorrected_errors: 0', '\tlast_physical: 5993660416', '']
        err = ['']
        rc = 0
        expected_results = {'status': 'finished', 'csum_discards': 0,
                            'super_errors': 0, 'data_extents_scrubbed': 81795,
                            'last_physical': 5993660416,
                            'tree_bytes_scrubbed': 86245376, 'no_csum': 272,
                            'read_errors': 0, 'verify_errors': 0,
                            'uncorrectable_errors': 0, 'malloc_errors': 0,
                            'unverified_errors': 0,
                            'tree_extents_scrubbed': 5264, 'duration': 16,
                            'kb_scrubbed': 2813896, 'csum_errors': 0,
                            'corrected_errors': 0}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(scrub_status(pool), expected_results,
                         msg=("Failed to identify scrub finished state."))

    def test_scrub_status_halted(self):
        """
        Test to see if scrub_status correctly identifies interrupted status
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ['scrub status for 8adf7f0b-65ec-4e00-83cc-7f5855201185',
               '\tscrub started at Sun Aug  6 12:18:39 2017, interrupted after 00:00:09, not running',  # noqa E501
               '\tdata_extents_scrubbed: 49335',
               '\ttree_extents_scrubbed: 9262',
               '\tdata_bytes_scrubbed: 2286493696',
               '\ttree_bytes_scrubbed: 151748608', '\tread_errors: 0',
               '\tcsum_errors: 0', '\tverify_errors: 0', '\tno_csum: 2816',
               '\tcsum_discards: 0', '\tsuper_errors: 0', '\tmalloc_errors: 0',
               '\tuncorrectable_errors: 0', '\tunverified_errors: 0',
               '\tcorrected_errors: 0', '\tlast_physical: 16706174976', '']
        err = ['']
        rc = 0
        expected_results = {'status': 'halted', 'csum_discards': 0,
                            'super_errors': 0, 'data_extents_scrubbed': 49335,
                            'last_physical': 16706174976,
                            'tree_bytes_scrubbed': 151748608, 'no_csum': 2816,
                            'read_errors': 0, 'verify_errors': 0,
                            'uncorrectable_errors': 0, 'malloc_errors': 0,
                            'unverified_errors': 0,
                            'tree_extents_scrubbed': 9262, 'duration': 9,
                            'kb_scrubbed': 2232904, 'csum_errors': 0,
                            'corrected_errors': 0}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(scrub_status(pool), expected_results,
                         msg=("Failed to identify scrub halted state."))

    def test_scrub_status_conn_reset(self):
        """
        Test to see if scrub_status correctly identifies 'no stats available'
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ['scrub status for 8adf7f0b-65ec-4e00-83cc-7f5855201185',
               '\tno stats available', '\tdata_extents_scrubbed: 0',
               '\ttree_extents_scrubbed: 0', '\tdata_bytes_scrubbed: 0',
               '\ttree_bytes_scrubbed: 0', '\tread_errors: 0',
               '\tcsum_errors: 0', '\tverify_errors: 0', '\tno_csum: 0',
               '\tcsum_discards: 0', '\tsuper_errors: 0', '\tmalloc_errors: 0',
               '\tuncorrectable_errors: 0', '\tunverified_errors: 0',
               '\tcorrected_errors: 0', '\tlast_physical: 0', '']
        err = ['WARNING: failed to read status: Connection reset by peer', '']
        rc = 0
        expected_results = {'status': 'conn-reset'}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(scrub_status(pool), expected_results,
                         msg=("Failed to identify conn-reset state."))

    def test_scrub_status_cancelled(self):
        """
        Test to see if scrub_status correctly identifies cancelled status
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ['scrub status for 8adf7f0b-65ec-4e00-83cc-7f5855201185',
               '\tscrub started at Mon Aug  7 15:29:52 2017 and was aborted after 00:04:56',  # noqa E501
               '\tdata_extents_scrubbed: 1292470',
               '\ttree_extents_scrubbed: 9299',
               '\tdata_bytes_scrubbed: 83593609216',
               '\ttree_bytes_scrubbed: 152354816', '\tread_errors: 0',
               '\tcsum_errors: 0', '\tverify_errors: 0', '\tno_csum: 5632',
               '\tcsum_discards: 0', '\tsuper_errors: 0', '\tmalloc_errors: 0',
               '\tuncorrectable_errors: 0', '\tunverified_errors: 0',
               '\tcorrected_errors: 0', '\tlast_physical: 103077314560', '']
        err = ['']
        rc = 0
        expected_results = {'status': 'cancelled', 'csum_discards': 0,
                            'super_errors': 0,
                            'data_extents_scrubbed': 1292470,
                            'last_physical': 103077314560,
                            'tree_bytes_scrubbed': 152354816, 'no_csum': 5632,
                            'read_errors': 0, 'verify_errors': 0,
                            'uncorrectable_errors': 0, 'malloc_errors': 0,
                            'unverified_errors': 0,
                            'tree_extents_scrubbed': 9299, 'duration': 296,
                            'kb_scrubbed': 81634384, 'csum_errors': 0,
                            'corrected_errors': 0}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(scrub_status(pool), expected_results,
                         msg=("Failed to identify cancelled state."))

    def test_share_id(self):
        """
        Test to see if share_id() successfully returns existing subvolume id's
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        # Typical output from subvol_list_helper(), a simple wrapper around
        # run_command with re-try's
        out = ['ID 257 gen 13616 top level 5 path rock-ons-root',
               'ID 259 gen 13616 top level 5 path plex-data',
               'ID 260 gen 13616 top level 5 path plex-config',
               'ID 261 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/83e4dde6b9cfddf46b75a07ec8d65ad87a748b98cf27de7d5b3298c1f3455ae4',  # noqa E501
               'ID 262 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/b670fb0c7ecd3d2c401fbfd1fa4d7a872fbada0a4b8c2516d0be18911c6b25d6',  # noqa E501
               'ID 263 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/29460ac934423a55802fcad24856827050697b4a9f33550bd93c82762fb6db8f',  # noqa E501
               'ID 264 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/d2a0ecffe6fa4ef3de9646a75cc629bbd9da7eead7f767cb810f9808d6b3ecb6',  # noqa E501
               'ID 265 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/a3a20fd46b6d67fdab1af5e4b1ce148d87b8012d8187edfea6b04b3704cba6c0',  # noqa E501
               'ID 266 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/1ed1f43a22cbe1f8380e0cef729e461f6b344be78e2d3723cbd1231d8cc562de',  # noqa E501
               'ID 267 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/bc9bc5a736c631cbc43d64c0d03392477ca06a2ac2bb2e68cabc511166525e1c',  # noqa E501
               'ID 268 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/600b3b23bb1613bd694a547865f8dbbf6118749300f846372f182d33b6cc7039',  # noqa E501
               'ID 269 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/a55eda61cffe86f4bef7a308ded5b9a64daed3db625ae33cf8c2b4926dfa4da6',  # noqa E501
               'ID 270 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/bd06bc691e41ca2e6ebbfb2e49f0dcea815f17f2575915cc16bd948398fe198f',  # noqa E501
               'ID 271 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/5dfde44c18f7bcac81e497b56b25e06af239999305c44970346ef2316479cddf',  # noqa E501
               'ID 272 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/26f44488da244735b4b0f4f5d1fd269f46f45959f8d32d53c58ce7f6566625db',  # noqa E501
               'ID 273 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/e6121e4ddc6bf59dc4cfabed58366f3c9d97a6477b0357f12dea89b20e61a194',  # noqa E501
               'ID 274 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/e2ebadbfcdb671f5de00f47470e435e7c73fc691e303bc15f5087a11f24439bc',  # noqa E501
               'ID 275 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/90549afba45a31f090522e483a39e5afc6c4c7129455636572d88534dd368fe6',  # noqa E501
               'ID 276 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/5b066908aceaaacb952253905f1e20ba42735439544fb91a4a5e594f1c705e08',  # noqa E501
               'ID 283 gen 13631 top level 5 path sftpdata',
               'ID 284 gen 13616 top level 5 path .snapshots/sftpdata/sftp-daily-snapshot_201508011700',  # noqa E501
               'ID 285 gen 13616 top level 5 path .snapshots/sftpdata/sftp-monthly-snapshot_201508011730',  # noqa E501
               'ID 286 gen 13616 top level 5 path .snapshots/sftpdata/sftp-daily-snapshot_201508021700',  # noqa E501
               'ID 287 gen 13616 top level 5 path .snapshots/sftpdata/sftp-weekly-snapshot_201508021715',  # noqa E501
               'ID 288 gen 13616 top level 5 path .snapshots/sftpdata/sftp-daily-snapshot_201508051700',  # noqa E501
               'ID 289 gen 13616 top level 5 path .snapshots/sftpdata/sftp-daily-snapshot_201508251700',  # noqa E501
               'ID 400 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/01a44504c48d528cf64d2691e5d362f328962560eb0427c6f53fb2300df87bd9',  # noqa E501
               'ID 401 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/97e9fc98a8bdb50045400594330b50d79ae6e8b3bf90bb7b63c34751f4c495e0',  # noqa E501
               'ID 402 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/b54b867d760328df6f7aca9934ddbbb5b2afebbbd9e228d86bede93324bcd0d2',  # noqa E501
               'ID 403 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/fe5a39fcbbb23a05a3478944d5ad5143b01d0b63362d935c86c03a9a38fa3006',  # noqa E501
               'ID 404 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/2b3b8ebd68c3baeb685d76e1f87ccd667b43ee7b6587a3beff4797ca70321bf1',  # noqa E501
               'ID 405 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/86c9daa3d5aa144423daf15d87bd20a2e9f133903893f7178871751f0c96051e',  # noqa E501
               'ID 406 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/fd9afcfa5754be3fa26d6a811717661e4cf7c42163216b8e2e076729b5397429',  # noqa E501
               'ID 407 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/cd8ea80e21c405a5a3db583d91f8d459a12f1dfb0a912af413cf52eca9b18bf1',  # noqa E501
               'ID 408 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/ebea89404d903a8fdbb8ae6ecc18e1a6cb63af0d4821b87385854310741b2679',  # noqa E501
               'ID 409 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/595cc965de9c2d4b2d909a2663d7f34eb3659a50cfab04455b5408883a2d0e4c',  # noqa E501
               'ID 410 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/68a23a078a69b225107bd75a3f53e4c10b5cc2e22a1bb9911c6666a0bd938734',  # noqa E501
               'ID 411 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/5c873fdd5c4eb8b0b4ec43b0e52620a8ced984675949132789870b3789d6f236',  # noqa E501
               'ID 412 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/8f201c360d8a0fba5fd9282814484f0709567aa4b7e34755855419c0de27f2cb',  # noqa E501
               'ID 413 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/e62fa2fe0b8877602f2ec1f41ced2e1ef20733b95f6f2dc95b44d6ce1e3a78a5',  # noqa E501
               'ID 414 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/bc8085f96802edf614fd1fc66bb28108bbd1e700bb96779fa977e7ac6d59e527',  # noqa E501
               'ID 415 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/2a8355cf96789fda77fa67ab99ca14e40fd9210b29635b363bf20ced53c22aa2',  # noqa E501
               'ID 416 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/ed6561db61c857c9ff9a63f578961a6f7619089191ab373ec81bede37f3c1426',  # noqa E501
               'ID 417 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/bcc04bfdc35f0b7174b67f9778354c7f14e73425ba054d39d52e7d8ad70c2e69',  # noqa E501
               'ID 418 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/0c680ed4d54df71ec6bd4a61a62e6ce4e9fb3c8a2bb84f299e30aea7dd99ef52',  # noqa E501
               'ID 419 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/a8090d90a27208860585f2e1abb823e365e078d4d5ec0ef5e9114f103d8b3cde',  # noqa E501
               'ID 420 gen 13616 top level 257 path rock-ons-root/btrfs/subvolumes/0717197731662beb1812fced93b463c772036f9c849b913a4d830e26c72a7222',  # noqa E501
               'ID 792 gen 13627 top level 5 path .snapshots/sftpdata/test-share-snaphot',  # noqa E501
               'ID 793 gen 13629 top level 5 path .snapshots/sftpdata/another-test-snapshot',  # noqa E501
               'ID 794 gen 13631 top level 5 path .snapshots/sftpdata/snapshot-name',  # noqa E501
               '']
        err = ['']
        rc = 0
        existing_share = 'snapshot-name'
        existing_share2 = 'sftpdata'
        nonexistent_share = 'abcdef'
        # if queried for the last entry "snapshot-name" we would expect:
        expected_result = '794'
        expected_result2 = '283'
        # setup run_command mock to return the above test data
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-mount'
        self.assertEqual(share_id(pool, existing_share), expected_result,
                         msg=("Failed to get existing share_id snapshot "
                              "example"))
        self.assertEqual(share_id(pool, existing_share2), expected_result2,
                         msg="Failed to get existing share_id regular example")
        with self.assertRaises(Exception):
            share_id(pool, nonexistent_share)

    def test_device_scan_all(self):
        """
        Test device_scan with no arguments passed which defaults to scanning
        the entire system
        """
        # setup mock output from a successful full system scan ie
        # run_command executing 'btrfs device scan'
        # In system wide scan mode device_scan simply returns the same so
        # these values stand as run_command mock and expected output.
        out = ['Scanning for Btrfs filesystems', '']
        err = ['']
        rc = 0
        self.mock_run_command.return_value = (out, err, rc)
        # Now test device_scan when executing the same, ie via no parameters
        # call where it should return the exact same output.
        self.assertEqual(device_scan(), (out, err, rc),
                         msg="Failed to return results of successful system "
                             "wide 'btrfs device scan'.")

    def test_device_scan_parameter(self):
        """
        Test device_scan across various input.
        """
        # Expected output for a detached or non existent device parameter.
        # This is also the expected output if an empty list is passed.
        out = err = ['']
        rc = 0
        self.assertEqual(
            device_scan(['detached-ea847422dff841fca3b716fb7dcdaa5a']),
            (out, err, rc),
            msg='Failed to ignore detached device.')
        self.mock_os_path_exists.return_value = False
        self.assertEqual(device_scan(['nonexistent-device']), (out, err, rc),
                         msg='Failed to ignore nonexistent-device.')
        self.assertEqual(device_scan([]), (out, err, rc),
                         msg='Failed to ignore empty list.')
        # Test for device_scan having been passed the base device name of a
        # partitioned device.
        # Mockup run_command return values for scanning a partitioned device:
        out = ["Scanning for Btrfs filesystems in '/dev/vdc'", '']
        err = ["ERROR: device scan failed on '/dev/vdc': Invalid argument", '']
        rc = 1
        # To make this test portable we have to mock os.path.exists() as True
        # so that our otherwise bogus block device is considered as existing.
        self.mock_os_path_exists.return_value = True
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(device_scan(['virtio-serial-1']), (out, err, rc),
                         msg='Failed to return results from non btrfs device.')

    def test_degraded_pools_found(self):
        """
        Test degraded_pools_found() across various btrfs fi show outputs.
        """
        # Setup mock output from/for run_command.
        # degraded_pools_found() only deals with out but we have err and rc
        # in case of future enhancement / requirement, ie other tests to come.

        fi_show_out = [[
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2304409600',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            "Label: 'rock-pool-2'  uuid: 52053a67-1a53-4cb8-bf17-69abca623bef",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 2155872256 path /dev/vde',
            '\tdevid    2 size 5368709120 used 16777216 path /dev/vdd',
            '',
            "Label: 'rock-pool'  uuid: 924d9d64-4943-4eac-a52e-1918e963a34f",
            '\tTotal devices 3 FS bytes used 475136',
            '\tdevid    1 size 5368709120 used 310378496 path /dev/vda',
            '\tdevid    2 size 5368709120 used 1107296256 path /dev/vdc',
            '\t*** Some devices missing',
            '', '']]
        num_deg = [1]
        err = [['']]
        rc = [0]

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2306293760',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            "Label: 'rock-pool-2'  uuid: 52053a67-1a53-4cb8-bf17-69abca623bef",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 2155872256 path /dev/vde',
            '\tdevid    2 size 5368709120 used 16777216 path /dev/vdd',
            '',
            'warning, device 2 is missing',
            "Label: 'rock-pool'  uuid: 924d9d64-4943-4eac-a52e-1918e963a34f",
            '\tTotal devices 3 FS bytes used 475136',
            '\tdevid    1 size 5368709120 used 310378496 path /dev/vda',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(1)
        err.append([''])
        rc.append(0)

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2297679872',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vda3',
            '',
            'warning, device 3 is missing',
            'warning, device 3 is missing',
            "Label: 'rock-pool-2'  uuid: 6b1e11db-dafb-470c-8ad2-165e1c6296a0",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    2 size 5368709120 used 16777216 path /dev/vdb',
            '\t*** Some devices missing',
            '',
            "Label: 'rock-pool'  uuid: b775142a-a9f7-46af-909c-379331b6abcb",
            '\tTotal devices 3 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 8388608 path /dev/vdd',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(2)
        err = ['bytenr mismatch, want=29687808, have=0',
               "Couldn't read tree root",
               'bytenr mismatch, want=20987904, have=0',
               'ERROR: cannot read chunk root', '']
        rc.append(0)

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2308558848',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            'warning, device 2 is missing',
            "Label: 'rock-pool'  uuid: 924d9d64-4943-4eac-a52e-1918e963a34f",
            '\tTotal devices 3 FS bytes used 475136',
            '\tdevid    1 size 5368709120 used 310378496 path /dev/vda',
            '\t*** Some devices missing',
            '',
            "Label: 'rock-pool-2'  uuid: 52053a67-1a53-4cb8-bf17-69abca623bef",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    2 size 5368709120 used 16777216 path /dev/vdc',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(2)
        err.append(['bytenr mismatch, want=29491200, have=0',
                    "Couldn't read tree root", ''])
        rc.append(0)

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2310893568',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '', ''])
        num_deg.append(0)
        err.append([''])
        rc.append(0)

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2295517184',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            "Label: 'rock-pool'  uuid: 83b73c7e-4165-48dd-a249-ef49450f4f13",
            '\tTotal devices 3 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 8388608 path /dev/vdf',
            '\tdevid    3 size 5368709120 used 16777216 path /dev/vde',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(1)
        err.append(['bytenr mismatch, want=29687808, have=0',
                    "Couldn't read tree root", ''])
        rc.append(0)

        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2311786496',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            'warning, device 1 is missing',
            'warning, device 2 is missing',
            'warning, device 2 is missing',
            "Label: 'rock-pool'  uuid: 924d9d64-4943-4eac-a52e-1918e963a34f",
            '\tTotal devices 3 FS bytes used 475136',
            '\tdevid    2 size 5368709120 used 1107296256 path /dev/vdc',
            '\tdevid    3 size 5368709120 used 1342177280 path /dev/vdd',
            '\t*** Some devices missing',
            '',
            "Label: 'rock-pool-2'  uuid: 52053a67-1a53-4cb8-bf17-69abca623bef",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 2155872256 path /dev/vdf',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(2)
        err.append(['bytenr mismatch, want=1104330752, have=26120339456',
                    "Couldn't read tree root",
                    'bytenr mismatch, want=20987904, have=0',
                    'ERROR: cannot read chunk root', ''])
        rc.append(0)

        # Quirky instance with apparently 3 degraded but "rock-pool-3" has a
        # "Total devices"=1 and there is one disk shown attached. Note
        # that there is no trailing "\t*** Some devices missing" but there
        # are multiple preceding lines indicating "device 2 is missing".
        # A non degraded mount of rock-pool-3 was then successfully achieved
        # the the output there after showed no signs of issue.
        # So we don't count this pool as degraded in degraded_pools_found().
        # But it would still be counted as degraded by is_pool_missing_dev()!!
        # This diversity in degraded pool assessment may prove useful later.
        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2.16GiB',
            '\tdevid    1 size 6.71GiB used 3.25GiB path /dev/vdb3',
            '',
            'warning, device 2 is missing',
            'warning, device 2 is missing',
            'bytenr mismatch, want=20987904, have=0',
            'ERROR: cannot read chunk root',
            "Label: 'rock-pool-3'  uuid: c013682a-51e3-4d92-a5e0-378acc5485da",
            '\tTotal devices 1 FS bytes used 208.00KiB',
            '\tdevid    1 size 5.00GiB used 536.00MiB path /dev/vdc',
            '',
            "Label: 'rock-pool-2'  uuid: 9828f1c6-51f7-4d40-a7d3-0a9fbe8a2cbb",
            '\tTotal devices 2 FS bytes used 400.00KiB',
            '\tdevid    1 size 5.00GiB used 2.01GiB path /dev/vdd',
            '\t*** Some devices missing',
            '',
            "Label: 'rock-pool'  uuid: 6245b4ec-d452-42ed-ad5a-2c9ae33e4f5d",
            '\tTotal devices 2 FS bytes used 336.00KiB',
            '\tdevid    2 size 5.00GiB used 848.00MiB path /dev/vde'
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(2)
        err.append(['bytenr mismatch, want=20987904, have=0',
                    'ERROR: cannot read chunk root', ''])
        rc.append(0)

        # 2 disks removed from last pool (mounted), pool then unmounted.
        fi_show_out.append([
            "Label: 'rockstor_install-test'  uuid: b3d201a8-b497-4365-a90d-a50c50b8e808",  # noqa E501
            '\tTotal devices 1 FS bytes used 2293907456',
            '\tdevid    1 size 7204765696 used 3489660928 path /dev/vdb3',
            '',
            "Label: 'rock-pool-2'  uuid: 7e2d0333-8075-4c0b-b8f8-fb072cac573f",
            '\tTotal devices 2 FS bytes used 409600',
            '\tdevid    1 size 5368709120 used 2155872256 path /dev/vda',
            '\tdevid    2 size 5368709120 used 16777216 path /dev/vdc',
            '',
            'warning, device 3 is missing',
            'warning, device 3 is missing',
            "Label: 'rock-pool'  uuid: 83b73c7e-4165-48dd-a249-ef49450f4f13",
            '\tTotal devices 3 FS bytes used 409600',
            '\tdevid    2 size 5368709120 used 2147483648 path /dev/vdd',
            '\t*** Some devices missing',
            '', ''])
        num_deg.append(1)
        err.append(['bytenr mismatch, want=20987904, have=0',
                    'ERROR: cannot read chunk root', ''])
        rc.append(0)

        # Cycle through each of the above mock_run_command data sets.
        for out, e, r, count in zip(fi_show_out, err, rc, num_deg):
            self.mock_run_command.return_value = (out, e, r)
            self.assertEqual(degraded_pools_found(), count,
                             msg='Un-expected degraded pool count. Mock ({}) '
                                 'count expected ({})'.format(out, count))
