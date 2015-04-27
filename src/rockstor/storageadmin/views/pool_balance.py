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
from storageadmin.serializers import PoolBalanceSerializer
from storageadmin.models import (Pool, PoolBalance, Disk)
import rest_framework_custom as rfc
from fs.btrfs import (balance_start, balance_status)

import logging
logger = logging.getLogger(__name__)


class PoolBalanceView(rfc.GenericView):
    serializer_class = PoolBalanceSerializer

    def _validate_pool(self, pname, request):
        try:
            return Pool.objects.get(name=pname)
        except:
            e_msg = ('Pool: %s does not exist' % pname)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            pool = self._validate_pool(self.kwargs['pname'], self.request)
            disk = Disk.objects.filter(pool=pool)[0]
            self._balance_status(pool, disk)
            return PoolBalance.objects.filter(pool=pool).order_by('-id')

    @transaction.commit_on_success
    def _balance_status(self, pool, disk):
        try:
            ps = PoolBalance.objects.filter(pool=pool).order_by('-id')[0]
        except:
            return Response()
        if (ps.status == 'started' or ps.status == 'running'):
            cur_status = balance_status(pool, disk.name)
            PoolBalance.objects.filter(id=ps.id).update(**cur_status)
        return ps

    @transaction.commit_on_success
    def post(self, request, pname, command=None):
        pool = self._validate_pool(pname, request)
        if (command is not None and command != 'status'):
            e_msg = ('Unknown balance command: %s' % command)
            handle_exception(Exception(e_msg), request)

        with self._handle_exception(request):
            disk = Disk.objects.filter(pool=pool)[0]
            ps = self._balance_status(pool, disk)
            if (command == 'status'):
                return Response(PoolBalanceSerializer(ps).data)
            force = request.DATA.get('force', False)
            if ((PoolBalance.objects.filter(pool=pool,
                                            status__regex=r'(started|running)')
                 .exists())):
                if (force):
                    p = PoolBalance.objects.filter(
                        pool=pool,
                        status__regex=r'(started|running)').order_by('-id')[0]
                    p.status = 'terminated'
                    p.save()
                else:
                    e_msg = ('A Balance process is already running for '
                             'pool(%s).' % pname)
                    handle_exception(Exception(e_msg), request)

            balance_pid = balance_start(pool, disk.name, force=force)
            ps = PoolBalance(pool=pool, pid=balance_pid)
            ps.save()
            return Response(PoolBalanceSerializer(ps).data)
