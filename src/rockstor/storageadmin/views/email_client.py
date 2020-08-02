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

import os
import re
import json
import stat
import distro
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import EmailClient, Appliance
from storageadmin.serializers import EmailClientSerializer
from storageadmin.util import handle_exception
import rest_framework_custom as rfc
from system.osi import run_command, gethostname, replace_line_if_found
from shutil import move
from tempfile import mkstemp
from system.services import systemctl
from system.email_util import send_test_email, test_smtp_auth
import logging

logger = logging.getLogger(__name__)


POSTMAP = "/usr/sbin/postmap"
HEADER = "####BEGIN: Rockstor section####"
FOOTER = "####END: Rockstor section####"
MAIN_CF = "/etc/postfix/main.cf"
MASTER_CF = "/etc/postfix/master.cf"
POSTFIX = "/usr/sbin/postfix"
SYSCONFIG_MAIL = "/etc/sysconfig/mail"
ROOT_FORWARD = "/root/.forward"
GENERIC = "/etc/postfix/generic"

# List of our used config options within main.cf; used to remove prior entries
# to avoid log warnings of "... overriding earlier entry: X"
MAIN_CF_OPTIONS = [
    "relayhost",
    "smtp_use_tls",
    "smtp_sasl_auth_enable",
    "smtp_sasl_password_maps",
    "smtp_tls_CAfile",
    "smtp_sasl_security_options",
    "smtp_sasl_tls_security_options",
    "smtp_generic_maps",
]


def rockstor_postfix_config(fo, smtp_server, port, revert):
    if revert is True:
        return
    distro_id = distro.id()
    if distro_id == "rockstor":
        CAfile_path = "/etc/ssl/certs/ca-bundle.crt"
    else:  # i.e. openSUSE Leap / Tumbleweed
        CAfile_path = "/etc/ssl/ca-bundle.pem"
    # If we move in the future to using yast here note /etc/sysconfig/postfix
    fo.write("{}\n".format(HEADER))
    fo.write("relayhost = [{}]:{}\n".format(smtp_server, port))
    fo.write("smtp_use_tls = yes\n")
    fo.write("smtp_sasl_auth_enable = yes\n")
    fo.write("smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd\n")
    fo.write("smtp_tls_CAfile = {}\n".format(CAfile_path))
    fo.write("smtp_sasl_security_options = noanonymous\n")
    # N.B. no "yast sysconfig set" option found for the following:
    fo.write("smtp_sasl_tls_security_options = noanonymous\n")
    fo.write("smtp_generic_maps = hash:/etc/postfix/generic\n")
    fo.write("{}\n".format(FOOTER))


