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
from django.db import transaction

from system.pinmanager import save_pincard, reset_password

import rest_framework_custom as rfc
from storageadmin.util import handle_exception

import logging

logger = logging.getLogger(__name__)


class PincardView(rfc.GenericView):
    @transaction.atomic
    def post(self, request, command, user):

        with self._handle_exception(request):

            if command == "create":
                response_data = save_pincard(user)
                logger.debug("Created new pincard for user with uid ({}).".format(user))

            if command == "reset":
                uid = request.data.get("uid")
                pinlist = request.data.get("pinlist")
                reset_response, reset_status = reset_password(user, uid, pinlist)
                response_data = {"response": reset_response, "status": reset_status}
                logger.debug(
                    "Received password reset request for user ({}).".format(user)
                )

            return Response(response_data)
        e_msg = ("Unsupported command ({}). Valid commands are create, reset.").format(
            command
        )
        handle_exception(Exception(e_msg), request)
