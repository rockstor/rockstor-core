"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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
from storageadmin.models import (Share, Disk)
from fs.btrfs import (mount_share, is_share_mounted)
import re
import shutil

import logging
logger = logging.getLogger(__name__)


class BootstrapServiceView(BaseServiceDetailView):
    name = 'rockstor-bootstrap'

    def post(self, request, command):
        service = Service.objects.get(name=self.name)

        if (command == 'start'):
            systemctl(self.name, 'enable')
            systemctl(self.name, 'start')
        elif (command == 'stop'):
            systemctl(self.name, 'stop')
            systemctl(self.name, 'disable')
        return Response()
