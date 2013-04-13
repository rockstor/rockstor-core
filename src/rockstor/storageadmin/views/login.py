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
Login api. logs the user in, returns error if incorrect login .
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import (authenticate, login, logout)
from storageadmin.util import handle_exception

import logging
logger = logging.getLogger(__name__)

class LoginView(APIView):
    def post(self, request):
        try:
            username = request.DATA['username']
            password = request.DATA['password']
            user = authenticate(username=username, password=password)
            if (user is not None and user.is_active):
                login(request, user)
                logger.debug('logged in from api')
                return Response({'msg': 'logged in'})
            else:
                return Response(status = status.HTTP_401_UNAUTHORIZED)
        except Exception, e:
            handle_exception(e, request)

