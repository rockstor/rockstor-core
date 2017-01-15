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
from system.pkg_mgmt import install_pkg
from django.db import transaction
from base_service import BaseServiceDetailView
from contextlib import contextmanager
from storageadmin.exceptions import RockStorAPIException
import os

import logging
logger = logging.getLogger(__name__)


class AFPServiceView(BaseServiceDetailView):

    service_name = 'netatalk'

    @staticmethod
    @contextmanager
    def _handle_exception(request, msg):
        try:
            yield
        except RockStorAPIException:
            raise
        except Exception as e:
            handle_exception(e, request, msg)

    @transaction.atomic
    def post(self, request, command):
        """
        execute a command on the service
        """
        e_msg = ('Failed to %s AFP service due to system error.' %
                 command)
        with self._handle_exception(request, e_msg):
            if (command == 'start'):
                if (not os.path.exists('/usr/sbin/afpd')):
                    install_pkg(self.service_name)
            self._switch_afpd(command)

        return Response()

    @classmethod
    def _switch_afpd(cls, switch):
        if (switch == 'start'):
            systemctl(cls.service_name, 'enable')
            systemctl(cls.service_name, 'start')
        else:
            systemctl(cls.service_name, 'disable')
            systemctl(cls.service_name, 'stop')
