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

import shutil
from rest_framework.response import Response
from storageadmin.util import handle_exception
from system.services import systemctl
from system.samba import (update_global_config, restart_samba)
from django.db import transaction
from django.conf import settings
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from storageadmin.models import SambaShare
from system.osi import md5sum

import logging
logger = logging.getLogger(__name__)


class SambaServiceView(BaseServiceDetailView):

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service_name = 'smb'
        service = Service.objects.get(name=service_name)
        if (command == 'config'):
            aso = Service.objects.get(name='active-directory')
            if (aso.config is not None):
                e_msg = ('Active Directory service is configured, so '
                         'Workgroup is automatically retrieved and cannot '
                         'be set manually')
                handle_exception(Exception(e_msg), request)

            try:
                config = request.data.get('config', {'workgroup': 'MYGROUP',})
                workgroup = config['workgroup']
                self._save_config(service, config)
                update_global_config(workgroup)
                restart_samba(hard=True)
            except Exception, e:
                e_msg = ('Samba could not be configured. Try again. '
                         'Exception: %s' % e.__str__())
                handle_exception(Exception(e_msg), request)
        else:
            try:
                if (command == 'stop'):
                    systemctl('smb', 'disable')
                    systemctl('nmb', 'disable')
                else:
                    systemd_name = '%s.service' % service_name
                    ss_dest = ('/etc/systemd/system/%s' % systemd_name)
                    ss_src = ('%s/%s' % (settings.CONFROOT, systemd_name))
                    sum1 = md5sum(ss_dest)
                    sum2 = md5sum(ss_src)
                    if (sum1 != sum2):
                        shutil.copy(ss_src, ss_dest)
                    systemctl('smb', 'enable')
                    systemctl('nmb', 'enable')
                systemctl('nmb', command)
                systemctl('smb', command)
            except Exception, e:
                e_msg = ('Failed to %s samba due to a system error: %s' % (command, e.__str__()))
                handle_exception(Exception(e_msg), request)
        return Response()
