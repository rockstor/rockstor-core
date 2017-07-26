"""
Copyright (c) 2012-2014 RockStor, Inc. <http://rockstor.com>
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
from django.conf import settings
from storageadmin.models import Share
from fs.btrfs import mount_share
import re
import shutil

import logging
logger = logging.getLogger(__name__)


class DockerServiceView(BaseServiceDetailView):
    name = 'docker'

    def _validate_root(self, request, root):
        try:
            return Share.objects.get(name=root)
        except Exception as e:
            logger.exception(e)
            e_msg = ('Share(%s) does not exist' % root)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, command):
        service = Service.objects.get(name=self.name)

        if (command == 'config'):
            config = request.data.get('config', None)
            root_share = config['root_share']
            self._validate_root(request, root_share)
            self._save_config(service, config)

        elif (command == 'start'):
            try:
                config = self._get_config(service)
            except:
                e_msg = ('Cannot start without configuration. '
                         'Please configure(System->Services) and try again.')
                handle_exception(Exception(e_msg), request)

            share = self._validate_root(request, config['root_share'])
            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
            if not share.is_mounted:
                mount_share(share, mnt_pt)

            inf = ('%s/docker.service' % (settings.CONFROOT))
            outf = '/etc/systemd/system/docker.service'
            with open(inf) as ino, open(outf, 'w') as outo:
                for l in ino.readlines():
                    if (re.match('ExecStart=', l) is not None):
                        outo.write('%s %s\n' % (l.strip(), mnt_pt))
                    else:
                        outo.write(l)
            socket_file = ('%s/docker.socket' % (settings.CONFROOT))
            shutil.copy(socket_file, '/etc/systemd/system/docker.socket')
            systemctl(self.name, 'enable')
            systemctl(self.name, 'start')
        elif (command == 'stop'):
            systemctl(self.name, 'stop')
            systemctl(self.name, 'disable')
        return Response()
