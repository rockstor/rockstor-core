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

"""
Pool view. for all things at pool level
"""
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Disk, Pool, Share, Snapshot)
from fs.btrfs import (btrfs_label, mount_root, btrfs_importable,
                      btrfs_raid_level, umount_root, subvol_list_helper,
                      snapshot_list)
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
import os

import logging
logger = logging.getLogger(__name__)


class PoolImportView(rfc.GenericView):

    RAID_LEVELS = ('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')

    def _pool_size(self, disks, raid_level):
        disk_size = None
        for d in disks:
            size = Disk.objects.get(name=d).size
            if (disk_size is None or disk_size > size):
                disk_size = size

        if (raid_level == self.RAID_LEVELS[0]):
            return disk_size
        if (raid_level == self.RAID_LEVELS[1]):
            return disk_size * len(disks)
        if (raid_level in self.RAID_LEVELS[2:4]):
            return disk_size * (len(disks) / 2)
        if (raid_level == self.RAID_LEVELS[4]):
            return disk_size * (len(disks) - 1)
        if (raid_level == self.RAID_LEVELS[5]):
            return disk_size * (len(disks) - 2)

    @transaction.commit_on_success
    def post(self, request, uuid):
        """
        import a pool with given uuid
        """
        disks = Disk.objects.filter(btrfs_uuid=uuid)

        if (not btrfs_importable(disks[0].name)):
            e_msg = ('btrfs check failed on device: %s Cannot automatically '
                     'import the pool with uuid: %s' % (disks[0].name, uuid))
            handle_exception(Exception(e_msg), request)


        #get name of the pool
        pname = btrfs_label(uuid)

        #mount the pool
        mount_root(pname, '/dev/%s' % disks[0].name)
        pool_mnt_pt = '%s/%s' % (settings.MNT_PT, pname)

        #get raid level
        raid_level = btrfs_raid_level(pname)
        if (raid_level is None):
            umount_root(pool_mnt_pt)
            e_msg = ('Problem while probing for the raid level of the pool.'
                     'Cannot automatically import the pool with uuid: %s' %
                     uuid)
            handle_exception(Exception(e_msg), request)

        #check for shares in the pool
        subvols, e, rc = subvol_list_helper(pool_mnt_pt)
        snap_list = snapshot_list(pool_mnt_pt)
        share_map = {}
        for s in subvols:
            s_fields = s.split()
            if (s_fields[-1] not in snap_list):
                share_map[s_fields[-1]] = s_fields[1]

        entries = os.listdir(pool_mnt_pt)
        e_msg_prefix = ('Only btrfs filesystem with nothing but subvolumes in '
                        'it can be imported.')
        for e in entries:
            if (os.path.isfile('%s/%s' % (pool_mnt_pt, e))):
                e_msg = ('%s Unexpected file %s found. Due to this reason, '
                         'pool with uuid: %s cannot be imported' %
                         (e_msg_prefix, e, uuid))
                handle_exception(Exception(e_msg), request)
            elif (e not in share_map):
                e_msg = ('%s Unexpected directory %s found. Due to this '
                         'reason, pool with uuid: %s cannot be imported' %
                         (e_msg_prefix, e, uuid))
                handle_exception(Exception(e_msg), request)

        #add pool model
        pool_size = self._pool_size(disks, raid_level)
        p = Pool(name=pname, raid=raid_level, size=pool_size, uuid=uuid)
        p.save()

        #import shares
        for s in share_map.keys():
            so = Share(pool=p, qgroup='0/%s' % share_map[s], name=s,
                       size=qgroup_size, subvol_name=s, replica=False)
            so.save()

            #import snapshots?
            for snap in snap_list:
                snap_fields = snap.split('_')
                snap_name = snap_fields[-1]
                sname = '_'.join(snap_fields[0:-1])
                if (sname == s):
                    snapo = Snapshot(share=so, name=snap_name,
                                     real_name=snap, qgroup=qgroup_id)
                    snapo.save()
