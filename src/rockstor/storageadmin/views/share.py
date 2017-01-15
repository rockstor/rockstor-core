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
from rest_framework.exceptions import NotFound
from django.db import transaction
from storageadmin.models import (Share, Pool, Snapshot, NFSExport, SambaShare,
                                 SFTP)
from smart_manager.models import Replica
from fs.btrfs import (add_share, remove_share, update_quota, share_usage,
                      set_property, mount_share, qgroup_id, qgroup_create)
from system.osi import is_share_mounted
from system.services import systemctl
from storageadmin.serializers import ShareSerializer, SharePoolSerializer
from storageadmin.util import handle_exception
from django.conf import settings
import rest_framework_custom as rfc
import json
from smart_manager.models import Service

import logging
logger = logging.getLogger(__name__)


class ShareMixin(object):

    @staticmethod
    def _validate_share_size(request, pool):
        size = request.data.get('size', pool.size)
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

    @staticmethod
    def _validate_compression(request):
        compression = request.data.get('compression', 'no')
        if (compression is None):
            compression = 'no'
        if (compression not in settings.COMPRESSION_TYPES):
            e_msg = ('Unsupported compression algorithm(%s). Use one of '
                     '%s' % (compression, settings.COMPRESSION_TYPES))
            handle_exception(Exception(e_msg), request)
        return compression

    @staticmethod
    def _validate_share(request, sname):
        try:
            share = Share.objects.get(name=sname)
            if (share.name == 'home' or share.name == 'root'):
                e_msg = ('Operation not permitted on this Share(%s) because '
                         'it is a special system Share' % sname)
                handle_exception(Exception(e_msg), request)
            return share
        except Share.DoesNotExist:
            e_msg = ('Share(%s) does not exist' % sname)
            handle_exception(Exception(e_msg), request)


class ShareListView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            sort_col = self.request.query_params.get('sortby', None)
            if (sort_col is not None):
                reverse = self.request.query_params.get('reverse', 'no')
                if (reverse == 'yes'):
                    reverse = True
                else:
                    reverse = False
                if (sort_col == 'usage'):
                    sort_col = 'rusage'
                return sorted(Share.objects.all(),
                              key=lambda u: getattr(u, sort_col),
                              reverse=reverse)
            # If this box is receiving replication backups, the first full-send
            # is interpreted as a Share(because it does not have a parent
            # subvol/snapshot) It is a transient subvolume that gets rolled
            # into a proper Share after 5 incremental-sends. Until then, keep
            # such transient shares hidden from the UI, mostly for costmetic
            # and UX reasons.
            return Share.objects.exclude(
                name__regex=r'^\.snapshots/.*/.*_replication_').order_by('-id')

    @transaction.atomic
    def post(self, request):
        # qgroup notes for shares. we need to create a qgroup prior to share
        # creation. qgroup ids 0/<subvol_id> automatically get created when a
        # subvolume(i.e., a Share or a Snapshot) is created. So let's create a
        # new qgroup: 2015/<some_number> whenever a Share is
        # created. <some_number> starts from 1 and is incremented as more
        # Shares are created. So, for the very first Share in a pool, it's
        # qgroup will be 1/1. 2015 is arbitrarily chose.

        # Before creating a new Share, we create the qgroup for it. And during
        # it's creation, we assign this qgroup to it. During it's creation a
        # 0/x qgroup will automatically be created, but it will become the
        # child of our explicitly-created qgroup(2015/x).

        # We will set the qgroup limit on our qgroup and it will enforce the
        # quota on every subvolume(i.e., Share and Snapshot) in that qgroup.

        # When a Share is deleted, we need to destroy two qgroups. One is it's
        # auto 0/x qgroup and the other is our explicitly-created 2015/y
        # qgroup.

        with self._handle_exception(request):
            pool_name = request.data.get('pool', None)
            try:
                pool = Pool.objects.get(name=pool_name)
            except:
                e_msg = ('Pool(%s) does not exist.' % pool_name)
                handle_exception(Exception(e_msg), request)
            compression = self._validate_compression(request)
            size = self._validate_share_size(request, pool)
            sname = request.data.get('sname', None)
            if ((sname is None or
                 re.match('%s$' % settings.SHARE_REGEX, sname) is None)):
                e_msg = ('Invalid characters in Share name. Following are '
                         'allowed: letter(a-z or A-Z), digit(0-9), '
                         'hyphen(-), underscore(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (len(sname) > 254):
                # btrfs subvolume names cannot exceed 254 characters.
                e_msg = ('Share name length cannot exceed 254 characters')
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(name=sname).exists()):
                e_msg = ('Share(%s) already exists. Choose a '
                         'different name' % sname)
                handle_exception(Exception(e_msg), request)

            if (Pool.objects.filter(name=sname).exists()):
                e_msg = ('A Pool with this name(%s) exists. Share '
                         'and Pool names must be distinct. Choose '
                         'a different name' % sname)
                handle_exception(Exception(e_msg), request)
            replica = False
            if ('replica' in request.data):
                replica = request.data['replica']
                if (type(replica) != bool):
                    e_msg = ('replica must be a boolean, not %s' %
                             type(replica))
                    handle_exception(Exception(e_msg), request)
            pqid = qgroup_create(pool)
            add_share(pool, sname, pqid)
            qid = qgroup_id(pool, sname)
            update_quota(pool, pqid, size * 1024)
            s = Share(pool=pool, qgroup=qid, pqgroup=pqid, name=sname,
                      size=size, subvol_name=sname, replica=replica,
                      compression_algo=compression)
            s.save()
            mnt_pt = '%s%s' % (settings.MNT_PT, sname)
            if (not is_share_mounted(sname)):
                mount_share(s, mnt_pt)
            if (compression != 'no'):
                set_property(mnt_pt, 'compression', compression)
            return Response(ShareSerializer(s).data)


