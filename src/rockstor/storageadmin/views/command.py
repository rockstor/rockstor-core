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

"""
System info etc..
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from system.osi import (uptime, refresh_nfs_exports)
from storageadmin.models import NFSExport
from nfs_helpers import create_nfs_export_input2
from storageadmin.util import handle_exception
from datetime import datetime
from django.utils.timezone import utc

import logging
logger = logging.getLogger(__name__)


class CommandView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, command):
        if (command == 'bootstrap'):
            try:
                logger.info('bootstrapping')
                exports = create_nfs_export_input2(NFSExport.objects.all())
                logger.info('export = %s' % exports)
                refresh_nfs_exports(exports)
                return Response()
            except Exception, e:
                e_msg = ('Unable to export all nfs shares due to a system error')
                logger.error(e_msg)
                logger.exception(e)
                handle_exception(Exception(e_msg), request)

        elif (command == 'utcnow'):
            return Response(datetime.utcnow().replace(tzinfo=utc))

        elif (command == 'uptime'):
            return Response(uptime())

