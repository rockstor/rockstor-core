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
from oauth2_provider.models import Application as OauthApplication
from storageadmin.models import (OauthApp, User)
from storageadmin.serializers import OauthAppSerializer
import rest_framework_custom as rfc
from storageadmin.exceptions import RockStorAPIException
from storageadmin.util import handle_exception


class OauthAppView(rfc.GenericView):
    serializer_class = OauthAppSerializer

    def get_queryset(self, *args, **kwargs):
        if ('name' in self.kwargs):
            self.paginate_by = 0
            try:
                return OauthApp.objects.get(name=self.kwargs['name'])
            except:
                return []
        return OauthApp.objects.all()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            name = request.data['name']
            username = request.user.username
            if (OauthApp.objects.filter(name=name).exists()):
                e_msg = ('application with name: %s already exists.' % name)
                handle_exception(Exception(e_msg), request)

            try:
                user = User.objects.get(username=username)
            except:
                e_msg = ('User with name: %s does not exist' % username)
                handle_exception(Exception(e_msg), request)

            client_type = OauthApplication.CLIENT_CONFIDENTIAL
            auth_grant_type = OauthApplication.GRANT_CLIENT_CREDENTIALS
            app = OauthApplication(name=name, client_type=client_type,
                                   authorization_grant_type=auth_grant_type,
                                   user=user.user)
            app.save()
            oauth_app = OauthApp(name=name, application=app, user=user)
            oauth_app.save()
            return Response(OauthAppSerializer(oauth_app).data)

    @transaction.atomic
    def delete(self, request, name):
        with self._handle_exception(request):
            try:
                app = OauthApp.objects.get(name=name)
            except:
                e_msg = ('application with name: %s does not exist' % name)
                handle_exception(Exception(e_msg), request)

            app.application.delete()
            app.delete()
            return Response()
