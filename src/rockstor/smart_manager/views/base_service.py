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

from smart_manager.models import Service, ServiceStatus
from django.conf import settings
from smart_manager.serializers import ServiceStatusSerializer
import json
import rest_framework_custom as rfc
from rest_framework.response import Response
from system.services import service_status
from django.db import transaction
from django.utils.timezone import utc
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ServiceMixin(object):
    def _save_config(self, service, config):
        if config is not None:
            service.config = json.dumps(config)
        else:
            service.config = None
        return service.save()

    def _get_config(self, service):
        return json.loads(service.config)

    def _get_or_create_sso(self, service):
        ts = datetime.utcnow().replace(tzinfo=utc)
        so = None
        if ServiceStatus.objects.filter(service=service).exists():
            so = ServiceStatus.objects.filter(service=service).order_by("-ts")[0]
        else:
            so = ServiceStatus(service=service, count=0)
        so.status = self._get_status(service)
        so.count += 1
        so.ts = ts
        so.save()
        return so

    def _get_status(self, service):
        try:
            config = None
            if service.config is not None:
                config = self._get_config(service)

            o, e, rc = service_status(service.name, config)
            if rc == 0:
                return True
            return False
        except Exception as e:
            msg = "Exception while querying status of service(%s): %s" % (
                service.name,
                e.__str__(),
            )
            logger.error(msg)
            logger.exception(e)
            return False


class BaseServiceView(ServiceMixin, rfc.GenericView):
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
                return sorted(
                    sos, cmp=lambda x, y: cmp(x.display_name, y.display_name)
                )  # noqa


class BaseServiceDetailView(ServiceMixin, rfc.GenericView):
    serializer_class = ServiceStatusSerializer

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        with self._handle_exception(self.request, msg=None):
            url_fields = self.request.path.strip("/").split("/")
            s = Service.objects.get(name=url_fields[3])
            self.paginate_by = 0
            serialized_data = ServiceStatusSerializer(self._get_or_create_sso(s))
            return Response(serialized_data.data)
