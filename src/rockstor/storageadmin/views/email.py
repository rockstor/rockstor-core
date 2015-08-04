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


POSTMAP = '/usr/sbin/postmap'
HEADER = '####BEGIN: Rockstor section####'
FOOTER = '####END: Rockstor section####'
MAIN_CF = '/etc/postfix/main.cf'
GEN_CF = '/etc/postfix/generic'


def rockstor_postfix_config(fo, hostname, smtp_server):
    fo.write('%s\n' % HEADER)
    fo.write('myhostname = %s\n' % hostname)
    fo.write('relayhost = [%s]:587\n' % smtp_server)
    fo.write('smtp_use_tls = yes\n')
    fo.write('smtp_sasl_auth_enable = yes\n')
    fo.write('smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd\n')
    fo.write('smtp_tls_CAfile = /etc/ssl/certs/ca-bundle.crt\n')
    fo.write('smtp_sasl_security_options = noanonymous\n')
    fo.write('smtp_sasl_tls_security_options = noanonymous\n')
    fo.write('smtp_generic_maps = hash:/etc/postfix/generic\n')
    fo.write('%s\n' % FOOTER)

def update_forward(email):
    with open('/root/.forward', 'w') as fo:
        fo.write('%s\n' % email)

def update_sasl(smtp_server, username, password):
    sasl_file = '/etc/postfix/sasl_passwd'
    with open(sasl_file, 'w') as fo:
        fo.write('[%s]:587 %s:%s\n' % (smtp_server, username, password))
    run_command([POSTMAP, sasl_file])

def update_alias(from_email, to_email):
    fh, npath = mkstemp()
    with open(GEN_CF) as gfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in gfo.readlines():
            if (re.match(HEADER, line) is not None):
                rockstor_section = True
                tfo.write('%s\n' % HEADER)
                tfo.write('%s %s\n' % (from_email, to_email))
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            tfo.write('%s\n' % HEADER)
            tfo.write('%s %s\n' % (from_email, to_email))
        tfo.write('%s\n' % FOOTER)
    move(npath, GEN_CF)
    run_command([POSTMAP, GEN_CF])

def update_postfix():
    fh, npath = mkstemp()
    with open(MAIN_CF) as mfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in mfo.readlines():
            if (re.match('####BEGIN: Rockstor postfix config####', line)
                is not None):
                rockstor_section = True
                rockstor_postfix_config(tfo, input)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_postfix_config(tfo, input)
    move(npath, MAIN_CF)


class EmailClientView(rfc.GenericView):
    serializer_class = EmailClientSerializer

    def get_queryset(self, *args, **kwargs):
        return EmailClient.objects.filter()

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            email = request.data.get('email')
            username = email.split('@')[0]
            smtp_server = request.data.get('smtp_server')
            name = request.data.get('name')
            password = request.data.get('password')
            eco = EmailClient(smtp_server=smtp_server, name=name, email=email)
            eco.save()
            update_sasl(smtp_server, username, password)
            update_alias()
            update_postfix()
            return Response(EmailClientSerializer(eco).data)

    @transaction.atomic
    def delete(self, request):
        EmailClient.objects.all().delete()
        return Response()
