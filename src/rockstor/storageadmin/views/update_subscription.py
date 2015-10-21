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

import requests
import json
import uuid
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import (UpdateSubscription, Appliance)
from storageadmin.util import handle_exception
from storageadmin.serializers import UpdateSubscriptionSerializer
import rest_framework_custom as rfc
from django.conf import settings
from system.pkg_mgmt import (repo_status, switch_repo)
import logging
logger = logging.getLogger(__name__)


class UpdateSubscriptionListView(rfc.GenericView):
    serializer_class = UpdateSubscriptionSerializer

    def get_queryset(self, *args, **kwargs):
        return UpdateSubscription.objects.all()

    def _toggle_repos(self, on='stable', off='testing', password=None):
        #toggle between testing and stabel repos
        ncd = settings.UPDATE_CHANNELS[on]
        fcd = settings.UPDATE_CHANNELS[off]
        try:
            offo = UpdateSubscription.objects.get(name=fcd['name'])
            offo.status = 'inactive'
            offo.save()
            switch_repo(offo, on=False)
        except UpdateSubscription.DoesNotExist:
            pass

        try:
            ono = UpdateSubscription.objects.get(name=ncd['name'])
        except UpdateSubscription.DoesNotExist:
            appliance = Appliance.objects.get(current_appliance=True)
            ono = UpdateSubscription(name=ncd['name'],
                                     description=ncd['description'],
                                     url=ncd['url'], appliance=appliance,
                                     status='active')
        ono.password = password
        status, text = repo_status(ono)
        ono.status = status
        ono.save()
        if (status == 'inactive'):
            e_msg = ('Activation code(%s) could not be authorized. '
                     'Verify the code and try again. If '
                     'the problem persists, contact '
                     'support@rockstor.com' % ono.password)
            raise Exception(e_msg)
        if (status != 'active'):
            e_msg = ('Failed to activate subscription. status code: '
                     '%s details: %s' % (status, text))
            raise Exception(e_msg)
        switch_repo(ono)
        return ono

    @transaction.commit_on_success
    def post(self, request, command):
        with self._handle_exception(request):
            if (command == 'activate-stable'):
                password = request.data.get('activation_code', None)
                if (password is None):
                    e_msg = ('Activation code is required for Stable subscription')
                    handle_exception(Exception(e_msg), request)
                stableo = self._toggle_repos(password=password)
                return Response(UpdateSubscriptionSerializer(stableo).data)

            if (command == 'activate-testing'):
                testingo = self._toggle_repos(on='testing', off='stable')
                return Response(UpdateSubscriptionSerializer(testingo).data)

            if (command == 'check-status'):
                name = request.data.get('name')
                stableo = UpdateSubscription.objects.get(name=name)
                if (stableo.password is not None):
                    stableo.status, text = repo_status(stableo)
                    stableo.save()
                return Response(UpdateSubscriptionSerializer(stableo).data)

class UpdateSubscriptionDetailView(rfc.GenericView):
    serializer_class = UpdateSubscriptionSerializer

    def get(self, *args, **kwargs):
        return Response()
