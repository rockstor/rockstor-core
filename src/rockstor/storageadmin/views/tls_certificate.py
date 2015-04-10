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
from storageadmin.models import TLSCertificate
from storageadmin.serializers import TLSCertificateSerializer
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


class TLSCertificateView(rfc.GenericView):
    serializer_class = TLSCertificateSerializer

    def get_queryset(self, *args, **kwargs):
        return TLSCertificate.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        with self._handle_exception(request):
            name = request.DATA.get('name')
            cert = request.DATA.get('cert')
            key = request.DATA.get('key')
            if (TLSCertificate.objects.filter(name=name).exists()):
                e_msg = ('Another certificate with the name(%s) already '
                         'exists.' % name)
                handle_exception(Exception(e_msg), request)
            fo, kpath = mkstemp()
            fo, cpath = mkstemp()
            with open(kpath, 'w') as kfo, open(cpath, 'w') as cfo:
                kfo.write(key)
                cfo.write(cert)
            try:
                o, e, rc = run_command([OPENSSL, 'rsa', '-noout', '-modulus',
                                        '-in', kpath])
            except Exception, e:
                logger.exception(e)
                e_msg = ('RSA key modulus could not be verified for the given '
                         'Private Key. Check and try again')
                handle_exception(Exception(e_msg), request)
            try:
                o2, e, rc = run_command([OPENSSL, 'x509', '-noout',
                                         '-modulus', '-in', cpath])
            except Exception, e:
                logger.exception(e)
                e_msg = ('RSA key modulus could not be verified for the given '
                         'Certificate. Check and try again')
                handle_exception(Exception(e_msg), request)
            if (o[0] != o2[0]):
                e_msg = ('Given Certificate and the Private Key do not match. '
                         'Check and try again')
                handle_exception(Exception(e_msg), request)
            move(kpath, '%s/rockstor.cert' % settings.CERTDIR)
            move(cpath, '%s/rockstor.key' % settings.CERTDIR)
            superctl('nginx', 'restart')
            co = TLSCertificate(name=name, certificate=cert, key=key)
            co.save()
            return Response(TLSCertificateSerializer(co).data)
