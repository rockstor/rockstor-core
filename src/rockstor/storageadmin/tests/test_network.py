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

from rest_framework import status
from rest_framework.test import APITestCase
from mock import patch
from storageadmin.tests.test_api import APITestMixin


class NetworkTests(APITestMixin, APITestCase):
    # Fixture from single ethernet KVM instance for now to start off new
    # mocking required after recent api change.
    fixtures = ['test_network.json']
    # TODO: Needs changing as API url different ie connection|devices|refresh
    # see referenced pr in setUpClass
    BASE_URL = '/api/network'

    @classmethod
    def setUpClass(cls):
        super(NetworkTests, cls).setUpClass()

        # N.B. major changes were made to network functionality via pr:
        # https://github.com/rockstor/rockstor-core/pull/1253
        # which added new network primitives via system/network.py

        # TODO: Needs a few mock changes, adding starters.

        # post mocks

        # devices map dictionary
        cls.patch_devices = patch('system.network.get_dev_config')
        cls.mock_devices = cls.patch_devices.start()
        cls.mock_devices.return_value = {
            'lo': {'dtype': 'loopback', 'mac': '00:00:00:00:00:00',
                   'state': '10 (unmanaged)', 'mtu': '65536'},
            'eth0': {'dtype': 'ethernet', 'mac': '52:54:00:58:5D:66',
                     'connection': 'eth0', 'state': '100 (connected)',
                     'mtu': '1500'}}

        # connections map dictionary
        cls.patch_connections = patch('system.network.get_con_config')
        cls.mock_connections = cls.patch_connections.start()
        cls.mock_connections.return_value = {
            '8dca3630-8c54-4ad7-8421-327cc2d3d14a':
                {'ctype': '802-3-ethernet',
                 'ipv6_addresses': None,
                 'ipv4_method': 'auto',
                 'ipv6_method': None,
                 'ipv6_dns': None,
                 'name': 'eth0',
                 'ipv4_addresses': '192.168.124.235/24',
                 'ipv6_gw': None,
                 'ipv4_dns': '192.168.124.1',
                 'state': 'activated',
                 'ipv6_dns_search': None,
                 '802-3-ethernet': {
                     'mac': '52:54:00:58:5D:66',
                     'mtu': 'auto',
                     'cloned_mac': None},
                 'ipv4_gw': '192.168.124.1',
                 'ipv4_dns_search': None}}


        # valid_connection
        cls.patch_valid_connection = patch('system.network.valid_connection')
        cls.mock_valid_connection = cls.patch_valid_connection.start()
        cls.mock_valid_connection.return_value = True

        # toggle_connection
        cls.patch_toggle_connection = patch('system.network.toggle_connection')
        cls.mock_toggle_connection = cls.patch_toggle_connection.start()
        cls.mock_toggle_connection.return_value = [''], [''], 0

        # delete_connection
        cls.patch_delete_connection = patch('system.network.delete_connection')
        cls.mock_delete_connection = cls.patch_delete_connection.start()
        cls.mock_delete_connection.return_value = [''], [''], 0

        # reload_connection
        cls.patch_reload_connection = patch('system.network.reload_connection')
        cls.mock_reload_connection = cls.patch_reload_connection.start()
        cls.mock_reload_connection.return_value = [''], [''], 0

        # new_connection_helper
        cls.patch_new_con_helper = patch(
            'system.network.new_connection_helper')
        cls.mock_new_con_helper = cls.patch_new_con_helper.start()
        cls.mock_new_con_helper.return_value = [''], [''], 0

        # new_ethernet_connection
        cls.patch_new_eth_conn = patch(
            'system.network.new_ethernet_connection')
        cls.mock_new_eth_conn = cls.patch_new_eth_conn.start()
        cls.mock_new_eth_conn.return_value = [''], [''], 0

        # new_member_helper
        cls.patch_new_mem_helper = patch('system.network.new_member_helper')
        cls.mock_new_mem_helper = cls.patch_new_mem_helper.start()
        cls.mock_new_mem_helper.return_value = [''], [''], 0

        # TODO: Also need to mock
        # system.network.new_team_connection
        # and
        # system.network.new_bond_connection

    @classmethod
    def tearDownClass(cls):
        super(NetworkTests, cls).tearDownClass()

    # TODO: Probably needs a re-write from here down due to API change.
    # N.B. There are working and current system level unit tests in:
    # src/rockstor/system/tests/test_system_network.py
    # Added via pr: "Add unit testing for core network functions" #2045 on GitHub

    # Fixture fix1.json has the test data. networks already exits in data are
    # 'enp0s3' and 'enp0s8'
    # TODO: AttributeError: 'HttpResponseNotFound' object has no attribute 'data'
    #  received on both below tests. Suspected as due to above referenced API change.
    # def test_get(self):
    #     """
    #     unauthorized access
    #     """
    #     # get base URL
    #     response = self.client.get(self.BASE_URL)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #
    #     # get with iname
    #     response = self.client.get('%s/enp0s3' % self.BASE_URL)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)

    # def test_put(self):
    #     """
    #     put, change itype
    #     """
    #     # TODO: test needs updating, interface now different.
    #     # invalid network interface
    #     data = {'itype': 'management'}
    #     response = self.client.put('%s/invalid' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = 'Network connection (invalid) does not exist.'
    #     self.assertEqual(response.data['detail'], e_msg)
    #
    #     # edit configuration with out providing config method
    #     data = {'method': '', 'itype': 'management'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = 'Method must be auto(for dhcp) or manual(for static IP). not: '
    #     self.assertEqual(response.data['detail'], e_msg)
    #
    #     # happy path
    #     data = {'method': 'auto', 'itype': 'management'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #     self.assertEqual(response.data['itype'], 'management')
    #
    #     # netmask set to None
    #     data = {'method': 'manual', 'ipaddr': '192.168.56.101',
    #             'netmask': None, 'gateway': '', 'dns_servers': '',
    #             'itype': 'io'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = ('Provided netmask value(None) is invalid. You can provide '
    #              'it in a IP address format(eg: 255.255.255.0) or number of '
    #              'bits(eg: 24)')
    #     self.assertEqual(response.data['detail'], e_msg)
    #
    #     # Invalid netmask
    #     data = {'method': 'manual', 'ipaddr': '192.168.56.101',
    #             'netmask': '111', 'gateway': '',
    #             'dns_servers': '', 'itype': 'io'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = ('Provided netmask value(111) is invalid. Number of bits in '
    #              'netmask must be between 1-32')
    #     self.assertEqual(response.data['detail'], e_msg)
    #
    #     # happy path
    #     data = {'method': 'manual', 'ipaddr': '192.168.56.101',
    #             'netmask': '225.225.225.0', 'gateway': '',
    #             'dns_servers': '', 'itype': 'io'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #     self.assertEqual(response.data['itype'], 'io')
    #
    #     # happy path
    #     data = {'method': 'auto', 'itype': 'management'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)
    #     self.assertEqual(response.data['itype'], 'management')
    #
    #     # Setting network interface itype to management when the othet network
    #     # is already set to management
    #     data = {'method': 'auto', 'itype': 'management'}
    #     response = self.client.put('%s/enp0s8' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = ('Another interface(enp0s3) is already configured for '
    #              'management. You must disable it first before making this '
    #              'change.')
    #     self.assertEqual(response.data['detail'], e_msg)
    #
    #     # provide ipaddress thats already been used by another interface
    #     data = {'method': 'manual', 'ipaddr': '10.0.3.15',
    #             'netmask': '225.225.225.0', 'gateway': '',
    #             'dns_servers': '', 'itype': 'io'}
    #     response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                      msg=response.data)
    #     e_msg = ('IP: 192.168.56.101 already in use by another '
    #              'interface: enp0s8')
    #     self.assertEqual(response.data['detail'], e_msg)
