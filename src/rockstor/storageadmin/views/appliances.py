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
import requests
import json
import uuid
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import (BasicAuthentication,
                                           SessionAuthentication,)
from storageadmin.auth import DigestAuthentication
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.core.mail import EmailMessage
from django.conf import settings
from storageadmin.models import Appliance
from storageadmin.models import SupportCase
from storageadmin.util import handle_exception
from storageadmin.serializers import ApplianceSerializer
from system.osi import hostid
from system.util import archive_logs
import os


import logging
logger = logging.getLogger(__name__)

class AppliancesView(APIView):
    authentication_classes = (DigestAuthentication, SessionAuthentication,
                              BasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, name=None):
      try:
        appliances = ApplianceSerializer(Appliance.objects.all())
        return Response(appliances.data);
      except Exception, e:
        handle_exception(e, request)

    def post(self, request):
      try:
        ip = request.DATA['ip']
        current_appliance = request.DATA['current_appliance']
        # authenticate if not adding current appliance
        if not current_appliance:
            username = request.DATA['username']
            password = request.DATA['password']
            url = 'https://%s/api/login' % ip
            logger.info('adding appliance %s at %s with %s %s' % (ip, url,
                username, password))
            r = requests.post(
                    url,
                    headers = {'content-type': 'application/json'},
                    verify=False,
                    data = json.dumps({'username': username,
                        'password': password}))
            logger.debug('in AppliancesView ')
            logger.debug(r.status_code)
            if (r.status_code != 200):
                raise Exception('Could not verify appliance %s' % ip)
            appliance = Appliance(ip = ip)
            appliance.save()
        else:
            appliance_uuid = ('%s:%s' % (hostid()[0][0], str(uuid.uuid4())))
            appliance = Appliance(uuid=appliance_uuid, ip=ip,
                                  current_appliance=True)
            appliance.save()
            # the current appliance is created - open a support case
            # and send email
            try: 
                notes = 'Appliance %s initialized' % appliance.uuid
                sc = SupportCase(notes=notes, status='created', 
                        case_type='auto')
                sc.save()
                emsg = EmailMessage(subject='support case',
                        body=notes,
                        from_email='rocky@customer.com',
                        to=[settings.SUPPORT['email']])
                emsg.send()
                sc.status = 'submitted'
                sc.save()
            except Exception, e:
                # if an exception occurs during the above, dont exit, 
                # the appliance should still be usable.
                logger.exception('exception while creating support \
                        case for Appliance initialization')

        return Response(ApplianceSerializer(appliance).data)
      except Exception, e:
        handle_exception(e, request)

    def delete(self, request, id):
        try:
            appliance = Appliance.objects.get(pk=id)
            appliance.delete()
            logger.debug('found appliance')
            return Response()
        except Exception, e:
            handle_exception(e, request)




