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
from system.osi import run_command
from system.services import systemctl
from system.nis import configure_nis
from django.db import transaction
from smart_manager.views.base_service import BaseServiceDetailView
from smart_manager.models import Service

import logging

logger = logging.getLogger(__name__)


class NISServiceView(BaseServiceDetailView):
    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        with self._handle_exception(request):
            service = Service.objects.get(name="nis")
            if command == "config":
                try:
                    config = request.data["config"]
                    configure_nis(config["domain"], config["server"])
                    self._save_config(service, config)
                except Exception as e:
                    logger.exception(e)
                    e_msg = "NIS could not be configured. Try again"
                    handle_exception(Exception(e_msg), request)

            else:
                try:
                    if command == "stop":
                        systemctl("ypbind", "disable")
                        systemctl("ypbind", "stop")
                    else:
                        # To instantiate our above config changes in /etc/yp.conf we:
                        run_command(["netconfig", "update", "-f"])
                        systemctl("ypbind", "enable")
                        systemctl("ypbind", "start")
                except Exception as e:
                    logger.exception(e)
                    e_msg = "Failed to %s NIS service due to system error." % command
                    handle_exception(Exception(e_msg), request)

            return Response()
