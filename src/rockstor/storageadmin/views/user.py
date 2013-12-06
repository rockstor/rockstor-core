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
from django.db import transaction
from django.conf import settings
from storageadmin.util import handle_exception
from django.contrib.auth.models import User as DjangoUser
from storageadmin.serializers import UserSerializer
from storageadmin.models import User
from generic_view import GenericView
from system.users import (useradd, usermod, userdel, get_epasswd, get_users,
                          update_shell)
from storageadmin.exceptions import RockStorAPIException

import logging
logger = logging.getLogger(__name__)

class UserView(GenericView):
    serializer_class = UserSerializer

    def get_queryset(self, *args, **kwargs):
        if ('username' in kwargs):
            self.paginate_by = 0
            try:
                return DjangoUser.objects.get(username=kwargs['username'])
            except:
                return []
        return DjangoUser.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        try:
            username = request.DATA['username']
            password = request.DATA['password']
            is_active = request.DATA['is_active']

            # Check that a django user with the same name does not exist
            if (DjangoUser.objects.filter(username=username).exists() or
                User.objects.filter(username=username).exists()):
                e_msg = ('user: %s already exists. Please choose a different'
                         'username' % username)
                handle_exception(Exception(e_msg), request)

            # Check that a unix user with the same name does not exist
            unix_users = get_users(min_uid=0, uname=username)
            if (username in unix_users):
                e_msg = ('user: %s exists as a system user. Please choose a '
                         'different username' % username)
                handle_exception(Exception(e_msg), request)

            # Create Django user
            auser = DjangoUser.objects.create_user(username, None, password)
            auser.is_active = is_active
            auser.save()

            # Create unix user
            max_uid = settings.START_UID
            shell = settings.DEFAULT_SHELL
            if (is_active):
                shell = settings.ADMIN_SHELL
            try:
                # Find max uid
                max_uid = User.objects.all().order_by('-uid')[0].uid
            except Exception, e:
                logger.exception(e)
                pass
            uid = max_uid + 1
            useradd(username, uid, shell)
            usermod(username, password)
            suser = User(username=username, uid=uid, gid=uid, user=auser)
            suser.save()

            return Response(UserSerializer(auser).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, username):
        user = self._get_user_object(request, username)
        try:
            # if password is present in input data, change password
            if ('password' in request.DATA):
                # change password
                password = request.DATA['password']
                usermod(username, password)
                user.set_password(password)
                user.save()
            # check if admin attribute has changed
            if ('is_active' in request.DATA):
                is_active = request.DATA['is_active']
                # put is through bacbone model save so is_active comes in
                # as a boolean
                if is_active != user.is_active:
                    if request.user.username == username:
                        e_msg = ('Cannot modify admin attribute of the '
                                 'currently logged in user')
                        handle_exception(Exception(e_msg), request)
                    user.is_active = is_active
                    shell = settings.DEFAULT_SHELL
                    if (is_active is True):
                        shell = settings.ADMIN_SHELL
                    update_shell(username, shell)
                    user.save()
            return Response(UserSerializer(user).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, username):
        user = self._get_user_object(request, username)
        try:
            if request.user.username == username:
                e_msg = ('Cannot delete the currently logged in user')
                handle_exception(Exception(e_msg), request)

            epw = get_epasswd(username)
            logger.debug('epw: %s' % repr(epw))
            if (epw is not None):
                userdel(username)
            user.delete()
            return Response()
        except Exception, e:
            handle_exception(e, request)

    def _get_user_object(self, request, username):
        try:
            user = DjangoUser.objects.get(username=username)
            return user
        except:
            e_msg = ('user: %s does not exist' % username)
            logger.debug(e_msg)
            handle_exception(Exception(e_msg), request)

