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
from storageadmin.models import (NetworkInterface, Appliance)
from storageadmin.util import handle_exception
from storageadmin.serializers import NetworkInterfaceSerializer
from system.osi import (config_network_device, network_devices, get_net_config,
                        restart_network_interface, get_default_interface,
                        update_issue)
from system.samba import update_samba_discovery
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)


class NetworkMixin(object):

    @staticmethod
    def _update_ni_obj(nio, values):
        nio.dname = values.get('dname', None)
        nio.mac = values.get('mac', None)
        nio.method = values.get('method', 'manual')
        nio.autoconnect = values.get('autoconnect', 'no')
        nio.netmask = values.get('netmask', None)
        nio.ipaddr = values.get('ipaddr', None)
        nio.gateway = values.get('gateway', None)
        nio.dns_servers = values.get('dns_servers', None)
        nio.ctype = values.get('ctype', None)
        nio.dtype = values.get('dtype', None)
        nio.dspeed = values.get('dspeed', None)
        nio.state = values.get('state', None)
        return nio

class NetworkListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkInterfaceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._net_scan()
            #to be deprecated soon
            update_samba_discovery()
        return NetworkInterface.objects.all()

    @classmethod
    @transaction.atomic
    def _net_scan(cls):
        default_if = get_default_interface()
        config_d = get_net_config(all=True)
        for dconfig in config_d.values():
            ni = None
            if (NetworkInterface.objects.filter(
                    name=dconfig['name']).exists()):
                ni = NetworkInterface.objects.get(name=dconfig['name'])
                ni = cls._update_ni_obj(ni, dconfig)
            else:
                ni = NetworkInterface(name=dconfig['name'],
                                      mac=dconfig.get('mac', None),
                                      method=dconfig.get('method', None),
                                      autoconnect=dconfig.get('autoconnect', None),
                                      netmask=dconfig.get('netmask', None),
                                      ipaddr=dconfig.get('ipaddr', None),
                                      gateway=dconfig.get('gateway', None),
                                      dns_servers=dconfig.get('dns_servers', None),)
            if (default_if == ni.name):
                ni.itype = 'management'
                try:
                    update_issue(dconfig['ipaddr'])
                except Exception, e:
                    logger.error('Unable to update /etc/issue. Exception: %s' % e.__str__())
            ni.save()
        devices = []
        for ni in NetworkInterface.objects.all():
            if (ni.name not in config_d):
                logger.debug('network interface(%s) does not exist in the '
                             'system anymore. Removing from db' % (ni.name))
                ni.delete()
            else:
                devices.append(ni)
        serializer = NetworkInterfaceSerializer(devices, many=True)
        return Response(serializer.data)

    def post(self, request):
        with self._handle_exception(request):
            return self._net_scan()


class NetworkDetailView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkInterfaceSerializer

    def get(self, *args, **kwargs):
        try:
            data = NetworkInterface.objects.get(name=self.kwargs['iname'])
            serialized_data = NetworkInterfaceSerializer(data)
            return Response(serialized_data.data)
        except:
            return Response()

    @transaction.atomic
    def delete(self, request, iname):
        with self._handle_exception(request):
            if (NetworkInterface.objects.filter(name=iname).exists()):
                i = NetworkInterface.objects.get(name=iname)
                i.delete()
            return Response()

    def _validate_netmask(self, request):
        netmask = request.data.get('netmask', None)
        e_msg = ('Provided netmask value(%s) is invalid. You can provide it '
                 'in a IP address format(eg: 255.255.255.0) or number of '
                 'bits(eg: 24)' % netmask)
        if (netmask is None):
            handle_exception(Exception(e_msg), request)
        bits = 0
        try:
            bits = int(netmask)
        except ValueError:
            #assume ip address format was provided
            bits = sum([bin(int(x)).count('1') for x in '255.255.255'.split('.')])
        if (bits < 1 or bits > 32):
            e_msg = ('Provided netmask value(%s) is invalid. Number of '
                     'bits in netmask must be between 1-32' % netmask)
            handle_exception(Exception(e_msg), request)
        return bits

    @transaction.atomic
    def put(self, request, iname):
        with self._handle_exception(request):
            if (not NetworkInterface.objects.filter(name=iname).exists()):
                e_msg = ('Netowrk interface(%s) does not exist.' % iname)
                handle_exception(Exception(e_msg), request)
            ni = NetworkInterface.objects.get(name=iname)

            itype = request.data['itype']
            if (itype != 'management'):
                itype = 'io'
            method = request.data.get('method')
            ni.onboot = 'yes'
            if (method == 'auto'):
                config_network_device(ni.name)
            elif (method == 'manual'):
                ipaddr = request.data.get('ipaddr')
                for i in NetworkInterface.objects.filter(ipaddr=ipaddr):
                    if (i.id != ni.id):
                        e_msg = ('IP: %s already in use by another '
                                 'interface: %s' % (ni.ipaddr, i.name))
                        handle_exception(Exception(e_msg), request)
                netmask = self._validate_netmask(request)
                gateway = request.data.get('gateway', None)
                dns_servers = request.data.get('dns_servers', None)
                config_network_device(ni.name, dtype=ni.dtype, method='manual',
                                      ipaddr=ipaddr, netmask=netmask,
                                      gateway=gateway, dns_servers=dns_servers)
            else:
                e_msg = ('Method must be auto(for dhcp) or manual(for static IP). not: %s' %
                         method)
                handle_exception(Exception(e_msg), request)
            dconfig = get_net_config(ni.name)[ni.name]
            ni = self._update_ni_obj(ni, dconfig)
            ni.save()
            if (itype == 'management'):
                a = Appliance.objects.get(current_appliance=True)
                a.ip = ni.ipaddr
                a.save()
                try:
                    update_issue(ni.ipaddr)
                except Exception, e:
                    logger.error('Unable to update /etc/issue. Exception: %s' % e.__str__())
            return Response(NetworkInterfaceSerializer(ni).data)
