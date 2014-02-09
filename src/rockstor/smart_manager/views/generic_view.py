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

from rest_framework import generics
from rest_framework.response import Response
from django.http import Http404
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from django.conf import settings


class GenericView(generics.ListCreateAPIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

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
        page_size = self.request.QUERY_PARAMS.get('page_size',
                                                  self.get_paginate_by(self.object_list))
        if page_size:
            packed = self.paginate_queryset(self.object_list, page_size)
            paginator, page, queryset, is_paginated = packed
            serializer = self.get_pagination_serializer(page)
        else:
            serializer = self.get_serializer(self.object_list)

        return Response(serializer.data)

    def get_allow_empty(self):
        if (self.paginate_by is None):
            return True
        return False

    def get_paginate_by(self, foo):
        if (self.paginate_by is not None and self.paginate_by == 0):
            return None
        return settings.PAGINATION['page_size']

