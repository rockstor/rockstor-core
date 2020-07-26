"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
from oauth2_provider.models import Application as OauthApplication
from storageadmin.models import OauthApp, User
from storageadmin.serializers import OauthAppSerializer
import rest_framework_custom as rfc
from storageadmin.util import handle_exception


class OauthAppView(rfc.GenericView):
    serializer_class = OauthAppSerializer

    def get_queryset(self, *args, **kwargs):
        if "name" in self.kwargs:
            self.paginate_by = 0
            try:
                return OauthApp.objects.get(name=self.kwargs["name"])
            except:
                return []
        return OauthApp.objects.all()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            name = request.data.get("name")
            username = request.user.username
            if OauthApp.objects.filter(name=name).exists():
                e_msg = (
                    "Application with name ({}) already exists. Choose a "
                    "different name."
                ).format(name)
                handle_exception(Exception(e_msg), request, status_code=400)

            try:
                user = User.objects.get(username=username)
            except:
                e_msg = "User with name ({}) does not exist.".format(username)
                handle_exception(Exception(e_msg), request)

            client_type = OauthApplication.CLIENT_CONFIDENTIAL
            auth_grant_type = OauthApplication.GRANT_CLIENT_CREDENTIALS
            app = OauthApplication(
                name=name,
                client_type=client_type,
                authorization_grant_type=auth_grant_type,
                user=user.user,
            )
            app.save()
            oauth_app = OauthApp(name=name, application=app, user=user)
            oauth_app.save()
            return Response(OauthAppSerializer(oauth_app).data)

    @transaction.atomic
    def delete(self, request, id):
        with self._handle_exception(request):
            try:
                app = OauthApp.objects.get(id=id)
            except:
                e_msg = "Application with id ({}) does not exist.".format(id)
                handle_exception(Exception(e_msg), request)

            if app.name == settings.OAUTH_INTERNAL_APP:
                e_msg = (
                    "Application with id ({}) cannot be deleted because "
                    "it is "
                    "used internally by Rockstor. If you really need to "
                    "delete it, login as root and use "
                    "{}bin/delete-api-key command. If you do delete it, "
                    "please create another one with the same name as it "
                    "is required by Rockstor "
                    "internally."
                ).format(id, settings.ROOT_DIR)
                handle_exception(Exception(e_msg), request, status_code=400)

            app.application.delete()
            app.delete()
            return Response()
