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
    fixtures = ['fix1.json']
    BASE_URL = '/api/network'

    @classmethod
    def setUpClass(cls):
        super(NetworkTests, cls).setUpClass()

        # post mocks

        cls.patch_config_network_device = patch(
            'storageadmin.views.network.config_network_device')
        cls.mock_config_network_device = cls.patch_config_network_device.start()  # noqa E501
        cls.mock_config_network_device.return_value = 'out', 'err', 0

        # return value is set as per the network interface configuration data
        # in fixture fix1.json
        cls.patch_get_net_config = patch(
            'storageadmin.views.network.get_net_config')
        cls.mock_get_net_config = cls.patch_get_net_config.start()
        cls.mock_get_net_config.return_value = {
            'enp0s3': {
                'autoconnect': 'yes',
                'name': 'enp0s3',
                'state': 'activated',
                'dname': 'enp0s3',
                'dtype': 'ethernet',
                'dspeed': '1000 Mb/s',
                'ipaddr': '192.168.56.101',
                'netmask': '255.255.255.0',
                'ctype': '802-3-ethernet',
                'mac': '08:00:27:F6:2C:85',
                'method': 'auto'},
            'enp0s8': {
                'dns_servers': '10.0.3.3',
                'dtype': 'ethernet',
                'ctype': '802-3-ethernet',
                'mac': '08:00:27:BA:4B:88',
                'gateway': '10.0.3.2',
                'autoconnect': 'yes',
                'name': 'enp0s8',
                'dname': 'enp0s8',
                'dspeed': '1000 Mb/s',
                'ipaddr': '10.0.3.15',
                'netmask': '255.255.255.0',
                'state': 'activated',
                'method': 'auto'
            }
        }

    @classmethod
    def tearDownClass(cls):
        super(NetworkTests, cls).tearDownClass()

    # Fixture fix1.json has the test data. networks already exits in data are
    # 'enp0s3' and 'enp0s8'
    def test_get(self):
        """
        unauthorized access
        """
        # get base URL
        response = self.client.get(self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

        # get with iname
        response = self.client.get('%s/enp0s3' % self.BASE_URL)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)

    def test_put(self):
        """
        put, change itype
        """
        # TODO: test needs updating, interface now different.
        # invalid network interface
        data = {'itype': 'management'}
        response = self.client.put('%s/invalid' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Network connection (invalid) does not exist.'
        self.assertEqual(response.data['detail'], e_msg)

        # edit configuration with out providing config method
        data = {'method': '', 'itype': 'management'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = 'Method must be auto(for dhcp) or manual(for static IP). not: '
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'method': 'auto', 'itype': 'management'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['itype'], 'management')

        # netmask set to None
        data = {'method': 'manual', 'ipaddr': '192.168.56.101',
                'netmask': None, 'gateway': '', 'dns_servers': '',
                'itype': 'io'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Provided netmask value(None) is invalid. You can provide '
                 'it in a IP address format(eg: 255.255.255.0) or number of '
                 'bits(eg: 24)')
        self.assertEqual(response.data['detail'], e_msg)

        # Invalid netmask
        data = {'method': 'manual', 'ipaddr': '192.168.56.101',
                'netmask': '111', 'gateway': '',
                'dns_servers': '', 'itype': 'io'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Provided netmask value(111) is invalid. Number of bits in '
                 'netmask must be between 1-32')
        self.assertEqual(response.data['detail'], e_msg)

        # happy path
        data = {'method': 'manual', 'ipaddr': '192.168.56.101',
                'netmask': '225.225.225.0', 'gateway': '',
                'dns_servers': '', 'itype': 'io'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['itype'], 'io')

        # happy path
        data = {'method': 'auto', 'itype': 'management'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_200_OK, msg=response.data)
        self.assertEqual(response.data['itype'], 'management')

        # Setting network interface itype to management when the othet network
        # is already set to management
        data = {'method': 'auto', 'itype': 'management'}
        response = self.client.put('%s/enp0s8' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('Another interface(enp0s3) is already configured for '
                 'management. You must disable it first before making this '
                 'change.')
        self.assertEqual(response.data['detail'], e_msg)

        # provide ipaddress thats already been used by another interface
        data = {'method': 'manual', 'ipaddr': '10.0.3.15',
                'netmask': '225.225.225.0', 'gateway': '',
                'dns_servers': '', 'itype': 'io'}
        response = self.client.put('%s/enp0s3' % self.BASE_URL, data=data)
        self.assertEqual(response.status_code,
                         status.HTTP_500_INTERNAL_SERVER_ERROR,
                         msg=response.data)
        e_msg = ('IP: 192.168.56.101 already in use by another '
                 'interface: enp0s8')
        self.assertEqual(response.data['detail'], e_msg)