def update_master():
    """
    Edits /etc/postfix/master.cf as required and then runs "postfix reload"
    Predominantly for openSUSE to ensure tlsmgr is un-remarked.
    Default permissions in both our CentOS base and within openSUSE:
    -rw-r--r-- 1 root root 6105 Oct 30  2018 /etc/postfix/master.cf
    source:
    "#tlsmgr    unix  -       -       n       1000?   1       tlsmgr"
    to become target:
    "tlsmgr    unix  -       -       n       1000?   1       tlsmgr"
    I.e. we un-remark this line
    :return:
    """
    distro_id = distro.id()
    if distro_id == "rockstor":
        return
    # master.cf edit
    tlsmgr_source = "#tlsmgr"
    tlsmgr_target = "tlsmgr    unix  -       -       n       1000?   1       tlsmgr"
    fh, npath = mkstemp()
    replaced = replace_line_if_found(MASTER_CF, npath, tlsmgr_source, tlsmgr_target)
    if replaced:
        move(npath, MASTER_CF)
    else:
        os.remove(npath)
    # Set file to rw- r-- r-- (644) via stat constants.
    os.chmod(MASTER_CF, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def disable_sysconfig_mail():
    """
    A default openSUSE install (JeOS and up) enforces email settings via
    sysconfig. As we are currently invested in 'hand configuring' our own email
    configuration disable this service.
    N.B. we assume openSUSE if not distro "rockstor"
    :return:
    """
    # We could do a distro check here but this works and avoids no file found
    if not os.path.isfile(SYSCONFIG_MAIL):
        return
    fh, npath = mkstemp()
    sysconfig_source = 'MAIL_CREATE_CONFIG="yes"'
    sysconfig_target = 'MAIL_CREATE_CONFIG="no"'
    replaced = replace_line_if_found(
        SYSCONFIG_MAIL, npath, sysconfig_source, sysconfig_target
    )
    if replaced:
        move(npath, SYSCONFIG_MAIL)
    else:
        os.remove(npath)
    # Set file to rw- r-- r-- (644) via stat constants.
    os.chmod(SYSCONFIG_MAIL, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


def update_forward(email, revert=False):
    with open(ROOT_FORWARD, "w") as fo:
        if not revert:
            # N.B. if we want local and forward then we need to also include
            # root@localhost as one of the comma separated emails.
            fo.write("{}, root\n".format(email))


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
    hostname = gethostname()
    with open(GENERIC, "w") as fo:
        if not revert:
            fo.write("@{} {}\n".format(hostname, sender))
            fo.write("@{}.localdomain {}\n".format(hostname, sender))
            # todo need an entry here to add @<hostname>.<domain>
    # Set file to r-- --- --- (400) via stat constants.
    os.chmod(GENERIC, stat.S_IRUSR)
    run_command([POSTMAP, GENERIC])
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod("{}.db".format(GENERIC), stat.S_IRUSR | stat.S_IWUSR)


def update_sasl(smtp_server, port, username, password, revert=False):
    sasl_file = "/etc/postfix/sasl_passwd"
    with open(sasl_file, "w") as fo:
        if not revert:
            fo.write("[{}]:{} {}:{}\n".format(smtp_server, port, username, password))
    # Set file to r-- --- --- (400) via stat constants.
    os.chmod(sasl_file, stat.S_IRUSR)
    run_command([POSTMAP, sasl_file])
    # Set file to rw- --- --- (600) via stat constants.
    os.chmod("{}.db".format(sasl_file), stat.S_IRUSR | stat.S_IWUSR)


def update_postfix(smtp_server, port, revert=False):
    # main.cf edit
    fh, npath = mkstemp()
    with open(MAIN_CF) as mfo, open(npath, "w") as tfo:
        rockstor_section = False
        for line in mfo.readlines():
            if re.match(HEADER, line) is not None:
                rockstor_section = True
                rockstor_postfix_config(tfo, smtp_server, port, revert)
                break
            else:
                # Copy current line as-is from MAIN_CF to our temp file (tfo)
                # unless we find the following entry:
                # "inet_protocols = all" as we need this to be:
                # "inet_protocols = ipv4" as our NetworkManager is ipv4 only.
                # Or if we find duplicates of our to-be-installed settings;
                if len(line) > 0 and line[0] is not "#":
                    if re.match("inet_protocols = all", line) is not None:
                        tfo.write("inet_protocols = ipv4\n")
                        continue
                    line_fields = line.split("=")
                    if (
                        len(line_fields) > 0
                        and line_fields[0].strip() in MAIN_CF_OPTIONS
                    ):
                        logger.info(
                            "master.cf: removing {}".format(line_fields[0].strip())
                        )
                        continue  # effectively removing these entries.
                tfo.write(line)
        if rockstor_section is False:
            rockstor_postfix_config(tfo, smtp_server, port, revert)
    move(npath, MAIN_CF)
    # Set file to rw- r-- r-- (644) via stat constants.
    os.chmod(MAIN_CF, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)


class EmailClientView(rfc.GenericView):
    serializer_class = EmailClientSerializer

    def get_queryset(self, *args, **kwargs):
        return EmailClient.objects.filter()

    @transaction.atomic
    def post(self, request, command=None):
        with self._handle_exception(request):

            commands_list = ["send-test-email", "check-smtp-auth"]
            if command is not None:
                if command not in commands_list:
                    e_msg = ("Unknown command ({}) is not supported.").format(command)
                    handle_exception(Exception(e_msg), request)

                if command == "send-test-email":
                    if EmailClient.objects.count() == 0:
                        e_msg = (
                            "E-mail account must be setup before a "
                            "test e-mail can be sent."
                        )
                        handle_exception(Exception(e_msg), request)

                    eco = EmailClient.objects.all()[0]
                    subject = ("Test message from Rockstor. Appliance id: {}").format(
                        Appliance.objects.get(current_appliance=True).uuid
                    )  # noqa E501
                    send_test_email(eco, subject)
                    return Response()

                elif command == "check-smtp-auth":
                    mail_auth = {}
                    sender = request.data.get("sender")
                    username = request.data.get("username")
                    mail_auth["username"] = (
                        sender if not username else username
                    )  # noqa E501
                    mail_auth["password"] = request.data.get("password")
                    mail_auth["smtp_server"] = request.data.get("smtp_server")
                    mail_auth["port"] = int(request.data.get("port", 587))

                    return Response(
                        json.dumps({"smtp_auth": test_smtp_auth(mail_auth)}),
                        content_type="application/json",
                    )

            sender = request.data.get("sender")
            # collect new username field
            username = request.data.get("username")
            # smtp auth - use username or if empty use sender
            username = sender if not username else username
            smtp_server = request.data.get("smtp_server")
            port = int(request.data.get("port", 587))
            name = request.data.get("name")
            password = request.data.get("password")
            receiver = request.data.get("receiver")
            eco = EmailClient(
                smtp_server=smtp_server,
                port=port,
                name=name,
                sender=sender,
                receiver=receiver,
                username=username,
            )
            eco.save()
            update_sasl(smtp_server, port, username, password)
            update_forward(receiver)
            update_generic(sender)
            update_postfix(smtp_server, port)
            disable_sysconfig_mail()
            update_master()
            # Restart ensures sevice is running, even if not running previously.
            systemctl("postfix", "enable")
            systemctl("postfix", "restart")
            return Response(EmailClientSerializer(eco).data)

    @transaction.atomic
    def delete(self, request):
        update_sasl("", "", "", "", revert=True)
        update_forward("", revert=True)
        update_generic("", revert=True)
        update_postfix("", "", revert=True)
        disable_sysconfig_mail()
        update_master()  # Not needed as no revert but preserves consistency
        # Restart ensures sevice is running, even if not running previously.
        systemctl("postfix", "restart")
        EmailClient.objects.all().delete()
        return Response()
