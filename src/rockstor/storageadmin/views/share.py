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
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (Share, Disk, Pool, Snapshot,
                                 NFSExport, SambaShare, SFTP)
from fs.btrfs import (add_share, remove_share, share_id, update_quota,
                      share_usage, set_property, mount_share)
from system.osi import is_share_mounted
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc


import logging
logger = logging.getLogger(__name__)


class ShareView(rfc.GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        if ('sname' in kwargs):
            self.paginate_by = 0
            try:
                return Share.objects.get(name=kwargs['sname'])
            except:
                return []
        sort_col = self.request.QUERY_PARAMS.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.QUERY_PARAMS.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Share.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Share.objects.all()

    def _validate_share_size(self, request, pool):
        size = request.DATA.get('size', pool.size)
        try:
            size = int(size)
        except:
            handle_exception(Exception('Share size must be an integer'),
                             request)
        if (size < settings.MIN_SHARE_SIZE):
            e_msg = ('Share size should atleast be %dKB. Given size is %dKB'
                     % (settings.MIN_SHARE_SIZE, size))
            handle_exception(Exception(e_msg), request)
        if (size > pool.size):
            return pool.size
        return size

    def _validate_compression(self, request):
        compression = request.DATA.get('compression', 'no')
        if (compression is None):
            compression = 'no'
        if (compression not in settings.COMPRESSION_TYPES):
            e_msg = ('Unsupported compression algorithm(%s). Use one of '
                     '%s' % (compression, settings.COMPRESSION_TYPES))
            handle_exception(Exception(e_msg), request)
        return compression

    @transaction.commit_on_success
    def put(self, request, sname):
        with self._handle_exception(request):
            if (not Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s does not exist' % sname)
                handle_exception(Exception(e_msg), request)

            share = Share.objects.get(name=sname)
            new_size = self._validate_share_size(request, share.pool)
            disk = Disk.objects.filter(pool=share.pool)[0]
            qgroup_id = self._update_quota(share.pool, disk.name,
                                           share.subvol_name, new_size)
            cur_usage = share_usage(share.pool, disk.name, qgroup_id)
            if (new_size < cur_usage):
                e_msg = ('Unable to resize because requested new size(%dKB) '
                         'is less than current usage(%dKB) of the share.' %
                         (new_size, cur_usage))
                handle_exception(Exception(e_msg), request)
            share.size = new_size
            share.save()
            return Response(ShareSerializer(share).data)

    @transaction.commit_on_success
    def post(self, request):
        with self._handle_exception(request):
            pool_name = request.DATA.get('pool', None)
            try:
                pool = Pool.objects.get(name=pool_name)
            except:
                e_msg = ('Pool with name: %s does not exist.' % pool_name)
                handle_exception(Exception(e_msg), request)
            compression = self._validate_compression(request)
            size = self._validate_share_size(request, pool)
            sname = request.DATA.get('sname', None)
            if ((sname is None or
                 re.match('%s$' % settings.SHARE_REGEX, sname) is None)):
                e_msg = ('Share name must start with a letter(a-z) and can '
                         'be followed by any of the following characters: '
                         'letter(a-z), digits(0-9), hyphen(-), underscore'
                         '(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s already exists.' % sname)
                handle_exception(Exception(e_msg), request)

            try:
                disk = Disk.objects.filter(pool=pool)[0]
            except:
                e_msg = ('Pool with name: %s does not have any disks in it.' %
                         pool_name)
                handle_exception(Exception(e_msg), request)

            replica = False
            if ('replica' in request.DATA):
                replica = request.DATA['replica']
                if (type(replica) != bool):
                    e_msg = ('replica must be a boolean, not %s' %
                             type(replica))
                    handle_exception(Exception(e_msg), request)
            add_share(pool, disk.name, sname)
            qgroup_id = self._update_quota(pool, disk.name, sname, size)
            s = Share(pool=pool, qgroup=qgroup_id, name=sname, size=size,
                      subvol_name=sname, replica=replica,
                      compression_algo=compression)
            s.save()
            mnt_pt = '%s%s' % (settings.MNT_PT, sname)
            if (not is_share_mounted(sname)):
                disk = Disk.objects.filter(pool=pool)[0].name
                mount_share(s, disk, mnt_pt)
            if (compression != 'no'):
                set_property(mnt_pt, 'compression', compression)
            return Response(ShareSerializer(s).data)

    def _update_quota(self, pool, disk_name, share_name, size):
        sid = share_id(pool, disk_name, share_name)
        qgroup_id = '0/' + sid
        update_quota(pool, disk_name, qgroup_id, size * 1024)
        return qgroup_id

    @transaction.commit_on_success
    def delete(self, request, sname):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        with self._handle_exception(request):
            try:
                share = Share.objects.get(name=sname)
            except:
                e_msg = ('Share: %s does not exist' % sname)
                handle_exception(Exception(e_msg), request)

            if (Snapshot.objects.filter(share=share,
                                        snap_type='replication').exists()):
                e_msg = ('Share(%s) cannot be deleted as it has replication '
                         'related snapshots.' % sname)
                handle_exception(Exception(e_msg), request)

            if (NFSExport.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) cannot be deleted as it is exported via '
                         'nfs. Delete nfs exports and try again' % sname)
                handle_exception(Exception(e_msg), request)

            if (SambaShare.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) cannot be deleted as it is shared via '
                         'Samba. Unshare and try again' % sname)
                handle_exception(Exception(e_msg), request)

            if (Snapshot.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) cannot be deleted as it has '
                         'snapshots. Delete snapshots and try again' % sname)
                handle_exception(Exception(e_msg), request)

            if (SFTP.objects.filter(share=share).exists()):
                e_msg = ('Share(%s) cannot be deleted as it is exported via '
                         'SFTP. Delete SFTP export and try again' % sname)
                handle_exception(Exception(e_msg), request)

            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            e_msg = ('Share(%s) is still mounted and cannot be deleted. '
                     'Trying again usually succeeds. But if it does not, '
                     'you can manually unmount it with'
                     ' command: /usr/bin/umount /mnt2/%s' % (sname, sname))
            try:
                remove_share(share.pool, pool_device, share.subvol_name)
            except Exception, e:
                logger.exception(e)
                handle_exception(Exception(e_msg), request)
            share.delete()
            return Response()
