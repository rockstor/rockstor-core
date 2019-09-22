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

import json
from django.db import transaction
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from storageadmin.models import (NetworkConnection, NetworkDevice,
                                 EthernetConnection, TeamConnection,
                                 BondConnection)
from smart_manager.models import Service
from storageadmin.util import handle_exception
from storageadmin.serializers import (NetworkDeviceSerializer,
                                      NetworkConnectionSerializer)
from system import network
import rest_framework_custom as rfc

import logging
logger = logging.getLogger(__name__)

MIN_MTU = 1500
MAX_MTU = 9000
DEFAULT_MTU = MIN_MTU


class NetworkMixin(object):
    # Runners for teams. @todo: support basic defaults + custom configuration.
    # @todo: lacp doesn't seem to be activating
    runners = {
        'broadcast': '{ "runner": {"name": "broadcast"}}',
        'roundrobin': '{ "runner": {"name": "roundrobin"}}',
        'activebackup': '{ "runner": {"name": "activebackup"}}',
        'loadbalance': '{ "runner": {"name": "loadbalance"}}',
        'lacp': '{ "runner": {"name": "lacp"}}',
    }
    team_profiles = ('broadcast', 'roundrobin', 'activebackup', 'loadbalance',
                     'lacp')
    bond_profiles = ('balance-rr', 'active-backup', 'balance-xor', 'broadcast',
                     '802.3ad', 'balance-tlb', 'balance-alb')

    @staticmethod
    @transaction.atomic
    def _update_or_create_ctype(co, ctype, config):
        if (ctype == '802-3-ethernet'):
            try:
                eco = EthernetConnection.objects.get(connection=co)
                eco.mac = config['mac']
                eco.cloned_mac = config['cloned_mac']
                eco.mtu = config['mtu']
                eco.save()
            except EthernetConnection.DoesNotExist:
                EthernetConnection.objects.create(connection=co, **config)
        elif (ctype == 'team'):
            try:
                tco = TeamConnection.objects.get(connection=co)
                tco.name = co.name
                tco.config = config['config']
                tco.save()
            except TeamConnection.DoesNotExist:
                TeamConnection.objects.create(connection=co, **config)
        elif (ctype == 'bond'):
            try:
                bco = BondConnection.objects.get(connection=co)
                bco.name = co.name
                bco.config = config['config']
                bco.save()
            except BondConnection.DoesNotExist:
                BondConnection.objects.create(connection=co, **config)
        else:
            logger.error('Unknown ctype: {} config: {}'.format(ctype, config))

    @staticmethod
    @transaction.atomic
    def _update_master(co, config, defer_list=None):
        if ('master' not in config):
            return config
        try:
            co.master = NetworkConnection.objects.get(name=config['master'])
        except (NetworkConnection.DoesNotExist,
                NetworkConnection.MultipleObjectsReturned):
            if (not isinstance(defer_list, list)):
                raise
            defer_list.append({'uuid': co.uuid, 'master': config['master']})
        del(config['master'])

    @classmethod
    @transaction.atomic
    def _refresh_connections(cls):
        cmap = network.get_con_config(network.get_con_list())
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
            # new connections not yet in administrative state.
            config = cmap[uuid]
            config['uuid'] = uuid
            ctype = ctype_d = None
            if ('ctype' in config):
                ctype = config['ctype']
                ctype_d = config[ctype]
                del(config[ctype])
                del(config['ctype'])
            if ('master' in config):
                defer_master_updates.append({'uuid': uuid, 'master':
                                             config['master']})
                del(config['master'])
            nco = NetworkConnection.objects.create(**config)
            if (ctype is not None):
                cls._update_or_create_ctype(nco, ctype, ctype_d)
        for e in defer_master_updates:
            slave_co = NetworkConnection.objects.get(uuid=e['uuid'])
            try:
                slave_co.master = NetworkConnection.objects.get(name=e['master'])  # noqa E501
            except (NetworkConnection.DoesNotExist,
                    NetworkConnection.MultipleObjectsReturned) as e:
                logger.exception(e)
            slave_co.save()

    @staticmethod
    @transaction.atomic
    def _refresh_devices():
        dmap = network.get_dev_config(network.get_dev_list())

        def update_connection(dconfig):
            if ('connection' in dconfig):
                try:
                    dconfig['connection'] = NetworkConnection.objects.get(
                        name=dconfig['connection'])
                except (NetworkConnection.DoesNotExist,
                        NetworkConnection.MultipleObjectsReturned) as e:
                    logger.exception(e)
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


class NetworkDeviceListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkDeviceSerializer

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._refresh_devices()
            # don't return unmanaged devices return
            # NetworkDevice.objects.filter(~Q(state='10 (unmanaged)'))
            return NetworkDevice.objects.all()


class NetworkConnectionListView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkConnectionSerializer
    ctypes = ('ethernet', 'team', 'bond')

    # ethtool is the default link watcher.

    config_methods = ('auto', 'manual')

    def get_queryset(self, *args, **kwargs):
        with self._handle_exception(self.request):
            self._refresh_connections()
            return NetworkConnection.objects.all()

    @staticmethod
    def _validate_devices(devices, request, size=2):
        if (not isinstance(devices, list)):
            raise Exception('devices must be a list')
        if (len(devices) < size):
            raise Exception(('A minimum of {} devices are '
                            'required.').format(size))
        for d in devices:
            try:
                NetworkDevice.objects.get(name=d)
                # if device belongs to another connection, change it.
            except NetworkDevice.DoesNotExist:
                e_msg = 'Unknown network device ({}).'.format(d)
                handle_exception(Exception(e_msg), request)
        return devices

    @transaction.atomic
    def post(self, request):
        with self._handle_exception(request):
            ipaddr = gateway = dns_servers = search_domains = None
            name = request.data.get('name')
            if (NetworkConnection.objects.filter(name=name).exists()):
                e_msg = ('Connection name ({}) is already in use. Choose a '
                         'different name.').format(name)
                handle_exception(Exception(e_msg), request)

            # auto of manual
            method = request.data.get('method')
            if (method not in self.config_methods):
                e_msg = ('Unsupported config method ({}). Supported ones '
                         'include: ({}).').format(method, self.config_methods)
                handle_exception(Exception(e_msg), request)
            if (method == 'manual'):
                # ipaddr is of the format <IP>/<netmask>. eg:
                # 192.168.1.2/24. If netmask is not given, it defaults to 32.
                ipaddr = request.data.get('ipaddr')
                gateway = request.data.get('gateway', None)
                dns_servers = request.data.get('dns_servers', None)
                search_domains = request.data.get('search_domains', None)

            # connection type can be one of ethernet, team or bond
            ctype = request.data.get('ctype')
            if (ctype not in self.ctypes):
                e_msg = ('Unsupported connection type ({}). Supported ones '
                         'include: ({}).').format(ctype, self.ctypes)
                handle_exception(Exception(e_msg), request)
            devices = request.data.get('devices', None)
            if (ctype == 'team'):
                # gather required input for team
                team_profile = request.data.get('team_profile')
                if (team_profile not in self.team_profiles):
                    e_msg = ('Unsupported team profile ({}). Supported ones '
                             'include: ({}).').format(team_profile,
                                                      self.team_profiles)
                    handle_exception(Exception(e_msg), request)
                self._validate_devices(devices, request)
                network.new_team_connection(name, self.runners[team_profile],
                                            devices, ipaddr, gateway,
                                            dns_servers, search_domains)

            elif (ctype == 'ethernet'):
                device = request.data.get('device')
                self._validate_devices([device], request, size=1)
                network.new_ethernet_connection(name, device, ipaddr, gateway,
                                                dns_servers, search_domains)

            elif (ctype == 'bond'):
                bond_profile = request.data.get('bond_profile')
                if (bond_profile not in self.bond_profiles):
                    e_msg = ('Unsupported bond profile ({}). Supported ones '
                             'include: ({}).').format(bond_profile,
                                                      self.bond_profiles)
                    handle_exception(Exception(e_msg), request)
                self._validate_devices(devices, request)
                network.new_bond_connection(name, bond_profile, devices,
                                            ipaddr, gateway, dns_servers,
                                            search_domains)

            return Response()


