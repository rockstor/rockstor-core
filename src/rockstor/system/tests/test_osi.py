"""
Copyright (c) 2012-2018 RockStor, Inc. <http://rockstor.com>
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
import operator
import unittest
from mock import patch

from system.osi import get_dev_byid_name, Disk, scan_disks, get_byid_name_map


class Pool(object):
    def __init__(self, raid, name):
        self.raid = raid
        self.name = name


class OSITests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd <root dir of rockstor ie /opt/rockstor>
    ./bin/test --settings=test-settings -v 3 -p test_osi*
    """
    def setUp(self):
        self.patch_run_command = patch('system.osi.run_command')
        self.mock_run_command = self.patch_run_command.start()

        # some procedures use os.path.exists so setup mock
        self.patch_os_path_exists = patch('os.path.exists')
        self.mock_os_path_exists = self.patch_os_path_exists.start()

        # some procedures use os.path.isfile so setup mock
        self.patch_os_path_isfile = patch('os.path.isfile')
        self.mock_os_path_isfile = self.patch_os_path_isfile.start()

        # root_disk() default mock - return /dev/sda for /dev/sda3 '/'
        self.patch_root_disk = patch('system.osi.root_disk')
        self.mock_root_disk = self.patch_root_disk.start()
        self.mock_root_disk.return_value = '/dev/sda'

    def tearDown(self):
        patch.stopall()

    def test_get_dev_byid_name(self):
        """
        Test get_dev_byid_name() across a range of inputs.
        """
        # Note in the first set we have a non DEVLINKS first line and
        # 3 equal length (37 char) names:
        # scsi-1ATA_QEMU_HARDDISK_sys-357-part1
        # scsi-0ATA_QEMU_HARDDISK_sys-357-part1
        # scsi-SATA_QEMU_HARDDISK_sys-357-part1
        # and one shorter, all for the same device.
        # ata-QEMU_HARDDISK_sys-357-part1
        dev_name = ['/dev/sda1']
        remove_path = [True]
        out = [[
            'COMPAT_SYMLINK_GENERATION=2',
            'DEVLINKS=/dev/disk/by-id/ata-QEMU_HARDDISK_sys-357-part1 /dev/disk/by-id/scsi-0ATA_QEMU_HARDDISK_sys-357-part1 /dev/disk/by-path/pci-0000:00:06.0-ata-1-part1 /dev/disk/by-id/scsi-1ATA_QEMU_HARDDISK_sys-357-part1 /dev/disk/by-uuid/c66d68dd-597e-4525-9eea-3add073378d0 /dev/disk/by-partuuid/8ae50ecc-d866-4187-a4ec-79b096bdf8ed /dev/disk/by-label/system /dev/disk/by-id/scsi-SATA_QEMU_HARDDISK_sys-357-part1',  # noqa E501
            'DEVNAME=/dev/sda1',
            'DEVPATH=/devices/pci0000:00/0000:00:06.0/ata1/host0/target0:0:0/0:0:0:0/block/sda/sda1',  # noqa E501
            'DEVTYPE=partition', 'DONT_DEL_PART_NODES=1', 'ID_ATA=1',
            'ID_ATA_FEATURE_SET_SMART=1',
            'ID_ATA_FEATURE_SET_SMART_ENABLED=1', 'ID_ATA_SATA=1',
            'ID_ATA_WRITE_CACHE=1', 'ID_ATA_WRITE_CACHE_ENABLED=1',
            'ID_BTRFS_READY=1', 'ID_BUS=ata', 'ID_FS_LABEL=system',
            'ID_FS_LABEL_ENC=system', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=c66d68dd-597e-4525-9eea-3add073378d0',
            'ID_FS_UUID_ENC=c66d68dd-597e-4525-9eea-3add073378d0',
            'ID_FS_UUID_SUB=76c503a3-3310-45ad-8457-38c35c2cf295',
            'ID_FS_UUID_SUB_ENC=76c503a3-3310-45ad-8457-38c35c2cf295',
            'ID_MODEL=QEMU_HARDDISK',
            'ID_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20',  # noqa E501
            'ID_PART_ENTRY_DISK=8:0', 'ID_PART_ENTRY_FLAGS=0x4',
            'ID_PART_ENTRY_NUMBER=1', 'ID_PART_ENTRY_OFFSET=2048',
            'ID_PART_ENTRY_SCHEME=gpt', 'ID_PART_ENTRY_SIZE=16775135',
            'ID_PART_ENTRY_TYPE=0fc63daf-8483-4772-8e79-3d69d8477de4',
            'ID_PART_ENTRY_UUID=8ae50ecc-d866-4187-a4ec-79b096bdf8ed',
            'ID_PART_TABLE_TYPE=dos',
            'ID_PART_TABLE_UUID=2c013305-39f1-42df-950b-f6953117e09c',
            'ID_PATH=pci-0000:00:06.0-ata-1',
            'ID_PATH_TAG=pci-0000_00_06_0-ata-1', 'ID_REVISION=2.5+',
            'ID_SCSI=1', 'ID_SCSI_INQUIRY=1',
            'ID_SERIAL=QEMU_HARDDISK_sys-357', 'ID_SERIAL_SHORT=sys-357',
            'ID_TYPE=disk', 'ID_VENDOR=ATA',
            'ID_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20', 'MAJOR=8',
            'MINOR=1', 'PARTN=1',
            'SCSI_IDENT_LUN_ATA=QEMU_HARDDISK_sys-357',
            'SCSI_IDENT_LUN_T10=ATA_QEMU_HARDDISK_sys-357',
            'SCSI_IDENT_LUN_VENDOR=sys-357', 'SCSI_IDENT_SERIAL=sys-357',
            'SCSI_MODEL=QEMU_HARDDISK',
            'SCSI_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20',
            'SCSI_REVISION=2.5+', 'SCSI_TPGS=0', 'SCSI_TYPE=disk',
            'SCSI_VENDOR=ATA',
            'SCSI_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20',
            'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=3052289',
            '']]
        err = [['']]
        rc = [0]
        # Expected return is always a tuple ('name-string', is_byid_boolean)
        expected_result = [('scsi-SATA_QEMU_HARDDISK_sys-357-part1', True)]
        # regular data pool disk member (whole disk).
        dev_name.append('sdb')
        remove_path.append(True)
        out.append([
            'COMPAT_SYMLINK_GENERATION=2',
            'DEVLINKS=/dev/disk/by-id/scsi-1ATA_QEMU_HARDDISK_QM00007 /dev/disk/by-id/scsi-0ATA_QEMU_HARDDISK_QM00007 /dev/disk/by-id/ata-QEMU_HARDDISK_QM00007 /dev/disk/by-label/rock-pool /dev/disk/by-id/scsi-SATA_QEMU_HARDDISK_QM00007 /dev/disk/by-path/pci-0000:00:06.0-ata-2 /dev/disk/by-uuid/429827fc-5ca9-4ca8-b152-f28d8a9d2737',  # noqa E501
            'DEVNAME=/dev/sdb',
            'DEVPATH=/devices/pci0000:00/0000:00:06.0/ata2/host1/target1:0:0/1:0:0:0/block/sdb',  # noqa E501
            'DEVTYPE=disk', 'DONT_DEL_PART_NODES=1', 'ID_ATA=1',
            'ID_ATA_FEATURE_SET_SMART=1',
            'ID_ATA_FEATURE_SET_SMART_ENABLED=1', 'ID_ATA_SATA=1',
            'ID_ATA_WRITE_CACHE=1', 'ID_ATA_WRITE_CACHE_ENABLED=1',
            'ID_BTRFS_READY=1', 'ID_BUS=ata', 'ID_FS_LABEL=rock-pool',
            'ID_FS_LABEL_ENC=rock-pool', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=429827fc-5ca9-4ca8-b152-f28d8a9d2737',
            'ID_FS_UUID_ENC=429827fc-5ca9-4ca8-b152-f28d8a9d2737',
            'ID_FS_UUID_SUB=0c17e54b-09e9-4074-9577-c26c9af499a1',
            'ID_FS_UUID_SUB_ENC=0c17e54b-09e9-4074-9577-c26c9af499a1',
            'ID_MODEL=QEMU_HARDDISK',
            'ID_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20',  # noqa E501
            'ID_PATH=pci-0000:00:06.0-ata-2',
            'ID_PATH_TAG=pci-0000_00_06_0-ata-2', 'ID_REVISION=2.5+',
            'ID_SCSI=1', 'ID_SCSI_INQUIRY=1',
            'ID_SERIAL=QEMU_HARDDISK_QM00007',
            'ID_SERIAL_SHORT=QM00007',
            'ID_TYPE=disk', 'ID_VENDOR=ATA',
            'ID_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20', 'MAJOR=8',
            'MINOR=16', 'MPATH_SBIN_PATH=/sbin',
            'SCSI_IDENT_LUN_ATA=QEMU_HARDDISK_QM00007',
            'SCSI_IDENT_LUN_T10=ATA_QEMU_HARDDISK_QM00007',
            'SCSI_IDENT_LUN_VENDOR=QM00007',
            'SCSI_IDENT_SERIAL=QM00007',
            'SCSI_MODEL=QEMU_HARDDISK',
            'SCSI_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20',
            'SCSI_REVISION=2.5+', 'SCSI_TPGS=0', 'SCSI_TYPE=disk',
            'SCSI_VENDOR=ATA',
            'SCSI_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20',
            'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=3063907',
            ''])
        err.append([''])
        rc.append(0)
        expected_result.append(('scsi-SATA_QEMU_HARDDISK_QM00007', True))
        # Typical call type when resizing / changing raid level of pool
        dev_name.append('/dev/sdc')
        remove_path.append(False)
        out.append([
            'COMPAT_SYMLINK_GENERATION=2',
            'DEVLINKS=/dev/disk/by-label/rock-pool /dev/disk/by-id/scsi-SATA_QEMU_HARDDISK_QM00009 /dev/disk/by-id/scsi-1ATA_QEMU_HARDDISK_QM00009 /dev/disk/by-path/pci-0000:00:06.0-ata-3 /dev/disk/by-id/scsi-0ATA_QEMU_HARDDISK_QM00009 /dev/disk/by-uuid/429827fc-5ca9-4ca8-b152-f28d8a9d2737 /dev/disk/by-id/ata-QEMU_HARDDISK_QM00009',  # noqa E501
            'DEVNAME=/dev/sdc',
            'DEVPATH=/devices/pci0000:00/0000:00:06.0/ata3/host2/target2:0:0/2:0:0:0/block/sdc',  # noqa E501
            'DEVTYPE=disk', 'DONT_DEL_PART_NODES=1', 'ID_ATA=1',
            'ID_ATA_FEATURE_SET_SMART=1',
            'ID_ATA_FEATURE_SET_SMART_ENABLED=1', 'ID_ATA_SATA=1',
            'ID_ATA_WRITE_CACHE=1', 'ID_ATA_WRITE_CACHE_ENABLED=1',
            'ID_BTRFS_READY=1', 'ID_BUS=ata', 'ID_FS_LABEL=rock-pool',
            'ID_FS_LABEL_ENC=rock-pool', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=429827fc-5ca9-4ca8-b152-f28d8a9d2737',
            'ID_FS_UUID_ENC=429827fc-5ca9-4ca8-b152-f28d8a9d2737',
            'ID_FS_UUID_SUB=21eade9f-1e18-499f-b506-d0b5b575b240',
            'ID_FS_UUID_SUB_ENC=21eade9f-1e18-499f-b506-d0b5b575b240',
            'ID_MODEL=QEMU_HARDDISK',
            'ID_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20',  # noqa E501
            'ID_PATH=pci-0000:00:06.0-ata-3',
            'ID_PATH_TAG=pci-0000_00_06_0-ata-3', 'ID_REVISION=2.5+',
            'ID_SCSI=1', 'ID_SCSI_INQUIRY=1',
            'ID_SERIAL=QEMU_HARDDISK_QM00009',
            'ID_SERIAL_SHORT=QM00009',
            'ID_TYPE=disk', 'ID_VENDOR=ATA',
            'ID_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20', 'MAJOR=8',
            'MINOR=32', 'MPATH_SBIN_PATH=/sbin',
            'SCSI_IDENT_LUN_ATA=QEMU_HARDDISK_QM00009',
            'SCSI_IDENT_LUN_T10=ATA_QEMU_HARDDISK_QM00009',
            'SCSI_IDENT_LUN_VENDOR=QM00009',
            'SCSI_IDENT_SERIAL=QM00009',
            'SCSI_MODEL=QEMU_HARDDISK',
            'SCSI_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20',
            'SCSI_REVISION=2.5+', 'SCSI_TPGS=0', 'SCSI_TYPE=disk',
            'SCSI_VENDOR=ATA',
            'SCSI_VENDOR_ENC=ATA\\x20\\x20\\x20\\x20\\x20',
            'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=3054291',
            ''])
        err.append([''])
        rc.append(0)
        expected_result.append(
            ('/dev/disk/by-id/scsi-SATA_QEMU_HARDDISK_QM00009', True))
        # Query on an openLUKS container (backed by bcache):
        # N.B. legacy versions of get_dev_byid_name() would auto add
        # /dev/mapper if dev name matched 'luks-' this was later removed in
        # favour of generating the full path in scan_disks().
        dev_name.append('/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad')
        remove_path.append(True)
        out.append([
            'DEVLINKS=/dev/disk/by-id/dm-name-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad /dev/disk/by-id/dm-uuid-CRYPT-LUKS1-a47f495032964504b9a42dc75681a6ad-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad /dev/disk/by-label/luks-pool-on-bcache /dev/disk/by-uuid/8ad02be6-fc5f-4342-bdd2-f992e7792a5b /dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad',  # noqa E501
            'DEVNAME=/dev/dm-0', 'DEVPATH=/devices/virtual/block/dm-0',
            'DEVTYPE=disk', 'DM_ACTIVATION=1',
            'DM_NAME=luks-a47f4950-3296-4504-b9a4-2dc75681a6ad',
            'DM_SUSPENDED=0', 'DM_UDEV_PRIMARY_SOURCE_FLAG=1',
            'DM_UDEV_RULES_VSN=2',
            'DM_UUID=CRYPT-LUKS1-a47f495032964504b9a42dc75681a6ad-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad',  # noqa E501
            'ID_FS_LABEL=luks-pool-on-bcache',
            'ID_FS_LABEL_ENC=luks-pool-on-bcache', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=8ad02be6-fc5f-4342-bdd2-f992e7792a5b',
            'ID_FS_UUID_ENC=8ad02be6-fc5f-4342-bdd2-f992e7792a5b',
            'ID_FS_UUID_SUB=70648d6c-be07-42ee-88ff-0e9c68a5415c',
            'ID_FS_UUID_SUB_ENC=70648d6c-be07-42ee-88ff-0e9c68a5415c',
            'MAJOR=251', 'MINOR=0', 'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=10617229', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(
            ('dm-name-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad', True))
        # Query on a bcache backing device, this assumes the udev rules as
        # detailed in forum wiki entry:
        # https://forum.rockstor.com/t/bcache-developers-notes/2762
        dev_name.append('bcache0')
        remove_path.append(True)
        out.append([
            'DEVLINKS=/dev/disk/by-id/bcache-QEMU_HARDDISK-bcache-bdev-1 /dev/disk/by-uuid/3efb3830-fee1-4a9e-a5c6-ea456bfc269e',  # noqa E501
            'DEVNAME=/dev/bcache0', 'DEVPATH=/devices/virtual/block/bcache0',
            'DEVTYPE=disk',
            'ID_BCACHE_BDEV_FS_UUID=c9ed805f-b141-4ce9-80c7-9f9e1f71195d',
            'ID_BCACHE_BDEV_MODEL=QEMU_HARDDISK',
            'ID_BCACHE_BDEV_SERIAL=bcache-bdev-1',
            'ID_BCACHE_CSET_UUID=16657e0a-a7e0-48bc-9a69-433c0f2cd920',
            'ID_FS_TYPE=crypto_LUKS', 'ID_FS_USAGE=crypto',
            'ID_FS_UUID=3efb3830-fee1-4a9e-a5c6-ea456bfc269e',
            'ID_FS_UUID_ENC=3efb3830-fee1-4a9e-a5c6-ea456bfc269e',
            'ID_FS_VERSION=1',
            'ID_SERIAL=bcache-c9ed805f-b141-4ce9-80c7-9f9e1f71195d',
            'MAJOR=252', 'MINOR=0', 'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=76148', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(('bcache-QEMU_HARDDISK-bcache-bdev-1', True))
        # regular virtio device hosting a LUKS container:
        dev_name.append('vdb')
        remove_path.append(True)
        out.append([
            'DEVLINKS=/dev/disk/by-id/virtio-serial-5 /dev/disk/by-path/virtio-pci-0000:00:0d.0 /dev/disk/by-uuid/41cd2e3c-3bd6-49fc-9f42-20e368a66efc',  # noqa E501
            'DEVNAME=/dev/vdb',
            'DEVPATH=/devices/pci0000:00/0000:00:0d.0/virtio4/block/vdb',
            'DEVTYPE=disk', 'ID_FS_TYPE=crypto_LUKS', 'ID_FS_USAGE=crypto',
            'ID_FS_UUID=41cd2e3c-3bd6-49fc-9f42-20e368a66efc',
            'ID_FS_UUID_ENC=41cd2e3c-3bd6-49fc-9f42-20e368a66efc',
            'ID_FS_VERSION=1', 'ID_PATH=virtio-pci-0000:00:0d.0',
            'ID_PATH_TAG=virtio-pci-0000_00_0d_0', 'ID_SERIAL=serial-5',
            'MAJOR=253', 'MINOR=16', 'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=4469', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(('virtio-serial-5', True))
        # legacy root drive (with serial "sys-drive-serial-number")
        dev_name.append('sda3')
        remove_path.append(True)
        out.append([
            'DEVLINKS=/dev/disk/by-id/ata-QEMU_HARDDISK_sys-drive-serial-num-part3 /dev/disk/by-label/rockstor_rockstor /dev/disk/by-path/pci-0000:00:05.0-ata-1.0-part3 /dev/disk/by-uuid/a98f88c2-2031-4bd3-9124-2f9d8a77987c',  # noqa E501
            'DEVNAME=/dev/sda3',
            'DEVPATH=/devices/pci0000:00/0000:00:05.0/ata3/host2/target2:0:0/2:0:0:0/block/sda/sda3',  # noqa E501
            'DEVTYPE=partition', 'ID_ATA=1', 'ID_ATA_FEATURE_SET_SMART=1',
            'ID_ATA_FEATURE_SET_SMART_ENABLED=1', 'ID_ATA_SATA=1',
            'ID_ATA_WRITE_CACHE=1', 'ID_ATA_WRITE_CACHE_ENABLED=1',
            'ID_BUS=ata', 'ID_FS_LABEL=rockstor_rockstor',
            'ID_FS_LABEL_ENC=rockstor_rockstor', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=a98f88c2-2031-4bd3-9124-2f9d8a77987c',
            'ID_FS_UUID_ENC=a98f88c2-2031-4bd3-9124-2f9d8a77987c',
            'ID_FS_UUID_SUB=81b9232f-0981-4753-ab0c-1a686b6ad3a9',
            'ID_FS_UUID_SUB_ENC=81b9232f-0981-4753-ab0c-1a686b6ad3a9',
            'ID_MODEL=QEMU_HARDDISK',
            'ID_MODEL_ENC=QEMU\\x20HARDDISK\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20\\x20',  # noqa E501
            'ID_PART_ENTRY_DISK=8:0', 'ID_PART_ENTRY_NUMBER=3',
            'ID_PART_ENTRY_OFFSET=2705408', 'ID_PART_ENTRY_SCHEME=dos',
            'ID_PART_ENTRY_SIZE=14071808', 'ID_PART_ENTRY_TYPE=0x83',
            'ID_PART_TABLE_TYPE=dos', 'ID_PATH=pci-0000:00:05.0-ata-1.0',
            'ID_PATH_TAG=pci-0000_00_05_0-ata-1_0', 'ID_REVISION=2.4.0',
            'ID_SERIAL=QEMU_HARDDISK_sys-drive-serial-num',
            'ID_SERIAL_SHORT=sys-drive-serial-num', 'ID_TYPE=disk', 'MAJOR=8',
            'MINOR=3', 'PARTN=3', 'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=81921', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(
            ('ata-QEMU_HARDDISK_sys-drive-serial-num-part3', True))
        # above legacy root device via virtio interface with no serial and so
        # no by-id name.
        dev_name.append('vda3')
        remove_path.append(True)
        out.append([
            'DEVLINKS=/dev/disk/by-label/rockstor_rockstor /dev/disk/by-path/virtio-pci-0000:00:09.0-part3 /dev/disk/by-uuid/a98f88c2-2031-4bd3-9124-2f9d8a77987c',  # noqa E501
            'DEVNAME=/dev/vda3',
            'DEVPATH=/devices/pci0000:00/0000:00:09.0/virtio3/block/vda/vda3',
            'DEVTYPE=partition', 'ID_FS_LABEL=rockstor_rockstor',
            'ID_FS_LABEL_ENC=rockstor_rockstor', 'ID_FS_TYPE=btrfs',
            'ID_FS_USAGE=filesystem',
            'ID_FS_UUID=a98f88c2-2031-4bd3-9124-2f9d8a77987c',
            'ID_FS_UUID_ENC=a98f88c2-2031-4bd3-9124-2f9d8a77987c',
            'ID_FS_UUID_SUB=81b9232f-0981-4753-ab0c-1a686b6ad3a9',
            'ID_FS_UUID_SUB_ENC=81b9232f-0981-4753-ab0c-1a686b6ad3a9',
            'ID_PART_ENTRY_DISK=253:0', 'ID_PART_ENTRY_NUMBER=3',
            'ID_PART_ENTRY_OFFSET=2705408', 'ID_PART_ENTRY_SCHEME=dos',
            'ID_PART_ENTRY_SIZE=14071808', 'ID_PART_ENTRY_TYPE=0x83',
            'ID_PART_TABLE_TYPE=dos', 'ID_PATH=virtio-pci-0000:00:09.0',
            'ID_PATH_TAG=virtio-pci-0000_00_09_0', 'MAJOR=253', 'MINOR=3',
            'PARTN=3', 'SUBSYSTEM=block', 'TAGS=:systemd:',
            'USEC_INITIALIZED=2699', ''])
        err.append([''])
        rc.append(0)
        expected_result.append(('vda3', False))
        # Cycle through each of the above parameter / run_command data sets.
        for dev, rp, o, e, r, expected in zip(dev_name, remove_path, out, err,
                                              rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            returned = get_dev_byid_name(dev, rp)
            self.assertEqual(returned, expected,
                             msg='Un-expected get_dev_byid_name() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))

    def test_get_dev_byid_name_node_not_found(self):
        """
        test get_dev_byid_name when supplied dev name not found
        This could happen if a device was live unplugged and udev removed it's
        /dev entries just prior to get_dev_byid_name()'s execution.
        Exercises error log of this event.
        """
        dev_name = '/dev/bogus'
        remove_path = True
        o = ['']
        e = ['device node not found', '']
        r = 2
        expected = ('bogus', False)
        self.mock_run_command.return_value = (o, e, r)
        returned = get_dev_byid_name(dev_name, remove_path)
        self.assertEqual(returned, expected,
                         msg='Un-expected get_dev_byid_name() result:\n '
                             'returned = ({}).\n '
                             'expected = ({}).'.format(returned, expected))

    def test_get_dev_byid_name_no_devlinks(self):
        """
        Test as yet un-observed circumstance of no DEVLINKS entry for:
        get_dev_byid_name(): exercises debug log of same.
        """
        dev_name = '/dev/arbitrary'
        remove_path = True
        o = ['']  # no entries of any kind
        e = ['']
        r = 0
        expected = ('arbitrary', False)
        self.mock_run_command.return_value = (o, e, r)
        returned = get_dev_byid_name(dev_name, remove_path)
        self.assertEqual(returned, expected,
                         msg='Un-expected get_dev_byid_name() result:\n '
                             'returned = ({}).\n '
                             'expected = ({}).'.format(returned, expected))

    def test_scan_disks_luks_on_bcache(self):
        """
        Test scan_disks() across a variety of mocked lsblk output.
        """
        # collection of ata, virtio driven devices with bcache (cache and
        # backing) device formats as well as a number of LUKS containers on
        # bcache backing devices and an example of LUKS on virtio dev directly.
        # Moc output for run_command with:
        # lsblk -P -o NAME,MODEL,SERIAL,SIZE,TRAN,VENDOR,HCTL,TYPE,FSTYPE,LABEL,UUID  # noqa E501
        out = [[
            'NAME="/dev/sdd" MODEL="QEMU HARDDISK   " SERIAL="bcache-cdev" SIZE="2G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="bcache" LABEL="" UUID="6efd5476-77a9-4f57-97a5-fa1a37d4338b"',  # noqa E501
            'NAME="/dev/bcache0" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="disk" FSTYPE="crypto_LUKS" LABEL="" UUID="3efb3830-fee1-4a9e-a5c6-ea456bfc269e"',  # noqa E501
            'NAME="/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="pool-on-mixed-luks" UUID="1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded"',  # noqa E501
            'NAME="/dev/bcache16" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="disk" FSTYPE="crypto_LUKS" LABEL="" UUID="a47f4950-3296-4504-b9a4-2dc75681a6ad"',  # noqa E501
            'NAME="/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="pool-on-mixed-luks" UUID="1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded"',  # noqa E501
            'NAME="/dev/sdb" MODEL="QEMU HARDDISK   " SERIAL="bcache-bdev-1" SIZE="2G" TRAN="sata" VENDOR="ATA     " HCTL="1:0:0:0" TYPE="disk" FSTYPE="bcache" LABEL="" UUID="c9ed805f-b141-4ce9-80c7-9f9e1f71195d"',  # noqa E501
            'NAME="/dev/bcache0" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="disk" FSTYPE="crypto_LUKS" LABEL="" UUID="3efb3830-fee1-4a9e-a5c6-ea456bfc269e"',  # noqa E501
            'NAME="/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="pool-on-mixed-luks" UUID="1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded"',  # noqa E501
            'NAME="/dev/vdb" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="0x1af4" HCTL="" TYPE="disk" FSTYPE="crypto_LUKS" LABEL="" UUID="41cd2e3c-3bd6-49fc-9f42-20e368a66efc"',  # noqa E501
            'NAME="/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="pool-on-mixed-luks" UUID="1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded"',  # noqa E501
            'NAME="/dev/sr0" MODEL="QEMU DVD-ROM    " SERIAL="QM00001" SIZE="1024M" TRAN="ata" VENDOR="QEMU    " HCTL="6:0:0:0" TYPE="rom" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdc" MODEL="QEMU HARDDISK   " SERIAL="bcache-bdev-2" SIZE="2G" TRAN="sata" VENDOR="ATA     " HCTL="2:0:0:0" TYPE="disk" FSTYPE="bcache" LABEL="" UUID="06754c95-4f78-4ffb-a243-5c85144d1833"',  # noqa E501
            'NAME="/dev/bcache16" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="disk" FSTYPE="crypto_LUKS" LABEL="" UUID="a47f4950-3296-4504-b9a4-2dc75681a6ad"',  # noqa E501
            'NAME="/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="pool-on-mixed-luks" UUID="1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded"',  # noqa E501
            'NAME="/dev/sda" MODEL="QEMU HARDDISK   " SERIAL="sys-drive-serial-num" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="0:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="820M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="c25eec5f-d4bd-4670-b756-e8b687562f6e"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="6.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="a98f88c2-2031-4bd3-9124-2f9d8a77987c"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="6b8e342c-6cd6-40e8-a134-db302fad3f20"',  # noqa E501
            'NAME="/dev/vda" MODEL="" SERIAL="" SIZE="3G" TRAN="" VENDOR="0x1af4" HCTL="" TYPE="disk" FSTYPE="btrfs" LABEL="rock-pool" UUID="d7e5987d-9428-4b4a-9abb-f3d564e4c467"',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/vda', model=None, serial='serial-6', size=3145728,
                 transport=None, vendor='0x1af4', hctl=None, type='disk',
                 fstype='btrfs', label='rock-pool',
                 uuid='d7e5987d-9428-4b4a-9abb-f3d564e4c467', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/bcache0', model=None,
                 serial='bcache-c9ed805f-b141-4ce9-80c7-9f9e1f71195d',
                 size=2097152, transport=None,
                 vendor=None, hctl=None,
                 type='disk',
                 fstype='crypto_LUKS', label=None,
                 uuid='3efb3830-fee1-4a9e-a5c6-ea456bfc269e',
                 parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad', model=None,  # noqa E501
                 serial='CRYPT-LUKS1-a47f495032964504b9a42dc75681a6ad-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad',  # noqa E501
                 size=2097152, transport=None, vendor=None, hctl=None,
                 type='crypt', fstype='btrfs', label='pool-on-mixed-luks',
                 uuid='1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdd', model='QEMU HARDDISK', serial='bcache-cdev',
                 size=2097152, transport='sata', vendor='ATA', hctl='3:0:0:0',
                 type='disk', fstype='bcachecdev', label=None,
                 uuid='6efd5476-77a9-4f57-97a5-fa1a37d4338b', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/bcache16', model=None,
                 serial='bcache-06754c95-4f78-4ffb-a243-5c85144d1833',
                 size=2097152, transport=None,
                 vendor=None, hctl=None,
                 type='disk',
                 fstype='crypto_LUKS', label=None,
                 uuid='a47f4950-3296-4504-b9a4-2dc75681a6ad',
                 parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e', model=None,  # noqa E501
                 serial='CRYPT-LUKS1-3efb3830fee14a9ea5c6ea456bfc269e-luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e',  # noqa E501
                 size=2097152, transport=None, vendor=None, hctl=None,
                 type='crypt', fstype='btrfs', label='pool-on-mixed-luks',
                 uuid='1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/vdb', model=None, serial='serial-5', size=2097152,
                 transport=None, vendor='0x1af4', hctl=None, type='disk',
                 fstype='crypto_LUKS', label=None,
                 uuid='41cd2e3c-3bd6-49fc-9f42-20e368a66efc', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sda3', model='QEMU HARDDISK',
                 serial='sys-drive-serial-num',
                 size=7025459, transport='sata', vendor='ATA', hctl='0:0:0:0',
                 type='part', fstype='btrfs', label='rockstor_rockstor',
                 uuid='a98f88c2-2031-4bd3-9124-2f9d8a77987c', parted=True,
                 root=True, partitions={}),
            Disk(name='/dev/sdb', model='QEMU HARDDISK', serial='bcache-bdev-1',  # noqa E501
                 size=2097152, transport='sata', vendor='ATA', hctl='1:0:0:0',
                 type='disk', fstype='bcache', label=None,
                 uuid='c9ed805f-b141-4ce9-80c7-9f9e1f71195d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdc', model='QEMU HARDDISK', serial='bcache-bdev-2',  # noqa E501
                 size=2097152, transport='sata', vendor='ATA', hctl='2:0:0:0',
                 type='disk', fstype='bcache', label=None,
                 uuid='06754c95-4f78-4ffb-a243-5c85144d1833', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc', model=None,  # noqa E501
                 serial='CRYPT-LUKS1-41cd2e3c3bd649fc9f4220e368a66efc-luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc',  # noqa E501
                 size=2097152, transport=None, vendor=None, hctl=None,
                 type='crypt', fstype='btrfs', label='pool-on-mixed-luks',
                 uuid='1fdd4b41-fdd0-40c4-8ae6-7d6309b09ded', parted=False,
                 root=False, partitions={})]]

        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            s_map = {
                '/dev/bcache0': 'bcache-c9ed805f-b141-4ce9-80c7-9f9e1f71195d',
                '/dev/bcache16': 'bcache-06754c95-4f78-4ffb-a243-5c85144d1833',
                '/dev/mapper/luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e': 'CRYPT-LUKS1-3efb3830fee14a9ea5c6ea456bfc269e-luks-3efb3830-fee1-4a9e-a5c6-ea456bfc269e',  # noqa E501
                '/dev/mapper/luks-a47f4950-3296-4504-b9a4-2dc75681a6ad': 'CRYPT-LUKS1-a47f495032964504b9a42dc75681a6ad-luks-a47f4950-3296-4504-b9a4-2dc75681a6ad',  # noqa E501
                '/dev/mapper/luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc': 'CRYPT-LUKS1-41cd2e3c3bd649fc9f4220e368a66efc-luks-41cd2e3c-3bd6-49fc-9f42-20e368a66efc',  # noqa E501
                '/dev/vdb': 'serial-5',
                '/dev/vda': 'serial-6'
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return

        # Establish dynamic mock behaviour for get_bcache_device_type().
        self.patch_dyn_get_bc_dev_type = patch('system.osi.get_bcache_device_type')  # noqa E501
        self.mock_dyn_get_bc_dev_type = self.patch_dyn_get_bc_dev_type.start()

        def dyn_bcache_device_type(*args, **kwargs):
            bc_dev_map = {
                '/dev/sdd': 'cdev',
                '/dev/sdb': 'bdev',
                '/dev/sdc': 'bdev'
            }
            if args[0] in bc_dev_map:
                return bc_dev_map[args[0]]
            else:
                return None
        self.mock_dyn_get_bc_dev_type.side_effect = dyn_bcache_device_type

        # Iterate the test data sets for run_command running lsblk.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576)
            returned.sort(key=operator.itemgetter(0))
            self.assertEqual(returned, expected,
                             msg='Un-expected scan_disks() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))

    def test_scan_disks_dell_perk_h710_md1220_36_disks(self):

        """
        Test scan_disks() with Direct attach storage shelf (Dell MD1220).
        Test data summarized from forum member kingwavy's submission in the
        following forum thread:
        https://forum.rockstor.com/t/disk-scan-errors-expected-string-or-buffer/4783
        Issue was multiple sda[a-z] devices were also labeled as root=True due
        to a naive match to actual base system drive sda ('/' on sda3) which in
        turn resulted in serial=None and or fake-serial when all devices had
        accessible serial via lsblk output.
        """
        # system as 36 disks sda-sdz (sda as partitioned sys disk) + sdaa-sdaj
        # N.B. listed in the order returned by lsblk.
        # All base device (ie sda of sda3) have lsblk accessible serials.
        out = [[
            'NAME="/dev/sdy" MODEL="HUC101212CSS600 " SERIAL="5000cca01d2766c0" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:11:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdf" MODEL="PERC H710 " SERIAL="6848f690e936450021a4585b05e46fcc" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:5:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sdab" MODEL="ST91000640SS  " SERIAL="5000c50063041947" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:14:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdo" MODEL="HUC101212CSS600 " SERIAL="5000cca01d21bc10" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:1:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdw" MODEL="ST91000640SS  " SERIAL="5000c500630450a3" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:9:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdd" MODEL="PERC H710 " SERIAL="6848f690e9364500219f33b21773ea22" SIZE="558.4G" TRAN="" VENDOR="DELL  " HCTL="0:2:3:0" TYPE="disk" FSTYPE="btrfs" LABEL="Test" UUID="612f1fc2-dfa8-4940-a1ad-e11c893b32ca"',  # noqa E501
            'NAME="/dev/sdm" MODEL="PERC H710 " SERIAL="6848f690e936450021acd1f30663b877" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:12:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sdu" MODEL="HUC101212CSS600 " SERIAL="5000cca01d273a24" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:7:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdai" MODEL="ST91000640SS  " SERIAL="5000c5006303ea0f" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:21:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdb" MODEL="PERC H710 " SERIAL="6848f690e9364500219f339b1610b547" SIZE="558.4G" TRAN="" VENDOR="DELL  " HCTL="0:2:1:0" TYPE="disk" FSTYPE="btrfs" LABEL="Test" UUID="612f1fc2-dfa8-4940-a1ad-e11c893b32ca"',  # noqa E501
            'NAME="/dev/sdk" MODEL="PERC H710 " SERIAL="6848f690e936450021acd1e705b389c6" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:10:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sds" MODEL="HUC101212CSS600 " SERIAL="5000cca01d217968" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:5:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdag" MODEL="ST91000640SS  " SERIAL="5000c50062cbc1f3" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:19:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdi" MODEL="PERC H710 " SERIAL="6848f690e936450021a4586906bd9742" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:8:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sdq" MODEL="HUC101212CSS600 " SERIAL="5000cca01d29f384" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:3:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdae" MODEL="INTEL SSDSC2KW24" SERIAL="CVLT6153072G240CGN" SIZE="223.6G" TRAN="sas" VENDOR="ATA " HCTL="1:0:17:0" TYPE="disk" FSTYPE="btrfs" LABEL="INTEL_SSD" UUID="a504bf03-0299-4648-8a95-c91aba291de8"',  # noqa E501
            'NAME="/dev/sdz" MODEL="ST91000640SS  " SERIAL="5000c5006304544b" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:12:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdg" MODEL="PERC H710 " SERIAL="6848f690e936450021ed61830ae57fbf" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:6:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sdac" MODEL="ST91000640SS  " SERIAL="5000c500630249cb" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:15:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdx" MODEL="ST91000640SS  " SERIAL="5000c50063044387" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:10:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sde" MODEL="PERC H710 " SERIAL="6848f690e9364500219f33bb17fe7d7b" SIZE="558.4G" TRAN="" VENDOR="DELL  " HCTL="0:2:4:0" TYPE="disk" FSTYPE="btrfs" LABEL="Test" UUID="612f1fc2-dfa8-4940-a1ad-e11c893b32ca"',  # noqa E501
            'NAME="/dev/sdaa" MODEL="ST91000640SS  " SERIAL="5000c50063044363" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:13:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdn" MODEL="HUC101212CSS600 " SERIAL="5000cca01d2144ac" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:0:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdv" MODEL="HUC101212CSS600 " SERIAL="5000cca01d21893c" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:8:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdaj" MODEL="INTEL SSDSC2KW24" SERIAL="CVLT6181019S240CGN" SIZE="223.6G" TRAN="sas" VENDOR="ATA " HCTL="1:0:22:0" TYPE="disk" FSTYPE="btrfs" LABEL="INTEL_SSD" UUID="a504bf03-0299-4648-8a95-c91aba291de8"',  # noqa E501
            'NAME="/dev/sdc" MODEL="PERC H710 " SERIAL="6848f690e936450021ed614a077c1b44" SIZE="7.3T" TRAN="" VENDOR="DELL  " HCTL="0:2:2:0" TYPE="disk" FSTYPE="btrfs" LABEL="BIGDATA" UUID="cb15142f-9d1e-4cb2-9b1f-adda3af6555f"',  # noqa E501
            'NAME="/dev/sdl" MODEL="PERC H710 " SERIAL="6848f690e936450021a4525005828671" SIZE="4.6T" TRAN="" VENDOR="DELL  " HCTL="0:2:11:0" TYPE="disk" FSTYPE="btrfs" LABEL="5TBWDGREEN" UUID="a37956a8-a175-4906-82c1-bf843132da1a"',  # noqa E501
            'NAME="/dev/sdt" MODEL="HUC101212CSS600 " SERIAL="5000cca01d2af91c" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:6:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdah" MODEL="ST91000640SS  " SERIAL="5000c50062cb366f" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:20:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sda" MODEL="PERC H710 " SERIAL="6848f690e936450018b7c3a11330997b" SIZE="278.9G" TRAN="" VENDOR="DELL  " HCTL="0:2:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="13.8G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="a34b82d0-c342-41e0-a58d-4f0a0027829d"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="264.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="7f7acdd7-493e-4bb5-b801-b7b7dc289535"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="5d2848ff-ae8f-4c2f-b825-90621076acc1"',  # noqa E501
            'NAME="/dev/sdj" MODEL="PERC H710 " SERIAL="6848f690e936450021a45f9904046a2f" SIZE="2.7T" TRAN="" VENDOR="DELL  " HCTL="0:2:9:0" TYPE="disk" FSTYPE="btrfs" LABEL="VMWARE_MECH_ARRAY" UUID="e6d13c0b-825f-4b43-81b6-7eb2b791b1c3"',  # noqa E501
            'NAME="/dev/sdr" MODEL="HUC101212CSS600 " SERIAL="5000cca01d2188e0" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:4:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdaf" MODEL="ST91000640SS  " SERIAL="5000c500630425df" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:18:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdh" MODEL="PERC H710 " SERIAL="6848f690e9364500219f33d919c7488a" SIZE="558.4G" TRAN="" VENDOR="DELL  " HCTL="0:2:7:0" TYPE="disk" FSTYPE="btrfs" LABEL="Test" UUID="612f1fc2-dfa8-4940-a1ad-e11c893b32ca"',  # noqa E501
            'NAME="/dev/sdp" MODEL="HUC101212CSS600 " SERIAL="5000cca01d21885c" SIZE="1.1T" TRAN="sas" VENDOR="HGST  " HCTL="1:0:2:0" TYPE="disk" FSTYPE="btrfs" LABEL="MD1220-DAS" UUID="12d76eb6-7aad-46ba-863e-d9c51e8e6f2d"',  # noqa E501
            'NAME="/dev/sdad" MODEL="INTEL SSDSC2KW24" SERIAL="CVLT618101SE240CGN" SIZE="223.6G" TRAN="sas" VENDOR="ATA " HCTL="1:0:16:0" TYPE="disk" FSTYPE="btrfs" LABEL="INTEL_SSD" UUID="a504bf03-0299-4648-8a95-c91aba291de8"',  # noqa E501
            ''
        ]]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/sda3', model='PERC H710',
                 serial='6848f690e936450018b7c3a11330997b', size=277558067,
                 transport=None, vendor='DELL', hctl='0:2:0:0', type='part',
                 fstype='btrfs', label='rockstor_rockstor',
                 uuid='7f7acdd7-493e-4bb5-b801-b7b7dc289535', parted=True,
                 root=True, partitions={}),
            Disk(name='/dev/sdt', model='HUC101212CSS600',
                 serial='5000cca01d2af91c',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:6:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdu', model='HUC101212CSS600',
                 serial='5000cca01d273a24',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:7:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdv', model='HUC101212CSS600',
                 serial='5000cca01d21893c',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:8:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdw', model='ST91000640SS', serial='5000c500630450a3',  # noqa E501
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:9:0',
                 type='disk', fstype='btrfs', label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdp', model='HUC101212CSS600',
                 serial='5000cca01d21885c',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:2:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdq', model='HUC101212CSS600',
                 serial='5000cca01d29f384',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:3:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdr', model='HUC101212CSS600',
                 serial='5000cca01d2188e0',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:4:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sds', model='HUC101212CSS600',
                 serial='5000cca01d217968',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:5:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdx', model='ST91000640SS', serial='5000c50063044387',  # noqa E501
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:10:0', type='disk', fstype='btrfs', label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdy', model='HUC101212CSS600',
                 serial='5000cca01d2766c0',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:11:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdz', model='ST91000640SS', serial='5000c5006304544b',  # noqa E501
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:12:0', type='disk', fstype='btrfs', label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdd', model='PERC H710',
                 serial='6848f690e9364500219f33b21773ea22', size=585524838,
                 transport=None, vendor='DELL', hctl='0:2:3:0', type='disk',
                 fstype='btrfs', label='Test',
                 uuid='612f1fc2-dfa8-4940-a1ad-e11c893b32ca', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sde', model='PERC H710',
                 serial='6848f690e9364500219f33bb17fe7d7b', size=585524838,
                 transport=None, vendor='DELL', hctl='0:2:4:0', type='disk',
                 fstype='btrfs', label='Test',
                 uuid='612f1fc2-dfa8-4940-a1ad-e11c893b32ca', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdf', model='PERC H710',
                 serial='6848f690e936450021a4585b05e46fcc', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:5:0', type='disk',
                 fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdg', model='PERC H710',
                 serial='6848f690e936450021ed61830ae57fbf', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:6:0', type='disk',
                 fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdb', model='PERC H710',
                 serial='6848f690e9364500219f339b1610b547', size=585524838,
                 transport=None, vendor='DELL', hctl='0:2:1:0', type='disk',
                 fstype='btrfs', label='Test',
                 uuid='612f1fc2-dfa8-4940-a1ad-e11c893b32ca', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdc', model='PERC H710',
                 serial='6848f690e936450021ed614a077c1b44', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:2:0', type='disk',
                 fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdl', model='PERC H710',
                 serial='6848f690e936450021a4525005828671', size=4939212390,
                 transport=None, vendor='DELL', hctl='0:2:11:0',
                 type='disk', fstype='btrfs', label='5TBWDGREEN',
                 uuid='a37956a8-a175-4906-82c1-bf843132da1a', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdm', model='PERC H710',
                 serial='6848f690e936450021acd1f30663b877', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:12:0',
                 type='disk', fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdn', model='HUC101212CSS600',
                 serial='5000cca01d2144ac',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:0:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdo', model='HUC101212CSS600',
                 serial='5000cca01d21bc10',
                 size=1181116006, transport='sas', vendor='HGST',
                 hctl='1:0:1:0',
                 type='disk', fstype='btrfs', label='MD1220-DAS',
                 uuid='12d76eb6-7aad-46ba-863e-d9c51e8e6f2d', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdh', model='PERC H710',
                 serial='6848f690e9364500219f33d919c7488a', size=585524838,
                 transport=None, vendor='DELL', hctl='0:2:7:0', type='disk',
                 fstype='btrfs', label='Test',
                 uuid='612f1fc2-dfa8-4940-a1ad-e11c893b32ca', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdi', model='PERC H710',
                 serial='6848f690e936450021a4586906bd9742', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:8:0', type='disk',
                 fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdj', model='PERC H710',
                 serial='6848f690e936450021a45f9904046a2f', size=2899102924,
                 transport=None, vendor='DELL', hctl='0:2:9:0', type='disk',
                 fstype='btrfs', label='VMWARE_MECH_ARRAY',
                 uuid='e6d13c0b-825f-4b43-81b6-7eb2b791b1c3', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdk', model='PERC H710',
                 serial='6848f690e936450021acd1e705b389c6', size=7838315315,
                 transport=None, vendor='DELL', hctl='0:2:10:0',
                 type='disk', fstype='btrfs', label='BIGDATA',
                 uuid='cb15142f-9d1e-4cb2-9b1f-adda3af6555f', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdaf', model='ST91000640SS',
                 serial='5000c500630425df',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:18:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdag', model='ST91000640SS',
                 serial='5000c50062cbc1f3',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:19:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdad', model='INTEL SSDSC2KW24',
                 serial='CVLT618101SE240CGN',
                 size=234461593, transport='sas', vendor='ATA',
                 hctl='1:0:16:0', type='disk', fstype='btrfs',
                 label='INTEL_SSD',
                 uuid='a504bf03-0299-4648-8a95-c91aba291de8', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdae', model='INTEL SSDSC2KW24',
                 serial='CVLT6153072G240CGN',
                 size=234461593, transport='sas', vendor='ATA',
                 hctl='1:0:17:0',
                 type='disk', fstype='btrfs', label='INTEL_SSD',
                 uuid='a504bf03-0299-4648-8a95-c91aba291de8', parted=False,
                 root=False, partitions={}),
            # N.B. we have sdab with serial=None, suspected due to first listed
            # matching base root device name of sda (sda3).
            Disk(name='/dev/sdab', model='ST91000640SS',
                 serial='5000c50063041947',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:14:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdac', model='ST91000640SS',
                 serial='5000c500630249cb',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:15:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdaa', model='ST91000640SS',
                 serial='5000c50063044363',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:13:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdaj', model='INTEL SSDSC2KW24',
                 serial='CVLT6181019S240CGN',
                 size=234461593, transport='sas', vendor='ATA',
                 hctl='1:0:22:0', type='disk', fstype='btrfs',
                 label='INTEL_SSD',
                 uuid='a504bf03-0299-4648-8a95-c91aba291de8', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdah', model='ST91000640SS',
                 serial='5000c50062cb366f',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:20:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdai', model='ST91000640SS',
                 serial='5000c5006303ea0f',
                 size=976748544, transport='sas', vendor='SEAGATE',
                 hctl='1:0:21:0', type='disk', fstype='btrfs',
                 label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=False, partitions={})
        ]]
        # As all serials are available via the lsblk we can avoid mocking
        # get_device_serial()
        # And given no bcache we can also avoid mocking
        # get_bcache_device_type()
        # Iterate the test data sets for run_command running lsblk.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            returned = scan_disks(1048576, test_mode=True)
            # TODO: Would be nice to have differences found shown.
            #
            expected.sort(key=operator.itemgetter(0))
            returned.sort(key=operator.itemgetter(0))
            self.assertEqual(returned, expected,
                             msg='Un-expected scan_disks() result:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned, expected))

    def test_scan_disks_27_plus_disks_regression_issue(self):
        """
        Suspected minimum disk set to trigger /dev/sda /dev/sda[a-z] serial bug
        when base root disk is /dev/sda ('/' on sda3):
        first listed sda[a-z] dev (sdab in below) gets serial = None
        second and subsequent listed sda[a-z] devs get serial = 'fake-serial-'

        Note also that in addition to the above;
        model, transport, vendor, and hctl
        info are lost or inherited from sda for all sda[a-z] devices.
        All are also labeled incorrectly as
        root=True:
        the root cause of this bug, see issue #1925.
        N.B. an element of the trigger data is FSTYPE="btrfs" on the sda[a-z]
        devices: without this the issue does not present.
        """
        out = [[
            'NAME="/dev/sdab" MODEL="ST91000640SS  " SERIAL="5000c50063041947" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:14:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sdai" MODEL="ST91000640SS  " SERIAL="5000c5006303ea0f" SIZE="931.5G" TRAN="sas" VENDOR="SEAGATE " HCTL="1:0:21:0" TYPE="disk" FSTYPE="btrfs" LABEL="SCRATCH" UUID="a90e6787-1c45-46d6-a2ba-41017a17c1d5"',  # noqa E501
            'NAME="/dev/sda" MODEL="PERC H710 " SERIAL="6848f690e936450018b7c3a11330997b" SIZE="278.9G" TRAN="" VENDOR="DELL  " HCTL="0:2:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="13.8G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="a34b82d0-c342-41e0-a58d-4f0a0027829d"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="264.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="7f7acdd7-493e-4bb5-b801-b7b7dc289535"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="5d2848ff-ae8f-4c2f-b825-90621076acc1"',  # noqa E501
            ''
        ]]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/sda3', model='PERC H710',
                 serial='6848f690e936450018b7c3a11330997b', size=277558067,
                 transport=None, vendor='DELL', hctl='0:2:0:0', type='part',
                 fstype='btrfs', label='rockstor_rockstor',
                 uuid='7f7acdd7-493e-4bb5-b801-b7b7dc289535', parted=True,
                 root=True, partitions={}),
            # N.B. we have sdab with serial=None, suspected due to first listed
            # matching base root device name of sda (sda3).
            Disk(name='/dev/sdab', model=None, serial=None, size=976748544,
                 transport=None, vendor=None, hctl=None, type='disk',
                 fstype='btrfs', label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=True, partitions={}),
            # Subsequent sda[a-z] device receives 'fake-serial-'
            Disk(name='/dev/sdai', model=None,
                 serial='fake-serial-',
                 size=976748544, transport=None, vendor=None, hctl=None,
                 type='disk', fstype='btrfs', label='SCRATCH',
                 uuid='a90e6787-1c45-46d6-a2ba-41017a17c1d5', parted=False,
                 root=True, partitions={})
        ]]
        # As all serials are available via the lsblk we can avoid mocking
        # get_device_serial()
        # And given no bcache we can also avoid mocking
        # get_bcache_device_type()
        # Iterate the test data sets for run_command running lsblk.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertNotEqual(returned, expected,
                                msg='Regression in sda[a-z] device:\n '
                                    'returned = ({}).\n '
                                    'expected = ({}).'.format(returned,
                                                              expected))

    def test_scan_disks_luks_sys_disk(self):
        """
        Test to ensure scan_disks() correctly identifies the CentOS, default
        encrypted system disk install "Encrypt this disk" installer setting
        which results in 2 luks volumes, one for swap and one for the btrfs
        volume; usually on sdX3. /boot (ie sdc1) is not encrypted.
        """
        # Example data for sdc system disk with 2 data disks. sdc has the 2
        # luks containers created by the installer.
        # Rockstor sees this install as system on hole disk dev (open luks dev)
        # ie the system btrfs volume is on whole disk not within a partition.
        out = [[
            'NAME="/dev/sdb" MODEL="QEMU HARDDISK   " SERIAL="2" SIZE="5G" TRAN="sata" VENDOR="ATA     " HCTL="5:0:0:0" TYPE="disk" FSTYPE="btrfs" LABEL="rock-pool" UUID="50b66542-9a19-4403-b5a0-cd22412d9ae9"',  # noqa E501
            'NAME="/dev/sr0" MODEL="QEMU DVD-ROM    " SERIAL="QM00005" SIZE="1024M" TRAN="sata" VENDOR="QEMU    " HCTL="2:0:0:0" TYPE="rom" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdc" MODEL="QEMU HARDDISK   " SERIAL="QM00013" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="6:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdc2" MODEL="" SERIAL="" SIZE="820M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="crypto_LUKS" LABEL="" UUID="3efae1ba-dbdf-4102-8bdc-e607e3448a7d"',  # noqa E501
            'NAME="/dev/mapper/luks-3efae1ba-dbdf-4102-8bdc-e607e3448a7d" MODEL="" SERIAL="" SIZE="818M" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="swap" LABEL="" UUID="1ef3c0a9-73b6-4271-a618-8fe4e580edac"',  # noqa E501
            'NAME="/dev/sdc3" MODEL="" SERIAL="" SIZE="6.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="crypto_LUKS" LABEL="" UUID="315111a6-8d37-447a-8dbf-0c9026abc456"',  # noqa E501
            'NAME="/dev/mapper/luks-315111a6-8d37-447a-8dbf-0c9026abc456" MODEL="" SERIAL="" SIZE="6.7G" TRAN="" VENDOR="" HCTL="" TYPE="crypt" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="d763b614-5eb3-45ac-8ac6-8f5aa5d0b74d"',  # noqa E501
            'NAME="/dev/sdc1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="bcd91aba-6f2d-441b-9f31-804ac094befe"',  # noqa E501
            'NAME="/dev/sda" MODEL="QEMU HARDDISK   " SERIAL="1" SIZE="5G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="btrfs" LABEL="rock-pool" UUID="50b66542-9a19-4403-b5a0-cd22412d9ae9"',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/mapper/luks-315111a6-8d37-447a-8dbf-0c9026abc456', model=None,  # noqa E501
                 serial='CRYPT-LUKS1-315111a68d37447a8dbf0c9026abc456-luks-315111a6-8d37-447a-8dbf-0c9026abc456',  # noqa E501
                 size=7025459, transport=None, vendor=None, hctl=None,
                 type='crypt', fstype='btrfs', label='rockstor_rockstor',
                 uuid='d763b614-5eb3-45ac-8ac6-8f5aa5d0b74d', parted=False,
                 root=True, partitions={}),
            Disk(name='/dev/sda', model='QEMU HARDDISK', serial='1', size=5242880,  # noqa E501
                 transport='sata', vendor='ATA', hctl='3:0:0:0', type='disk',
                 fstype='btrfs', label='rock-pool',
                 uuid='50b66542-9a19-4403-b5a0-cd22412d9ae9', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdb', model='QEMU HARDDISK', serial='2', size=5242880,  # noqa E501
                 transport='sata', vendor='ATA', hctl='5:0:0:0', type='disk',
                 fstype='btrfs', label='rock-pool',
                 uuid='50b66542-9a19-4403-b5a0-cd22412d9ae9', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdc', model='QEMU HARDDISK', serial='QM00013',
                 size=8388608, transport='sata', vendor='ATA', hctl='6:0:0:0',
                 type='disk', fstype='crypto_LUKS', label=None,
                 uuid='315111a6-8d37-447a-8dbf-0c9026abc456', parted=True,
                 root=False, partitions={'/dev/sdc3': 'crypto_LUKS'})
        ]]

        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            s_map = {
                '/dev/mapper/luks-315111a6-8d37-447a-8dbf-0c9026abc456': 'CRYPT-LUKS1-315111a68d37447a8dbf0c9026abc456-luks-315111a6-8d37-447a-8dbf-0c9026abc456'  # noqa E501
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return
        # Given no bcache we can also avoid mocking get_bcache_device_type()
        #
        # Ensure we correctly mock our root_disk value away from file default
        # of sda as we now have a root_disk on luks:
        self.mock_root_disk.return_value = '/dev/mapper/luks-315111a6-8d37-447a-8dbf-0c9026abc456'  # noqa E501

        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertEqual(returned, expected,
                             msg='LUKS sys disk id regression:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned,
                                                           expected))

    def test_scan_disks_btrfs_in_partition(self):
        """
        Test btrfs in partition on otherwise generic install. System disk sda
        data disk (for btrfs in partition) virtio with serial "serial-1"
        prepared as follows with regard to partition / formatting:

        First data set:

        yum install dosfstools
        parted -a optimal /dev/disk/by-id/virtio-serial-1
        mklabel msdos
        mkpart primary fat32 1 50%
        mkpart primary ext2 50% 100%
        quit
        mkfs.fat -s2 -F 32 /dev/disk/by-id/virtio-serial-1-part1
        mkfs.btrfs -L btrfs-in-partition /dev/disk/by-id/virtio-serial-1-part2

        Second data set (42nd scsi drive with a btrfs partiiton plus sda root):

        parted -a optimal /dev/sdap
        mklabel msdos
        mkpart primary fat32 1 50%
        mkpart primary ext2 50% 100%
        quit
        mkfs.fat -s2 -F 32 /dev/sdap1
        mkfs.btrfs -L btrfs-in-partition /dev/sdap2

        Should result in appropriate "partitions=" entry for base devices of
        /dev/disk/by-id/virtio-serial-1 (/dev/vda in below test data) and
        /dev/sdap

        The second data set is to check for a regression re false positive when
        root on sda, ie 'Regex to identify a partition on the base_root_disk.'
        """
        out = [[
            'NAME="/dev/sr0" MODEL="QEMU DVD-ROM    " SERIAL="QM00001" SIZE="1024M" TRAN="ata" VENDOR="QEMU    " HCTL="0:0:0:0" TYPE="rom" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda" MODEL="QEMU HARDDISK   " SERIAL="QM00005" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="2:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="820M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="aaf61037-23b1-4c3b-81ca-6d07f3ed922d"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="6.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="355f53a4-24e1-465e-95f3-7c422898f542"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="04ce9f16-a0a0-4db8-8719-1083a0d4f381"',  # noqa E501
            'NAME="/dev/vda" MODEL="" SERIAL="" SIZE="8G" TRAN="" VENDOR="0x1af4" HCTL="" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/vda2" MODEL="" SERIAL="" SIZE="4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="btrfs-in-partition" UUID="55284332-af66-4ca0-9647-99d9afbe0ec5"',  # noqa E501
            'NAME="/dev/vda1" MODEL="" SERIAL="" SIZE="4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="vfat" LABEL="" UUID="8F05-D915"',  # noqa E501
            ''], [
            'NAME="/dev/sr0" MODEL="QEMU DVD-ROM    " SERIAL="QM00001" SIZE="1024M" TRAN="ata" VENDOR="QEMU    " HCTL="0:0:0:0" TYPE="rom" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda" MODEL="QEMU HARDDISK   " SERIAL="QM00005" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="2:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="820M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="aaf61037-23b1-4c3b-81ca-6d07f3ed922d"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="6.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="355f53a4-24e1-465e-95f3-7c422898f542"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="04ce9f16-a0a0-4db8-8719-1083a0d4f381"',  # noqa E501
            'NAME="/dev/sdap" MODEL="QEMU HARDDISK   " SERIAL="42nd-scsi" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdap2" MODEL="" SERIAL="" SIZE="4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="btrfs-in-partition" UUID="55284332-af66-4ca0-9647-99d9afbe0ec5"',  # noqa E501
            'NAME="/dev/sdap1" MODEL="" SERIAL="" SIZE="4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="vfat" LABEL="" UUID="8F05-D915"',  # noqa E501
            ''
        ]]
        err = [['']]
        rc = [0]
        # Second lsblk moc output is a duplicate of our first set for err, rc.
        err.append(err[0])
        rc.append(0)
        expected_result = [[
            # Note partitions entry within vda, consistent with cli prep.
            Disk(name='/dev/vda', model=None, serial='serial-1', size=4194304,
                 transport=None, vendor='0x1af4', hctl=None, type='disk',
                 fstype='btrfs', label='btrfs-in-partition',
                 uuid='55284332-af66-4ca0-9647-99d9afbe0ec5', parted=True,
                 root=False,
                 partitions={'/dev/vda1': 'vfat', '/dev/vda2': 'btrfs'}),
            Disk(name='/dev/sda3', model='QEMU HARDDISK', serial='QM00005',
                 size=7025459, transport='sata', vendor='ATA', hctl='2:0:0:0',
                 type='part', fstype='btrfs', label='rockstor_rockstor',
                 uuid='355f53a4-24e1-465e-95f3-7c422898f542', parted=True,
                 root=True, partitions={})
        ], [
            # Note sdap (42nd disk) hand crafted from above vda entry
            Disk(name='/dev/sdap', model='QEMU HARDDISK', serial='42nd-scsi',
                 size=4194304, transport='sata', vendor='ATA', hctl='3:0:0:0',
                 type='disk', fstype='btrfs', label='btrfs-in-partition',
                 uuid='55284332-af66-4ca0-9647-99d9afbe0ec5', parted=True,
                 root=False,
                 partitions={'/dev/sdap1': 'vfat', '/dev/sdap2': 'btrfs'}),
            Disk(name='/dev/sda3', model='QEMU HARDDISK', serial='QM00005',
                 size=7025459, transport='sata', vendor='ATA', hctl='2:0:0:0',
                 type='part', fstype='btrfs', label='rockstor_rockstor',
                 uuid='355f53a4-24e1-465e-95f3-7c422898f542', parted=True,
                 root=True, partitions={})
        ]]
        # No LUKS or bcache mocking necessary as none in test data.
        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            s_map = {
                '/dev/vda': 'serial-1'
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return
        # Leaving test file default of "sda" for root_disk() see top of file.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertEqual(returned, expected,
                             msg='Btrfs in partition data disk regression:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned,
                                                           expected))

    def test_scan_disks_mdraid_sys_disk(self):
        """
        Test of scan_disks() on a system installed as per the:
        "Mirroring Rockstor OS using Linux Raid" at:
        http://rockstor.com/docs/mdraid-mirror/boot_drive_howto.html
        ie btrfs system volume on top of an mdraid dev. With swap and /boot
        also on their own mdraid devices.
        lsblk
        NAME      MAJ:MIN RM  SIZE RO TYPE  MOUNTPOINT
        sdb         8:16   0    8G  0 disk
        --sdb2      8:18   0  954M  0 part
        ----md125   9:125  0  954M  0 raid1 /boot
        --sdb3      8:19   0  1.4G  0 part
        ----md126   9:126  0  1.4G  0 raid1 [SWAP]
        --sdb1      8:17   0  5.7G  0 part
        ----md127   9:127  0  5.7G  0 raid1 /mnt2/rockstor_rockstor
        sr0        11:0    1  791M  0 rom
        sda         8:0    0    8G  0 disk
        --sda2      8:2    0  954M  0 part
        ----md125   9:125  0  954M  0 raid1 /boot
        --sda3      8:3    0  1.4G  0 part
        ----md126   9:126  0  1.4G  0 raid1 [SWAP]
        --sda1      8:1    0  5.7G  0 part
        ----md127   9:127  0  5.7G  0 raid1 /mnt2/rockstor_rockstor


        """
        out = [[
            'NAME="/dev/sdb" MODEL="QEMU HARDDISK   " SERIAL="md-serial-2" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdb2" MODEL="" SERIAL="" SIZE="954M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:boot" UUID="fc9fc706-e831-6b14-591e-0bc5bb008681"',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="954M" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="ext4" LABEL="" UUID="9df7d0f5-d109-4e84-a0f0-03a0cf0c03ad"',  # noqa E501
            'NAME="/dev/sdb3" MODEL="" SERIAL="" SIZE="1.4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:swap" UUID="9ed64a0b-10d2-72f9-4120-0f662c5b5d66"',  # noqa E501
            'NAME="/dev/md125" MODEL="" SERIAL="" SIZE="1.4G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="swap" LABEL="" UUID="1234d230-0aca-4b1d-9a10-c66744464d12"',  # noqa E501
            'NAME="/dev/sdb1" MODEL="" SERIAL="" SIZE="5.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:root" UUID="183a555f-3a90-3f7d-0726-b4109a1d78ba"',  # noqa E501
            'NAME="/dev/md127" MODEL="" SERIAL="" SIZE="5.7G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="59800daa-fdfd-493f-837d-18e9b46bbb46"',  # noqa E501
            'NAME="/dev/sr0" MODEL="QEMU DVD-ROM    " SERIAL="QM00001" SIZE="791M" TRAN="ata" VENDOR="QEMU    " HCTL="0:0:0:0" TYPE="rom" FSTYPE="iso9660" LABEL="Rockstor 3 x86_64" UUID="2017-07-02-03-11-01-00"',  # noqa E501
            'NAME="/dev/sda" MODEL="QEMU HARDDISK   " SERIAL="md-serial-1" SIZE="8G" TRAN="sata" VENDOR="ATA     " HCTL="2:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sda2" MODEL="" SERIAL="" SIZE="954M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:boot" UUID="fc9fc706-e831-6b14-591e-0bc5bb008681"',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="954M" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="ext4" LABEL="" UUID="9df7d0f5-d109-4e84-a0f0-03a0cf0c03ad"',  # noqa E501
            'NAME="/dev/sda3" MODEL="" SERIAL="" SIZE="1.4G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:swap" UUID="9ed64a0b-10d2-72f9-4120-0f662c5b5d66"',  # noqa E501
            'NAME="/dev/md125" MODEL="" SERIAL="" SIZE="1.4G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="swap" LABEL="" UUID="1234d230-0aca-4b1d-9a10-c66744464d12"',  # noqa E501
            'NAME="/dev/sda1" MODEL="" SERIAL="" SIZE="5.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="linux_raid_member" LABEL="rockstor:root" UUID="183a555f-3a90-3f7d-0726-b4109a1d78ba"',  # noqa E501
            'NAME="/dev/md127" MODEL="" SERIAL="" SIZE="5.7G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="59800daa-fdfd-493f-837d-18e9b46bbb46"',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/md127', model='[2] md-serial-1[0] md-serial-2[1] raid1',  # noqa E501
                 serial='183a555f:3a903f7d:0726b410:9a1d78ba', size=5976883,
                 transport=None, vendor=None, hctl=None, type='raid1',
                 fstype='btrfs', label='rockstor_rockstor',
                 uuid='59800daa-fdfd-493f-837d-18e9b46bbb46', parted=False,
                 root=True, partitions={}),
            Disk(name='/dev/sda', model='QEMU HARDDISK', serial='md-serial-1',
                 size=8388608, transport='sata', vendor='ATA', hctl='2:0:0:0',
                 type='disk', fstype='linux_raid_member', label=None,
                 uuid=None, parted=True, root=False,
                 partitions={'/dev/sda3': 'linux_raid_member',
                             '/dev/sda1': 'linux_raid_member'}),
            Disk(name='/dev/sdb', model='QEMU HARDDISK', serial='md-serial-2',
                 size=8388608, transport='sata', vendor='ATA', hctl='3:0:0:0',
                 type='disk', fstype='linux_raid_member', label=None,
                 uuid=None, parted=True, root=False,
                 partitions={'/dev/sdb3': 'linux_raid_member',
                             '/dev/sdb1': 'linux_raid_member'})
        ]]
        # No LUKS or bcache mocking necessary as none in test data.
        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            s_map = {
                '/dev/md125': 'fc9fc706:e8316b14:591e0bc5:bb008681',
                '/dev/md126': '9ed64a0b:10d272f9:41200f66:2c5b5d66',
                '/dev/md127': '183a555f:3a903f7d:0726b410:9a1d78ba'
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return
        # Ensure we correctly mock our root_disk value away from file default
        # of sda as we now have a root_disk on md device.
        self.mock_root_disk.return_value = '/dev/md127'
        # As we have an mdraid device of interest (the system disk) it's model
        # info field is used to present basic info on it's members serials:
        # We mock this as otherwise our wide scope run_command() mock breaks
        # this function.
        self.patch_get_md_members = patch('system.osi.get_md_members')
        self.mock_get_md_members = self.patch_get_md_members.start()
        self.mock_get_md_members.return_value = '[2] md-serial-1[0] ' \
                                                'md-serial-2[1] raid1'
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertEqual(returned, expected,
                             msg='mdraid under btrfs sys vol regression:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned,
                                                           expected))

    def test_scan_disks_intel_bios_raid_sys_disk(self):
        """
        Intel motherboard based firmware raid sys disk install, Essentially
        interfaced by mdraid but with differing device names.
        sdb           8:16   0 149.1G  0 disk
        --md126       9:126  0   149G  0 raid1
        ----md126p3 259:2    0 146.6G  0 md    /mnt2/rockstor_rockstor00
        ----md126p1 259:0    0   500M  0 md    /boot
        ----md126p2 259:1    0     2G  0 md    [SWAP]
        sdc           8:32   0 149.1G  0 disk
        --md126       9:126  0   149G  0 raid1
        ----md126p3 259:2    0 146.6G  0 md    /mnt2/rockstor_rockstor00
        ----md126p1 259:0    0   500M  0 md    /boot
        ----md126p2 259:1    0     2G  0 md    [SWAP]
        sda           8:0    0 298.1G  0 disk

        cat /proc/mdstat
        Personalities : [raid1]
        md126 : active raid1 sdb[1] sdc[0]
            156288000 blocks super external:/md127/0 [2/2] [UU]

        md127 : inactive sdb[1](S) sdc[0](S)
            5544 blocks super external:imsm

        unused devices: <none>

        """
        out = [[
            'NAME="/dev/sdb" MODEL="TOSHIBA MK1652GS" SERIAL="Z8A9CAZUT" SIZE="149.1G" TRAN="sata" VENDOR="ATA     " HCTL="1:0:0:0" TYPE="disk" FSTYPE="isw_raid_member" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="149G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126p3" MODEL="" SERIAL="" SIZE="146.6G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="btrfs" LABEL="rockstor_rockstor00" UUID="1c59b842-5d08-4472-a731-c593ab0bff93"',  # noqa E501
            'NAME="/dev/md126p1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="ext4" LABEL="" UUID="40e4a91f-6b08-4ea0-b0d1-e43d145558b3"',  # noqa E501
            'NAME="/dev/md126p2" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="swap" LABEL="" UUID="43d2f3dc-38cd-49ef-9e18-be35297c1412"',  # noqa E501
            'NAME="/dev/sdc" MODEL="SAMSUNG HM160HI " SERIAL="S1WWJ9BZ408430" SIZE="149.1G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="isw_raid_member" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="149G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126p3" MODEL="" SERIAL="" SIZE="146.6G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="btrfs" LABEL="rockstor_rockstor00" UUID="1c59b842-5d08-4472-a731-c593ab0bff93"',  # noqa E501
            'NAME="/dev/md126p1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="ext4" LABEL="" UUID="40e4a91f-6b08-4ea0-b0d1-e43d145558b3"',  # noqa E501
            'NAME="/dev/md126p2" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="swap" LABEL="" UUID="43d2f3dc-38cd-49ef-9e18-be35297c1412"',  # noqa E501
            'NAME="/dev/sda" MODEL="WDC WD3200AAKS-7" SERIAL="WD-WMAV20342011" SIZE="298.1G" TRAN="sata" VENDOR="ATA     " HCTL="0:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/md126p3',
                 model='[2] Z8A9CAZUT[0] S1WWJ9BZ408430[1] raid1',
                 serial='a300e6b0:5d69eee6:98a2354a:0ba1e1eb', size=153721241,
                 transport=None, vendor=None, hctl=None, type='md',
                 fstype='btrfs', label='rockstor_rockstor00',
                 uuid='1c59b842-5d08-4472-a731-c593ab0bff93', parted=True,
                 root=True, partitions={}),
            Disk(name='/dev/sda', model='WDC WD3200AAKS-7',
                 serial='WD-WMAV20342011', size=312580505, transport='sata',
                 vendor='ATA', hctl='0:0:0:0', type='disk', fstype=None,
                 label=None, uuid=None, parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/sdb', model='TOSHIBA MK1652GS', serial='Z8A9CAZUT',
                 size=156342681, transport='sata', vendor='ATA',
                 hctl='1:0:0:0', type='disk', fstype='isw_raid_member',
                 label=None, uuid=None, parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/sdc', model='SAMSUNG HM160HI', serial='S1WWJ9BZ408430',  # noqa E501
                 size=156342681, transport='sata', vendor='ATA',
                 hctl='3:0:0:0', type='disk', fstype='isw_raid_member',
                 label=None, uuid=None, parted=False, root=False,
                 partitions={})
        ]]

        # No LUKS or bcache mocking necessary as none in test data.
        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            # Note in the following our md126p3 partition has the same serial
            # as it's base device.
            s_map = {
                '/dev/md126': 'a300e6b0:5d69eee6:98a2354a:0ba1e1eb',
                '/dev/md126p3': 'a300e6b0:5d69eee6:98a2354a:0ba1e1eb',
                '/dev/md127': 'a88a8eda:1e459751:3341ad9b:fe3031a0'
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return
        # Ensure we correctly mock our root_disk value away from file default
        # of sda as we now have a root_disk on md device.
        self.mock_root_disk.return_value = '/dev/md126'
        # As we have an mdraid device of interest (the system disk) it's model
        # info field is used to present basic info on it's members serials:
        # We mock this as otherwise our wide scope run_command() mock breaks
        # this function.
        self.patch_get_md_members = patch('system.osi.get_md_members')
        self.mock_get_md_members = self.patch_get_md_members.start()
        self.mock_get_md_members.return_value = '[2] Z8A9CAZUT[0] ' \
                                                'S1WWJ9BZ408430[1] raid1'
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertEqual(returned, expected,
                             msg='bios raid under btrfs sys vol regression:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned,
                                                           expected))

    def test_scan_disks_intel_bios_raid_data_disk(self):
        """
        Intel motherboard based firmware raid data disk identification.
        Boot disk as Sandisk USB 3.0 Extreme.
        Data disk as a raid1 intel raid array.
        N.B. as a non mdraid install is missing mdadm the following is required
        for an mdraid compound device to auto assembled:
        yum install mdadm
        After a reboot any mdraid intel bios or otherwise, should be assembled.
        cat /proc/mdstat
        Personalities : [raid1]
        md126 : active raid1 sdb[1] sdc[0]
            156288000 blocks super external:/md127/0 [2/2] [UU]

        md127 : inactive sdb[1](S) sdc[0](S)
            5544 blocks super external:imsm

        unused devices: <none>

        """
        # Out and expected_results have sda stripped for simplicity.
        out = [[
            'NAME="/dev/sdd" MODEL="Extreme         " SERIAL="AA010312161642210668" SIZE="29.2G" TRAN="usb" VENDOR="SanDisk " HCTL="6:0:0:0" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/sdd2" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="422cc263-788e-4a74-a127-99695c380a2c"',  # noqa E501
            'NAME="/dev/sdd3" MODEL="" SERIAL="" SIZE="26.7G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor" UUID="d030d7ee-4c85-4317-96bf-6ff766fec9ef"',  # noqa E501
            'NAME="/dev/sdd1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="35c11bd3-bba1-4869-8a51-1e6bfaec15a2"',  # noqa E501
            'NAME="/dev/sdb" MODEL="TOSHIBA MK1652GS" SERIAL="Z8A9CAZUT" SIZE="149.1G" TRAN="sata" VENDOR="ATA     " HCTL="1:0:0:0" TYPE="disk" FSTYPE="isw_raid_member" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="149G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126p3" MODEL="" SERIAL="" SIZE="146.6G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="btrfs" LABEL="rockstor_rockstor00" UUID="1c59b842-5d08-4472-a731-c593ab0bff93"',  # noqa E501
            'NAME="/dev/md126p1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="ext4" LABEL="" UUID="40e4a91f-6b08-4ea0-b0d1-e43d145558b3"',  # noqa E501
            'NAME="/dev/md126p2" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="swap" LABEL="" UUID="43d2f3dc-38cd-49ef-9e18-be35297c1412"',  # noqa E501
            'NAME="/dev/sdc" MODEL="SAMSUNG HM160HI " SERIAL="S1WWJ9BZ408430" SIZE="149.1G" TRAN="sata" VENDOR="ATA     " HCTL="3:0:0:0" TYPE="disk" FSTYPE="isw_raid_member" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126" MODEL="" SERIAL="" SIZE="149G" TRAN="" VENDOR="" HCTL="" TYPE="raid1" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/md126p3" MODEL="" SERIAL="" SIZE="146.6G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="btrfs" LABEL="rockstor_rockstor00" UUID="1c59b842-5d08-4472-a731-c593ab0bff93"',  # noqa E501
            'NAME="/dev/md126p1" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="ext4" LABEL="" UUID="40e4a91f-6b08-4ea0-b0d1-e43d145558b3"',  # noqa E501
            'NAME="/dev/md126p2" MODEL="" SERIAL="" SIZE="2G" TRAN="" VENDOR="" HCTL="" TYPE="md" FSTYPE="swap" LABEL="" UUID="43d2f3dc-38cd-49ef-9e18-be35297c1412"',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        expected_result = [[
            Disk(name='/dev/sdc', model='SAMSUNG HM160HI', serial='S1WWJ9BZ408430',  # noqa E501
                 size=156342681, transport='sata', vendor='ATA',
                 hctl='3:0:0:0', type='disk', fstype='isw_raid_member',
                 label=None, uuid=None, parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/sdb', model='TOSHIBA MK1652GS', serial='Z8A9CAZUT',
                 size=156342681, transport='sata', vendor='ATA',
                 hctl='1:0:0:0', type='disk', fstype='isw_raid_member',
                 label=None, uuid=None, parted=False, root=False,
                 partitions={}),
            Disk(name='/dev/sdd3', model='Extreme', serial='AA010312161642210668',  # noqa E501
                 size=27996979, transport='usb', vendor='SanDisk',
                 hctl='6:0:0:0', type='part', fstype='btrfs',
                 label='rockstor_rockstor',
                 uuid='d030d7ee-4c85-4317-96bf-6ff766fec9ef', parted=True,
                 root=True, partitions={}),
            Disk(name='/dev/md126',
                 model='[2] Z8A9CAZUT[0] S1WWJ9BZ408430[1] raid1',
                 serial='a300e6b0:5d69eee6:98a2354a:0ba1e1eb', size=153721241,
                 transport=None, vendor=None, hctl=None, type='raid1',
                 fstype='btrfs', label='rockstor_rockstor00',
                 uuid='1c59b842-5d08-4472-a731-c593ab0bff93', parted=True,
                 root=False, partitions={'/dev/md126p3': 'btrfs'})
        ]]

        # No LUKS or bcache mocking necessary as none in test data.
        # Establish dynamic mock behaviour for get_disk_serial()
        self.patch_dyn_get_disk_serial = patch('system.osi.get_disk_serial')
        self.mock_dyn_get_disk_serial = self.patch_dyn_get_disk_serial.start()

        # TODO: Alternatively consider using get_disk_serial's test mode.
        def dyn_disk_serial_return(*args, **kwargs):
            # Entries only requred here if lsblk test data has no serial info:
            # eg for bcache, LUKS, mdraid, and virtio type devices.
            # Note in the following our md126p3 partition has the same serial
            # as it's base device.
            s_map = {
                '/dev/md126': 'a300e6b0:5d69eee6:98a2354a:0ba1e1eb',
                '/dev/md126p3': 'a300e6b0:5d69eee6:98a2354a:0ba1e1eb',
                '/dev/md127': 'a88a8eda:1e459751:3341ad9b:fe3031a0'
            }
            # First argument in get_disk_serial() is device_name, key off this
            # for our dynamic mock return from s_map (serial map).
            if args[0] in s_map:
                return s_map[args[0]]
            else:
                # indicate missing test data via return as we should supply all
                # non lsblk available serial devices so as to limit our testing
                # to
                return 'missing-mock-serial-data-for-dev-{}'.format(args[0])
        self.mock_dyn_get_disk_serial.side_effect = dyn_disk_serial_return
        # Ensure we correctly mock our root_disk value away from file default.
        self.mock_root_disk.return_value = '/dev/sdd'
        # As we have an mdraid device of interest (the data disk) it's model
        # info field is used to present basic info on it's members serials:
        # We mock this as otherwise our wide scope run_command() mock breaks
        # this function.
        self.patch_get_md_members = patch('system.osi.get_md_members')
        self.mock_get_md_members = self.patch_get_md_members.start()
        self.mock_get_md_members.return_value = '[2] Z8A9CAZUT[0] ' \
                                                'S1WWJ9BZ408430[1] raid1'
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            self.assertEqual(returned, expected,
                             msg='bios raid non sys disk regression:\n '
                                 'returned = ({}).\n '
                                 'expected = ({}).'.format(returned,
                                                           expected))

    def test_scan_disks_nvme_sys_disk(self):
        """
        Post pr #1925 https://github.com/rockstor/rockstor-core/pull/1946
        a regression was observed for nvme system disk installs. Essentially
        they were no longer recognized as attached, ie scan_disks() did not
        return them. As a result they became detached on existing installs.
        Thanks to forum member Jorma_Tuomainen in the following forum thread
        for supplying this instance data to be used as a regression test set.
        """
        # Test data based on 2 data drives (sdb, sdb) and an nvme system drive
        # /dev/nvme0n1 as the base device.
        out = [[
            'NAME="/dev/sdb" MODEL="WDC WD100EFAX-68" SERIAL="7PKNDX1C" SIZE="9.1T" TRAN="sata" VENDOR="ATA " HCTL="1:0:0:0" TYPE="disk" FSTYPE="btrfs" LABEL="Data" UUID="d2f76ce6-85fd-4615-b4f8-77e1b6a69c60"',  # noqa E501
            'NAME="/dev/sda" MODEL="WDC WD100EFAX-68" SERIAL="7PKP0MNC" SIZE="9.1T" TRAN="sata" VENDOR="ATA " HCTL="0:0:0:0" TYPE="disk" FSTYPE="btrfs" LABEL="Data" UUID="d2f76ce6-85fd-4615-b4f8-77e1b6a69c60"',  # noqa E501
            'NAME="/dev/nvme0n1" MODEL="INTEL SSDPEKKW128G7 " SERIAL="BTPY72910KCW128A" SIZE="119.2G" TRAN="" VENDOR="" HCTL="" TYPE="disk" FSTYPE="" LABEL="" UUID=""',  # noqa E501
            'NAME="/dev/nvme0n1p3" MODEL="" SERIAL="" SIZE="7.8G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="swap" LABEL="" UUID="d33115d8-3d8c-4f65-b560-8ebf72d08fbc"',  # noqa E501
            'NAME="/dev/nvme0n1p1" MODEL="" SERIAL="" SIZE="200M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="vfat" LABEL="" UUID="53DC-1323"',  # noqa E501
            'NAME="/dev/nvme0n1p4" MODEL="" SERIAL="" SIZE="110.8G" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="btrfs" LABEL="rockstor_rockstor00" UUID="4a05477f-cd4a-4614-b264-d029d98928ab"',  # noqa E501
            'NAME="/dev/nvme0n1p2" MODEL="" SERIAL="" SIZE="500M" TRAN="" VENDOR="" HCTL="" TYPE="part" FSTYPE="ext4" LABEL="" UUID="497a9eda-a655-4fc4-bad8-2d9aa8661980"',  # noqa E501
            '']]
        err = [['']]
        rc = [0]
        # Second lsblk moc output is a duplicate of our first set.
        out.append(out[0])
        err.append(err[0])
        rc.append(0)
        # Setup expected results
        expected_result = [[
            Disk(name='/dev/sda', model='WDC WD100EFAX-68', serial='7PKP0MNC',
                 size=9771050598, transport='sata', vendor='ATA',
                 hctl='0:0:0:0', type='disk', fstype='btrfs', label='Data',
                 uuid='d2f76ce6-85fd-4615-b4f8-77e1b6a69c60', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdb', model='WDC WD100EFAX-68', serial='7PKNDX1C',
                 size=9771050598, transport='sata', vendor='ATA',
                 hctl='1:0:0:0', type='disk', fstype='btrfs', label='Data',
                 uuid='d2f76ce6-85fd-4615-b4f8-77e1b6a69c60', parted=False,
                 root=False, partitions={})
        ], [
            Disk(name='/dev/nvme0n1p4', model='INTEL SSDPEKKW128G7',
                 serial='BTPY72910KCW128A', size=116182220, transport=None,
                 vendor=None, hctl=None, type='part', fstype='btrfs',
                 label='rockstor_rockstor00',
                 uuid='4a05477f-cd4a-4614-b264-d029d98928ab', parted=True,
                 root=True, partitions={}),
            Disk(name='/dev/sda', model='WDC WD100EFAX-68', serial='7PKP0MNC',
                 size=9771050598, transport='sata', vendor='ATA',
                 hctl='0:0:0:0', type='disk', fstype='btrfs', label='Data',
                 uuid='d2f76ce6-85fd-4615-b4f8-77e1b6a69c60', parted=False,
                 root=False, partitions={}),
            Disk(name='/dev/sdb', model='WDC WD100EFAX-68', serial='7PKNDX1C',
                 size=9771050598, transport='sata', vendor='ATA',
                 hctl='1:0:0:0', type='disk', fstype='btrfs', label='Data',
                 uuid='d2f76ce6-85fd-4615-b4f8-77e1b6a69c60', parted=False,
                 root=False, partitions={})
        ]]
        # Second expected instance is where the nvme system disk is identified.
        # As all serials are available via the lsblk we can avoid mocking
        # get_device_serial()
        # And given no bcache we can also avoid mocking
        # get_bcache_device_type()
        # Ensure we correctly mock our root_disk value away from file default
        # of sda as we now have a root_disk on an nvme device.
        self.mock_root_disk.return_value = '/dev/nvme0n1'
        # Iterate the test data sets for run_command running lsblk.
        for o, e, r, expected in zip(out, err, rc, expected_result):
            self.mock_run_command.return_value = (o, e, r)
            # itemgetter(0) referenced the first item within our Disk
            # collection by which to sort (key) ie name. N.B. 'name' failed.
            expected.sort(key=operator.itemgetter(0))
            returned = scan_disks(1048576, test_mode=True)
            returned.sort(key=operator.itemgetter(0))
            # TODO: Would be nice to have differences found shown.
            if len(expected) == 2:  # no system disk only the 2 data disks
                self.assertNotEqual(returned, expected,
                                    msg='Nvme sys disk missing regression:\n '
                                        'returned = ({}).\n '
                                        'expected = ({}).'.format(returned,
                                                                  expected))
            if len(expected) == 3:
                # assumed to be our correctly reported 1 x sys + 2 x data disks
                self.assertEqual(returned, expected,
                                 msg='Un-expected scan_disks() result:\n '
                                     'returned = ({}).\n '
                                     'expected = ({}).'.format(returned,
                                                               expected))

    def test_get_byid_name_map_prior_command_mock(self):
        """
        Test get_byid_name_map() for prior mapping between canonical
        and by-id device name mapping.
        Note that the 'new' variant of this behaviour, tested later, only
        involved the change of the mocked run_command output.
        """
        # The following test data of 'ls -l' contains; sdd, sde, and sda3 with
        # same length by-id mappings that are also their only mappings.
        # This allows testing for returning the expected wwn-..., not the
        # regression tested here of "scsi-... type name. As per
        # get_dev_byid_name()'s reverse lexicographical return priority we
        # would now expect the wwn-... type names if there are not others
        # available and all available by-id are of the same length.
        # Thanks to forum member juchong for submitting this command output.

        out = [
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-HGST_HUH728080ALE600_2EKXANGP -> ../../sdb',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-VMware_Virtual_SATA_CDRW_Drive_00000000000000000001 -> ../../sr0',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68L0BN1_WD-WX11D6651995 -> ../../sdg',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68L0BN1_WD-WX31DB58YJF0 -> ../../sdh',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WX11DB4H8VJJ -> ../../sdf',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WX21DC42ELAT -> ../../sdc',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WXM1H84CXAUJ -> ../../sdi',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-35000cca252017870 -> ../../sdd',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-35000cca252017ef4 -> ../../sde',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636 -> ../../sda',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part1 -> ../../sda1',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part2 -> ../../sda2',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part3 -> ../../sda3',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca23bf728eb -> ../../sdb',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca252017870 -> ../../sdd',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca252017ef4 -> ../../sde',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee20b77be35 -> ../../sdf',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee20dd22144 -> ../../sdg',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee260e5c696 -> ../../sdi',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee26114d4cb -> ../../sdc',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee26293bbea -> ../../sdh',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636 -> ../../sda',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part1 -> ../../sda1',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part2 -> ../../sda2',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part3 -> ../../sda3',  # noqa E501
        ]
        err = ['']
        rc = 0
        expected = {
            'sda1': 'scsi-36000c29df1181dd53db36b41b3582636-part1',
            'sdf': 'ata-WDC_WD60EFRX-68MYMN1_WD-WX11DB4H8VJJ',
            'sdd': 'scsi-35000cca252017870',
            'sde': 'scsi-35000cca252017ef4',
            'sr0': 'ata-VMware_Virtual_SATA_CDRW_Drive_00000000000000000001',
            'sdg': 'ata-WDC_WD60EFRX-68L0BN1_WD-WX11D6651995',
            'sda2': 'scsi-36000c29df1181dd53db36b41b3582636-part2',
            'sda': 'scsi-36000c29df1181dd53db36b41b3582636',
            'sdb': 'ata-HGST_HUH728080ALE600_2EKXANGP',
            'sdc': 'ata-WDC_WD60EFRX-68MYMN1_WD-WX21DC42ELAT',
            'sdh': 'ata-WDC_WD60EFRX-68L0BN1_WD-WX31DB58YJF0',
            'sdi': 'ata-WDC_WD60EFRX-68MYMN1_WD-WXM1H84CXAUJ',
            'sda3': 'scsi-36000c29df1181dd53db36b41b3582636-part3'}
        self.mock_run_command.return_value = (out, err, rc)
        returned = get_byid_name_map()
        self.maxDiff = None
        self.assertDictEqual(returned, expected)

    def test_get_byid_name_map(self):
        """
        Test get_byid_name_map() for expected by-id device name mapping.
        """
        # The following test data of 'ls -lr' contains; sdd, sde, and sda3 with
        # same length by-id mappings that are also their only mappings.
        # This allows testing for returning the expected wwn-..., not the
        # "scsi-... type name. As per get_dev_byid_name()'s revised reverse
        # lexicographical return priority we would now expect the wwn-... type
        # names if there are no others available and all available by-id are
        # of the same length.
        # This ls -lr output is derived from the ls -l output supplied by forum
        # member juchong.

        out = [
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part3 -> ../../sda3',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part2 -> ../../sda2',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636-part1 -> ../../sda1',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x6000c29df1181dd53db36b41b3582636 -> ../../sda',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee26293bbea -> ../../sdh',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee26114d4cb -> ../../sdc',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee260e5c696 -> ../../sdi',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee20dd22144 -> ../../sdg',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x50014ee20b77be35 -> ../../sdf',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca252017ef4 -> ../../sde',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca252017870 -> ../../sdd',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 wwn-0x5000cca23bf728eb -> ../../sdb',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part3 -> ../../sda3',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part2 -> ../../sda2',  # noqa E501
            'lrwxrwxrwx 1 root root 10 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636-part1 -> ../../sda1',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-36000c29df1181dd53db36b41b3582636 -> ../../sda',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-35000cca252017ef4 -> ../../sde',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 scsi-35000cca252017870 -> ../../sdd',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WXM1H84CXAUJ -> ../../sdi',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WX21DC42ELAT -> ../../sdc',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68MYMN1_WD-WX11DB4H8VJJ -> ../../sdf',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68L0BN1_WD-WX31DB58YJF0 -> ../../sdh',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-WDC_WD60EFRX-68L0BN1_WD-WX11D6651995 -> ../../sdg',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-VMware_Virtual_SATA_CDRW_Drive_00000000000000000001 -> ../../sr0',  # noqa E501
            'lrwxrwxrwx 1 root root 9 Oct 22 23:40 ata-HGST_HUH728080ALE600_2EKXANGP -> ../../sdb',  # noqa E501
        ]
        err = ['']
        rc = 0
        # The order of the following is unimportant as it's a dictionary but is
        # preserved on the index to aid comparison with:
        # test_get_byid_name_map_prior_command_mock()
        expected = {
            'sda1': 'wwn-0x6000c29df1181dd53db36b41b3582636-part1',
            'sdf': 'ata-WDC_WD60EFRX-68MYMN1_WD-WX11DB4H8VJJ',
            'sdd': 'wwn-0x5000cca252017870',
            'sde': 'wwn-0x5000cca252017ef4',
            'sr0': 'ata-VMware_Virtual_SATA_CDRW_Drive_00000000000000000001',
            'sdg': 'ata-WDC_WD60EFRX-68L0BN1_WD-WX11D6651995',
            'sda2': 'wwn-0x6000c29df1181dd53db36b41b3582636-part2',
            'sda': 'wwn-0x6000c29df1181dd53db36b41b3582636',
            'sdb': 'ata-HGST_HUH728080ALE600_2EKXANGP',
            'sdc': 'ata-WDC_WD60EFRX-68MYMN1_WD-WX21DC42ELAT',
            'sdh': 'ata-WDC_WD60EFRX-68L0BN1_WD-WX31DB58YJF0',
            'sdi': 'ata-WDC_WD60EFRX-68MYMN1_WD-WXM1H84CXAUJ',
            'sda3': 'wwn-0x6000c29df1181dd53db36b41b3582636-part3'}
        self.mock_run_command.return_value = (out, err, rc)
        returned = get_byid_name_map()
        self.maxDiff = None
        self.assertDictEqual(returned, expected)
