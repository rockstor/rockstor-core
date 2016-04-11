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
from tempfile import mkstemp
from shutil import move
from django.db import transaction
from django.conf import settings
from rest_framework.response import Response
from storageadmin.models import (NetworkInterface, NetworkConnection, NetworkDevice, Appliance, EthernetConnection)
from storageadmin.util import handle_exception
from storageadmin.serializers import (NetworkInterfaceSerializer, NetworkDeviceSerializer, NetworkConnectionSerializer)
from system.osi import (config_network_device, get_net_config, update_issue)
from system.samba import update_samba_discovery
from system.services import superctl
from system import network
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)


class NetworkMixin(object):

    @staticmethod
    def _update_ni_obj(nio, values):
        nio.dname = values.get('dname', nio.dname)
        nio.mac = values.get('mac', nio.mac)
        nio.method = values.get('method', 'manual')
        nio.autoconnect = values.get('autoconnect', 'no')
        nio.netmask = values.get('netmask', nio.netmask)
        nio.ipaddr = values.get('ipaddr', nio.ipaddr)
        nio.gateway = values.get('gateway', nio.gateway)
        nio.dns_servers = values.get('dns_servers', nio.dns_servers)
        nio.ctype = values.get('ctype', nio.ctype)
        nio.dtype = values.get('dtype', nio.dtype)
        nio.dspeed = values.get('dspeed', nio.dspeed)
        nio.state = values.get('state', nio.state)
        return nio

    @staticmethod
    def _update_nginx(ipaddr=None):
        #update nginx config and restart the service
        conf = '%s/etc/nginx/nginx.conf' % settings.ROOT_DIR
        fo, npath = mkstemp()
        with open(conf) as ifo, open(npath, 'w') as tfo:
            for line in ifo.readlines():
                if (re.search('listen.*80 default_server', line) is not None):
                    substr = 'listen 80'
                    if (ipaddr is not None):
                        substr = 'listen %s:80' % ipaddr
                    line = re.sub(r'listen.*80', substr, line)
                elif (re.search('listen.*443 default_server', line) is not None):
                    substr = 'listen 443'
                    if (ipaddr is not None):
                        substr = 'listen %s:443' % ipaddr
                    line = re.sub(r'listen.*443', substr, line)
                tfo.write(line)
        move(npath, conf)
        superctl('nginx', 'restart')

    @classmethod
    @transaction.atomic
    def _refresh_ni(cls):
        config_d = get_net_config(all=True)
        for dconfig in config_d.values():
            ni = None
            if (NetworkInterface.objects.filter(
                    name=dconfig['name']).exists()):
                ni = NetworkInterface.objects.get(name=dconfig['name'])
                ni = cls._update_ni_obj(ni, dconfig)
            else:
                ni = NetworkInterface(name=dconfig.get('name', None),
                                      dname=dconfig.get('dname', None),
                                      dtype=dconfig.get('dtype', None),
                                      dspeed=dconfig.get('dspeed', None),
                                      mac=dconfig.get('mac', None),
                                      method=dconfig.get('method', None),
                                      autoconnect=dconfig.get('autoconnect', None),
                                      netmask=dconfig.get('netmask', None),
                                      ipaddr=dconfig.get('ipaddr', None),
                                      gateway=dconfig.get('gateway', None),
                                      dns_servers=dconfig.get('dns_servers', None),
                                      ctype=dconfig.get('ctype', None),
                                      state=dconfig.get('state', None))
            ni.save()
        for ni in NetworkInterface.objects.all():
            if (ni.dname not in config_d):
                logger.debug('network interface(%s) does not exist in the '
                             'system anymore. Removing from db' % (ni.name))
                ni.delete()

    @staticmethod
    @transaction.atomic
    def _update_or_create_ctype(co, ctype, config):
        if (ctype == '802-3-ethernet'):
            try:
                eco = EthernetConnection.objects.filter(connection=co).update(**config)
            except EthernetConnection.DoesNotExist:
                EthernetConnection.objects.create(**config)
            #elif's for other types of connections

    @staticmethod
    @transaction.atomic
    def _update_master(co, config, defer_list=None):
        if ('master' not in config):
            return config
        try:
            co.master = NetworkConnection.objects.get(name=config['master'])
        except NetworkConnection.DoesNotExist:
            if (not isinstance(defer_list, list)):
                raise
            defer_list.append({'uuid': co.uuid, 'master': config['master']})
        del(config['master'])

    @classmethod
    @transaction.atomic
    def _refresh_connections(cls):
        cmap = network.connections()
        defer_master_updates = []
        for nco in NetworkConnection.objects.all():
            if (nco.uuid not in cmap):
                nco.delete()
                continue
            config = cmap[nco.uuid]
            if ('ctype' in config):
                ctype = config['ctype']
                cls._update_or_create_ctype(nco, ctype, config[ctype])
                del(config[ctype])
                del(config['ctype'])
            cls._update_master(nco, config, defer_master_updates)
            NetworkConnection.objects.filter(uuid=nco.uuid).update(**config)
            del cmap[nco.uuid]
        for uuid in cmap:
            #new connections not yet in administrative state.
            config = cmap[uuid]
            config['uuid'] = uuid
            ctype = ctype_d = None
            if ('ctype' in config):
                ctype = config['ctype']
                ctype_d = config[ctype]
                del(config[ctype])
                del(config['ctype'])
            if ('master' in config):
                defer_master_updates.append({'uuid': uuid, 'master': config['master']})
                del(config['master'])
            nco = NetworkConnection.objects.create(**config)
            if (ctype is not None):
                cls._update_or_create_ctype(nco, ctype, ctype_d)
        for e in defer_master_updates:
            slave_co = NetworkConnection.objects.get(uuid=e['uuid'])
            slave_co.master = NetworkConnection.objects.get(name=e['master'])
            slave_co.save()

    @staticmethod
    @transaction.atomic
    def _refresh_devices():
        dmap = network.devices()
        def update_connection(dconfig):
            if ('connection' in dconfig):
                try:
                    dconfig['connection'] = NetworkConnection.objects.get(name=dconfig['connection'])
                except NetworkConnection.DoesNotExist:
                    dconfig['connection'] = None

        for ndo in NetworkDevice.objects.all():
            if (ndo.name not in dmap):
                ndo.delete()
                continue
            dconfig = dmap[ndo.name]
            update_connection(dconfig)
            NetworkDevice.objects.filter(name=ndo.name).update(**dconfig)
            del dmap[ndo.name]
        for dev in dmap:
            dconfig = dmap[dev]
            dconfig['name'] = dev
            update_connection(dconfig)
            NetworkDevice.objects.create(**dconfig)


class NetworkListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkInterfaceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._refresh_ni()
            #@todo to be deprecated soon
            update_samba_discovery()
            return NetworkInterface.objects.all()


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
            bits = sum([bin(int(x)).count('1') for x in netmask.split('.')])
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

            itype = request.data.get('itype', 'unassigned')
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
            dconfig = get_net_config(name=ni.name)[ni.dname]
            ni = self._update_ni_obj(ni, dconfig)
            if (itype == 'management' and ni.itype != 'management'):
                for i in NetworkInterface.objects.filter(itype='management'):
                    if (i.name != ni.name):
                        e_msg = ('Another interface(%s) is already configured '
                                 'for management. You must disable it first '
                                 'before making this change.' % i.name)
                        handle_exception(Exception(e_msg), request)
                a = Appliance.objects.get(current_appliance=True)
                a.ip = ni.ipaddr
                a.save()
            ni.itype = itype
            ni.save()
            if (ni.itype == 'management'):
                try:
                    update_issue(ni.ipaddr)
                except Exception, e:
                    logger.error('Unable to update /etc/issue. Exception: %s' % e.__str__())

                try:
                    self._update_nginx(ni.ipaddr)
                except Exception, e:
                    logger.error('Failed to update Nginx. Exception: %s' % e.__str__())
            else:
                try:
                    self._update_nginx()
                except Exception, e:
                    logger.error('Failed to update Nginx. Exception: %s' % e.__str__())

            return Response(NetworkInterfaceSerializer(ni).data)


class NetworkDeviceListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkDeviceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._refresh_devices()
            return NetworkDevice.objects.all()


class NetworkConnectionListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkConnectionSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._refresh_connections()
            return NetworkConnection.objects.all()
