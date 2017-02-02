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
from system.services import systemctl, service_status
from system.samba import (update_global_config, restart_samba,
                          get_global_config)
from django.db import transaction
from django.conf import settings
from base_service import BaseServiceDetailView
from smart_manager.models import Service
from system.osi import md5sum
from smart_manager.serializers import ServiceStatusSerializer

import logging
logger = logging.getLogger(__name__)


class SambaServiceView(BaseServiceDetailView):
    service_name = 'smb'

    @transaction.atomic
    def get(self, request, *args, **kwargs):
        with self._handle_exception(self.request, msg=None):
            so = Service.objects.get(name=self.service_name)
            config = get_global_config()
            self._save_config(so, config)
            sd = ServiceStatusSerializer(self._get_or_create_sso(so))
            return Response(sd.data)

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        service = Service.objects.get(name=self.service_name)

        if (command == 'config'):
            try:
                config = request.data.get('config', {})
                global_config = {}
                if 'global_config' in config:
                    gc_lines = config['global_config'].split('\n')
                    for l in gc_lines:
                        gc_param = l.strip().split(' = ')
                        if (len(gc_param) == 2):
                            if '=' in gc_param[0]:
                                raise Exception(
                                    'Syntax error, one param has wrong '
                                    'spaces around equal signs, '
                                    'please check syntax of '
                                    '\'%s\'' % ''.join(gc_param))
                            global_config[gc_param[0].strip().lower()] = gc_param[1].strip()  # noqa
                    # #E501 Default set current workgroup to one got via samba
                    # config page
                    global_config['workgroup'] = config['workgroup']
                else:
                    global_config = config
                # Check Active Directory config and status if AD configured and
                # ON set workgroup to AD retrieved workgroup else AD not
                # running and leave workgroup to one choosen by user
                adso = Service.objects.get(name='active-directory')
                adconfig = None
                adso_status = 1
                if (adso.config is not None):
                    adconfig = self._get_config(adso)
                    adso_out, adso_err, adso_status = service_status(
                        'active-directory', adconfig)
                    if adso_status == 0:
                        global_config['workgroup'] = adconfig['workgroup']
                    else:
                        adconfig = None

                self._save_config(service, global_config)
                update_global_config(global_config, adconfig)
                restart_samba(hard=True)
            except Exception as e:
                e_msg = ('Samba could not be configured. Try again. '
                         'Exception: %s' % e.__str__())
                handle_exception(Exception(e_msg), request)
        else:
            try:
                if (command == 'stop'):
                    systemctl('smb', 'disable')
                    systemctl('nmb', 'disable')
                else:
                    systemd_name = '%s.service' % self.service_name
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
            except Exception as e:
                e_msg = ('Failed to %s samba due to a system error: %s'
                         % (command, e.__str__()))
                handle_exception(Exception(e_msg), request)
        return Response()
