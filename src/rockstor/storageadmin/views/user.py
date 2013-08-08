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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from storageadmin.auth import DigestAuthentication
from django.db import transaction
from django.conf import settings
from storageadmin.util import handle_exception
from django.contrib.auth.models import User as DjangoUser
from storageadmin.serializers import UserSerializer
from storageadmin.models import User
from generic_view import GenericView
from system.users import (useradd, usermod, userdel, get_epasswd, get_users)
from storageadmin.exceptions import RockStorAPIException

import logging
logger = logging.getLogger(__name__)

class UserView(GenericView):
    serializer_class = UserSerializer

    def get_queryset(self, *args, **kwargs):
        if ('username' in kwargs):
            self.paginate_by = None
            return User.objects.filter(name=kwargs['username'])
        return User.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        try:
            username = request.DATA['username']
            password = request.DATA['password']
            utype = request.DATA['utype']
            if (DjangoUser.objects.filter(username=username).exists() or
                User.objects.filter(name=username).exists()):
                e_msg = ('user: %s already exists. Choose a different'
                         'username' % username)
                handle_exception(Exception({'username': e_msg}), request)
            unix_users = get_users(min_uid=0, uname=username)
            if (username in unix_users):
                e_msg = ('user: %s exists as a system user. Choose a '
                         'different username' % username)
                handle_exception(Exception({'username': e_msg}), request)

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
            suser.save()
            return Response(UserSerializer(suser).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, username):
        suser, auser = self._get_user_objects(request, username)
        try:
            password = request.DATA['password']
            usermod(username, password)
            if (auser is not None):
                auser.set_password(password)
                auser.save()
            suser.password = get_epasswd(username)
            suser.save()
            return Response(UserSerializer(suser).data)
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, username):
        suser, auser = self._get_user_objects(request, username)
        try:
            epw = get_epasswd(username)
            logger.debug('epw: %s' % repr(epw))
            if (epw is not None):
                userdel(username)
            suser.delete()
            if (auser is not None):
                auser.delete()
            logger.debug('deleted user %s' % username)
            return Response()
        except Exception, e:
            handle_exception(e, request)

    def _get_user_objects(self, request, username):
        try:
            suser = User.objects.get(name=username)
            auser = None
            if (suser.admin is True):
                auser = DjangoUser.objects.get(username=username)
            return (suser, auser)
        except:
            e_msg = ('user: %s does not exist' % username)
            handle_exception(Exception(e_msg), request)
