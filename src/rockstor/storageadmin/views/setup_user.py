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

import re
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import transaction
from storageadmin.util import handle_exception
from django.contrib.auth.models import User as DjangoUser
from storageadmin.serializers import UserSerializer
from storageadmin.models import User, Setup
from system.users import (useradd, usermod, userdel, get_epasswd)
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

class SetupUserView(APIView):
    
    @transaction.commit_on_success
    def post(self, request):
        try:
            # check if any users have been created already
            # if so, throw an exception
            users = User.objects.all()
            if len(users) > 0:
                raise Exception("A user has already been created")

            # if no users have been created, proceed to create one
            username = request.DATA['username']
            password = request.DATA['password']
            utype = request.DATA['utype']
            admin = False
            if (utype == 'admin'):
                admin = True
                auser = DjangoUser.objects.create_user(username, None,
                                                       password)
            max_uid = settings.START_UID
            shell = settings.USER_SHELL
            try:
                max_uid = User.objects.all().order_by('-uid')[0].uid
            except:
                pass
            uid = max_uid + 1
            useradd(username, uid, shell)
            usermod(username, password)
            epw = get_epasswd(username)
            suser = User(name=username, password=epw, uid=uid,
                         gid=uid, admin=admin)
            
            # save setup status
            suser.save()
            setup = Setup.objects.all()[0]
            setup.setup_user = True
            setup.save()

            return Response(UserSerializer(suser).data)
        except Exception, e:
            handle_exception(e, request)


