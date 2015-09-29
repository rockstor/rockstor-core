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
import logging
logger = logging.getLogger(__name__)


class UpdateSubscriptionListView(rfc.GenericView):
    serializer_class = UpdateSubscriptionSerializer

    def get_queryset(self, *args, **kwargs):
        return UpdateSubscription.objects.all()

    @transaction.commit_on_success
    def post(self, request, command):
        with self._handle_exception(request):
            if (command == 'activate-stable'):
                cd = settings.UPDATE_CHANNELS['stable']
                try:
                    stableo = UpdateSubscription.objects.get(name=cd['name'])
                except UpdateSubscription.DoesNotExist:
                    appliance = Appliance.objects.get(current_appliance=True)
                    stableo = UpdateSubscription(name=cd['name'],
                                                 description=cd['description'],
                                                 url=cd['url'], appliance=appliance,
                                                 status='inactive')
                stableo.password = request.data.get('activation_code')
                stableo.status = 'active'
                stableo.save()
                return Response(UpdateSubscriptionSerializer(stableo).data)

            if (command == 'check-status'):
                name = request.data.get('name')
                stableo = UpdateSubscription.objects.get(name=name)
                if (stableo.password is not None):
                    stableo.status = repo_status(stableo)
                    stableo.save()
                return Response(UpdateSubscriptionSerializer(stableo).data)


class UpdateSubscriptionDetailView(rfc.GenericView):
    serializer_class = UpdateSubscriptionSerializer

    def get(self, *args, **kwargs):
        return Response()
