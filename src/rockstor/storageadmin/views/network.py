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

from django.db import transaction
from rest_framework.response import Response
from storageadmin.models import NetworkInterface
from storageadmin.util import handle_exception
from storageadmin.serializers import NetworkInterfaceSerializer
from system.osi import (get_mac_addr, config_network_device, restart_network,
                        network_devices, get_net_config)
from storageadmin.exceptions import RockStorAPIException
from generic_view import GenericView


class NetworkView(GenericView):
    serializer_class = NetworkInterfaceSerializer

    def get_queryset(self, *args, **kwargs):
        if ('iname' in kwargs):
            self.paginate_by = 0
            try:
                return NetworkInterface.objects.get(name=kwargs['iname'])
            except:
                return []
        return NetworkInterface.objects.all()

    @transaction.commit_on_success
    def post(self, request):
        for d in network_devices():
            if (NetworkInterface.objects.filter(name=d).exists()):
                continue
            dconfig = get_net_config(d)
            new_device = NetworkInterface(name=d, mac=dconfig['mac'],
                                          boot_proto=dconfig['bootproto'],
                                          onboot=dconfig['onboot'],
                                          network=dconfig['network'],
                                          netmask=dconfig['netmask'],
                                          ipaddr=dconfig['ipaddr'])
            new_device.save()
        devices = NetworkInterface.objects.all()
        serializer = NetworkInterfaceSerializer(devices)
        return Response(serializer.data)

    def put(self, request, iname):
        try:
            if (not NetworkInterface.objects.filter(name=iname).exists()):
                e_msg = ('Interface with name: %s does not exist.' % iname)
                handle_exception(Exception(e_msg), request)

            ni = NetworkInterface.objects.get(name=iname)
            ipaddr = request.DATA['ipaddr']
            for i in NetworkInterface.objects.filter(ipaddr=ipaddr):
                if (i.id != ni.id):
                    e_msg = ('IP: %s already in use' % ipaddr)
                    handle_exception(Exception(e_msg), request)

            ni.boot_proto = 'static'
            ni.onboot = 'yes'
            ni.network = request.DATA['network']
            ni.netmask = request.DATA['netmask']
            ni.ipaddr = ipaddr
            ni.save()
            config_network_device(ni.name, ni.mac, ni.ipaddr, ni.netmask)
            restart_network()
            return Response(NetworkInterfaceSerializer(ni).data)
        except RockStorAPIException:
            raise
        except Exception, e:
            handle_exception(e, request)

    @transaction.commit_on_success
    def delete(self, request, iname):
        try:
            if (NetworkInterface.objects.filter(name=iname).exists()):
                i = NetworkInterface.objects.get(name=iname)
                i.delete()
            return Response()
        except Exception, e:
            handle_exception(e, request)

