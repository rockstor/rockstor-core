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
        service.config = json.dumps(config)
        return service.save()

    def _get_config(self, service):
        return json.loads(service.config)

    def _get_or_create_sso(self, service):
        ts = datetime.utcnow().replace(tzinfo=utc)
        so = None
        if (ServiceStatus.objects.filter(service=service).exists()):
            so = ServiceStatus.objects.filter(service=service).order_by('-ts')[0]
        else:
            so = ServiceStatus(service=service, count=0)
        so.status = self._get_status(service)
        so.count += 1
        so.ts = ts
        so.save()
        return so

    def _get_status(self, service):
        try:
            o, e, rc = service_status(service.name)
            if (rc == 0):
                return True
            return False
        except Exception, e:
            msg = ('Exception while querying status of service: %s' % service.name)
            logger.error(msg)
            logger.exception(e)
            return False