class PoolShareListView(ShareMixin, rfc.GenericView):
    serializer_class = SharePoolSerializer

    def get_queryset(self, *args, **kwargs):
        pool = Pool.objects.get(name=self.kwargs.get('pname'))
        return pool.share_set.all()


class ShareDetailView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def get(self, *args, **kwargs):
        try:
            data = Share.objects.get(name=self.kwargs['sname'])
            serialized_data = ShareSerializer(data)
            return Response(serialized_data.data)
        except Share.DoesNotExist:
            raise NotFound(detail=None)

    @transaction.atomic
    def put(self, request, sname):
        with self._handle_exception(request):
            share = self._validate_share(request, sname)
            if ('size' in request.data):
                new_size = self._validate_share_size(request, share.pool)
                qid = qgroup_id(share.pool, share.subvol_name)
                cur_rusage, cur_eusage = share_usage(share.pool, qid)
                if (new_size < cur_rusage):
                    e_msg = ('Unable to resize because requested new '
                             'size(%dKB) is less than current usage(%dKB)'
                             'of the share.' %
                             (new_size, cur_rusage))
                    handle_exception(Exception(e_msg), request)
                update_quota(share.pool, share.pqgroup, new_size * 1024)
                share.size = new_size
            if ('compression' in request.data):
                new_compression = self._validate_compression(request)
                if (share.compression_algo != new_compression):
                    share.compression_algo = new_compression
                    mnt_pt = '%s%s' % (settings.MNT_PT, sname)
                    if (new_compression == 'no'):
                        new_compression = ''
                    set_property(mnt_pt, 'compression', new_compression)
            share.save()
            return Response(ShareSerializer(share).data)

    @staticmethod
    def _rockon_check(request, sname, force):
        s = Service.objects.get(name='docker')
        if (s.config is None):
            return

        config = json.loads(s.config)
        if (config.get('root_share') == sname):
            if (force):
                # turn off docker service, nullify config.
                systemctl(s.name, 'stop')
                systemctl(s.name, 'disable')
                s.config = None
                return s.save()
            e_msg = ('Share(%s) cannot be deleted because it is in use '
                     'by Rock-on service. If you must delete anyway, select '
                     'the force checkbox and try again.' % sname)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def delete(self, request, sname, command=''):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        force = True if (command == 'force') else False
        with self._handle_exception(request):
            share = self._validate_share(request, sname)
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

            if (Replica.objects.filter(share=sname).exists()):
                e_msg = ('Share(%s) is configured for replication. If you are '
                         'sure, delete the replication task and try again.'
                         % sname)
                handle_exception(Exception(e_msg), request)

            self._rockon_check(request, sname, force=force)

            try:
                remove_share(share.pool, share.subvol_name, share.pqgroup,
                             force=force)
            except Exception as e:
                logger.exception(e)
                e_msg = ('Failed to delete the Share(%s). Error from '
                         'the OS: %s' % (sname, e.__str__()))
                handle_exception(Exception(e_msg), request)
            share.delete()
            return Response()
