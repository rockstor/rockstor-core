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
from storageadmin.models import EmailClient
from storageadmin.serializers import EmailClientSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from system.osi import run_command
from shutil import move
from tempfile import mkstemp
from django.conf import settings
from system.services import superctl
import logging
logger = logging.getLogger(__name__)

OPENSSL = '/usr/bin/openssl'


class EmailClientView(rfc.GenericView):
    serializer_class = EmailClientSerializer

    def get_queryset(self, *args, **kwargs):
        return EmailClient.objects.filter()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            email = request.data.get('email')
            smtp_server = request.data.get('smtp_server')
            name = request.data.get('name')
            password = request.data.get('password')

            eco = EmailClient(smtp_server=smtp_server, name=name, email=email)
            eco.save()

            return Response(EmailClientSerializer(eco).data)

    @transaction.atomic
    def delete(self, request):
        EmailClient.objects.all().delete()
        return Response()
