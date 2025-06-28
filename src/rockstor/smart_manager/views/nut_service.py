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

import logging
from django.db import transaction
from rest_framework.response import Response
from smart_manager.models import Service
from smart_manager.views import BaseServiceDetailView
from storageadmin.util import handle_exception
from system.nut import configure_nut
from system.services import systemctl

logger = logging.getLogger(__name__)


class NUTServiceView(BaseServiceDetailView):
    service_name = "nut"

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        with self._handle_exception(request):
            service = Service.objects.get(name=self.service_name)
            if command == "config":
                try:
                    config = request.data.get("config")
                    configure_nut(config)
                    self._save_config(service, config)
                except Exception as e:
                    logger.exception(e)
                    e_msg = "NUT could not be configured. Please try again"
                    handle_exception(Exception(e_msg), request)
            else:
                # By now command is != config so hopefully start or stop.
                # Try dealing with this command by passing to switch_nut
                # N.B. as config may not be good or even exist we try and
                # if exception then suggest config as cause.
                # Otherwise users would see system level error which is dumped
                # to logs. Email support is offered with log zip.
                try:
                    self._switch_nut(command, self._get_config(service))
                    logger.info("NUT-UPS toggled")
                except Exception as e:
                    logger.exception(e)
                    e_msg = (
                        "Failed to %s NUT-UPS service due to a system "
                        "error. Check the service is configured "
                        "correctly via it's spanner icon." % command
                    )
                    handle_exception(Exception(e_msg), request)
        return Response()

    @staticmethod
    def _switch_nut(switch, config):
        if switch == "start":
            # empty config causes a type error before we get here, this we
            # catch and suggest settings but just in case we check here also.
            if not config:
                raise Exception("NUT un-configured; please configure first.")
            # don't start nut-server when in netclient mode.
            if config["mode"] == "netclient":
                systemctl("nut-server", "disable")
                systemctl("nut-server", "stop")
            else:  # presumably starting in standalone or netserver mode
                systemctl("nut-server", "enable")
                systemctl("nut-server", "start")
            # in all three modes we always enable and reload nut-monitor
            systemctl("nut-monitor", "enable")
            systemctl("nut-monitor", "reload-or-restart")
        else:  # disable and stop monitor and server regardless of mode
            # just as well as config may have changed.
            systemctl("nut-monitor", "disable")
            systemctl("nut-monitor", "stop")
            systemctl("nut-server", "disable")
            systemctl("nut-server", "stop")
