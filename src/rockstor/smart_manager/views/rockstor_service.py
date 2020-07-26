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

from rest_framework.response import Response
from storageadmin.util import handle_exception
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.models import NetworkConnection
import ztask_helpers


import logging

logger = logging.getLogger(__name__)


class RockstorServiceView(BaseServiceDetailView):
    name = "rockstor"

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name=self.name)
        if command == "config":
            try:
                config = request.data.get("config")
                try:
                    listener_port = int(config["listener_port"])
                except ValueError:
                    raise Exception(
                        "Listener Port must be a valid port number between 0-65535"
                    )

                if listener_port < 0 or listener_port > 65535:
                    raise Exception("Invalid listener port(%d)" % listener_port)
                ni = config["network_interface"]
                if len(ni.strip()) == 0:  # empty string
                    ztask_helpers.restart_rockstor.async(None, listener_port)
                else:
                    try:
                        nco = NetworkConnection.objects.get(name=ni)
                    except NetworkConnection.DoesNotExist:
                        raise Exception("Network Connection(%s) does not exist." % ni)
                    # @todo: we should make restart transparent to the user.
                    ztask_helpers.restart_rockstor.async(nco.ipaddr, listener_port)
                self._save_config(service, config)
                return Response()
            except Exception as e:
                e_msg = (
                    "Failed to configure Rockstor service. Try again. "
                    "Exception: %s" % e.__str__()
                )
                handle_exception(Exception(e_msg), request)

        e_msg = (
            "%s service can only be configured from the UI. When "
            "configured, it is automatically restarted. To explicitly "
            "start/stop/restart, login to the terminal and use "
            "systemctl" % self.name
        )
        handle_exception(Exception(e_msg), request)
