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

import unittest
from mock import patch

from system.osi import get_dev_byid_name


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

        # some procedures use os.path..isfile so setup mock
        self.patch_os_path_isfile = patch('os.path.isfile')
        self.mock_os_path_isfile = self.patch_os_path_isfile.start()

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
        dev_name.append('luks-a47f4950-3296-4504-b9a4-2dc75681a6ad')
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
