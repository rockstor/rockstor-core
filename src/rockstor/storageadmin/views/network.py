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
    def _restart_wrapper(ni, request):
            try:
                restart_network_interface(ni.name)
            except Exception, e:
                logger.exception(e)
                e_msg = ('Failed to configure network interface(%s) due'
                         ' to a system error' % ni.name)
                handle_exception(Exception(e_msg), request)


class NetworkListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkInterfaceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._net_scan()
            #to be deprecated soon
            update_samba_discovery()
        return NetworkInterface.objects.all()

    @staticmethod
    @transaction.atomic
    def _net_scan():
        default_if = get_default_interface()
        config_d = get_net_config(all=True)
        for dconfig in config_d.values():
            ni = None
            if (NetworkInterface.objects.filter(
                    name=dconfig['name']).exists()):
                ni = NetworkInterface.objects.get(name=dconfig['name'])
                ni.dname = dconfig.get('dname', None)
                ni.mac = dconfig.get('mac', None)
                ni.method = dconfig.get('method', 'manual')
                ni.autoconnect = dconfig.get('autoconnect', 'no')
                ni.netmask = dconfig.get('netmask', None)
                ni.ipaddr = dconfig.get('ipaddr', None)
                ni.gateway = dconfig.get('gateway', None)
                ni.dns_servers = dconfig.get('dns_servers', None)
                ni.ctype = dconfig.get('ctype', None)
                ni.dtype = dconfig.get('dtype', None)
                ni.dspeed = dconfig.get('dspeed', None)
                ni.state = dconfig.get('state', None)
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
            boot_proto = request.data['boot_protocol']
            ni.onboot = 'yes'
            if (boot_proto == 'dhcp'):
                config_network_device(ni.alias)
            elif (boot_proto == 'static'):
                ipaddr = request.data.get('ipaddr')
                for i in NetworkInterface.objects.filter(ipaddr=ipaddr):
                    if (i.id != ni.id):
                        e_msg = ('IP: %s already in use by another '
                                 'interface: %s' % (ni.ipaddr, i.name))
                        handle_exception(Exception(e_msg), request)
                netmask = self._validate_netmask(request)
                gateway = request.data.get('gateway', None)
                dns_servers = request.data.get('dns_servers', None)
                logger.debug('ip: %s netmask: %s gateway: %s dns_servers: %s '
                             'domain: %s' % (ipaddr, netmask, gateway, dns_servers, domain))
                config_network_device(ni.alias, boot_proto='static',
                                      ipaddr=ipaddr, netmask=netmask,
                                      gateway=gateway, dns_servers=dns_servers)
            else:
                e_msg = ('Boot protocol must be dhcp or static. not: %s' %
                         boot_proto)
                handle_exception(Exception(e_msg), request)
            #restarting not needed?
            #self._restart_wrapper(ni, request)
            dconfig = get_net_config(ni.name)[ni.name]
            ni.dname = dconfig.get('dname', None)
            ni.mac = dconfig.get('mac', None)
            ni.method = dconfig.get('method', 'manual')
            ni.autoconnect = dconfig.get('autoconnect', 'no')
            ni.netmask = dconfig.get('netmask', None)
            ni.ipaddr = dconfig.get('ipaddr', None)
            ni.gateway = dconfig.get('gateway', None)
            ni.dns_servers = dconfig.get('dns_servers', None)
            ni.ctype = dconfig.get('ctype', None)
            ni.dtype = dconfig.get('dtype', None)
            ni.dspeed = dconfig.get('dspeed', None)
            ni.state = dconfig.get('state', None)
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
