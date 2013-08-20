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

from smart_manager.models import SProbe
from django.conf import settings
from django.db import transaction
from storageadmin.util import handle_exception
from smart_manager.serializers import (SProbeSerializer, PaginatedSProbe)
from rest_framework.response import Response
import zmq
import os
from django.http import Http404
import logging
logger = logging.getLogger(__name__)
from generic_sprobe import GenericSProbeView
from django.core.paginator import Paginator
from smart_manager.taplib.probe_config import TAP_MAP


class AdvancedSProbeView(GenericSProbeView):

    empty_error = u"Empty list and '%(class_name)s.allow_empty' is False."
    #overriding parent method to pass *args and **kwargs down to get_queryset
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset(*args, **kwargs)
        self.object_list = self.filter_queryset(queryset)

        # Default is to allow empty querysets.  This can be altered by setting
        # `.allow_empty = False`, to raise 404 errors on empty querysets.
        allow_empty = self.get_allow_empty()
        if not allow_empty and not self.object_list:
            class_name = self.__class__.__name__
            error_msg = self.empty_error % {'class_name': class_name}
            raise Http404(error_msg)

        # Pagination size is set by the `.paginate_by` attribute,
        # which may be `None` to disable pagination.
        page_size = self.get_paginate_by(self.object_list)
        if page_size:
            packed = self.paginate_queryset(self.object_list, page_size)
            paginator, page, queryset, is_paginated = packed
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list)

        return Response(serializer.data)

    def get_queryset(self, *args, **kwargs):

        pname = self.request.path.split('/')[4]
        limit = self.request.QUERY_PARAMS.get('limit',
                                              settings.PAGINATION['max_limit'])
        limit = int(limit)
        t1 = self.request.QUERY_PARAMS.get('t1', None)
        t2 = self.request.QUERY_PARAMS.get('t2', None)
        pid = None
        if ('pid' in kwargs):
            pid = kwargs['pid']
        if (pid is None):
            self.serializer_class = SProbeSerializer
            try:
                return SProbe.objects.filter(name=pname).order_by('-ts')[0:limit]
            except:
                e_msg = ('No smart probe instances exist for: %s' % pname)
                handle_exception(Exception(e_msg), self.request)

        command = None
        if ('command' in kwargs):
            command = kwargs['command']
        if (command is None):
            self.serializer_class = SProbeSerializer
            self.paginate_by = None
            return SProbe.objects.filter(name=pname, id=pid)

        if (command != 'data'):
            e_msg = ('unknown command: %s' % repr(command))
            handle_exception(Exception(e_msg), self.request)

        ro = None
        try:
            ro = SProbe.objects.get(name=pname, id=pid)
        except:
            e_msg = ('Probe: %s with id: %s does not exist' % (pname,
                                                               pid))
            handle_exception(Exception(e_msg), self.request)

        if (t1 is not None and t2 is not None):
            return self.model_obj.objects.filter(rid=ro, ts__gt=t1,
                                                 ts__lte=t2)
        return self.model_obj.objects.filter(rid=ro).order_by('-ts')[0:limit]

    def _validate_probe(self, pname, pid, request):
        try:
            return SProbe.objects.get(name=pname, id=pid)
        except:
            e_msg = ('Probe: %s with id: %s does not exist' % (pname, pid))
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def post(self, request, pid=None, command=None):
        """
        start or stop a smart probe
        """
        #get the task uuid from the url string
        pname = request.path.split('/')[4]
        task = {}
        ro = None
        if (pid is None): #start a probe
            #if there's a recipe already running, throw error
            if (SProbe.objects.filter(name=pname,
                                      state__regex=r'(created|running)').exists()):
                e_msg = ('Smart probe: %s already running' % pname)
                handle_exception(Exception(e_msg), request)
            #if max number of probes already running, throw error
            num_live = len(SProbe.objects.filter(state__regex=r'(created|running'))
            if (num_live > settings.MAX_TAP_WORKERS):
                e_msg = ('Maximum number(%d) of smart probes running. Cannot '
                         'start another one until one of them is stopped' %
                         settings.MAX_TAP_WORKERS)
                handle_exception(Exception(e_msg), request)

            #get last id
            cur_id = 0
            try:
                cur_id = SProbe.objects.all().order_by('-ts')[0].id
            except:
                logger.info('no previous probe ids found for: %s' % pname)

            ro = SProbe(name=pname, smart=True, state='created')
            ro.save()
            kernel_module = os.path.join(settings.TAP_DIR,
                                         TAP_MAP[pname]['location'] + '.ko')
            task = {
                'module': kernel_module,
                'tap': pname,
                'action': 'start',
                'roid': cur_id + 1,
                }
        else:
            ro = self._validate_probe(pname, pid, request)
            if (command not in ('stop', 'status',)):
                e_msg = ('command: %s not supported.' % command)
                handle_exception(Exception(e_msg), request)
            if (command == 'status'):
                return self._paginated_response((ro,), request)
            if (ro.state == 'stopped' or ro.state == 'error'):
                e_msg = ('Probe: %s with id: %s already in state: %s. It '
                         'cannot be stopped.' % (pname, pid, ro.state))
                handle_exception(Exception(e_msg), request)
            task = {
                'tap': pname,
                'action': 'stop',
                'roid': ro.id,
                }

        ctx = zmq.Context()
        task_socket = ctx.socket(zmq.PUSH)
        task_socket.connect('tcp://%s:%d' % settings.TAP_SERVER)
        task_socket.send_json(task)
        return self._paginated_response((ro,), request)

    def _paginated_response(self, qs, request):
        p = Paginator(qs, 100)
        data = p.page(1)
        serializer_context = {'request': request}
        serializer = PaginatedSProbe(data, context=serializer_context)
        return Response(serializer.data)
