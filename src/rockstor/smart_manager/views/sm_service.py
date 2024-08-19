"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

from rest_framework.response import Response
from storageadmin.util import handle_exception
from system.services import superctl
from django.db import transaction
from smart_manager.views.base_service import BaseServiceDetailView
from smart_manager.models import Service
import logging

logger = logging.getLogger(__name__)


class ServiceMonitorView(BaseServiceDetailView):
    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name="service-monitor")
        if command == "config":
            # nothing to really configure atm. just save the model
            try:
                config = request.data["config"]
                self._save_config(service, config)
            except Exception as e:
                logger.exception(e)
                e_msg = "Service Monitor could not be configured. Try again"
                handle_exception(Exception(e_msg), request)

        else:
            try:
                superctl(service.name, command)
            except Exception as e:
                logger.exception(e)
                e_msg = "Failed to %s Service Monitor due to a system error." % command
                handle_exception(Exception(e_msg), request)

        return Response()
