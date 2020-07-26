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

from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Appliance, EmailClient
from storageadmin.views.email_client import update_generic
from storageadmin.util import handle_exception
from storageadmin.serializers import ApplianceSerializer

from system.osi import hostid, sethostname, gethostname
import rest_framework_custom as rfc
from cli.rest_util import api_call, set_token
from smart_manager.models import Replica


import logging

logger = logging.getLogger(__name__)


class ApplianceListView(rfc.GenericView):
    serializer_class = ApplianceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._update_hostname()
            return Appliance.objects.all()

    @staticmethod
    @transaction.atomic
    def _update_hostname():
        a = Appliance.objects.get(current_appliance=True)
        cur_hostname = gethostname()
        if cur_hostname != a.hostname:
            a.hostname = cur_hostname
        if a.ipaddr != a.ip:
            a.ip = a.ipaddr
        a.save()

    def _get_remote_appliance(self, request, ip, port, client_id, client_secret):
        with self._handle_exception(request):
            base_url = "https://%s:%s" % (ip, port)
            try:
                set_token(
                    client_id=client_id, client_secret=client_secret, url=base_url
                )
            except Exception as e:
                e_msg = (
                    "Failed to authenticate on remote appliance. Verify "
                    "port number, id and secret are correct and try "
                    "again."
                )
                handle_exception(Exception(e_msg), request)
            try:
                ad = api_call("%s/api/appliances/1" % base_url, save_error=False)
                return ad["uuid"]
            except Exception as e:
                logger.exception(e)
                e_msg = (
                    "Failed to get remote appliance information. Verify "
                    "all inputs and try again."
                )
                handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        with self._handle_exception(request):
            ip = request.data.get("ip", "")
            current_appliance = request.data.get("current_appliance")
            # authenticate if not adding current appliance
            if Appliance.objects.filter(ip=ip).exists():
                e_msg = (
                    "The appliance with ip = {} already exists and "
                    "cannot be added again."
                ).format(ip)
                handle_exception(Exception(e_msg), request)

            if current_appliance is False:
                client_id = request.data.get("client_id", None)
                if client_id is None:
                    raise Exception("ID is required")
                client_secret = request.data.get("client_secret", None)
                if client_secret is None:
                    raise Exception("Secret is required")
                try:
                    mgmt_port = int(request.data["mgmt_port"])
                except Exception as e:
                    logger.exception(e)
                    e_msg = (
                        "Invalid management port ({}) supplied. Try again."
                    ).format(request.data["mgmt_port"])
                    handle_exception(Exception(e_msg), request)
                url = "https://%s" % ip
                if mgmt_port != 443:
                    url = "%s:%s" % (url, mgmt_port)
                ra_uuid = self._get_remote_appliance(
                    request, ip, mgmt_port, client_id, client_secret
                )
                appliance = Appliance(
                    uuid=ra_uuid,
                    ip=ip,
                    mgmt_port=mgmt_port,
                    client_id=client_id,
                    client_secret=client_secret,
                )
                appliance.save()
            else:
                appliance = Appliance(uuid=hostid(), ip=ip, current_appliance=True)
                if "hostname" in request.data:
                    appliance.hostname = request.data["hostname"]
                appliance.save()
                sethostname(appliance.hostname)
            return Response(ApplianceSerializer(appliance).data)


class ApplianceDetailView(rfc.GenericView):
    serializer_class = ApplianceSerializer

    def get(self, *args, **kwargs):
        with self._handle_exception(self.request):
            data = Appliance.objects.get(id=self.kwargs.get("appid"))
            serialized_data = ApplianceSerializer(data)
            return Response(serialized_data.data)

    @transaction.atomic
    def put(self, request, appid):
        try:
            appliance = Appliance.objects.get(pk=appid)
        except Exception as e:
            logger.exception(e)
            e_msg = "Appliance id ({}) does not exist.".format(appid)
            handle_exception(Exception(e_msg), request)

        try:
            appliance.hostname = request.data["hostname"]
            appliance.save()
            sethostname(appliance.hostname)
            if EmailClient.objects.count() > 0:
                current_email = EmailClient.objects.all()[0]
                update_generic(current_email.sender)
            return Response()
        except Exception as e:
            logger.exception(e)
            e_msg = ("Failed updating hostname for appliance with id = ({}).").format(
                appid
            )
            handle_exception(e, request)

    @transaction.atomic
    def delete(self, request, appid):
        try:
            appliance = Appliance.objects.get(pk=appid)
        except Exception as e:
            logger.exception(e)
            e_msg = "Appliance id ({}) does not exist.".format(appid)
            handle_exception(Exception(e_msg), request)

        if Replica.objects.filter(appliance=appliance.uuid).exists():
            e_msg = (
                "Appliance cannot be deleted because there are "
                "replication tasks defined for it. If you are sure, "
                "delete them and try again."
            )
            handle_exception(Exception(e_msg), request)

        try:
            appliance.delete()
            return Response()
        except Exception as e:
            logger.exception(e)
            e_msg = "Delete failed for appliance with id = ({}).".format(appid)
            handle_exception(e, request)
