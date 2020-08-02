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
from system.services import systemctl
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from system.shell import update_shell_config, restart_shell
import json
import logging

logger = logging.getLogger(__name__)


class ShellInABoxServiceView(BaseServiceDetailView):
    service_name = "shellinaboxd"

    def post(self, request, command):
        service = Service.objects.get(name=self.service_name)

        if command == "config":
            config = request.data.get("config")
            self._save_config(service, config)
            shelltype = config.get("shelltype")
            css = config.get("css")
            update_shell_config(shelltype, css)
            restart_shell(self.service_name)

        elif command == "start":
            # Assert config from db to re-establish our config file.
            # Avoids using package default config on first enable.
            # TODO: config assert every time is a little heavy / overkill.
            config = json.loads(service.config)
            shelltype = config.get("shelltype")
            css = config.get("css")
            update_shell_config(shelltype, css)
            systemctl(self.service_name, "enable")
            systemctl(self.service_name, "start")

        elif command == "stop":
            systemctl(self.service_name, "stop")
            systemctl(self.service_name, "disable")

        return Response()
