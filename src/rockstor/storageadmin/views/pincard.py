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
            logger.debug(f"Command ({command}) received for username: ({user}).")
            if command == "create":
                response_data = save_pincard(user)
                logger.debug(f"Created/Recreated pincard for username: ({user}).")

            if command == "reset":
                uid = request.data.get("uid")
                pinlist = request.data.get("pinlist")
                reset_response, reset_status = reset_password(user, uid, pinlist)
                response_data = {"response": reset_response, "status": reset_status}
                logger.debug(f"Processed password reset request for username ({user}).")
                logger.debug(f"reset status: ({reset_status}).")

            return Response(response_data)

        e_msg = f"Unsupported command ({command}). Valid commands are create, reset."
        handle_exception(Exception(e_msg), request)
