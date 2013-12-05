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
from storageadmin.models import (Share, Snapshot, Disk, Pool, Snapshot,
                                 NFSExport, SambaShare)
from fs.btrfs import (add_share, remove_share, share_id, update_quota,
                      share_usage, is_share_mounted)
from storageadmin.serializers import ShareSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from django.conf import settings
from generic_view import GenericView


import logging
logger = logging.getLogger(__name__)


class ShareView(GenericView):
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

    def _validate_share_size(self, request, size):
        e_msg = None
        if (size < settings.MIN_SHARE_SIZE):
            e_msg = ('Share size should atleast be %dKB. Given size is %dKB'
                     % (settings.MIN_SHARE_SIZE, size))
        elif (size > settings.MAX_SHARE_SIZE):
            e_msg = ('Share size cannot be more than %dKB. Given size is %dKB' %
                     (settings.MAX_SHARE_SIZE, size))
        if (e_msg is not None):
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def put(self, request, sname):
        try:
            if (not Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s does not exist' % sname)
                handle_exception(Exception(e_msg), request)

            share = Share.objects.get(name=sname)
            new_size = int(request.DATA['size'])
            self._validate_share_size(request, new_size)

            disk = Disk.objects.filter(pool=share.pool)[0]
            qgroup_id = self._update_quota(share.pool.name, disk.name,
                                           share.subvol_name, new_size)
            cur_usage = share_usage(share.pool.name, disk.name, qgroup_id)
            if (new_size < cur_usage):
                e_msg = ('Unable to resize because requested new size(%dKB) '
                         'is less than current usage(%dKB) of the share.' %
                         (new_size, cur_usage))
                handle_exception(Exception(e_msg), request)
            share.size = new_size
            share.save()
            return Response(ShareSerializer(share).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request):
        try:
            sname = request.DATA['sname']
            if (re.match('%s$' % settings.SHARE_REGEX, sname) is None):
                e_msg = ('Share name must start with a letter(a-z) and can'
                         ' be followed by any of the following characters: '
                         'letter(a-z), digits(0-9), hiphen(-), underscore'
                         '(_) or a period(.).')
                handle_exception(Exception(e_msg), request)

            if (Share.objects.filter(name=sname).exists()):
                e_msg = ('Share with name: %s already exists.' % sname)
                handle_exception(Exception(e_msg), request)

            pool_name = request.DATA['pool']
            size = int(request.DATA['size']) #in KB
            self._validate_share_size(request, size)
            pool = None
            try:
                pool = Pool.objects.get(name=pool_name)
            except:
                e_msg = ('Pool with name: %s does not exist.' % pool_name)
                handle_exception(Exception(e_msg), request)

            disk = None
            try:
                disk = Disk.objects.filter(pool=pool)[0]
            except:
                e_msg = ('Pool with name: %s does not have any disks in it.' %
                         pool_name)
                handle_exception(Exception(e_msg), request)

            add_share(pool_name, disk.name, sname)
            qgroup_id = self._update_quota(pool_name, disk.name, sname, size)
            s = Share(pool=pool, qgroup=qgroup_id, name=sname, size=size,
                      subvol_name=sname)
            s.save()
            return Response(ShareSerializer(s).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def _update_quota(self, pool_name, disk_name, share_name, size):
        sid = share_id(pool_name, disk_name, share_name)
        qgroup_id = '0/' + sid
        update_quota(pool_name, disk_name, qgroup_id, size * 1024)
        return qgroup_id

    @transaction.commit_on_success
    def delete(self, request, sname):
        """
        For now, we delete all snapshots, if any of the share and delete the
        share itself.
        """
        try:
            try:
                share = Share.objects.get(name=sname)
            except:
                e_msg = ('Share: %s does not exist' % sname)
                handle_exception(Exception(e_msg), request)

            if (NFSExport.objects.filter(share=share).exists()):
                e_msg = ('Share: %s cannot be deleted as it is exported via '
                         'nfs. Delete nfs exports and try again' % sname)
                handle_exception(Exception(e_msg), request)

            if (SambaShare.objects.filter(share=share).exists()):
                e_msg = ('Share: %s cannot be deleted as it is shared via '
                         'Samba. Unshare and try again' % sname)
                handle_exception(Exception(e_msg), request)

            if (Snapshot.objects.filter(share=share).exists()):
                e_msg = ('Share: %s cannot be deleted as it has '
                         'snapshots. Delete snapshots and try again' % sname)
                handle_exception(Exception(e_msg), request)

            pool_device = Disk.objects.filter(pool=share.pool)[0].name
            e_msg = ('Share: %s is still mounted and cannot be deleted.'
                     ' Try again later' % sname)
            try:
                remove_share(share.pool.name, pool_device, share.subvol_name)
            except Exception, e:
                logger.exception(e)
                handle_exception(Exception(e_msg), request)
            share.delete()
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
