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


import re
import pickle
import time
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view
from django.db import transaction
from storageadmin.serializers import PoolInfoSerializer
from storageadmin.models import (Disk, Pool, Share, PoolBalance)
from fs.btrfs import (add_pool, pool_usage, resize_pool_cmd, umount_root,
                      btrfs_uuid, mount_root, start_balance, usage_bound,
                      remove_share, enable_quota, disable_quota, rescan_quotas,
                      start_resize_pool)
from system.osi import remount, trigger_udev_update
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
from django_ztask.models import Task
import json

import logging
logger = logging.getLogger(__name__)


class PoolMixin(object):
    serializer_class = PoolInfoSerializer
    RAID_LEVELS = ('single', 'raid0', 'raid1', 'raid10', 'raid5', 'raid6')

    @staticmethod
    def _validate_disk(d, request):
        # TODO: Consider moving this and related code to id based validation.
        try:
            return Disk.objects.get(name=d)
        except:
            e_msg = 'Disk with name ({}) does not exist.'.format(d)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_disk_id(diskId, request):
        try:
            return Disk.objects.get(id=diskId)
        except:
            e_msg = 'Disk with id ({}) does not exist.'.format(diskId)
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _role_filter_disk_names(disks, request):
        """
        Takes a series of disk objects and filters them based on their roles.
        For disk with a redirect role the role's value is substituted for that
        disks name. This effects a name re-direction for redirect role disks.
        N.B. Disk model now has sister code under Disk.target_name property.
        :param disks:  list of disks object
        :param request:
        :return: list of disk names post role filter processing
        """
        # TODO: Consider revising to use new Disk.target_name property.
        try:
            # Build dictionary of disks with roles
            role_disks = {d for d in disks if d.role is not None}
            # Build a dictionary of redirected disk names with their
            # associated redirect role values.
            # By using only role_disks we avoid json.load(None)
            redirect_disks = {d.name: json.loads(d.role).get("redirect", None)
                              for d in role_disks if
                              'redirect' in json.loads(d.role)}
            # Replace d.name with redirect role value for redirect role disks.
            # Our role system stores the /dev/disk/by-id name (without path)
            # for redirected disks so use that value instead as our disk name:
            dnames = [
                d.name if d.name not in redirect_disks else redirect_disks[
                    d.name] for d in disks]
            return dnames
        except:
            e_msg = 'Problem with role filter of disks.'
            handle_exception(Exception(e_msg), request)

    @staticmethod
    def _validate_new_quota_state(request):
        logger.debug('#### validate_new_quota_state received new_state '
                     '=({}).'.format(request.data.get('quotas')))
        new_val = request.data.get('quotas', 'Enabled')
        if new_val is None:
            # We default to Quotas enabled if input is in doubt.
            new_val = 'Enabled'
        if new_val != 'Enabled' and new_val != 'Disabled':
            e_msg = ('Unsupported quotas request ({}). '
                     'Expecting "Enabled" or "Disabled"'.format(new_val))
            handle_exception(Exception(e_msg), request)
        return new_val

    @staticmethod
    def _validate_compression(request):
        # Define default compression value, if not entered, as 'no'.
        compression = request.data.get('compression', 'no')
        if (compression is None or compression == ''):
            compression = 'no'
        if (compression not in settings.COMPRESSION_TYPES):
            e_msg = ('Unsupported compression algorithm ({}). Use one of '
                     '{}.').format(compression, settings.COMPRESSION_TYPES)
            handle_exception(Exception(e_msg), request)
        return compression

    @staticmethod
    def _validate_mnt_options(request):
        mnt_options = request.data.get('mnt_options', None)
        if (mnt_options is None):
            return ''
        allowed_options = {
            'alloc_start': int,
            'autodefrag': None,
            'clear_cache': None,
            'commit': int,
            'compress-force': settings.COMPRESSION_TYPES,
            'degraded': None,
            'discard': None,
            'fatal_errors': None,
            'inode_cache': None,
            'max_inline': int,
            'metadata_ratio': int,
            'noacl': None,
            'noatime': None,
            'nodatacow': None,
            'nodatasum': None,
            'nospace_cache': None,
            'nossd': None,
            'ro': None,
            'rw': None,
            'skip_balance': None,
            'space_cache': None,
            'ssd': None,
            'ssd_spread': None,
            'thread_pool': int,
            '': None,
        }
        o_fields = mnt_options.split(',')
        for o in o_fields:
            v = None
            if (re.search('=', o) is not None):
                o, v = o.split('=')
            if (o not in allowed_options):
                e_msg = ('mount option ({}) not allowed. Make sure there are '
                         'no whitespaces in the input. Allowed options: '
                         '({}).').format(o, sorted(allowed_options.keys()))
                handle_exception(Exception(e_msg), request)
            if ((o == 'compress-force' and
                 v not in allowed_options['compress-force'])):
                e_msg = ('compress-force is only allowed with '
                         '{}.').format(settings.COMPRESSION_TYPES)
                handle_exception(Exception(e_msg), request)
            # changed conditional from "if (type(allowed_options[o]) is int):"
            if (allowed_options[o] is int):
                try:
                    int(v)
                except:
                    e_msg = ('Value for mount option ({}) must be an '
                             'integer.').format(o)
                    handle_exception(Exception(e_msg), request)
        return mnt_options

    @classmethod
    def _remount(cls, request, pool):
        compression = cls._validate_compression(request)
        mnt_options = cls._validate_mnt_options(request)
        if ((compression == pool.compression and
             mnt_options == pool.mnt_options)):
            return Response()

        with transaction.atomic():
            pool.compression = compression
            pool.mnt_options = mnt_options
            pool.save()

        if (re.search('noatime', mnt_options) is None):
            mnt_options = ('%s,relatime,atime' % mnt_options)

        if (re.search('compress-force', mnt_options) is None):
            mnt_options = ('%s,compress=%s' % (mnt_options, compression))

        with open('/proc/mounts') as mfo:
            mount_map = {}
            for l in mfo.readlines():
                share_name = None
                if (re.search(
                        '%s|%s' % (settings.NFS_EXPORT_ROOT, settings.MNT_PT),
                        l) is not None):
                    share_name = l.split()[1].split('/')[2]
                elif (re.search(settings.SFTP_MNT_ROOT, l) is not None):
                    share_name = l.split()[1].split('/')[3]
                else:
                    continue
                if (share_name not in mount_map):
                    mount_map[share_name] = [l.split()[1], ]
                else:
                    mount_map[share_name].append(l.split()[1])
        failed_remounts = []
        try:
            pool_mnt = '/mnt2/%s' % pool.name
            remount(pool_mnt, mnt_options)
        except:
            failed_remounts.append(pool_mnt)
        for share in mount_map.keys():
            if (Share.objects.filter(pool=pool, name=share).exists()):
                for m in mount_map[share]:
                    try:
                        remount(m, mnt_options)
                    except Exception as e:
                        logger.exception(e)
                        failed_remounts.append(m)
        if (len(failed_remounts) > 0):
            e_msg = ('Failed to remount the following mounts.\n {}.\n '
                     'Try again or do the following as root (may cause '
                     'downtime):\n1. systemctl stop rockstor.\n'
                     '2. unmount manually.\n'
                     '3. systemctl start rockstor.\n').format(failed_remounts)
            handle_exception(Exception(e_msg), request)
        return Response(PoolInfoSerializer(pool).data)

    @classmethod
    def _quotas(cls, request, pool):
        new_quota_state = cls._validate_new_quota_state(request)
        # If no change from current pool quota state then do nothing
        current_state = 'Enabled'
        if not pool.quotas_enabled:
            current_state = 'Disabled'
        if new_quota_state == current_state:
            return Response()
        try:
            if new_quota_state == 'Enabled':
                # Current issue with requiring enable to be executed twice !!!
                # As of 4.12.4-1.el7.elrepo.x86_64
                # this avoids "ERROR: quota rescan failed: Invalid argument"
                # when attempting a rescan.
                # Look similar to https://patchwork.kernel.org/patch/9928635/
                enable_quota(pool)
                enable_quota(pool)
                # As of 4.12.4-1.el7.elrepo.x86_64
                # The second above enable_quota() call currently initiates a
                # rescan so the following is redundant; however this may not
                # always be the case so leaving as it will auto skip if a scan
                # in in progress anyway.
                rescan_quotas(pool)
            else:
                disable_quota(pool)
        except:
            e_msg = 'Failed to Enable (and rescan) / Disable Quotas for ' \
                    'Pool ({}). Requested quota state ' \
                    'was ({}).'.format(pool.name, new_quota_state)
            handle_exception(Exception(e_msg), request)
        return Response(PoolInfoSerializer(pool).data)

    def _balance_start(self, pool, force=False, convert=None):
        mnt_pt = mount_root(pool)
        if convert is None and pool.raid == 'single':
            # Btrfs balance without convert filters will convert dup level
            # metadata on a single level data pool to raid1 on multi disk
            # pools. Avoid by explicit convert in this instance.
            logger.info('Preserve single data, dup metadata by explicit '
                        'convert.')
            convert = 'single'
        start_balance.async(mnt_pt, force=force, convert=convert)
        tid = 0
        count = 0
        while (tid == 0 and count < 25):
            for t in Task.objects.all():
                if (pickle.loads(t.args)[0] == mnt_pt):
                    tid = t.uuid
            time.sleep(0.2)  # 200 milliseconds
            count += 1
        logger.debug('balance tid = ({}).'.format(tid))
        return tid

    def _resize_pool_start(self, pool, dnames, add=True):
        """
        Async initiator for resize_pool(pool, dnames, add=False) as when a
        device is deleted it initiates a btrfs internal balance which is not
        accessible to 'btrfs balance status' but is a balance nevertheless.
        Based on _balance_start()
        :param pool:  Pool object.
        :param dnames: list of by-id device names without paths.
        :param add: True if adding dnames, False if deleting (removing) dnames.
        :return: 0 if
        """
        tid = 0
        cmd = resize_pool_cmd(pool, dnames, add)
        if cmd is None:
            return tid
        logger.info('Beginning device resize on pool ({}). '
                    'Changed member devices:({}).'.format(pool.name, dnames))
        if add:
            # Mostly instantaneous so avoid complexity/overhead of django ztask
            start_resize_pool(cmd)
            return tid
        # Device delete initiates long running internal balance: start async.
        start_resize_pool.async(cmd)
        # Try to find django-ztask id for (25*0.2) 5 seconds via cmd args match
        count = 0
        while tid == 0 and count < 25:
            for t in Task.objects.all():
                if pickle.loads(t.args)[0] == cmd:
                    tid = t.uuid
            time.sleep(0.2)  # 200 milliseconds
            count += 1
        logger.debug('Pool resize tid = ({}).'.format(tid))
        return tid

