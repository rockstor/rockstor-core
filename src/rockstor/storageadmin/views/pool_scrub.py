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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.util import handle_exception
from storageadmin.serializers import PoolScrubSerializer
from storageadmin.models import (Pool, PoolScrub, Disk)
import rest_framework_custom as rfc
from fs.btrfs import (scrub_start, scrub_status, is_share_mounted, mount_root)
from storageadmin.exceptions import RockStorAPIException
from datetime import timedelta

import logging
logger = logging.getLogger(__name__)

class PoolScrubView(rfc.GenericView):
    serializer_class = PoolScrubSerializer

    def _validate_pool(self, pname, request):
        try:
            return Pool.objects.get(name=pname)
        except:
            e_msg = ('Pool: %s does not exist' % pname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        pool = self._validate_pool(kwargs['pname'], self.request)
        return PoolScrub.objects.filter(pool=pool).order_by('-id')

    @transaction.commit_on_success
    def post(self, request, pname, command=None):
        pool = self._validate_pool(pname, request)
        if (command is not None and command != 'status'):
            e_msg = ('Unknown scrub command: %s' % command)
            handle_exception(Exception(e_msg), request)

        try:
            disk = Disk.objects.filter(pool=pool)[0]
            if (command == 'status'):
                try:
                    ps = PoolScrub.objects.filter(pool=pool).order_by('-id')[0]
                except:
                    return Response()
                if (ps.status == 'started' or ps.status == 'running'):
                    cur_status = scrub_status(pname, disk.name)
                    ps.status = cur_status['status']
                    if (cur_status['status'] == 'finished'):
                        duration = int(cur_status['duration'])
                        ps.end_time = (ps.start_time +
                                       timedelta(seconds=duration))
                        ps.kb_scrubbed = cur_status['kb_scrubbed']
                        ps.errors = cur_status['errors']
                        ps.save()
                return Response(PoolScrubSerializer(ps).data)

            if ((PoolScrub.objects.filter(pool=pool,
                                          status__regex=r'(started|running)')
                 .exists())):
                e_msg = ('Active scrub exists for the pool: %s' % pname)
                handle_exception(Exception(e_msg), request)

            scrub_pid = scrub_start(pname, disk.name)
            ps = PoolScrub(pool=pool, pid=scrub_pid)
            ps.save()
            return Response(PoolScrubSerializer(ps).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)
