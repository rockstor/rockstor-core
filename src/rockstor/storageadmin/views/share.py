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
from storageadmin.models import (Share, Disk, Pool, Snapshot,
                                 NFSExport, SambaShare, SFTP)
from fs.btrfs import (add_share, remove_share, update_quota,
                      share_usage, set_property, mount_share, qgroup_id,
                      shares_info)
from system.osi import is_share_mounted
from storageadmin.serializers import ShareSerializer
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

class ShareListView(ShareMixin, rfc.GenericView):
    serializer_class = ShareSerializer

    def get_queryset(self, *args, **kwargs):
        self._refresh_shares_state();
        sort_col = self.request.query_params.get('sortby', None)
        if (sort_col is not None and sort_col == 'usage'):
            reverse = self.request.query_params.get('reverse', 'no')
            if (reverse == 'yes'):
                reverse = True
            else:
                reverse = False
            return sorted(Share.objects.all(), key=lambda u: u.cur_usage(),
                          reverse=reverse)
        return Share.objects.all()

    @transaction.atomic
    def _refresh_shares_state(self):
        for p in Pool.objects.all():
            disk = Disk.objects.filter(pool=p)[0].name
            shares = [s.name for s in Share.objects.filter(pool=p)]
            shares_d = shares_info('%s%s' % (settings.MNT_PT, p.name))
            for s in shares:
                if (s not in shares_d):
                    Share.objects.get(pool=p, name=s).delete()
            for s in shares_d:
                if (s in shares):
                    continue
                nso = Share(pool=p, qgroup=shares_d[s], name=s, size=p.size,
                            subvol_name=s)
                nso.save()
                mount_share(nso, disk, '%s%s' % (settings.MNT_PT, s))

    @transaction.atomic
    def post(self, request):
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
                e_msg = ('Share name must start with a alphanumeric(a-z0-9) '
                         'character and can be followed by any of the '
                         'following characters: letter(a-z), digits(0-9), '
                         'hyphen(-), underscore(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(name=sname).exists()):
                e_msg = ('Share(%s) already exists. Choose a different name' % sname)
                handle_exception(Exception(e_msg), request)

            if (Pool.objects.filter(name=sname).exists()):
                e_msg = ('A Pool with this name(%s) exists. Share and Pool names '
                         'must be distinct. Choose a different name' % sname)
                handle_exception(Exception(e_msg), request)
            disk = Disk.objects.filter(pool=pool)[0]
            replica = False
            if ('replica' in request.data):
                replica = request.data['replica']
                if (type(replica) != bool):
                    e_msg = ('replica must be a boolean, not %s' %
                             type(replica))
                    handle_exception(Exception(e_msg), request)
            add_share(pool, disk.name, sname)
            qid = qgroup_id(pool, disk.name, sname)
            update_quota(pool, disk.name, qid, size * 1024)
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
            if (not Share.objects.filter(name=sname).exists()):
                e_msg = ('Share(%s) does not exist.' % sname)
                handle_exception(Exception(e_msg), request)
            share = Share.objects.get(name=sname)
            if ('size' in request.data):
                new_size = self._validate_share_size(request, share.pool)
                disk = Disk.objects.filter(pool=share.pool)[0]
                qid = qgroup_id(share.pool, disk.name, share.subvol_name)
                cur_usage = share_usage(share.pool, disk.name, qid)
                if (new_size < cur_usage):
                    e_msg = ('Unable to resize because requested new size(%dKB) '
                             'is less than current usage(%dKB) of the share.' %
                             (new_size, cur_usage))
                    handle_exception(Exception(e_msg), request)
                update_quota(share.pool, disk.name, qid, new_size * 1024)
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
    def _rockon_check(request, sname):
        try:
            s = Service.objects.get(name='docker')
            config = json.loads(s.config)
        except Exception, e:
            return logger.exception(e)

        if ('root_share' in config):
            if (config['root_share'] == sname):
                e_msg = ('Share(%s) cannot be deleted because it is in use '
                         'by Rock-on service. If you really need to delete '
                         'it, (1)turn the service off, (2)change its '
                         'configuration to use a different Share and then '
                         '(3)try deleting this Share(%s) again.' %
                         (sname, sname))
                handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def delete(self, request, sname):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        with self._handle_exception(request):
            try:
                share = Share.objects.get(name=sname)
            except:
                e_msg = ('Share(%s) does not exist.' % sname)
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

            self._rockon_check(request, sname)

            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            e_msg = ('Share(%s) may still be mounted and cannot be deleted. '
                     'Trying again usually succeeds. But if it does not, '
                     'you can manually unmount it with'
                     ' command: /usr/bin/umount /mnt2/%s' % (sname, sname))
            try:
                remove_share(share.pool, pool_device, share.subvol_name)
            except Exception, e:
                logger.exception(e)
                e_msg = ('%s . Error from the OS: %s' % (e_msg, e.__str__()))
                handle_exception(Exception(e_msg), request)
            share.delete()
            return Response()