class PoolListView(PoolMixin, rfc.GenericView):
    def get_queryset(self, *args, **kwargs):
        sort_col = self.request.query_params.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.query_params.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Pool.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Pool.objects.all()

    @transaction.atomic
    def post(self, request):
        """
        input is a list of disks, raid_level and name of the pool.
        """
        with self._handle_exception(request):
            disks = [self._validate_disk(d, request) for d in
                     request.data.get('disks')]
            pname = request.data['pname']
            if (re.match('%s$' % settings.POOL_REGEX, pname) is None):
                e_msg = ('Invalid characters in pool name. Following '
                         'characters are allowed: letter(a-z or A-Z), '
                         'digit(0-9), '
                         'hyphen(-), underscore(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (len(pname) > 255):
                e_msg = 'Pool name must be less than 255 characters.'
                handle_exception(Exception(e_msg), request)

            if (Pool.objects.filter(name=pname).exists()):
                e_msg = ('Pool ({}) already exists. '
                         'Choose a different name.').format(pname)
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(name=pname).exists()):
                e_msg = ('A share with this name ({}) exists. Pool and share '
                         'names must be distinct. '
                         'Choose a different name.').format(pname)
                handle_exception(Exception(e_msg), request)

            for d in disks:
                if (d.btrfs_uuid is not None):
                    e_msg = ('Another BTRFS filesystem exists on this '
                             'disk ({}). '
                             'Erase the disk and try again.').format(d.name)
                    handle_exception(Exception(e_msg), request)

            raid_level = request.data['raid_level']
            if (raid_level not in self.RAID_LEVELS):
                e_msg = ('Unsupported raid level. Use one of: '
                         '{}.').format(self.RAID_LEVELS)
                handle_exception(Exception(e_msg), request)
            # consolidated raid0 & raid 1 disk check
            if (raid_level in self.RAID_LEVELS[1:3] and len(disks) <= 1):
                e_msg = ('At least 2 disks are required for the raid level: '
                         '{}.').format(raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[3]):
                if (len(disks) < 4):
                    e_msg = ('A minimum of 4 drives are required for the '
                             'raid level: {}.').format(raid_level)
                    handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[4] and len(disks) < 2):
                e_msg = ('2 or more disks are required for the raid '
                         'level: {}.').format(raid_level)
                handle_exception(Exception(e_msg), request)
            if (raid_level == self.RAID_LEVELS[5] and len(disks) < 3):
                e_msg = ('3 or more disks are required for the raid '
                         'level: {}.').format(raid_level)
                handle_exception(Exception(e_msg), request)

            compression = self._validate_compression(request)
            mnt_options = self._validate_mnt_options(request)
            dnames = self._role_filter_disk_names(disks, request)
            p = Pool(name=pname, raid=raid_level, compression=compression,
                     mnt_options=mnt_options)
            p.save()
            p.disk_set.add(*disks)
            # added for loop to save disks appears p.disk_set.add(*disks) was
            # not saving disks in test environment
            for d in disks:
                d.pool = p
                d.save()
            add_pool(p, dnames)
            p.size = p.usage_bound()
            p.uuid = btrfs_uuid(dnames[0])
            p.save()
            # Now we ensure udev info is updated via system wide trigger
            # as per pool resize add, only here it is for a new pool.
            trigger_udev_update()
            return Response(PoolInfoSerializer(p).data)


