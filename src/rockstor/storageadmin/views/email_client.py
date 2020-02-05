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

import os
import re
import json
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (EmailClient, Appliance)
from storageadmin.serializers import EmailClientSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from system.osi import run_command, gethostname
from shutil import move
from tempfile import mkstemp
from system.services import systemctl
from system.email_util import send_test_email, test_smtp_auth
import logging
logger = logging.getLogger(__name__)


POSTMAP = '/usr/sbin/postmap'
HEADER = '####BEGIN: Rockstor section####'
FOOTER = '####END: Rockstor section####'
MAIN_CF = '/etc/postfix/main.cf'


def rockstor_postfix_config(fo, smtp_server, port, revert):
    if (revert is True):
        return
    fo.write('%s\n' % HEADER)
    fo.write('relayhost = [%s]:%d\n' % (smtp_server, port))
    fo.write('smtp_use_tls = yes\n')
    fo.write('smtp_sasl_auth_enable = yes\n')
    fo.write('smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd\n')
    fo.write('smtp_tls_CAfile = /etc/ssl/certs/ca-bundle.crt\n')
    fo.write('smtp_sasl_security_options = noanonymous\n')
    fo.write('smtp_sasl_tls_security_options = noanonymous\n')
    fo.write('smtp_generic_maps = hash:/etc/postfix/generic\n')
    fo.write('%s\n' % FOOTER)


def update_forward(email, revert=False):
    with open('/root/.forward', 'w') as fo:
        if (not revert):
            fo.write('%s, root\n' % email)


def update_generic(sender, revert=False):
    """
    overrites the contents of /etc/postfix/generic with the following mapping
    @<hostname> <sender-email-address>
    @<hostname>.localdomain <sender-email-address>
    Then sets the file permissions and runs "postmap generic" to create the db
    file and change it's permissions in turn.
    :param sender: email address entered as the sender email account
    :param revert: if True wipe the generic_file and db (defaults to False)
    :return:
    """
    generic_file = '/etc/postfix/generic'
    hostname = gethostname()
    with open(generic_file, 'w') as fo:
        if (not revert):
            fo.write('@%s %s\n' % (hostname, sender))
            fo.write('@%s.localdomain %s\n' % (hostname, sender))
            # todo need an entry here to add @<hostname>.<domain>
    os.chmod(generic_file, 400)
    run_command([POSTMAP, generic_file])
    os.chmod('%s.db' % generic_file, 600)


def update_sasl(smtp_server, port, username, password, revert=False):
    sasl_file = '/etc/postfix/sasl_passwd'
    with open(sasl_file, 'w') as fo:
        if (not revert):
            fo.write('[%s]:%d %s:%s\n' %
                     (smtp_server, port, username, password))
    os.chmod(sasl_file, 400)
    run_command([POSTMAP, sasl_file])
    os.chmod('%s.db' % sasl_file, 600)


def update_postfix(smtp_server, port, revert=False):
    fh, npath = mkstemp()
    with open(MAIN_CF) as mfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in mfo.readlines():
            if (re.match(HEADER, line) is not None):
                rockstor_section = True
                rockstor_postfix_config(tfo, smtp_server, port, revert)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_postfix_config(tfo, smtp_server, port, revert)
    move(npath, MAIN_CF)
    os.chmod(MAIN_CF, 644)


class EmailClientView(rfc.GenericView):
    serializer_class = EmailClientSerializer

    def get_queryset(self, *args, **kwargs):
        return EmailClient.objects.filter()

    @transaction.atomic
    def post(self, request, command=None):
        with self._handle_exception(request):

            commands_list = ['send-test-email', 'check-smtp-auth']
            if (command is not None):
                if (command not in commands_list):
                    e_msg = ('Unknown command ({}) is '
                             'not supported.').format(command)
                    handle_exception(Exception(e_msg), request)

                if (command == 'send-test-email'):
                    if (EmailClient.objects.count() == 0):
                        e_msg = ('E-mail account must be setup before a '
                                 'test e-mail can be sent.')
                        handle_exception(Exception(e_msg), request)

                    eco = EmailClient.objects.all()[0]
                    subject = ('Test message from Rockstor. Appliance id: '
                               '{}').format(Appliance.objects.get(current_appliance=True).uuid)  # noqa E501
                    send_test_email(eco, subject)
                    return Response()

                elif (command == 'check-smtp-auth'):
                    mail_auth = {}
                    sender = request.data.get('sender')
                    username = request.data.get('username')
                    mail_auth['username'] = sender if not username else username  # noqa E501
                    mail_auth['password'] = request.data.get('password')
                    mail_auth['smtp_server'] = request.data.get('smtp_server')
                    mail_auth['port'] = int(request.data.get('port', 587))

                    return Response(
                        json.dumps({'smtp_auth': test_smtp_auth(mail_auth)}),
                        content_type="application/json")

            sender = request.data.get('sender')
            # collect new username field
            username = request.data.get('username')
            # smtp auth - use username or if empty use sender
            username = sender if not username else username
            smtp_server = request.data.get('smtp_server')
            port = int(request.data.get('port', 587))
            name = request.data.get('name')
            password = request.data.get('password')
            receiver = request.data.get('receiver')
            eco = EmailClient(smtp_server=smtp_server, port=port, name=name,
                              sender=sender, receiver=receiver,
                              username=username)
            eco.save()
            update_sasl(smtp_server, port, username, password)
            update_forward(receiver)
            update_generic(sender)
            update_postfix(smtp_server, port)
            systemctl('postfix', 'restart')
            return Response(EmailClientSerializer(eco).data)

    @transaction.atomic
    def delete(self, request):
        update_sasl('', '', '', '', revert=True)
        update_forward('', revert=True)
        update_generic('', revert=True)
        update_postfix('', '', revert=True)
        systemctl('postfix', 'restart')
        EmailClient.objects.all().delete()
        return Response()
