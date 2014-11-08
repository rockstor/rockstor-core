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
from storageadmin.serializers import SUserSerializer
from storageadmin.models import User
import rest_framework_custom as rfc
from system.users import (useradd, usermod, userdel, get_users,
                          update_shell, smbpasswd, add_ssh_key)
from storageadmin.exceptions import RockStorAPIException
import pwd
from system.ssh import is_pub_key
import logging
logger = logging.getLogger(__name__)


class UserView(rfc.GenericView):
    serializer_class = SUserSerializer
    exclude_list = ('root', 'nobody', 'bin', 'daemon', 'adm', 'sync',
                    'shutdown', 'halt', 'mail', 'operator', 'dbus', 'rpc',
                    'avahi', 'avahi-autoipd', 'rpcuser', 'nfsnobody',
                    'postgres', 'ntp', 'nginx', 'postfix', 'sshd', )

    def get_queryset(self, *args, **kwargs):
        if ('username' in kwargs):
            self.paginate_by = 0
            try:
                return User.objects.get(username=kwargs['username'])
            except:
                return []
        return self._combined_users()

    def _combined_users(self):
        users = list(User.objects.all())
        sys_users = get_users(min_uid=0)
        for u in sys_users.keys():
            if (User.objects.filter(username=u).exists()):
                continue
            users.append(User(username=u, uid=int(sys_users[u][0]),
                              gid=int(sys_users[u][1]), admin=False))
        return users

    def _validate_input(self, request):
        input_fields = {}
        username = request.DATA.get('username', None)
        if (username is None or username == ''):
            e_msg = ('Username must be a valid string')
            handle_exception(Exception(e_msg), request)
        input_fields['username'] = username
        password = request.DATA.get('password', None)
        if (password is None or password == ''):
            e_msg = ('Password must be a valid string')
            handle_exception(Exception(e_msg), request)
        input_fields['password'] = password
        admin = request.DATA.get('admin', False)
        if (type(admin) != bool):
            e_msg = ('Admin(user type) must be a boolean')
            handle_exception(Exception(e_msg), request)
        input_fields['admin'] = admin
        shell = request.DATA.get('shell', '/bin/bash')
        if (shell not in settings.VALID_SHELLS):
            e_msg = ('shell(%s) is not valid. Valid shells are %s' %
                     (shell, settings.VALID_SHELLS))
            handle_exception(Exception(e_msg), request)
        input_fields['shell'] = shell
        email = request.DATA.get('email', None)
        if (email is not None and type(email) != unicode):
            e_msg = ('Email must be a valid string. not: %s' % type(email))
            handle_exception(Exception(e_msg), request)
        input_fields['email'] = email
        input_fields['homedir'] = request.DATA.get(
            'homedir', '/home/%s' % username)
        input_fields['uid'] = request.DATA.get('uid', None)
        input_fields['gid'] = request.DATA.get('gid', None)
        input_fields['public_key'] = self._validate_public_key(request)
        return input_fields

    def _validate_public_key(self, request):
        public_key = request.DATA.get('public_key', None)
        if (public_key is not None and not is_pub_key(public_key)):
            e_msg = ('Public key is invalid')
            handle_exception(Exception(e_msg), request)

    @transaction.commit_on_success
    def post(self, request):
        try:
            invar = self._validate_input(request)

            # Check that a django user with the same name does not exist
            e_msg = ('user: %s already exists. Please choose a different'
                     ' username' % invar['username'])
            if (DjangoUser.objects.filter(
                    username=invar['username']).exists()):
                handle_exception(Exception(e_msg), request)
            users = self._combined_users()
            for u in users:
                if (u.username == invar['username']):
                    handle_exception(Exception(e_msg), request)
                if (u.uid == invar['uid']):
                    e_msg = ('uid: %d already exists.' % invar['uid'])
                    handle_exception(Exception(e_msg), request)
                if (u.gid == invar['gid']):
                    e_msg = ('gic: %d already exists.' % invar['gid'])
                    handle_exception(Exception(e_msg), request)

            if (invar['admin']):
                # Create Django user
                auser = DjangoUser.objects.create_user(invar['username'],
                                                       None, invar['password'])
                auser.is_active = True
                auser.save()

            useradd(invar['username'], invar['shell'], uid=invar['uid'],
                    gid=invar['gid'])
            pw_entries = pwd.getpwnam(invar['username'])
            invar['uid'] = pw_entries[2]
            invar['gid'] = pw_entries[3]
            usermod(invar['username'], invar['password'])
            smbpasswd(invar['username'], invar['password'])
            if (invar['public_key'] is not None):
                add_ssh_key(invar['username'], invar['public_key'])
            del(invar['password'])
            suser = User(**invar)
            suser.save()
            return Response(SUserSerializer(suser).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def put(self, request, username):
        suser = self._get_user_object(request, username)
        try:
            # if password is present in input data, change password
            if ('password' in request.DATA):
                # change password
                password = request.DATA['password']
                usermod(username, password)
                smbpasswd(username, password)
                suser.user.set_password(password)
                suser.user.save()
            # check if admin attribute has changed
            if ('is_active' in request.DATA):
                is_active = request.DATA['is_active']
                # put is through bacbone model save so is_active comes in
                # as a boolean
                if is_active != suser.user.is_active:
                    if request.user.username == username:
                        e_msg = ('Cannot modify admin attribute of the '
                                 'currently logged in user')
                        handle_exception(Exception(e_msg), request)
                    suser.user.is_active = is_active
                    shell = settings.DEFAULT_SHELL
                    if (is_active is True):
                        shell = settings.ADMIN_SHELL
                    update_shell(username, shell)
                    suser.user.save()
                    suser.save()
            if ('public_key' in request.DATA):
                add_ssh_key(username, request.DATA['public_key'])
                suser.public_key = request.DATA['public_key']
                suser.save()
            return Response(UserSerializer(suser.user).data)
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
            user.delete()
            if (epw is not None):
                userdel(username)
            return Response()
        except RockStorAPIException:
            raise
        except Exception, e:
            logger.exception(e)
            e_msg = ('User deletion is not currently supported.')
            handle_exception(Exception(e_msg), request)

    def _get_user_object(self, request, username):
        try:
            return User.objects.get(username=username)
        except:
            e_msg = ('user: %s does not exist' % username)
            logger.debug(e_msg)
            handle_exception(Exception(e_msg), request)
