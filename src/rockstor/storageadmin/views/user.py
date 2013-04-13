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
view for anything at the share level
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from django.db import transaction
from django.conf import settings
from storageadmin.util import handle_exception
from django.contrib.auth.models import User
from storageadmin.serializers import UserSerializer

import logging
logger = logging.getLogger(__name__)

class UserView(APIView):
    
    def get(self, request, id=None):
        try:
            if (id is None):
                return Response(UserSerializer(User.objects.all()).data)
            else:
                user = UserSerializer(User.objects.get(pk=id))
                return Response(user.data)
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def post(self, request):
        try:
            username = request.DATA['username']
            password = request.DATA['password']
            user = User.objects.create_user(username, None, password)
            return Response(UserSerializer(user).data)
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, id):
        try:
            password = request.DATA['password']
            user = User.objects.get(pk=id)
            user.set_password(password)
            user.save()
            return Response(UserSerializer(user).data)
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, id):
        try:
            user_to_delete = User.objects.get(pk=id)
            logger.debug('deleting user %s' % user_to_delete)
            user_to_delete.delete()
            return Response()
        except Exception, e:
            handle_exception(e, request)