class PoolDetailView(PoolMixin, rfc.GenericView):
    def get(self, *args, **kwargs):
        try:
            pool = Pool.objects.get(id=self.kwargs['pid'])
            serialized_data = PoolInfoSerializer(pool)
            return Response(serialized_data.data)
        except Pool.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

    @transaction.atomic
    def put(self, request, pid, command):
        """
        resize a pool.
        @pname: pool's name
        @command: 'add' - add a list of disks and hence expand the pool
                  'remove' - remove a list of disks and hence shrink the pool
                  'remount' - remount the pool, to apply changed mount options
                  'quotas' - request pool quota setting change
        """
        with self._handle_exception(request):
            try:
                pool = Pool.objects.get(id=pid)
            except:
                e_msg = 'Pool with id ({}) does not exist.'.format(pid)
                handle_exception(Exception(e_msg), request)

            if (pool.role == 'root' and command != 'quotas'):
                e_msg = ('Edit operations are not allowed on this pool ({}) '
                         'as it contains the operating '
                         'system.').format(pool.name)
                handle_exception(Exception(e_msg), request)

            if (command == 'remount'):
                return self._remount(request, pool)

            if (command == 'quotas'):
                # There is a pending btrfs change that allows for quota state
                # change on unmounted Volumes (pools).
                return self._quotas(request, pool)

            if not pool.is_mounted:
                e_msg = ('Pool member / raid edits require an active mount. '
                         'Please see the "Maintenance required" section.')
                handle_exception(Exception(e_msg), request)

            if command == 'remove' and \
                    request.data.get('disks', []) == ['missing']:
                disks = []
                logger.debug('Remove missing request skipping disk validation')
            else:
                disks = [self._validate_disk_id(diskId, request) for diskId in
                         request.data.get('disks', [])]

            num_disks_selected = len(disks)
            dnames = self._role_filter_disk_names(disks, request)
            new_raid = request.data.get('raid_level', pool.raid)

            if (command == 'add'):
                # Only attached disks can be selected during an add operation.
                num_total_attached_disks = pool.disk_set.attached().count() \
                                  + num_disks_selected
                for d in disks:
                    if (d.pool is not None):
                        e_msg = ('Disk ({}) cannot be added to this pool ({}) '
                                 'because it belongs to another pool ({})'
                                 '.').format(d.name, pool.name, d.pool.name)
                        handle_exception(Exception(e_msg), request)
                    if (d.btrfs_uuid is not None):
                        e_msg = ('Disk ({}) has a BTRFS filesystem from the '
                                 'past. If you really like to add it, wipe it '
                                 'from the Storage -> Disks screen of the '
                                 'web-ui.').format(d.name)
                        handle_exception(Exception(e_msg), request)

                if pool.raid == 'single' and new_raid == 'raid10':
                    # TODO: Consider removing once we have better space calc.
                    # Avoid extreme raid level change upwards (space issues).
                    e_msg = ('Pool migration from {} to {} is not '
                             'supported.').format(pool.raid, new_raid)
                    handle_exception(Exception(e_msg), request)

                if (new_raid == 'raid10' and num_total_attached_disks < 4):
                    e_msg = ('A minimum of 4 drives are required for the '
                             'raid level: raid10.')
                    handle_exception(Exception(e_msg), request)

                if (new_raid == 'raid6' and num_total_attached_disks < 3):
                    e_msg = ('A minimum of 3 drives are required for the '
                             'raid level: raid6.')
                    handle_exception(Exception(e_msg), request)

                if (new_raid == 'raid5' and num_total_attached_disks < 2):
                    e_msg = ('A minimum of 2 drives are required for the '
                             'raid level: raid5.')
                    handle_exception(Exception(e_msg), request)

                if (PoolBalance.objects.filter(
                        pool=pool,
                        status__regex=r'(started|running|cancelling|pausing|paused)').exists()):  # noqa E501
                    e_msg = ('A Balance process is already running or paused '
                             'for this pool ({}). Resize is not supported '
                             'during a balance process.').format(pool.name)
                    handle_exception(Exception(e_msg), request)

                # _resize_pool_start() add dev mode is quick so no async or tid
                self._resize_pool_start(pool, dnames)
                force = False
                # During dev add we also offer raid level change, if selected
                # blanket apply '-f' to allow for reducing metadata integrity.
                if new_raid != pool.raid:
                    force = True
                # Django-ztask initialization as balance is long running.
                tid = self._balance_start(pool, force=force, convert=new_raid)
                ps = PoolBalance(pool=pool, tid=tid)
                ps.save()

                pool.raid = new_raid
                for d_o in disks:
                    d_o.pool = pool
                    d_o.save()
                # Now we ensure udev info is updated via system wide trigger
                trigger_udev_update()
            elif (command == 'remove'):
                if (new_raid != pool.raid):
                    e_msg = ('Raid configuration cannot be changed while '
                             'removing disks.')
                    handle_exception(Exception(e_msg), request)
                detached_disks_selected = 0
                for d in disks:  # to be removed
                    if (d.pool is None or d.pool != pool):
                        e_msg = ('Disk ({}) cannot be removed because it does '
                                 'not belong to this '
                                 'pool ({}).').format(d.name, pool.name)
                        handle_exception(Exception(e_msg), request)
                    if re.match('detached-', d.name) is not None:
                        detached_disks_selected += 1
                if detached_disks_selected >= 3:
                    # Artificial constraint but no current btrfs raid level yet
                    # allows for > 2 dev detached and we have a mounted vol.
                    e_msg = ('We currently only support removing two'
                             'detached disks at a time.')
                    handle_exception(Exception(e_msg), request)
                attached_disks_selected = (
                            num_disks_selected - detached_disks_selected)
                remaining_attached_disks = (
                            pool.disk_set.attached().count() - attached_disks_selected)
                if (pool.raid == 'raid0'):
                    e_msg = ('Disks cannot be removed from a pool with this '
                             'raid ({}) configuration.').format(pool.raid)
                    handle_exception(Exception(e_msg), request)

                if (pool.raid == 'raid1' and remaining_attached_disks < 2):
                    e_msg = ('Disks cannot be removed from this pool '
                             'because its raid configuration (raid1) '
                             'requires a minimum of 2 disks.')
                    handle_exception(Exception(e_msg), request)

                if (pool.raid == 'raid10' and remaining_attached_disks < 4):
                    e_msg = ('Disks cannot be removed from this pool '
                             'because its raid configuration (raid10) '
                             'requires a minimum of 4 disks.')
                    handle_exception(Exception(e_msg), request)

                if (pool.raid == 'raid5' and remaining_attached_disks < 2):
                    e_msg = ('Disks cannot be removed from this pool because '
                             'its raid configuration (raid5) requires a '
                             'minimum of 2 disks.')
                    handle_exception(Exception(e_msg), request)

                if (pool.raid == 'raid6' and remaining_attached_disks < 3):
                    e_msg = ('Disks cannot be removed from this pool because '
                             'its raid configuration (raid6) requires a '
                             'minimum of 3 disks.')
                    handle_exception(Exception(e_msg), request)

                usage = pool_usage('/%s/%s' % (settings.MNT_PT, pool.name))
                size_cut = 0
                for d in disks:
                    size_cut += d.allocated
                if size_cut >= (pool.size - usage):
                    e_msg = ('Removing disks ({}) may shrink the pool by '
                             '{} KB, which is greater than available free '
                             'space {} KB. This is '
                             'not supported.').format(dnames, size_cut, usage)
                    handle_exception(Exception(e_msg), request)

                # Unlike resize_pool_start() with add=True a remove has an
                # implicit balance where the removed disks contents are
                # re-distributed across the remaining pool members.
                # This internal balance cannot currently be monitored by the
                # usual 'btrfs balance status /mnt_pt' command. So we have to
                # use our own mechanism to assess it's status.
                # Django-ztask initialization:
                tid = self._resize_pool_start(pool, dnames, add=False)
                ps = PoolBalance(pool=pool, tid=tid, internal=True)
                ps.save()

                # Setting disk.pool = None for all removed members is redundant
                # as our next disk scan will re-find them until such time as
                # our async task, and it's associated dev remove, has completed
                # it's internal balance. This can take hours.

            else:
                e_msg = 'Command ({}) is not supported.'.format(command)
                handle_exception(Exception(e_msg), request)
            pool.size = pool.usage_bound()
            pool.save()
            return Response(PoolInfoSerializer(pool).data)

    @transaction.atomic
    def delete(self, request, pid, command=''):
        force = True if (command == 'force') else False
        with self._handle_exception(request):
            try:
                pool = Pool.objects.get(id=pid)
            except:
                e_msg = 'Pool with id ({}) does not exist.'.format(pid)
                handle_exception(Exception(e_msg), request)

            if (pool.role == 'root'):
                e_msg = ('Deletion of pool ({}) is not allowed as it contains '
                         'the operating system.').format(pool.name)
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(pool=pool).exists()):
                if not force:
                    e_msg = ('Pool ({}) is not empty. Delete is not allowed '
                             'until all shares in the pool '
                             'are deleted.').format(pool.name)
                    handle_exception(Exception(e_msg), request)
                for so in Share.objects.filter(pool=pool):
                    remove_share(so.pool, so.subvol_name, so.pqgroup,
                                 force=force)
            pool_path = ('%s%s' % (settings.MNT_PT, pool.name))
            umount_root(pool_path)
            pool.delete()
            try:
                # TODO: this call fails as the inheritance of disks was removed
                # We need another method to invoke this as self no good now.
                self._update_disk_state()
            except Exception as e:
                logger.error(('Exception while updating disk state: '
                             '({}).').format(e.__str__()))
            return Response()


@api_view()
def get_usage_bound(request):
    """Simple view to relay the computed usage bound to the front end."""
    disk_sizes = [int(size) for size in
                  request.query_params.getlist('disk_sizes[]')]
    raid_level = request.query_params.get('raid_level', 'single')
    return Response(usage_bound(disk_sizes, len(disk_sizes), raid_level))
