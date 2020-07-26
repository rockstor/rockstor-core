"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

from smart_manager.models import Service
from django.conf import settings
from smart_manager.serializers import ServiceStatusSerializer
import rest_framework_custom as rfc
from django.db import transaction
from service_mixin import ServiceMixin
import logging

logger = logging.getLogger(__name__)
# TODO: BaseService2View should be a 'list' endpoint


class BaseServiceListView(ServiceMixin, rfc.GenericView):
    serializer_class = ServiceStatusSerializer

    @transaction.atomic
    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            limit = self.request.query_params.get(
                "limit", settings.REST_FRAMEWORK["MAX_LIMIT"]
            )
            limit = int(limit)
            url_fields = self.request.path.strip("/").split("/")
            if len(url_fields) < 4:
                sos = []
                for s in Service.objects.all():
                    sos.append(self._get_or_create_sso(s))
                return sos
