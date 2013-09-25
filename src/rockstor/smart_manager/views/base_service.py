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

from smart_manager.models import (Service, ServiceStatus)
from django.conf import settings
from smart_manager.serializers import ServiceStatusSerializer
import logging
logger = logging.getLogger(__name__)
from advanced_sprobe import AdvancedSProbeView
import json


class BaseServiceView(AdvancedSProbeView):
    serializer_class = ServiceStatusSerializer

    def get_queryset(self, *args, **kwargs):

        limit = self.request.QUERY_PARAMS.get('limit',
                                              settings.PAGINATION['max_limit'])
        limit = int(limit)
        url_fields = self.request.path.strip('/').split('/')
        if (len(url_fields) < 4):
            sos = []
            for s in Service.objects.all():
                if (ServiceStatus.objects.filter(service=s).exists()):
                    so = ServiceStatus.objects.filter(service=s).order_by('-ts')[0]
                    sos.append(so)
            return sos
        s = Service.objects.get(name=url_fields[3])
        self.paginate_by = 0
        return ServiceStatus.objects.filter(service=s).order_by('-ts')[0]

    def _save_config(self, service, config):
        service.config = json.dumps(config)
        return service.save()
