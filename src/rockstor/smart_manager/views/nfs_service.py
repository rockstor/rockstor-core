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
from system.services import init_service_op, chkconfig
from system.nis import configure_nis
from django.db import transaction
from base_service import BaseServiceView
from smart_manager.models import Service

import logging
logger = logging.getLogger(__name__)


class NFSServiceView(BaseServiceView):

    @transaction.commit_on_success
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name='nfs')
        if (command == 'config'):
            #nothing to really configure atm. just save the model
            try:
                config = request.DATA['config']
                self._save_config(service, config)
            except Exception, e:
                logger.exception(e)
                e_msg = ('NFS could not be configured. Try again')
                handle_exception(Exception(e_msg), request)

        else:
            try:
                switch = 'on'
                if (command == 'stop'):
                    switch = 'off'
                chkconfig('nfs', switch)
                init_service_op('nfs', command)
            except Exception, e:
                logger.exception(e)
                e_msg = ('Failed to %s NFS due to a system error.')
                handle_exception(Exception(e_msg), request)

        return Response()
