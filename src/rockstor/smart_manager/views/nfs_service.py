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
from smart_manager.models import Service

import logging

logger = logging.getLogger(__name__)


class NFSServiceView(BaseServiceDetailView):
    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name="nfs")
        service_name = "nfs-server"
        if command == "config":
            # nothing to really configure atm. just save the model
            try:
                config = request.data["config"]
                self._save_config(service, config)
            except Exception as e:
                e_msg = (
                    "NFS could not be configured due to the following "
                    "exception. You could try again. %s" % e.__str__()
                )
                handle_exception(Exception(e_msg), request)

        else:
            try:
                if command == "stop":
                    systemctl(service_name, "disable")
                    systemctl(service_name, "stop")
                else:
                    systemctl(service_name, "enable")
                    # chkconfig('rpcbind', 'on')
                    # init_service_op('rpcbind', command)
                    systemctl(service_name, "restart")
                # init_service_op('nfs', command)
            except Exception as e:
                e_msg = "Failed to %s NFS due to this error: %s" % (
                    command,
                    e.__str__(),
                )
                handle_exception(Exception(e_msg), request)

        return Response()
