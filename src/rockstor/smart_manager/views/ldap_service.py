"""
Copyright (c) 2012-2021 RockStor, Inc. <http://rockstor.com>
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

import logging
import socket
from os.path import dirname

from django.db import transaction
from rest_framework.response import Response

from .base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.util import handle_exception
from system.directory_services import (
    update_nss,
    sssd_add_ldap,
    sssd_remove_ldap,
    validate_tls_cert,
    sssd_update_services,
)
from system.services import systemctl

logger = logging.getLogger(__name__)


class LdapServiceView(BaseServiceDetailView):
    @staticmethod
    def _resolve_check(server, request):
        try:
            socket.gethostbyname(server)
        except Exception as e:
            e_msg = (
                "The LDAP server({}) could not be resolved. Check "
                "your DNS configuration and try again. "
                "Lower level error: {}".format(server, e.__str__())
            )
            handle_exception(Exception(e_msg), request)

    def _config(self, service, request):
        try:
            return self._get_config(service)
        except Exception as e:
            e_msg = (
                "Missing configuration. Please configure the "
                "service and try again. Exception: {}".format(e.__str__())
            )
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        with self._handle_exception(request):
            service = Service.objects.get(name="ldap")
            if command == "config":
                try:
                    config = request.data["config"]

                    # Name resolution check
                    self._resolve_check(config.get("server"), request)

                    self._save_config(service, config)
                except Exception as e:
                    logger.exception(e)
                    e_msg = "LDAP could not be configured. Try again"
                    handle_exception(Exception(e_msg), request)

            elif command == "start":
                # Get config from database
                config = self._config(service, request)
                server = config.get("server")
                cert = config.get("cert")

                # @todo: add NTP check as for active_directory?
                # Name resolution check
                self._resolve_check(server, request)

                # TLS certificate check
                validate_tls_cert(server, cert)

                # Extract and format all info of interest
                ldap_params = {
                    "server": server,
                    "basedn": config.get("basedn"),
                    "ldap_uri": "".join(["ldap://", server]),
                    "cacertpath": cert,
                    "cacert_dir": dirname(cert),
                    "enumerate": config.get("enumerate"),
                }
                # Update SSSD config
                try:
                    sssd_add_ldap(ldap_params)
                    # Ensure ifp service is activated
                    sssd_update_services(service="ifp")
                    systemctl("sssd", "enable")
                except Exception as e:
                    logger.exception(e)
                    e_msg = "Failed to start LDAP service due to system error."
                    handle_exception(Exception(e_msg), request)
                # Update nsswitch.conf
                update_nss(["passwd", "group"], "sss")

            elif command == "stop":
                config = self._config(service, request)
                try:
                    sssd_remove_ldap(config.get("server"))
                    systemctl("sssd", "disable")
                    systemctl("sssd", "stop")
                except Exception as e:
                    logger.exception(e)
                    e_msg = "Failed to stop LDAP service due to system error."
                    handle_exception(Exception(e_msg), request)
                # Remove domain from SSSD config
                update_nss(["passwd", "group"], "sss", remove=True)

            return Response()
