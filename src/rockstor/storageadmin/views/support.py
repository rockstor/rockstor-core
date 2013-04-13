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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication)
from rest_framework.permissions import IsAuthenticated
from storageadmin.auth import DigestAuthentication
from django.db import transaction
from django.conf import settings
from django.core.mail import EmailMessage
from storageadmin.models import SupportCase
from storageadmin.serializers import SupportSerializer
from storageadmin.util import handle_exception
from storageadmin.exceptions import RockStorAPIException
from system.util import archive_logs
import os

import logging
logger = logging.getLogger(__name__)

class SupportView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    CASE_TYPES = ('auto', 'manual',)
    CASE_STATUS = ('submitted', 'resolved',)

    def get(self, request, caseid=None):
        try:
            if (caseid is None):
                ss = SupportSerializer(SupportCase.objects.all())
                return Response(ss.data)
            try:
                sc_o = SupportCase.objects.get(id=caseid)
                return Response(SupportSerializer(sc_o).data)
            except:
                e_msg = ('Unknown support case: %s' % caseid)
                handle_exception(Exception(e_msg), request)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    def post(self, request):
        return Response()

    @transaction.commit_on_success
    def put(self, request, caseid=None):
        try:
            if (caseid is None):

                future_id = len(SupportCase.objects.all()) + 1
                case_type = request.DATA['type']
                if (case_type not in self.CASE_TYPES):
                    e_msg = ('Unsupported case type: %s. Possible choices: %s'
                             % (case_type, self.CASE_TYPES))
                    handle_exception(Exception(e_msg), request)

                notes = request.DATA['notes']
                log_loc = settings.SUPPORT['log_loc']
                archive_name = ('%s-%d.tgz' % (os.path.dirname(log_loc),
                                               future_id))
                archive_logs(archive_name, log_loc)
                sc = SupportCase(notes=notes, zipped_log=archive_name,
                                 status='created', case_type=case_type)
                try:
                    emsg = EmailMessage(subject='support case',
                                        body='from customer foo',
                                        from_email='rocky@customer.com',
                                        to=[settings.SUPPORT['email']])
                    emsg.attach_file(archive_name)
                    emsg.send()
                    sc.status = 'submitted'
                except Exception, e:
                    handle_exception(e, request)
            else:
                if (not SupportCase.objects.filter(id=caseid).exists()):
                    e_msg = ('Support case: %s does not exist' % caseid)
                    handle_exception(Exception(e_msg), request)
                new_status = request.DATA['status']
                if (new_status not in self.CASE_STATUS):
                    e_msg = ('Unknown case status. It should be one of: %s' %
                             self.CASE_STATUS)
                    handle_exception(Exception(e_msg), request)
                sc = SupportCase.objects.get(id=caseid)
                sc.status = new_status
            sc.save()
            return Response(SupportSerializer(sc).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

