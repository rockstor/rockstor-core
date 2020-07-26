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
from system.services import systemctl
from django.db import transaction
from base_service import BaseServiceDetailView
from system.snmp import configure_snmp
from smart_manager.models import Service


import logging

logger = logging.getLogger(__name__)


class SNMPServiceView(BaseServiceDetailView):

    service_name = "snmpd"

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        e_msg = "Failed to %s SNMP service due to system error." % command
        with self._handle_exception(request, e_msg):
            if command == "config":
                service = Service.objects.get(name=self.service_name)
                config = request.data.get("config", {})
                if type(config) != dict:
                    e_msg = "config dictionary is required input"
                    handle_exception(Exception(e_msg), request)
                for option in (
                    "syslocation",
                    "syscontact",
                    "rocommunity",
                ):
                    if option not in config:
                        e_msg = "%s is missing in config" % option
                        handle_exception(Exception(e_msg), request)
                    if config[option] is None or config[option] == "":
                        e_msg = "%s cannot be empty" % option
                        handle_exception(Exception(e_msg), request)
                if "aux" not in config:
                    e_msg = "aux is missing in config: %s" % config
                    handle_exception(Exception(e_msg), request)
                if type(config["aux"]) != list:
                    e_msg = "aux must be a list in config: %s" % config
                    handle_exception(Exception(e_msg), request)

                configure_snmp(config)
                self._save_config(service, config)
            else:
                self._switch_snmp(command)
        return Response()

    @classmethod
    def _switch_snmp(cls, switch):
        if switch == "start":
            systemctl(cls.service_name, "enable")
            systemctl(cls.service_name, "start")
        else:
            systemctl(cls.service_name, "disable")
            systemctl(cls.service_name, "stop")