class NetworkConnectionDetailView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkConnectionSerializer

    def get(self, *args, **kwargs):
        try:
            data = NetworkConnection.objects.get(id=self.kwargs['id'])
            sdata = NetworkConnectionSerializer(data)
            return Response(sdata.data)
        except NetworkConnection.DoesNotExist:
            raise NotFound(detail=None)

    @staticmethod
    def _nco(request, id):
        try:
            return NetworkConnection.objects.get(id=id)
        except NetworkConnection.DoesNotExist:
            e_msg = 'Network connection ({}) does not exist.'.format(id)
            handle_exception(Exception(e_msg), request)

    @transaction.atomic
    def put(self, request, id):

        with self._handle_exception(request):
            nco = self._nco(request, id)
            method = request.data.get('method')
            mtu = DEFAULT_MTU
            try:
                e_msg = ('The mtu must be an integer in {} - {} '
                         'range.').format(MIN_MTU, MAX_MTU)
                mtu = int(request.data.get('mtu', DEFAULT_MTU))
                if mtu < MIN_MTU or mtu > MAX_MTU:
                    handle_exception(Exception(e_msg), request)
            except ValueError:
                handle_exception(Exception(e_msg), request)
            ipaddr = gateway = dns_servers = search_domains = None
            if (method == 'manual'):
                ipaddr = request.data.get('ipaddr', None)
                gateway = request.data.get('gateway', None)
                dns_servers = request.data.get('dns_servers', None)
                search_domains = request.data.get('search_domains', None)

            if (nco.ctype == 'ethernet'):
                device = nco.networkdevice_set.first().name
                self._delete_connection(nco)
                network.new_ethernet_connection(nco.name, device, ipaddr,
                                                gateway, dns_servers,
                                                search_domains, mtu)
            elif (nco.ctype == 'team'):
                team_profile = nco.team_profile
                devices = []
                for child_nco in NetworkConnection.objects.filter(master=nco):
                    devices.append(child_nco.networkdevice_set.first().name)

                self._delete_connection(nco)
                network.new_team_connection(
                    nco.name, self.runners[team_profile], devices, ipaddr,
                    gateway, dns_servers, search_domains, mtu)

            return Response(NetworkConnectionSerializer(nco).data)

    @staticmethod
    def _delete_connection(nco):
        for mnco in nco.networkconnection_set.all():
            network.delete_connection(mnco.uuid)
        network.delete_connection(nco.uuid)
        nco.delete()

    @transaction.atomic
    def delete(self, request, id):
        with self._handle_exception(request):
            nco = self._nco(request, id)
            restricted = False
            try:
                so = Service.objects.get(name='rockstor')
                config = json.loads(so.config)
                if (config['network_interface'] == nco.name):
                    restricted = True
            except Exception as e:
                logger.exception(e)
            if (restricted):
                e_msg = ('This connection ({}) is designated for '
                         'management and cannot be deleted. If you really '
                         'need to delete it, change the Rockstor service '
                         'configuration and try again.').format(nco.name)
                handle_exception(Exception(e_msg), request)
            self._delete_connection(nco)
            return Response()

    @transaction.atomic
    def post(self, request, id, switch):
        # switch the connection up, down or reload.
        with self._handle_exception(request):
            nco = self._nco(request, id)
            if (switch == 'up' and nco.ctype in ('team', 'bond')):
                # order_by('name') because in some cases member interfaces must
                # be brought up in order. eg: active-backup.
                for mnco in nco.networkconnection_set.all().order_by('name'):
                    logger.debug('upping {} {}'.format(mnco.name, mnco.uuid))
                    network.toggle_connection(mnco.uuid, switch)
            else:
                network.toggle_connection(nco.uuid, switch)
            return Response(NetworkConnectionSerializer(nco).data)


class NetworkStateView(rfc.GenericView, NetworkMixin):
    serializer_class = NetworkConnectionSerializer

    def get_queryset(self, *args, **kwargs):
        return NetworkConnection.objects.all()

    def post(self, request):
        with self._handle_exception(request):
            self._refresh_connections()
            self._refresh_devices()
            ns = NetworkConnectionSerializer(
                NetworkConnection.objects.all(), many=True)
            return Response(ns.data)
