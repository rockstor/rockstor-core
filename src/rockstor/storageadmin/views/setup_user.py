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
from storageadmin.views import UserView

import logging
logger = logging.getLogger(__name__)

class SetupUserView(UserView):

    authentication_classes = ()
    permission_classes = ()

    @transaction.commit_on_success
    def post(self, request):
        setup = Setup.objects.all()[0]
        setup.setup_user = True
        setup.save()
        return super(SetupUserView, self).post(request)

    def put(self, request, username):
        pass

    def delete(self, request, username):
        pass
