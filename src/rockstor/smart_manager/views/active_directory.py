"""
Copyright (c) 2012-2013 RockStor, Inc. <http://rockstor.com>
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
from system.services import (toggle_auth_service, systemctl)
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service

import logging
logger = logging.getLogger(__name__)


class ActiveDirectoryServiceView(BaseServiceDetailView):

    @transaction.atomic
    def post(self, request, command):

        with self._handle_exception(request):
            service = Service.objects.get(name='active-directory')
            if (command == 'config'):
                try:
                    config = request.data.get('config')
                    #1. Name resolution check

                    #2. ntp check

                    #3. realm discover check?
                    self._save_config(service, config)
                except Exception, e:
                    logger.exception(e)
                    e_msg = ('Active Directory integration could not be configured. Try again')
                    handle_exception(Exception(e_msg), request)

            elif (command == 'start'):
                #1. make sure ntpd is running, or else, don't start.

                #2. Name resolution check?

                #3. Add AD server to /etc/resolv.conf
                # Is this necessary or should we just add it as another name server to the management interface?

                #4. realmd stuff
                # Do we need to realm permit all?. depends on login-policy attribute in sssd.conf

                #5. Restart sshd to load the new PAM configuration.

                #6. Restart SSSD. Is this necessary?
                # systemctl restart sssd.service

                pass
            elif (command == 'stop'):
                pass

            return Response()
