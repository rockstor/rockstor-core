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
import json
import unittest
from fs.btrfs import (pool_raid, is_subvol, volume_usage, balance_status,
                      share_id, device_scan, scrub_status,
                      degraded_pools_found, snapshot_idmap, get_property,
                      parse_snap_details, shares_info, get_snap,
                      dev_stats_zero, get_dev_io_error_stats, DefaultSubvol,
                      default_subvol)
from mock import patch


class Pool(object):
    def __init__(self, raid, name, role=None):
        self.raid = raid
        self.name = name
        self.role = role


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
        """
        Presents the raid identification function with example data & compares
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
                                 'level {}'.format(raid_level))

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

    def test_balance_status_finished(self):
        """
        Moc return value of run_command executing btrfs balance status
        pool_mount_point for a Pool with "No balance" indicated, this is
        interpreted as a finished /non running balance and returns percent
        done as 100%.
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["No balance found on '/mnt2/test-pool'", '']
        err = ['']
        rc = 0
        expected_results = {'status': 'finished', 'percent_done': 100}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-pool'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=('Failed to correctly identify balance finished '
                              'status'))

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
        out = ["Balance on '/mnt2/test-pool' is running",
               '7 out of about 114 chunks balanced (8 considered),  94% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'running', 'percent_done': 6}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-pool'
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
        out = ["Balance on '/mnt2/test-pool' is running, cancel requested",
               ('15 out of about 114 chunks balanced (16 considered),  '
                '87% left'),
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'cancelling', 'percent_done': 13}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-pool'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance cancel "
                              "requested status"))

    def test_balance_status_pause_requested(self):
        """
        As per test_balance_status_in_progress(self) but while pause requested
        :return:
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Balance on '/mnt2/test-pool' is running, pause requested",
               '3 out of about 114 chunks balanced (4 considered),  97% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'pausing', 'percent_done': 3}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-pool'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance pause "
                              "requested status"))

    def test_balance_status_paused(self):
        """Test to see if balance_status() correctly identifies a Paused balance
        state.  :return:

        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Balance on '/mnt2/test-pool' is paused",
               '3 out of about 114 chunks balanced (4 considered),  97% left',
               '']
        err = ['']
        # N.B. the return code for in progress balance = 1
        rc = 1
        expected_results = {'status': 'paused', 'percent_done': 3}
        self.mock_run_command.return_value = (out, err, rc)
        self.mock_mount_root.return_value = '/mnt2/test-pool'
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance "
                              "paused status"))

    def test_balance_status_unknown_unmounted(self):
        """
        Test balance status of 'unknown' such as when a pool is not mounted
        and fails the built in attempt to ensure it is, prior to the btrfs
        balance status command execution. An example of this is when a pool
        is unmounted, degraded, and has no required 'degraded' mount option.
        """
        pool = Pool(raid='raid0', name='test-pool')
        mnt_error = (
            "Error running a command. cmd = /bin/mount /dev/disk/by-label/test-pool "  # noqa E501
            "/mnt2/test-pool -o ro,compress=no. rc = 32. stdout = ['']. stderr = "  # noqa E501
            "['mount: wrong fs type, bad option, bad superblock on /dev/vda,', '"  # noqa E501
            "       missing codepage or helper program, or other error', '', '  "  # noqa E501
            "In some cases useful info is found in syslog - try', '       dmesg | "  # noqa E501
            "tail or so.', '']")
        expected_results = {'status': 'unknown'}

        self.mock_mount_root.side_effect = Exception(mnt_error)
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance unknown"
                              "status via mount exception failure"))

    def test_balance_status_unknown_parsing(self):
        """
        Test of balance status of 'unknown' as a result of a parsing failure
        of the output from btrfs balance status mnt_pt
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = ["Essentially nonsense output re: '/mnt2/test-pool'", '']
        err = ['']
        rc = 0
        expected_results = {'status': 'unknown'}

        self.mock_mount_root.return_value = '/mnt2/test-pool'
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(balance_status(pool), expected_results,
                         msg=("Failed to correctly identify balance unknown"
                              "status via parsing failure"))

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

    def test_snapshot_idmap_no_snaps(self):
        """
         Tests for empty return when no snapshots found
        """
        out = ['']
        err = ['']
        rc = 0
        pool = Pool(raid='raid0', name='test-pool')
        expected_result = {}
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(snapshot_idmap(pool), expected_result,
                         msg="Failed expected idmap - no snaps.")

    def test_snapshot_idmap_home_rollback(self):
        """
        Tests for a home as snap itself due to rollback to prior snap
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = [
            'ID 284 gen 43480 cgen 40482 top level 5 otime 2018-05-02 17:04:26 path home',  # noqa E501
            '']
        err = ['']
        rc = 0
        expected_result = {'284': 'home'}
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(snapshot_idmap(pool), expected_result,
                         msg="Failed expected idmap - home reverted to snap.")

    def test_snapshot_idmap_home_rollback_snap(self):
        """
        Tests for home reverted to prior snap (clone) which is then snapshoted:
        as home was previously reverted to a rw snap it becomes a (rw) snapshot
        itself; which can in turn have it's own snaps.
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = [
            'ID 284 gen 43480 cgen 40482 top level 5 otime 2018-05-02 17:04:26 path home',  # noqa E501
            'ID 286 gen 43444 cgen 43444 top level 5 otime 2018-05-28 11:51:11 path .snapshots/home/home-snap-1',  # noqa E501
            '']
        err = ['']
        rc = 0
        expected_result = {'284': 'home', '286': '.snapshots/home/home-snap-1'}
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(snapshot_idmap(pool), expected_result,
                         msg="Failed expected idmap - single home snap.")

    def test_snapshot_idmap_mid_replication(self):
        """
        Test mid replication snapshot idmap (bi directional)
        """
        pool = Pool(raid='raid0', name='test-pool')
        out = [
            'ID 311 gen 162 cgen 162 top level 5 otime 2018-05-13 20:55:02 path .snapshots/rock-share/rock-share_1_replication_27',  # noqa E501
            'ID 313 gen 167 cgen 167 top level 5 otime 2018-05-13 21:00:01 path .snapshots/rock-share/rock-share_1_replication_28',  # noqa E501
            'ID 333 gen 280 cgen 275 top level 5 otime 2018-05-24 19:40:02 path C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share',  # noqa E501
            'ID 334 gen 284 cgen 280 top level 5 otime 2018-05-24 19:45:02 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_47',  # noqa E501
            'ID 335 gen 289 cgen 284 top level 5 otime 2018-05-24 19:50:02 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_48',  # noqa E501
            'ID 336 gen 289 cgen 289 top level 5 otime 2018-05-24 19:55:02 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_49',  # noqa E501
            '']
        err = ['']
        rc = 0
        expected_result = {
            '313': '.snapshots/rock-share/rock-share_1_replication_28',
            '334': '.snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_47',  # noqa E501
            '311': '.snapshots/rock-share/rock-share_1_replication_27',
            '336': '.snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_49',  # noqa E501
            '333': 'C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share',
            '335': '.snapshots/C583C37F-08AE-478B-A726-E95235D1712B_dev-rock-share/dev-rock-share_1_replication_48'}  # noqa E501
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(snapshot_idmap(pool), expected_result,
                         msg="Failed expected idmap - mid replication.")

    def test_snapshot_idmap_snapper_root(self):
        """
        Test snapper rollback enabled root, with some Rockstor native snapshots
        """
        pool = Pool(raid='raid0', name='test-pool', role='root')
        out = [
            'ID 272 gen 1725 cgen 44 top level 267 otime 2018-06-02 12:40:42 path @/.snapshots/2/snapshot',  # noqa E501
            'ID 283 gen 1725 cgen 84 top level 267 otime 2018-06-02 13:02:31 path @/.snapshots/13/snapshot',  # noqa E501
            'ID 284 gen 1725 cgen 88 top level 267 otime 2018-06-02 13:05:55 path @/.snapshots/14/snapshot',  # noqa E501
            'ID 287 gen 1725 cgen 96 top level 267 otime 2018-06-02 13:10:46 path @/.snapshots/17/snapshot',  # noqa E501
            'ID 288 gen 1725 cgen 97 top level 267 otime 2018-06-02 13:11:17 path @/.snapshots/18/snapshot',  # noqa E501
            'ID 289 gen 1725 cgen 1411 top level 268 otime 2018-06-03 17:21:23 path .snapshots/home/home-snap',  # noqa E501
            'ID 296 gen 2644 cgen 2644 top level 268 otime 2018-06-04 20:50:32 path .snapshots/test-share/snap-test-share',  # noqa E501
            'ID 297 gen 2656 cgen 2647 top level 268 otime 2018-06-04 20:51:50 path .snapshots/home/home-snap-writable',  # noqa E501
            'ID 298 gen 2656 cgen 2656 top level 268 otime 2018-06-04 20:55:39 path home-snap-writable-clone',  # noqa E501
            'ID 299 gen 2763 cgen 2763 top level 267 otime 2018-06-05 16:48:08 path @/.snapshots/19/snapshot',  # noqa E501
            'ID 301 gen 2767 cgen 2766 top level 267 otime 2018-06-05 16:49:10 path @/.snapshots/20/snapshot',  # noqa E501
            '']
        err = ['']
        rc = 0
        expected_result = {'301': '.snapshots/20/snapshot',
                           '289': '.snapshots/home/home-snap',
                           '288': '.snapshots/18/snapshot',
                           '272': '.snapshots/2/snapshot',
                           '298': 'home-snap-writable-clone',
                           '299': '.snapshots/19/snapshot',
                           '296': '.snapshots/test-share/snap-test-share',
                           '297': '.snapshots/home/home-snap-writable',
                           '283': '.snapshots/13/snapshot',
                           '284': '.snapshots/14/snapshot',
                           '287': '.snapshots/17/snapshot'}
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(snapshot_idmap(pool), expected_result,
                         msg="Failed expected idmap - mid replication.")

    def test_get_property_all(self):
        """
        Test get_property function for returning all available properties
        """
        mnt_pt = 'mock-mount'
        out = ['ro=false', 'compression=lzo', 'label=test', '']
        err = ['']
        rc = 0
        expected_result = {'compression': 'lzo', 'ro': False, 'label': 'test'}
        self.mock_run_command.return_value = (out, err, rc)
        self.assertEqual(get_property(mnt_pt), expected_result,
                         msg="Failed get all properties return test.")

    def test_get_property_compression(self):
        """
        Test for a property that is not set, ie compression when not set.
        """
        mnt_pt = 'mock-mount'
        out = ['']
        err = ['']
        rc = 0
        self.mock_run_command.return_value = (out, err, rc)
        self.assertIsNone(get_property(mnt_pt, 'compression'),
                          msg="Failed get compression - 'None' expected.")

    def test_get_property_ro(self):
        """
        Test get_property ro property specified function
        """
        mnt_pt = 'mock-mount'
        out = ['ro=false', '']
        err = ['']
        rc = 0
        # False expected
        self.mock_run_command.return_value = (out, err, rc)
        self.assertFalse(get_property(mnt_pt, 'ro'),
                         msg="Failed ro False return.")
        out = ['ro=true', '']
        self.mock_run_command.return_value = (out, err, rc)
        self.assertTrue(get_property(mnt_pt, 'ro'),
                        msg="Failed ro True return.")

    def test_parse_snap_details(self):
        """
        Test parse_snap_details() over a range of inputs
        """
        # setup mock patch for get_property() in fs.btrfs
        self.patch_get_property = patch('fs.btrfs.get_property')
        self.mock_get_property = self.patch_get_property.start()

        p_mnt_pt = '/mnt2/test-pool'
        # Build lists of test data, including get_property() mock return vals.

        # regular (ro) replication snapshot
        snap_rel_paths = ['.snapshots/rock-share/rock-share_1_replication_27']
        ro_prop = [True]
        # (snap_name, writable, is_clone)
        expected = [('rock-share_1_replication_27', False, False)]

        # regular (rw) snapshot of 'share'
        snap_rel_paths.append('.snapshots/rock-share/writable-rock-share-snap')
        ro_prop.append(False)
        # (snap_name, writable, is_clone)
        expected.append(('writable-rock-share-snap', True, False))

        # clone (rw) snapshot of 'share' (ie top level dir)
        snap_rel_paths.append('rock-share-clone')
        ro_prop.append(False)
        # (snap_name, writable, is_clone
        # Note that as we consider this a share (clone) is has snap_name=None.
        expected.append((None, True, True))

        # Cycle through snap_rel_paths / ro_property / expected return values.
        for s_rel_path, ro, result in zip(snap_rel_paths, ro_prop, expected):
            self.mock_get_property.return_value = ro
            self.assertEqual(parse_snap_details(p_mnt_pt, s_rel_path), result,
                             msg="Passed Pool mount point={}, snap_rel_path"
                                 "={} but returned (snap_name, writable, is_"
                                 "clone) = {} .".format(p_mnt_pt, s_rel_path,
                                                        result))

    def test_shares_info_system_pool_used(self):
        """
        Test shares_info() on a systems pool with some snaps / clones.
        """
        # Set role='root' as testing system pool subvol exclusion mechanism.
        pool = Pool(raid='raid0', name='test-pool', role='root')
        # N.B. in this data set home is a snap ie has been rolled back to a rw
        # snapshot.
        snap_idmap_return = {'319': '.snapshots/home/home-snap-writable',
                             '324': '.snapshots/sys-pool-share/snap-sys-pool-share',  # noqa E501
                             '316': '.snapshots/home/home-snap',
                             '323': 'clone-sys-pool-share',
                             '320': '.snapshots/home/home-snap-writable-visible',  # noqa E501
                             '321': '.snapshots/home-clone/home-clone-snap-writable',  # noqa E501
                             '326': '.snapshots/sys-pool-share/snap-writable-visible-sys-pool-share',  # noqa E501
                             '327': '.snapshots/clone-sys-pool-share/snap-clone-sys-pool-share',  # noqa E501
                             '298': 'home-clone',
                             '325': '.snapshots/sys-pool-share/snap-writable-sys-pool-share',  # noqa E501
                             '296': 'home',
                             '328': '.snapshots/clone-sys-pool-share/snap-clone-sys-pool-share-writable',  # noqa E501
                             '329': '.snapshots/clone-sys-pool-share/snap-clone-sys-pool-share-writable-visible'}  # noqa E501
        self.patch_snap_idmap = patch('fs.btrfs.snapshot_idmap')
        self.mock_snap_idmap = self.patch_snap_idmap.start()
        self.mock_snap_idmap.return_value = snap_idmap_return
        # mock 'btrfs subvol_list_-p' (via run_command) return values
        out = ['ID 257 gen 4986 parent 5 top level 5 path @',
               'ID 258 gen 4986 parent 257 top level 257 path var',
               'ID 259 gen 4534 parent 257 top level 257 path usr/local',
               'ID 260 gen 4986 parent 257 top level 257 path tmp',
               'ID 261 gen 4532 parent 257 top level 257 path srv',
               'ID 262 gen 4538 parent 257 top level 257 path root',
               'ID 263 gen 4986 parent 257 top level 257 path opt',
               'ID 265 gen 4056 parent 257 top level 257 path boot/grub2/x86_64-efi',  # noqa E501
               'ID 266 gen 4532 parent 257 top level 257 path boot/grub2/i386-pc',  # noqa E501
               'ID 296 gen 4968 parent 257 top level 257 path home',
               'ID 298 gen 4971 parent 257 top level 257 path home-clone',
               'ID 316 gen 4954 parent 257 top level 257 path .snapshots/home/home-snap',  # noqa E501
               'ID 319 gen 4963 parent 257 top level 257 path .snapshots/home/home-snap-writable',  # noqa E501
               'ID 320 gen 4966 parent 257 top level 257 path .snapshots/home/home-snap-writable-visible',  # noqa E501
               'ID 321 gen 4971 parent 257 top level 257 path .snapshots/home-clone/home-clone-snap-writable',  # noqa E501
               'ID 322 gen 4982 parent 257 top level 257 path sys-pool-share',
               'ID 323 gen 4986 parent 257 top level 257 path clone-sys-pool-share',  # noqa E501
               'ID 324 gen 4979 parent 257 top level 257 path .snapshots/sys-pool-share/snap-sys-pool-share',  # noqa E501
               'ID 325 gen 4980 parent 257 top level 257 path .snapshots/sys-pool-share/snap-writable-sys-pool-share',  # noqa E501
               'ID 326 gen 4981 parent 257 top level 257 path .snapshots/sys-pool-share/snap-writable-visible-sys-pool-share',  # noqa E501
               'ID 327 gen 4984 parent 257 top level 257 path .snapshots/clone-sys-pool-share/snap-clone-sys-pool-share',  # noqa E501
               'ID 328 gen 4985 parent 257 top level 257 path .snapshots/clone-sys-pool-share/snap-clone-sys-pool-share-writable',  # noqa E501
               'ID 329 gen 4986 parent 257 top level 257 path .snapshots/clone-sys-pool-share/snap-clone-sys-pool-share-writable-visible',  # noqa E501
               '']
        err = ['']
        rc = 0
        self.mock_run_command.return_value = (out, err, rc)
        # default_subvol
        self.patch_default_subvol = patch('fs.btrfs.default_subvol')
        self.mock_default_subvol = self.patch_default_subvol.start()
        self.mock_default_subvol.return_value = DefaultSubvol("257", "@", False)
        # parse_snap_details
        self.patch_parse_snap_details = patch('fs.btrfs.parse_snap_details')
        self.mock_parse_snap_details = self.patch_parse_snap_details.start()

        def parse_snap_details_return(*args, **kwargs):
            # We have a few clone shares (snaps at top level) in our test data:
            clones = ['home', 'home-clone', 'clone-sys-pool-share']
            if args[1] in clones:
                # (snap_name, writable, is_clone)
                return None, True, True
            else:
                # brand all others as writable - ok for subvol filter test.
                return 'arbitrary-name', True, False
        # From above we expect the following Rockstor relevant shares:
        expected = {'home': '0/296', 'home-clone': '0/298',
                    'clone-sys-pool-share': '0/323', 'sys-pool-share': '0/322'}
        self.mock_parse_snap_details.side_effect = parse_snap_details_return
        returned = shares_info(pool)
        self.assertEqual(returned, expected,
                         msg="Failed system pool share/clone filtering:\n"
                             "returned {},\nexpected {}.\n".format(returned,
                                                                   expected))

    def test_shares_info_legacy_system_pool_used(self):
        """
        Test shares_info() on legacy systems pool with some snaps and clones.
        """
        # Set role='root' as testing system pool subvol exclusion mechanism.
        pool = Pool(raid='raid0', name='test-pool', role='root')
        # N.B. in this data set home is a snap ie has been rolled back from a
        # snapshot.
        snap_idmap_return = {'288': 'home-clone',
                             '290': 'clone-sys-pool-share',
                             '284': 'home',
                             '287': '.snapshots/home/home-snap-writable',
                             '286': '.snapshots/home/home-snap'}
        self.patch_snap_idmap = patch('fs.btrfs.snapshot_idmap')
        self.mock_snap_idmap = self.patch_snap_idmap.start()
        self.mock_snap_idmap.return_value = snap_idmap_return
        # mock 'btrfs subvol_list_-p' (via run_command) return values
        # N.B. here we see the systemd root/var/lib/machines subvol.
        out = ['ID 257 gen 45769 parent 5 top level 5 path root',
               'ID 260 gen 43499 parent 257 top level 257 path root/var/lib/machines',  # noqa E501
               'ID 284 gen 44893 parent 5 top level 5 path home',
               'ID 286 gen 44739 parent 5 top level 5 path .snapshots/home/home-snap',  # noqa E501
               'ID 287 gen 44742 parent 5 top level 5 path .snapshots/home/home-snap-writable',  # noqa E501
               'ID 288 gen 44893 parent 5 top level 5 path home-clone',
               'ID 289 gen 44912 parent 5 top level 5 path sys-pool-share',
               'ID 290 gen 44912 parent 5 top level 5 path clone-sys-pool-share',  # noqa E501
               '']
        err = ['']
        rc = 0
        self.mock_run_command.return_value = (out, err, rc)
        # default_subvol
        self.patch_default_subvol = patch('fs.btrfs.default_subvol')
        self.mock_default_subvol = self.patch_default_subvol.start()
        self.mock_default_subvol.return_value = DefaultSubvol("5", "(FS_TREE)", False)
        # parse_snap_details
        self.patch_parse_snap_details = patch('fs.btrfs.parse_snap_details')
        self.mock_parse_snap_details = self.patch_parse_snap_details.start()

        def parse_snap_details_return(*args, **kwargs):
            # We have a few clone shares (snaps at top level) in our test data:
            clones = ['home', 'home-clone', 'clone-sys-pool-share']
            if args[1] in clones:
                # (snap_name, writable, is_clone)
                return None, True, True
            else:
                # brand all others as writable - ok for subvol filter test.
                return 'arbitrary-name', True, False
        self.mock_parse_snap_details.side_effect = parse_snap_details_return
        # From above we expect the following Rockstor relevant shares:
        expected = {'home': '0/284', 'home-clone': '0/288',
                    'clone-sys-pool-share': '0/290',
                    'sys-pool-share': '0/289'}
        returned = shares_info(pool)
        self.assertEqual(returned, expected,
                         msg="Failed system pool share/clone filtering:\n"
                             "returned {},\nexpected {}.\n".format(returned,
                                                                   expected))

    def test_shares_info_legacy_system_pool_fresh(self):
        """
        Test shares_info() on fresh legacy systems pool, no snaps or clones.
        """
        # Set role='root' as testing system pool subvol exclusion mechanism.
        pool = Pool(raid='raid0', name='test-pool', role='root')
        snap_idmap_return = {}
        self.patch_snap_idmap = patch('fs.btrfs.snapshot_idmap')
        self.mock_snap_idmap = self.patch_snap_idmap.start()
        self.mock_snap_idmap.return_value = snap_idmap_return
        # mock 'btrfs subvol_list_-p' (via run_command) return values
        # Note the systemd root/var/lib/machines subvol to be excluded.
        out = ['ID 257 gen 98733 parent 5 top level 5 path home',
               'ID 258 gen 99195 parent 5 top level 5 path root',
               'ID 260 gen 78538 parent 258 top level 258 path root/var/lib/machines',  # noqa E501
               '']
        err = ['']
        rc = 0
        self.mock_run_command.return_value = (out, err, rc)
        # default_subvol
        self.patch_default_subvol = patch('fs.btrfs.default_subvol')
        self.mock_default_subvol = self.patch_default_subvol.start()
        self.mock_default_subvol.return_value = DefaultSubvol("5", "(FS_TREE)", False)
        self.patch_parse_snap_details = patch('fs.btrfs.parse_snap_details')
        self.mock_parse_snap_details = self.patch_parse_snap_details.start()
        # From above we expect the following Rockstor relevant shares:
        expected = {'home': '0/257'}
        # Mocked return value in following = (snap_name, writable, is_clone)
        # ie no clones
        self.mock_parse_snap_details.return_value = 'foo-bar', True, False
        returned = shares_info(pool)
        self.assertEqual(returned, expected,
                         msg="Failed system pool share/clone filtering:\n"
                             "returned {},\nexpected {}.\n".format(returned,
                                                                   expected))

    def test_shares_info_system_pool_post_btrfs_subvol_list_path_changes(self):
        """
        Later 'btrfs subvolume list -p' defaults to supplying path relative to
        pool, rather than supplied subvolume.
        ie prior change 'subvol list' item:
        'ID 257 gen 4986 parent 5 top level 5 path @'
        'ID 296 gen 4968 parent 257 top level 257 path home',
        post changes:
        'ID 257 gen 1725 parent 5 top level 5 path @'
        'ID 264 gen 1725 parent 257 top level 257 path @/home'
        Note: path now include it's root of @ (
        Also drops -o option and outputs nothing when used (silent failure)!
        """
        # Set role='root' as testing system pool subvol exclusion mechanism.
        pool = Pool(raid='raid0', name='test-pool', role='root')
        # example data includes default snapper 'system' snapshots & no clones.
        snap_idmap_return = {'289': '.snapshots/home/home-snap',
                             '288': '.snapshots/18/snapshot',
                             '272': '.snapshots/2/snapshot',
                             '283': '.snapshots/13/snapshot',
                             '284': '.snapshots/14/snapshot',
                             '287': '.snapshots/17/snapshot'}
        self.patch_snap_idmap = patch('fs.btrfs.snapshot_idmap')
        self.mock_snap_idmap = self.patch_snap_idmap.start()
        self.mock_snap_idmap.return_value = snap_idmap_return
        # mock 'btrfs subvol_list_-p' (via run_command) return values
        # Note the previously absent '@/' path additions.
        out = ['ID 257 gen 1725 parent 5 top level 5 path @',
               'ID 258 gen 1776 parent 257 top level 257 path @/var',
               'ID 259 gen 1725 parent 257 top level 257 path @/usr/local',
               'ID 260 gen 1776 parent 257 top level 257 path @/tmp',
               'ID 261 gen 1725 parent 257 top level 257 path @/srv',
               'ID 262 gen 1737 parent 257 top level 257 path @/root',
               'ID 263 gen 1776 parent 257 top level 257 path @/opt',
               'ID 264 gen 1725 parent 257 top level 257 path @/home',
               'ID 265 gen 1725 parent 257 top level 257 path @/boot/grub2/x86_64-efi',  # noqa E501
               'ID 266 gen 1725 parent 257 top level 257 path @/boot/grub2/i386-pc',  # noqa E501
               'ID 267 gen 1725 parent 257 top level 257 path @/.snapshots',
               'ID 268 gen 1738 parent 267 top level 267 path @/.snapshots/1/snapshot',  # noqa E501
               'ID 272 gen 1725 parent 267 top level 267 path @/.snapshots/2/snapshot',  # noqa E501
               'ID 283 gen 1725 parent 267 top level 267 path @/.snapshots/13/snapshot',  # noqa E501
               'ID 284 gen 1725 parent 267 top level 267 path @/.snapshots/14/snapshot',  # noqa E501
               'ID 287 gen 1725 parent 267 top level 267 path @/.snapshots/17/snapshot',  # noqa E501
               'ID 288 gen 1725 parent 267 top level 267 path @/.snapshots/18/snapshot',  # noqa E501
               'ID 289 gen 1725 parent 268 top level 268 path .snapshots/home/home-snap',  # noqa E501
               'ID 291 gen 1725 parent 268 top level 268 path sys-share-test',
               'ID 292 gen 1725 parent 268 top level 268 path sys-share-test-2',  # noqa E501
               'ID 293 gen 1725 parent 268 top level 268 path test-share',
               'ID 294 gen 1725 parent 268 top level 268 path ghost-share', '']
        err = ['']
        rc = 0
        # default_subvol
        self.patch_default_subvol = patch('fs.btrfs.default_subvol')
        self.mock_default_subvol = self.patch_default_subvol.start()
        self.mock_default_subvol.return_value = DefaultSubvol("268", "@/.snapshots/1/snapshot", True)
        # run_command
        self.mock_run_command.return_value = (out, err, rc)
        # parse_snap_details
        self.patch_parse_snap_details = patch('fs.btrfs.parse_snap_details')
        self.mock_parse_snap_details = self.patch_parse_snap_details.start()
        # From above we expect the following Rockstor relevant shares:
        expected = {'home': '0/264', 'test-share': '0/293',
                    'sys-share-test-2': '0/292', 'sys-share-test': '0/291',
                    'ghost-share': '0/294'}
        # Mocked return value in following = (snap_name, writable, is_clone)
        # ie no clones
        self.mock_parse_snap_details.return_value = 'foo-bar', True, False
        returned = shares_info(pool)
        self.assertEqual(returned, expected,
                         msg="Failed system pool share/clone filtering:\n"
                             "returned {},\nexpected {}.\n".format(returned,
                                                                   expected))

    def test_shares_info_system_pool_boot_to_snapshot_root_user_share(self):
        """
        As per test_shares_info_system_pool_post_btrfs_subvol_list_path_changes() this
        test concerns more modern "btrfs subvolume list -p" behaviour but in the context
        our or 'Built on openSUSE' system pool user created shares not being reported
        post creation due to our filtering our subvols of snapshots and given a boot to
        snapshot makes our user share have a parent that is also a snapshot. Fix was to
        make an exception for this exclusion if the parent id of the snapshot was also
        the default_id of this pool (the boot to snapshot config).
        We are testing for he detection of the user created share that post cretion in
        later Leap15.1+ versions would then vanish post bottom up read via shares_info()
        when ROOT pool was boot to snapshot enabled.
        ID 257 gen 19 parent 5 top level 5 path @
        -- ID 258 gen 14951 parent 257 top level 257 path @/.snapshots
        --- ID 259 gen 15544 parent 258 top level 258 path @/.snapshots/1/snapshot
        ---- ID 292 gen 941 parent 259 top level 259 path test_share_01
        :return:
        """
        # Set role='root' as testing system pool subvol exclusion mechanism.
        pool = Pool(raid='raid0', name='test-pool', role='root')
        # example data includes default snapper 'system' snapshots & no clones.
        snap_idmap_return = {'357': '.snapshots/81/snapshot',
                             '365': '.snapshots/88/snapshot',
                             '360': '.snapshots/84/snapshot',
                             '331': '.snapshots/57/snapshot',
                             '332': '.snapshots/58/snapshot',
                             '270': '.snapshots/2/snapshot',
                             '356': '.snapshots/80/snapshot',
                             '355': '.snapshots/79/snapshot',
                             '259': '.snapshots/1/snapshot',  # Our current ROOT snap
                             '353': '.snapshots/78/snapshot',
                             '352': '.snapshots/77/snapshot',
                             '351': '.snapshots/76/snapshot',
                             '350': '.snapshots/75/snapshot',
                             '364': '.snapshots/87/snapshot',
                             '361': '.snapshots/85/snapshot',
                             '363': '.snapshots/86/snapshot',
                             '359': '.snapshots/83/snapshot',
                             '358': '.snapshots/82/snapshot'}
        self.patch_snap_idmap = patch('fs.btrfs.snapshot_idmap')
        self.mock_snap_idmap = self.patch_snap_idmap.start()
        self.mock_snap_idmap.return_value = snap_idmap_return
        # mock 'btrfs subvol_list_-p' (via run_command) return values
        out = ['ID 257 gen 19 parent 5 top level 5 path @',
               'ID 258 gen 16031 parent 257 top level 257 path @/.snapshots',
               'ID 259 gen 16312 parent 258 top level 258 path @/.snapshots/1/snapshot',
               'ID 260 gen 1656 parent 257 top level 257 path @/home',
               'ID 261 gen 16318 parent 257 top level 257 path @/opt',
               'ID 262 gen 16225 parent 257 top level 257 path @/root',
               'ID 263 gen 11789 parent 257 top level 257 path @/srv',
               'ID 264 gen 16318 parent 257 top level 257 path @/tmp',
               'ID 265 gen 16318 parent 257 top level 257 path @/var',
               'ID 266 gen 15722 parent 257 top level 257 path @/usr/local',
               'ID 267 gen 11793 parent 257 top level 257 path @/boot/grub2/i386-pc',
               'ID 268 gen 20 parent 257 top level 257 path @/boot/grub2/x86_64-efi',
               'ID 270 gen 30 parent 258 top level 258 path @/.snapshots/2/snapshot',
               # The following is our user created share with ROOT snap parent.
               'ID 292 gen 941 parent 259 top level 259 path test_share_01',
               'ID 331 gen 7527 parent 258 top level 258 path @/.snapshots/57/snapshot',
               'ID 332 gen 7547 parent 258 top level 258 path @/.snapshots/58/snapshot',
               'ID 350 gen 11335 parent 258 top level 258 path @/.snapshots/75/snapshot',
               'ID 351 gen 11344 parent 258 top level 258 path @/.snapshots/76/snapshot',
               'ID 352 gen 11346 parent 258 top level 258 path @/.snapshots/77/snapshot',
               'ID 353 gen 11348 parent 258 top level 258 path @/.snapshots/78/snapshot',
               'ID 355 gen 11371 parent 258 top level 258 path @/.snapshots/79/snapshot',
               'ID 356 gen 11577 parent 258 top level 258 path @/.snapshots/80/snapshot',
               'ID 357 gen 11578 parent 258 top level 258 path @/.snapshots/81/snapshot',
               'ID 358 gen 11595 parent 258 top level 258 path @/.snapshots/82/snapshot',
               'ID 359 gen 11596 parent 258 top level 258 path @/.snapshots/83/snapshot',
               'ID 360 gen 11761 parent 258 top level 258 path @/.snapshots/84/snapshot',
               'ID 361 gen 11784 parent 258 top level 258 path @/.snapshots/85/snapshot',
               'ID 363 gen 11792 parent 258 top level 258 path @/.snapshots/86/snapshot',
               'ID 364 gen 14949 parent 258 top level 258 path @/.snapshots/87/snapshot',
               'ID 365 gen 14950 parent 258 top level 258 path @/.snapshots/88/snapshot',
               '']
        err = ['']
        rc = 0
        # default_subvol
        self.patch_default_subvol = patch('fs.btrfs.default_subvol')
        self.mock_default_subvol = self.patch_default_subvol.start()
        self.mock_default_subvol.return_value = DefaultSubvol("259", "@/.snapshots/1/snapshot", True)
        # run_command
        self.mock_run_command.return_value = (out, err, rc)
        # parse_snap_details
        self.patch_parse_snap_details = patch('fs.btrfs.parse_snap_details')
        self.mock_parse_snap_details = self.patch_parse_snap_details.start()
        # Mocked return value in following = (snap_name, writable, is_clone)
        # ie no clones
        self.mock_parse_snap_details.return_value = 'foo-bar', True, False

        expected = {'home': '0/260', 'test_share_01': '0/292'}
        returned = shares_info(pool)
        self.assertEqual(returned, expected,
                         msg="Failed system pool share/clone filtering:\n"
                             "returned {},\nexpected {}.\n".format(returned,
                                                                   expected))

# TODO: test_shares_info_system_pool_fresh

    def test_get_snap_legacy(self):
        """
        Test get_snap() across various input.
        """
        # example output from
        # get_snap() called with
        subvol = '/mnt2/test-pool/.snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share'  # noqa E501
        oldest = True
        num_retain = 3
        regex = '_replication_'
        test_mode = True
        out = [['ID 258 gen 184 top level 5 path new-share',
                'ID 295 gen 184 top level 5 path .snapshots/new-share/new-share-snap',  # noqa E501
                'ID 304 gen 220 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_test-share',  # noqa E501
                'ID 305 gen 222 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_1',  # noqa E501
                '']]
        err = [['']]
        rc = [0]
        # the return in above case was correctly None as num_retains=3
        expected_result = [None]

        out.append(['ID 258 gen 184 top level 5 path new-share',
                    'ID 295 gen 184 top level 5 path .snapshots/new-share/new-share-snap',  # noqa E501
                    'ID 304 gen 220 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_test-share',  # noqa E501
                    'ID 305 gen 227 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_1',  # noqa E501
                    'ID 306 gen 227 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_165',  # noqa E501
                    ''])
        err.append([''])
        rc.append(0)
        # the return in above case was correctly None as num_retains=3
        expected_result.append(None)

        out.append(['ID 258 gen 184 top level 5 path new-share',
                    'ID 295 gen 184 top level 5 path .snapshots/new-share/new-share-snap',  # noqa E501
                    'ID 304 gen 220 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_test-share',  # noqa E501
                    'ID 305 gen 227 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_1',  # noqa E501
                    'ID 306 gen 230 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_165',  # noqa E501
                    'ID 307 gen 230 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_167',  # noqa E501
                    ''])
        err.append([''])
        rc.append(0)
        # the return in above was correctly None as num_retains=3 (last time)
        expected_result.append(None)

        out.append(['ID 258 gen 184 top level 5 path new-share',
                    'ID 295 gen 184 top level 5 path .snapshots/new-share/new-share-snap',  # noqa E501
                    'ID 304 gen 220 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_test-share',  # noqa E501
                    'ID 305 gen 227 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_1',  # noqa E501
                    'ID 306 gen 230 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_165',  # noqa E501
                    'ID 307 gen 233 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_167',  # noqa E501
                    'ID 308 gen 233 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_test-share/test-share_6_replication_168',  # noqa E501
                    ''])
        err.append([''])
        rc.append(0)
        expected_result.append('test-share_6_replication_1')
        # Cycle through each of the above mock_run_command data sets.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            # print('each out = {}'.format(o))
            # print('each expected = {}'.format(expected))
            self.mock_run_command.return_value = (o, e, r)
            returned = get_snap(subvol, oldest, num_retain, regex, test_mode)
            self.assertEqual(returned, expected,
                             msg='Un-expected get_snap() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))

    def test_get_snap_2(self):
        """
        More get_snap() test data taken after btrfs.py refactoring
        """
        # example output from
        # get_snap() called with
        subvol = '/mnt2/rock-pool/.snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share'  # noqa E501
        # post processed share_name=C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share  # noqa E501
        oldest = True
        num_retain = 2
        regex = '_replication_'
        test_mode = True
        out = [['ID 260 gen 52 top level 5 path clone-from-rock-share-snap',
               'ID 293 gen 268 top level 5 path rock-share',
               'ID 328 gen 345 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share',  # noqa E501
               'ID 329 gen 347 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_1',  # noqa E501
               '']]
        err = [['']]
        rc = [0]
        expected_result = [None]

        out.append(['ID 260 gen 52 top level 5 path clone-from-rock-share-snap',  # noqa E501
               'ID 293 gen 268 top level 5 path rock-share',
               'ID 328 gen 345 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share',  # noqa E501
               'ID 329 gen 350 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_1',  # noqa E501
               'ID 330 gen 350 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_48',  # noqa E501
               ''])
        err.append([''])
        rc.append(0)
        expected_result.append(None)

        out.append(['ID 260 gen 52 top level 5 path clone-from-rock-share-snap',  # noqa E501
               'ID 293 gen 268 top level 5 path rock-share',
               'ID 328 gen 345 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share',  # noqa E501
               'ID 329 gen 350 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_1',  # noqa E501
               'ID 330 gen 353 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_48',  # noqa E501
               'ID 331 gen 353 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_49',  # noqa E501
               ''])
        err.append([''])
        rc.append(0)
        expected_result.append('rep-test-share_3_replication_1')

        out.append(['ID 260 gen 52 top level 5 path clone-from-rock-share-snap',  # noqa E501
               'ID 293 gen 268 top level 5 path rock-share',
               'ID 329 gen 350 top level 5 path C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share',  # noqa E501
               'ID 330 gen 353 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_48',  # noqa E501
               'ID 331 gen 357 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_49',  # noqa E501
               'ID 332 gen 357 top level 5 path .snapshots/C583C37F-08AE-478B-A726-E95235D1712B_rep-test-share/rep-test-share_3_replication_50',  # noqa E501
               ''])
        err.append([''])
        rc.append(0)
        expected_result.append('rep-test-share_3_replication_48')
        # Cycle through each of the above mock_run_command data sets.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            # print('each out = {}'.format(o))
            # print('each expected = {}'.format(expected))
            self.mock_run_command.return_value = (o, e, r)
            returned = get_snap(subvol, oldest, num_retain, regex, test_mode)
            self.assertEqual(returned, expected,
                             msg='Un-expected get_snap() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))

    def test_dev_stats_zero(self):
        """
        Present various return codes from run_command() to test the function of
        dev_stats_zero(). All non rc elements not currently relevant but may
        serve future tests so included as is.
        """
        # run_command mock output set:
        # legacy system pool
        out = [['[/dev/vda3].write_io_errs    0',
                '[/dev/vda3].read_io_errs     0',
                '[/dev/vda3].flush_io_errs    0',
                '[/dev/vda3].corruption_errs  0',
                '[/dev/vda3].generation_errs  0',
                '']]
        err = [['']]
        rc = [0]
        expected_result = [True]  # rc = 0 is not errors found in results
        # run_command mock output set:
        out.append(['[/dev/vdb].write_io_errs    0',
                    '[/dev/vdb].read_io_errs     0',
                    '[/dev/vdb].flush_io_errs    0',
                    '[/dev/vdb].corruption_errs  5',
                    '[/dev/vdb].generation_errs  0',
                    ''])
        err.append([''])
        rc.append(64)
        expected_result.append(False)  # bit 6 set in rc means non zero errors.
        # run_command mock output set:
        # 3 open LUKS containers as members.
        out.append([
            '[/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e].write_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e].read_io_errs     0',  # noqa E501
            '[/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e].flush_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e].corruption_errs  0',  # noqa E501
            '[/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e].generation_errs  0',  # noqa E501
            '[/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc].write_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc].read_io_errs     0',  # noqa E501
            '[/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc].flush_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc].corruption_errs  0',  # noqa E501
            '[/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc].generation_errs  0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].write_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].read_io_errs     0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].flush_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].corruption_errs  0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].generation_errs  0',  # noqa E501
            ''])
        err.append([''])
        rc.append(0)
        expected_result.append(True)
        # Cycle through the above run_command mock sets.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            returned = dev_stats_zero('arbitrary_unit_test_mount_point')
            # print('each out = {}'.format(o))
            # print('each expected = {}'.format(expected))
            # print('each returned value = {}'.format(returned))
            msg = ('Un-expected dev_stats_zero() result for rc = {}. \n '
                   'returned = ({}).\n expected = ({}).'.format(r, returned,
                                                                expected))
            self.assertEqual(returned, expected, msg=msg)

    def test_get_dev_io_error_stats(self):
        """
        Present various device io error stats and return codes to
        get_dev_io_error_stats()
        """
        # legacy system pool device
        #
        out = [['[/dev/vda3].write_io_errs    0',
                '[/dev/vda3].read_io_errs     0',
                '[/dev/vda3].flush_io_errs    0',
                '[/dev/vda3].corruption_errs  0',
                '[/dev/vda3].generation_errs  0',
                '']]
        err = [['']]
        rc = [0]
        expected_result = [
            ('{"generation_errs": "0", "corruption_errs": "0", '
             '"read_io_errs": "0", "write_io_errs": "0", '
             '"flush_io_errs": "0"}')
        ]
        # /dev/disk/by-id/dm-name-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad
        out.append([
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].write_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].read_io_errs     0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].flush_io_errs    0',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].corruption_errs  42',  # noqa E501
            '[/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad].generation_errs  0',  # noqa E501
            ''])
        err.append([''])
        rc.append(64)
        expected_result.append(
            ('{"generation_errs": "0", "corruption_errs": "42", '
             '"read_io_errs": "0", "write_io_errs": "0", '
             '"flush_io_errs": "0"}')
        )
        # a non mounted device:
        out.append([''])
        err.append([
            "ERROR: '/dev/disk/by-id/virtio-serial-5' is not a mounted btrfs device",  # noqa E501
            ''])
        rc.append(1)
        expected_result.append(None)
        # errors found
        out.append([
            '[/dev/sdc].write_io_errs    204669',
            '[/dev/sdc].read_io_errs     81232',
            '[/dev/sdc].flush_io_errs    782',
            '[/dev/sdc].corruption_errs  2985',
            '[/dev/sdc].generation_errs  47',
            ''])
        err.append([''])
        rc.append(64)
        expected_result.append(
            ('{"generation_errs": "47", "corruption_errs": "2985", '
             '"read_io_errs": "81232", "write_io_errs": "204669", '
             '"flush_io_errs": "782"}')
        )
        # Cycle through the above run_command mock sets.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            returned = get_dev_io_error_stats('arbitrary_unit_test_dev_name')
            # As we are testing the default (json_format=True) output type we
            # need to sort our returned and expected to allow for comparison.
            # Convert to dict and back to json (with a key sort):
            if returned is not None:
                returned = json.dumps(json.loads(returned), sort_keys=True)
            if expected is not None:
                expected = json.dumps(json.loads(expected), sort_keys=True)
            # print('each out = {}'.format(o))
            # print('each expected = {}'.format(expected))
            # print('each returned value = {}'.format(returned))
            msg = ('Un-expected get_dev_io_error_stats() result: rc = {}. \n '
                   'returned = ({}).\n expected = ({}).'.format(r, returned,
                                                                expected))
            if expected is None:
                self.assertIsNone(returned, msg=msg)
            else:
                self.assertEqual(returned, expected, msg=msg)

    def test_default_subvol(self):
        """
        Present known real output from "btrfs subvol get-default /" and test the parsing
        function of default_subvol()
        """
        # Legacy CentOS based install (default subvol not set so will default to ID 5)
        # N.B. this is also the output expected from a regular data pool on Rockstor:
        # e.g. "btrfs subvol get-default /mnt2/rock-pool/"
        # ID 5 (FS_TREE)
        # Relevant if we ever expand this function to take a pool mount point parameter.
        out = [['ID 5 (FS_TREE)', '']]
        err = [['']]
        rc = [0]
        expected_result = [DefaultSubvol("5", "(FS_TREE)", False)]
        # openSUSE Leap 15.1 boot-to-snap enabled but in default state, no rollback
        out.append(['ID 259 gen 60199 top level 258 path @/.snapshots/1/snapshot', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(DefaultSubvol("259", "@/.snapshots/1/snapshot", True))
        # openSUSE Leap 15.2 beta boot-to-snap enabled and rolled back to prior snap
        out.append(['ID 456 gen 24246 top level 258 path @/.snapshots/117/snapshot', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(DefaultSubvol("456", "@/.snapshots/117/snapshot", True))
        # openSUSE Leap 15.2 beta NO boot-to-snap - deselected during install.
        # On Root disks less than 17.5 GB (around 16GB btrfs system pool) this is the
        # default install. Rockstor ISO installs enforce boot-to-snap irrispective.
        out.append(['ID 256 gen 2858 top level 5 path @', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(DefaultSubvol("256", "@", False))
        for o, e, r, expected in zip(out, err, rc, expected_result):
            # print('each out = {}'.format(o))
            # print('each expected = {}'.format(expected))
            self.mock_run_command.return_value = (o, e, r)
            returned = default_subvol()
            self.assertEqual(returned, expected,
                             msg='Un-expected default_subvol() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))
