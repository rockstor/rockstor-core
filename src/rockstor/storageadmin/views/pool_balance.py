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
from django_ztask.models import Task
from storageadmin.util import handle_exception
from storageadmin.serializers import PoolBalanceSerializer
from storageadmin.models import (Pool, PoolBalance)
import rest_framework_custom as rfc
from fs.btrfs import balance_status, balance_status_internal
from pool import PoolMixin

import logging
logger = logging.getLogger(__name__)


class PoolBalanceView(PoolMixin, rfc.GenericView):
    serializer_class = PoolBalanceSerializer

    @staticmethod
    def _validate_pool(pid, request):
        try:
            return Pool.objects.get(id=pid)
        except:
            e_msg = 'Pool ({}) does not exist.'.format(pid)
            handle_exception(Exception(e_msg), request)

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            pool = self._validate_pool(self.kwargs['pid'], self.request)
            self._balance_status(pool)
            return PoolBalance.objects.filter(pool=pool).order_by('-id')

    @staticmethod
    @transaction.atomic
    def _balance_status(pool):
        try:
            # acquire a handle on the last pool balance status db entry
            ps = PoolBalance.objects.filter(pool=pool).order_by('-id')[0]
        except:
            # return empty handed if we have no 'last entry' to update
            return Response()
        # Check if we have a running task which matches our last pool status
        # tid
        if (Task.objects.filter(uuid=ps.tid).exists()):
            to = Task.objects.get(uuid=ps.tid)
            if (to.failed is not None):
                ps.status = 'failed'
                ps.message = to.last_exception
                ps.end_time = to.failed
                ps.save()
                to.delete()
                return ps
        # Get the current status of balance on this pool, irrespective of
        # a running balance task, ie command line intervention.
        if ps.internal:
            cur_status = balance_status_internal(pool)
        else:
            cur_status = balance_status(pool)
        previous_status = ps.status
        # TODO: future "Balance Cancel" button should call us to have these
        # TODO: values updated in the db table ready for display later.
        if previous_status == 'cancelling' \
                and cur_status['status'] == 'finished':
            # override current status as 'cancelled'
            cur_status['status'] = 'cancelled'
            cur_status['message'] = \
                'cancelled at %s%% complete' % ps.percent_done
            # and retain prior percent finished value
            cur_status['percent_done'] = ps.percent_done
        if previous_status == 'failed' \
                and cur_status['status'] == 'finished':
            # override current status as 'failed'
            cur_status['status'] = 'failed'
            # and retain prior percent finished value
            cur_status['percent_done'] = ps.percent_done

        if previous_status != 'finished' and previous_status != 'cancelled':
            # update the last pool balance status with current status info.
            PoolBalance.objects.filter(id=ps.id).update(**cur_status)
        return ps

    @transaction.atomic
    def post(self, request, pid, command=None):
        pool = self._validate_pool(pid, request)
        if (command is not None and command != 'status'):
            e_msg = 'Unknown balance command ({}).'.format(command)
            handle_exception(Exception(e_msg), request)

        with self._handle_exception(request):
            ps = self._balance_status(pool)
            if (command == 'status'):
                return Response(PoolBalanceSerializer(ps).data)
            force = request.data.get('force', False)
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
                             'pool ({}).').format(pool.name)
                    handle_exception(Exception(e_msg), request)

            tid = self._balance_start(pool, force=force)
            ps = PoolBalance(pool=pool, tid=tid)
            ps.save()
            return Response(PoolBalanceSerializer(ps).data)
