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
from system.services import systemctl
from system.samba import (update_global_config, restart_samba)
from django.db import transaction
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.models import SambaShare

import logging
logger = logging.getLogger(__name__)


class SambaServiceView(BaseServiceDetailView):

    @transaction.commit_on_success
    def post(self, request, command):
        """
        execute a command on the service
        """
        service_name = 'smb'
        service = Service.objects.get(name=service_name)
        if (command == 'config'):
            #nothing to really configure atm. just save the model
            try:
                config = request.data.get('config', {'workgroup': 'MYGROUP',})
                workgroup = config['workgroup']
                self._save_config(service, config)
                update_global_config(workgroup)
                restart_samba()
            except Exception, e:
                e_msg = ('Samba could not be configured. Try again. '
                         'Exception: %s' % e.__str__())
                handle_exception(Exception(e_msg), request)
        else:
            try:
                switch = 'on'
                if (command == 'stop'):
                    switch = 'off'
                if (command == 'stop'):
                    systemctl('smb', 'disable')
                    systemctl('nmb', 'disable')
                else:
                    systemctl('smb', 'enable')
                    systemctl('nmb', 'enable')
                systemctl('smb', command)
                systemctl('nmb', command)
            except Exception, e:
                logger.exception(e)
                e_msg = ('Failed to %s samba due to a system error.' % command)
                handle_exception(Exception(e_msg), request)
        return Response()
