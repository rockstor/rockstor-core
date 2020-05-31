"""
Copyright (c) 2012-2020 Rockstor, Inc. <http://rockstor.com>
This file is part of Rockstor.

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

from base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.util import handle_exception
from system.ssh import toggle_sftp_service

logger = logging.getLogger(__name__)


class SFTPServiceView(BaseServiceDetailView):
    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service_name = "sftp"
        service = Service.objects.get(name=service_name)
        if command == "config":
            #  nothing to really configure atm. just save the model
            try:
                config = request.data["config"]
                self._save_config(service, config)
            except Exception as e:
                logger.exception(e)
                e_msg = "SFTP could not be configured. Try again"
                handle_exception(Exception(e_msg), request)

        else:
            try:
                if command == "start":
                    toggle_sftp_service()
                else:
                    toggle_sftp_service(switch=False)
            except Exception as e:
                logger.exception(e)
                e_msg = "Failed to {} SFTP due to a system error.".format(command)
                handle_exception(Exception(e_msg), request)
        return Response()
