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
from system.services import superctl
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.models import NetworkConnection

import logging

logger = logging.getLogger(__name__)


class ReplicationServiceView(BaseServiceDetailView):
    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name="replication")
        if command == "config":
            try:
                config = request.data["config"]
                try:
                    listener_port = int(config["listener_port"])
                except ValueError:
                    raise Exception(
                        "Listener Port must be a valid port number between 0-65535"
                    )

                if listener_port < 0 or listener_port > 65535:
                    raise Exception("Invalid listener port(%d)" % listener_port)
                ni = config["network_interface"]
                if not NetworkConnection.objects.filter(name=ni).exists():
                    raise Exception("Network Interface(%s) does not exist." % ni)
                self._save_config(service, config)
                return Response()
            except Exception as e:
                e_msg = (
                    "Failed to configure Replication. Try again. "
                    "Exception: %s" % e.__str__()
                )
                handle_exception(Exception(e_msg), request)

        if command == "start":
            try:
                config = self._get_config(service)
            except:
                e_msg = (
                    "Configuration undefined. Configure the service "
                    "first before starting."
                )
                handle_exception(Exception(e_msg), request)

            if not NetworkConnection.objects.filter(
                name=config["network_interface"]
            ).exists():
                e_msg = (
                    "Network interface does not exist. Update your "
                    "configuration and try again."
                )
                handle_exception(Exception(e_msg), request)
        try:
            superctl(service.name, command)
            return Response()
        except Exception as e:
            e_msg = "Failed to %s Replication due to an error: %s" % (
                command,
                e.__str__(),
            )
            handle_exception(Exception(e_msg), request)
