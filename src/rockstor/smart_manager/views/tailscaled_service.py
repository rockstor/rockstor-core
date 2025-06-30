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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import json
import logging

from django.db import transaction
from rest_framework.response import Response

from smart_manager.models import Service
from smart_manager.views.base_service import BaseServiceDetailView
from storageadmin.exceptions import RockStorAPIException
from storageadmin.util import handle_exception
from system.exceptions import CommandException
from system.services import systemctl
from system.tailscale import (
    tailscale_up,
    validate_ts_custom_config,
    get_ts_auth_url,
    tailscale_down,
    validate_ts_hostname,
    TS_NOT_INSTALLED_E_MSG,
)

logger = logging.getLogger(__name__)


class TailscaledServiceView(BaseServiceDetailView):
    name = "tailscaled"

    @transaction.atomic
    def post(self, request, command, action=None):
        service = Service.objects.get(name=self.name)

        if action == "login":
            # The tailscaled daemon should already be running when the Tailscale
            # service is configured, but still ensure that here
            systemctl(self.name, "start")
            config = None
            try:
                config = self._get_config(service)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "Cannot start without configuration. "
                    "Please configure (System->Services) and try again."
                )
                handle_exception(Exception(e_msg), request)
            # Start tailscale up so that it's creating the authURL
            tailscale_up(config=config, timeout=2)

            # Retrieve AuthURL and make sure it has been generated
            auth_url = get_ts_auth_url()
            logger.debug(f"Tailscale login URL was retrieved as: {auth_url}")
            # Save auth_url to service config so that we can create the login button
            config["auth_url"] = auth_url
            service.config = json.dumps(config)
            service.save()

        elif action == "logout":
            logger.debug("LOGOUT from tailscale is not yet implemented")

        elif command == "config":
            config = request.data.get("config", None)
            logger.debug(f"{service.display_name} config: {config}")
            if config is None:
                e_msg = (
                    f"No configuration for the {service.display_name} service could be found. "
                    "Please try again. If the problem persists, email support@rockstor.com "
                    "with this message, or inquire on our forum (https://forum.rockstor.com)."
                )
                raise RockStorAPIException(status_code=400, detail=e_msg)
            # Ensure hostname complies with requirements and adjust as needed
            config = validate_ts_hostname(config)
            # Parse and validate the custom_config key
            if "custom_config" in config:
                cc_lines = config["custom_config"].split("\n")
                cc_lines = validate_ts_custom_config(cc_lines)
                config["custom_config"] = cc_lines
            self._save_config(service, config)

            # As the user saves the Tailscale service config, we assume they want
            # to use it so we enable and start the tailscaled daemon.
            # This will create the tailscale tun device and allow us to get
            # an authURL during the "login" action
            try:
                systemctl(self.name, "stop")
                systemctl(self.name, "enable")
                systemctl(self.name, "start")
            except Exception as e:
                logger.exception(e)
                e_msg = "An error occurred with tailscaled.service."
                if e.__class__ == CommandException:
                    if e.err == [
                        "Failed to stop tailscaled.service: Unit tailscaled.service not loaded.",
                        "",
                    ]:
                        e_msg = TS_NOT_INSTALLED_E_MSG
                handle_exception(Exception(e_msg), request)

        elif command == "start":
            config = None
            try:
                config = self._get_config(service)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "Cannot start without configuration. "
                    "Please configure (System->Services) and try again."
                )
                handle_exception(Exception(e_msg), request)

            # Start tailscale
            # Account for install with restored Tailscale config, but no Tailscale installed.
            try:
                tailscale_up(config=config)
            except Exception as e:
                logger.exception(e)
                if e.__class__ == FileNotFoundError:
                    e_msg = TS_NOT_INSTALLED_E_MSG
                else:
                    e_msg = "An error occurred running `tailscale up`."
                handle_exception(Exception(e_msg), request)

        elif command == "stop":
            config = None
            try:
                # Ensure that auth_url is no-longer in the service's config
                config = self._get_config(service)
                found = config.pop("auth_url", None)
                if found is not None:
                    self._save_config(service, config)
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "An error occurred while trying to cleanup the auth_url "
                    "from the service's configuration."
                )
                handle_exception(Exception(e_msg), request)
            finally:
                tailscale_down(config=config)

        return Response()
