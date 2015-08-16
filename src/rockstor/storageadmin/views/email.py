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
from system.services import systemctl
import logging
logger = logging.getLogger(__name__)


POSTMAP = '/usr/sbin/postmap'
HEADER = '####BEGIN: Rockstor section####'
FOOTER = '####END: Rockstor section####'
MAIN_CF = '/etc/postfix/main.cf'


def rockstor_postfix_config(fo, smtp_server, revert):
    if (revert is True):
        return
    fo.write('%s\n' % HEADER)
    fo.write('relayhost = [%s]:587\n' % smtp_server)
    fo.write('smtp_use_tls = yes\n')
    fo.write('smtp_sasl_auth_enable = yes\n')
    fo.write('smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd\n')
    fo.write('smtp_tls_CAfile = /etc/ssl/certs/ca-bundle.crt\n')
    fo.write('smtp_sasl_security_options = noanonymous\n')
    fo.write('smtp_sasl_tls_security_options = noanonymous\n')
    fo.write('%s\n' % FOOTER)

def update_forward(email, revert=False):
    with open('/root/.forward', 'w') as fo:
        if (not revert):
            fo.write('%s, root\n' % email)

def update_sasl(smtp_server, sender, password, revert=False):
    sasl_file = '/etc/postfix/sasl_passwd'
    with open(sasl_file, 'w') as fo:
        if (not revert):
            fo.write('[%s]:587 %s:%s\n' % (smtp_server, sender, password))
    run_command([POSTMAP, sasl_file])

def update_postfix(smtp_server, revert=False):
    fh, npath = mkstemp()
    with open(MAIN_CF) as mfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in mfo.readlines():
            if (re.match(HEADER, line)
                is not None):
                rockstor_section = True
                rockstor_postfix_config(tfo, smtp_server, revert)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_postfix_config(tfo, smtp_server, revert)
    move(npath, MAIN_CF)


class EmailClientView(rfc.GenericView):
    serializer_class = EmailClientSerializer

    def get_queryset(self, *args, **kwargs):
        return EmailClient.objects.filter()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            sender = request.data.get('sender')
            username = sender.split('@')[0]
            smtp_server = request.data.get('smtp_server')
            name = request.data.get('name')
            password = request.data.get('password')
            receiver = request.data.get('receiver')
            eco = EmailClient(smtp_server=smtp_server, name=name, sender=sender, receiver=receiver)
            eco.save()
            update_sasl(smtp_server, sender, password)
            update_forward(receiver)
            update_postfix(smtp_server)
            systemctl('postfix', 'restart')
            return Response(EmailClientSerializer(eco).data)

    @transaction.atomic
    def delete(self, request):
        update_sasl('', '', '', revert=True)
        update_forward('', revert=True)
        update_postfix('', revert=True)
        systemctl('postfix', 'restart')
        EmailClient.objects.all().delete()
        return Response()
