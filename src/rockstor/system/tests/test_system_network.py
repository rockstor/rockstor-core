"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

Rockstor is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published
by the Free Software Foundation; either version 2 of the License,
or (at your option) any later version.

Rockstor is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
import unittest
from unittest.mock import patch, mock_open, call

from system.exceptions import CommandException
from system.network import (
    get_dev_config,
    get_con_config,
    enable_ip_forwarding,
    SYSCTL_CONFD_PATH,
    SYSCTL,
    disable_ip_forwarding,
)


class MockDirEntry:
    """Create a fake DirEntry object
    A DirEntry object is what's os.scandir returns. To properly mock os.scandir,
    we thus need to re-create what it would return. We currently only need some
    of the attributes that a real DirEntry has, so let's include only these:
    - name
    - path
    - is_file: bool
    """

    def __init__(self, name, path, is_file):
        self.name = name
        self.path = path
        self._is_file = is_file

    def is_file(self):
        return self._is_file


class SystemNetworkTests(unittest.TestCase):
    """
    The tests in this suite can be run via the following command:
    cd /opt/rockstor/src/rockstor
    export DJANGO_SETTINGS_MODULE=settings
    poetry run django-admin test -p test_system_network.py -v 2
    """

    def setUp(self):
        self.patch_run_command = patch("system.network.run_command")
        self.mock_run_command = self.patch_run_command.start()

    def tearDown(self):
        patch.stopall()

    def test_get_dev_config(self):
        """
        This tests for correct parsing of nmcli device config by get_dev_config(),
        which should return a dict with detailed config for each network device detected.
        """
        dev_name = ["enp0s3"]
        out = [
            [
                "GENERAL.DEVICE:                         enp0s3",
                "GENERAL.TYPE:                           ethernet",
                "GENERAL.HWADDR:                         08:00:27:AB:1C:C3",
                "GENERAL.MTU:                            1500",
                "GENERAL.STATE:                          100 (connected)",
                "GENERAL.CONNECTION:                     enp0s3",
                "GENERAL.CON-PATH:                       /org/freedesktop/NetworkManager/ActiveConnection/1",
                "WIRED-PROPERTIES.CARRIER:               on",
                "IP4.ADDRESS[1]:                         192.168.1.14/24",
                "IP4.GATEWAY:                            192.168.1.1",
                "IP4.ROUTE[1]:                           dst = 0.0.0.0/0, nh = 192.168.1.1, mt = 100",
                "IP4.ROUTE[2]:                           dst = 192.168.1.0/24, nh = 0.0.0.0, mt = 100",
                "IP4.DNS[1]:                             192.168.1.1",
                "IP6.ADDRESS[1]:                         fe80::dcd3:6b5f:52a1:abfa/64",
                "IP6.GATEWAY:                            --",
                "IP6.ROUTE[1]:                           dst = fe80::/64, nh = ::, mt = 100",
                "IP6.ROUTE[2]:                           dst = ff00::/8, nh = ::, mt = 256, table=255",
                "",
            ]
        ]
        err = [[""]]
        rc = [0]
        expected_result = [
            {
                "enp0s3": {
                    "dtype": "ethernet",
                    "mac": "08:00:27:AB:1C:C3",
                    "connection": "enp0s3",
                    "state": "100 (connected)",
                    "mtu": "1500",
                }
            }
        ]

        dev_name.append("lo")
        out.append(
            [
                "GENERAL.DEVICE:                         lo",
                "GENERAL.TYPE:                           loopback",
                "GENERAL.HWADDR:                         00:00:00:00:00:00",
                "GENERAL.MTU:                            65536",
                "GENERAL.STATE:                          10 (unmanaged)",
                "GENERAL.CONNECTION:                     --",
                "GENERAL.CON-PATH:                       --",
                "IP4.ADDRESS[1]:                         127.0.0.1/8",
                "IP4.GATEWAY:                            --",
                "IP6.ADDRESS[1]:                         ::1/128",
                "IP6.GATEWAY:                            --",
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        expected_result.append(
            {
                "lo": {
                    "dtype": "loopback",
                    "mac": "00:00:00:00:00:00",
                    "state": "10 (unmanaged)",
                    "mtu": "65536",
                }
            }
        )
        # @todo: Add more types of devices, such as docker0, wifi, eth, veth, etc...

        # Cycle through each of the above parameter / run_command data sets.
        for dev, o, e, r, expected in zip(dev_name, out, err, rc, expected_result):
            dev_list = [dev]
            self.mock_run_command.return_value = (o, e, r)
            returned = get_dev_config(dev_list)
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected get_dev_config() result:\n "
                "returned = ({}).\n "
                "expected = ({}).".format(returned, expected),
            )

    def test_get_dev_config_dev_not_found(self):
        """
        Test get_dev_config() if device is not found / vanished.
        It should return an empty dict.
        """
        dev_name = ["vethXX"]
        expected_result = {}
        self.mock_run_command.side_effect = CommandException(
            err=["Error: Device 'vethXX' not found.", ""],
            cmd=["/usr/bin/nmcli", "d", "show", "vethXX"],
            out=[""],
            rc=10,
        )
        returned = get_dev_config(dev_name)
        self.assertEqual(
            returned,
            expected_result,
            msg="Un-expected get_dev_config() result:\n "
            "returned = ({}).\n "
            "expected = ({}).\n "
            "for dev_name: {}".format(returned, expected_result, dev_name),
        )

    def test_get_dev_config_exception(self):
        """
        Test get_dev_config() if nmcli returns error code != 10.
        It should raise an exception (CommandException).
        """
        dev_name = ["vethXX"]
        self.mock_run_command.side_effect = CommandException(
            err=["Error: Device 'vethXX' not found.", ""],
            cmd=["/usr/bin/nmcli", "d", "show", "vethXX"],
            out=[""],
            rc=1,
        )
        with self.assertRaises(CommandException):
            get_dev_config(dev_name)

    def test_get_con_config(self):
        """
        This tests for correct parsing of nmcli connection config by get_con_config(),
        which should return a dict with detailed config for each network connection detected.
        """
        # Mock and patch docker-specific calls
        self.patch_docker_status = patch("system.network.docker_status")
        self.mock_docker_status = self.patch_docker_status.start()
        self.mock_docker_status.return_value = True

        self.patch_dnets = patch("system.network.dnets")
        self.mock_dnets = self.patch_dnets.start()

        self.patch_dnet_inspect = patch("system.network.dnet_inspect")
        self.mock_dnet_inspect = self.patch_dnet_inspect.start()

        con_name = ["c54ea011-0e23-43fa-8f06-23429b9ce714"]
        out = [
            [
                "connection.id:                          enp0s3",
                "connection.uuid:                        c54ea011-0e23-43fa-8f06-23429b9ce714",
                "connection.stable-id:                   --",
                "connection.type:                        802-3-ethernet",
                "connection.interface-name:              enp0s3",
                "connection.autoconnect:                 yes",
                "connection.autoconnect-priority:        0",
                "connection.autoconnect-retries:         -1 (default)",
                "connection.auth-retries:                -1",
                "connection.timestamp:                   1558054875",
                "connection.read-only:                   no",
                "connection.permissions:                 --",
                "connection.zone:                        --",
                "connection.master:                      --",
                "connection.slave-type:                  --",
                "connection.autoconnect-slaves:          -1 (default)",
                "connection.secondaries:                 --",
                "connection.gateway-ping-timeout:        0",
                "connection.metered:                     unknown",
                "connection.lldp:                        default",
                "connection.mdns:                        -1 (default)",
                "802-3-ethernet.port:                    --",
                "802-3-ethernet.speed:                   0",
                "802-3-ethernet.duplex:                  --",
                "802-3-ethernet.auto-negotiate:          no",
                "802-3-ethernet.mac-address:             --",
                "802-3-ethernet.cloned-mac-address:      --",
                "802-3-ethernet.generate-mac-address-mask:--",
                "802-3-ethernet.mac-address-blacklist:   --",
                "802-3-ethernet.mtu:                     auto",
                "802-3-ethernet.s390-subchannels:        --",
                "802-3-ethernet.s390-nettype:            --",
                "802-3-ethernet.s390-options:            --",
                "802-3-ethernet.wake-on-lan:             default",
                "802-3-ethernet.wake-on-lan-password:    --",
                "ipv4.method:                            auto",
                "ipv4.dns:                               --",
                "ipv4.dns-search:                        --",
                'ipv4.dns-options:                       ""',
                "ipv4.dns-priority:                      0",
                "ipv4.addresses:                         --",
                "ipv4.gateway:                           --",
                "ipv4.routes:                            --",
                "ipv4.route-metric:                      -1",
                "ipv4.route-table:                       0 (unspec)",
                "ipv4.ignore-auto-routes:                no",
                "ipv4.ignore-auto-dns:                   no",
                "ipv4.dhcp-client-id:                    --",
                "ipv4.dhcp-timeout:                      0 (default)",
                "ipv4.dhcp-send-hostname:                yes",
                "ipv4.dhcp-hostname:                     --",
                "ipv4.dhcp-fqdn:                         --",
                "ipv4.never-default:                     no",
                "ipv4.may-fail:                          yes",
                "ipv4.dad-timeout:                       -1 (default)",
                "ipv6.method:                            auto",
                "ipv6.dns:                               --",
                "ipv6.dns-search:                        --",
                'ipv6.dns-options:                       ""',
                "ipv6.dns-priority:                      0",
                "ipv6.addresses:                         --",
                "ipv6.gateway:                           --",
                "ipv6.routes:                            --",
                "ipv6.route-metric:                      -1",
                "ipv6.route-table:                       0 (unspec)",
                "ipv6.ignore-auto-routes:                no",
                "ipv6.ignore-auto-dns:                   no",
                "ipv6.never-default:                     no",
                "ipv6.may-fail:                          yes",
                "ipv6.ip6-privacy:                       -1 (unknown)",
                "ipv6.addr-gen-mode:                     stable-privacy",
                "ipv6.dhcp-duid:                         --",
                "ipv6.dhcp-send-hostname:                yes",
                "ipv6.dhcp-hostname:                     --",
                "ipv6.token:                             --",
                "proxy.method:                           none",
                "proxy.browser-only:                     no",
                "proxy.pac-url:                          --",
                "proxy.pac-script:                       --",
                "GENERAL.NAME:                           enp0s3",
                "GENERAL.UUID:                           c54ea011-0e23-43fa-8f06-23429b9ce714",
                "GENERAL.DEVICES:                        enp0s3",
                "GENERAL.STATE:                          activated",
                "GENERAL.DEFAULT:                        yes",
                "GENERAL.DEFAULT6:                       no",
                "GENERAL.SPEC-OBJECT:                    --",
                "GENERAL.VPN:                            no",
                "GENERAL.DBUS-PATH:                      /org/freedesktop/NetworkManager/ActiveConnection/1",
                "GENERAL.CON-PATH:                       /org/freedesktop/NetworkManager/Settings/1",
                "GENERAL.ZONE:                           --",
                "GENERAL.MASTER-PATH:                    --",
                "IP4.ADDRESS[1]:                         192.168.1.14/24",
                "IP4.GATEWAY:                            192.168.1.1",
                "IP4.ROUTE[1]:                           dst = 0.0.0.0/0, nh = 192.168.1.1, mt = 100",
                "IP4.ROUTE[2]:                           dst = 192.168.1.0/24, nh = 0.0.0.0, mt = 100",
                "IP4.DNS[1]:                             192.168.1.1",
                "DHCP4.OPTION[1]:                        broadcast_address = 192.168.1.255",
                "DHCP4.OPTION[2]:                        dhcp_lease_time = 86400",
                "DHCP4.OPTION[3]:                        dhcp_message_type = 5",
                "DHCP4.OPTION[4]:                        dhcp_server_identifier = 192.168.1.1",
                "DHCP4.OPTION[5]:                        domain_name_servers = 192.168.1.1",
                "DHCP4.OPTION[6]:                        expiry = 1558140678",
                "DHCP4.OPTION[7]:                        ip_address = 192.168.1.14",
                "DHCP4.OPTION[8]:                        network_number = 192.168.1.0",
                "DHCP4.OPTION[9]:                        next_server = 0.0.0.0",
                "DHCP4.OPTION[10]:                       requested_broadcast_address = 1",
                "DHCP4.OPTION[11]:                       requested_classless_static_routes = 1",
                "DHCP4.OPTION[12]:                       requested_domain_name = 1",
                "DHCP4.OPTION[13]:                       requested_domain_name_servers = 1",
                "DHCP4.OPTION[14]:                       requested_domain_search = 1",
                "DHCP4.OPTION[15]:                       requested_host_name = 1",
                "DHCP4.OPTION[16]:                       requested_interface_mtu = 1",
                "DHCP4.OPTION[17]:                       requested_ms_classless_static_routes = 1",
                "DHCP4.OPTION[18]:                       requested_nis_domain = 1",
                "DHCP4.OPTION[19]:                       requested_nis_servers = 1",
                "DHCP4.OPTION[20]:                       requested_ntp_servers = 1",
                "DHCP4.OPTION[21]:                       requested_rfc3442_classless_static_routes = 1",
                "DHCP4.OPTION[22]:                       requested_routers = 1",
                "DHCP4.OPTION[23]:                       requested_static_routes = 1",
                "DHCP4.OPTION[24]:                       requested_subnet_mask = 1",
                "DHCP4.OPTION[25]:                       requested_time_offset = 1",
                "DHCP4.OPTION[26]:                       requested_wpad = 1",
                "DHCP4.OPTION[27]:                       routers = 192.168.1.1",
                "DHCP4.OPTION[28]:                       subnet_mask = 255.255.255.0",
                "IP6.ADDRESS[1]:                         fe80::dcd3:6b5f:52a1:abfa/64",
                "IP6.GATEWAY:                            --",
                "IP6.ROUTE[1]:                           dst = fe80::/64, nh = ::, mt = 100",
                "IP6.ROUTE[2]:                           dst = ff00::/8, nh = ::, mt = 256, table=255",
                "",
            ]
        ]
        err = [[""]]
        rc = [0]
        dnets_out = [""]
        dnet_inspect_out = [""]
        expected_result = [
            {
                "c54ea011-0e23-43fa-8f06-23429b9ce714": {
                    "ctype": "802-3-ethernet",
                    "ipv6_addresses": None,
                    "ipv4_method": "auto",
                    "ipv6_method": None,
                    "ipv6_dns": None,
                    "name": "enp0s3",
                    "ipv4_addresses": "192.168.1.14/24",
                    "ipv6_gw": None,
                    "ipv4_dns": "192.168.1.1",
                    "state": "activated",
                    "ipv6_dns_search": None,
                    "802-3-ethernet": {"mac": None, "mtu": "auto", "cloned_mac": None},
                    "ipv4_gw": "192.168.1.1",
                    "ipv4_dns_search": None,
                }
            }
        ]

        # Default docker bridge
        con_name.append("7ffa9c37-4559-4608-80de-ea77a27876cd")
        out.append(
            [
                "connection.id:                          docker0",
                "connection.uuid:                        7ffa9c37-4559-4608-80de-ea77a27876cd",
                "connection.stable-id:                   --",
                "connection.type:                        bridge",
                "connection.interface-name:              docker0",
                "connection.autoconnect:                 no",
                "connection.autoconnect-priority:        0",
                "connection.autoconnect-retries:         -1 (default)",
                "connection.multi-connect:               0 (default)",
                "connection.auth-retries:                -1",
                "connection.timestamp:                   1593384718",
                "connection.read-only:                   no",
                "connection.permissions:                 --",
                "connection.zone:                        --",
                "connection.master:                      --",
                "connection.slave-type:                  --",
                "connection.autoconnect-slaves:          -1 (default)",
                "connection.secondaries:                 --",
                "connection.gateway-ping-timeout:        0",
                "connection.metered:                     unknown",
                "connection.lldp:                        default",
                "connection.mdns:                        -1 (default)",
                "connection.llmnr:                       -1 (default)",
                "connection.wait-device-timeout:         -1",
                "ipv4.method:                            manual",
                "ipv4.dns:                               --",
                "ipv4.dns-search:                        --",
                "ipv4.dns-options:                       --",
                "ipv4.dns-priority:                      100",
                "ipv4.addresses:                         172.17.0.1/16",
                "ipv4.gateway:                           --",
                "ipv4.routes:                            --",
                "ipv4.route-metric:                      -1",
                "ipv4.route-table:                       0 (unspec)",
                "ipv4.routing-rules:                     --",
                "ipv4.ignore-auto-routes:                no",
                "ipv4.ignore-auto-dns:                   no",
                "ipv4.dhcp-client-id:                    --",
                "ipv4.dhcp-iaid:                         --",
                "ipv4.dhcp-timeout:                      0 (default)",
                "ipv4.dhcp-send-hostname:                yes",
                "ipv4.dhcp-hostname:                     --",
                "ipv4.dhcp-fqdn:                         --",
                "ipv4.dhcp-hostname-flags:               0x0 (none)",
                "ipv4.never-default:                     no",
                "ipv4.may-fail:                          yes",
                "ipv4.dad-timeout:                       -1 (default)",
                "ipv6.method:                            ignore",
                "ipv6.dns:                               --",
                "ipv6.dns-search:                        --",
                "ipv6.dns-options:                       --",
                "ipv6.dns-priority:                      100",
                "ipv6.addresses:                         --",
                "ipv6.gateway:                           --",
                "ipv6.routes:                            --",
                "ipv6.route-metric:                      -1",
                "ipv6.route-table:                       0 (unspec)",
                "ipv6.routing-rules:                     --",
                "ipv6.ignore-auto-routes:                no",
                "ipv6.ignore-auto-dns:                   no",
                "ipv6.never-default:                     no",
                "ipv6.may-fail:                          yes",
                "ipv6.ip6-privacy:                       -1 (unknown)",
                "ipv6.addr-gen-mode:                     stable-privacy",
                "ipv6.dhcp-duid:                         --",
                "ipv6.dhcp-iaid:                         --",
                "ipv6.dhcp-send-hostname:                yes",
                "ipv6.dhcp-hostname:                     --",
                "ipv6.dhcp-hostname-flags:               0x0 (none)",
                "ipv6.token:                             --",
                "bridge.mac-address:                     --",
                "bridge.stp:                             no",
                "bridge.priority:                        32768",
                "bridge.forward-delay:                   15",
                "bridge.hello-time:                      2",
                "bridge.max-age:                         20",
                "bridge.ageing-time:                     300",
                "bridge.group-forward-mask:              0",
                "bridge.multicast-snooping:              yes",
                "bridge.vlan-filtering:                  no",
                "bridge.vlan-default-pvid:               1",
                "bridge.vlans:                           --",
                "proxy.method:                           none",
                "proxy.browser-only:                     no",
                "proxy.pac-url:                          --",
                "proxy.pac-script:                       --",
                "GENERAL.NAME:                           docker0",
                "GENERAL.UUID:                           7ffa9c37-4559-4608-80de-ea77a27876cd",
                "GENERAL.DEVICES:                        docker0",
                "GENERAL.IP-IFACE:                       docker0",
                "GENERAL.STATE:                          activated",
                "GENERAL.DEFAULT:                        no",
                "GENERAL.DEFAULT6:                       no",
                "GENERAL.SPEC-OBJECT:                    --",
                "GENERAL.VPN:                            no",
                "GENERAL.DBUS-PATH:                      /org/freedesktop/NetworkManager/ActiveConnection/2",
                "GENERAL.CON-PATH:                       /org/freedesktop/NetworkManager/Settings/2",
                "GENERAL.ZONE:                           --",
                "GENERAL.MASTER-PATH:                    --",
                "IP4.ADDRESS[1]:                         172.17.0.1/16",
                "IP4.GATEWAY:                            --",
                "IP4.ROUTE[1]:                           dst = 172.17.0.0/16, nh = 0.0.0.0, mt = 0",
                "IP6.GATEWAY:                            --",
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        dnets_out.append("")
        dnet_inspect_out.append(
            {
                "Ingress": False,
                "Name": "bridge",
                "Created": "2020-08-11T11:06:06.107666148-04:00",
                "EnableIPv6": False,
                "Labels": {},
                "Driver": "bridge",
                "Attachable": False,
                "ConfigOnly": False,
                "Internal": False,
                "ConfigFrom": {"Network": ""},
                "Options": {
                    "com.docker.network.bridge.name": "docker0",
                    "com.docker.network.bridge.default_bridge": "true",
                    "com.docker.network.bridge.enable_ip_masquerade": "true",
                    "com.docker.network.driver.mt": "1500",
                    "com.docker.network.bridge.host_binding_ipv4": "0.0.0.0",
                    "com.docker.network.bridge.enable_icc": "true",
                },
                "IPAM": {
                    "Config": [{"Subnet": "172.17.0.0/16", "Gateway": "172.17.0.1"}],
                    "Driver": "default",
                    "Options": None,
                },
                "Scope": "local",
                "Id": "fc57dc3d46f9c27bc9b094e58be282b7fca57db3480e0e27e8dd83e0241ad0c8",
                "Containers": {},
            }
        )
        expected_result.append(
            {
                "7ffa9c37-4559-4608-80de-ea77a27876cd": {
                    "bridge": {
                        "aux_address": None,
                        "subnet": "172.17.0.0/16",
                        "internal": False,
                        "host_binding": "0.0.0.0",
                        "docker_name": "docker0",
                        "icc": True,
                        "ip_masquerade": False,
                        "dgateway": "172.17.0.1",
                        "ip_range": None,
                    },
                    "ctype": "bridge",
                    "ipv6_addresses": None,
                    "ipv4_method": "manual",
                    "ipv6_method": None,
                    "ipv6_dns": None,
                    "name": "docker0",
                    "ipv4_addresses": "172.17.0.1/16",
                    "ipv6_gw": None,
                    "ipv4_dns": None,
                    "state": "activated",
                    "ipv6_dns_search": None,
                    "ipv4_gw": None,
                    "ipv4_dns_search": None,
                }
            }
        )

        # User-created rocknet
        con_name.append("c344cf82-783e-420e-9d02-30980e058ae5")
        out.append(
            [
                "connection.id:                          br-6088a34098e0",
                "connection.uuid:                        c344cf82-783e-420e-9d02-30980e058ae5",
                "connection.stable-id:                   --",
                "connection.type:                        bridge",
                "connection.interface-name:              br-6088a34098e0",
                "connection.autoconnect:                 no",
                "connection.autoconnect-priority:        0",
                "connection.autoconnect-retries:         -1 (default)",
                "connection.multi-connect:               0 (default)",
                "connection.auth-retries:                -1",
                "connection.timestamp:                   1593385318",
                "connection.read-only:                   no",
                "connection.permissions:                 --",
                "connection.zone:                        --",
                "connection.master:                      --",
                "connection.slave-type:                  --",
                "connection.autoconnect-slaves:          -1 (default)",
                "connection.secondaries:                 --",
                "connection.gateway-ping-timeout:        0",
                "connection.metered:                     unknown",
                "connection.lldp:                        default",
                "connection.mdns:                        -1 (default)",
                "connection.llmnr:                       -1 (default)",
                "connection.wait-device-timeout:         -1",
                "ipv4.method:                            manual",
                "ipv4.dns:                               --",
                "ipv4.dns-search:                        --",
                "ipv4.dns-options:                       --",
                "ipv4.dns-priority:                      100",
                "ipv4.addresses:                         172.20.0.1/16",
                "ipv4.gateway:                           --",
                "ipv4.routes:                            --",
                "ipv4.route-metric:                      -1",
                "ipv4.route-table:                       0 (unspec)",
                "ipv4.routing-rules:                     --",
                "ipv4.ignore-auto-routes:                no",
                "ipv4.ignore-auto-dns:                   no",
                "ipv4.dhcp-client-id:                    --",
                "ipv4.dhcp-iaid:                         --",
                "ipv4.dhcp-timeout:                      0 (default)",
                "ipv4.dhcp-send-hostname:                yes",
                "ipv4.dhcp-hostname:                     --",
                "ipv4.dhcp-fqdn:                         --",
                "ipv4.dhcp-hostname-flags:               0x0 (none)",
                "ipv4.never-default:                     no",
                "ipv4.may-fail:                          yes",
                "ipv4.dad-timeout:                       -1 (default)",
                "ipv6.method:                            ignore",
                "ipv6.dns:                               --",
                "ipv6.dns-search:                        --",
                "ipv6.dns-options:                       --",
                "ipv6.dns-priority:                      100",
                "ipv6.addresses:                         --",
                "ipv6.gateway:                           --",
                "ipv6.routes:                            --",
                "ipv6.route-metric:                      -1",
                "ipv6.route-table:                       0 (unspec)",
                "ipv6.routing-rules:                     --",
                "ipv6.ignore-auto-routes:                no",
                "ipv6.ignore-auto-dns:                   no",
                "ipv6.never-default:                     no",
                "ipv6.may-fail:                          yes",
                "ipv6.ip6-privacy:                       -1 (unknown)",
                "ipv6.addr-gen-mode:                     stable-privacy",
                "ipv6.dhcp-duid:                         --",
                "ipv6.dhcp-iaid:                         --",
                "ipv6.dhcp-send-hostname:                yes",
                "ipv6.dhcp-hostname:                     --",
                "ipv6.dhcp-hostname-flags:               0x0 (none)",
                "ipv6.token:                             --",
                "bridge.mac-address:                     --",
                "bridge.stp:                             no",
                "bridge.priority:                        32768",
                "bridge.forward-delay:                   15",
                "bridge.hello-time:                      2",
                "bridge.max-age:                         20",
                "bridge.ageing-time:                     300",
                "bridge.group-forward-mask:              0",
                "bridge.multicast-snooping:              yes",
                "bridge.vlan-filtering:                  no",
                "bridge.vlan-default-pvid:               1",
                "bridge.vlans:                           --",
                "proxy.method:                           none",
                "proxy.browser-only:                     no",
                "proxy.pac-url:                          --",
                "proxy.pac-script:                       --",
                "GENERAL.NAME:                           br-6088a34098e0",
                "GENERAL.UUID:                           c344cf82-783e-420e-9d02-30980e058ae5",
                "GENERAL.DEVICES:                        br-6088a34098e0",
                "GENERAL.IP-IFACE:                       br-6088a34098e0",
                "GENERAL.STATE:                          activated",
                "GENERAL.DEFAULT:                        no",
                "GENERAL.DEFAULT6:                       no",
                "GENERAL.SPEC-OBJECT:                    --",
                "GENERAL.VPN:                            no",
                "GENERAL.DBUS-PATH:                      /org/freedesktop/NetworkManager/ActiveConnection/3",
                "GENERAL.CON-PATH:                       /org/freedesktop/NetworkManager/Settings/3",
                "GENERAL.ZONE:                           --",
                "GENERAL.MASTER-PATH:                    --",
                "IP4.ADDRESS[1]:                         172.20.0.1/16",
                "IP4.GATEWAY:                            --",
                "IP4.ROUTE[1]:                           dst = 172.20.0.0/16, nh = 0.0.0.0, mt = 0",
                "IP6.GATEWAY:                            --",
                "",
            ]
        )
        err.append([""])
        rc.append(0)
        dnets_out.append(["rocknet01"])
        dnet_inspect_out.append(
            {
                "Ingress": False,
                "Name": "rocknet01",
                "Created": "2020-08-07T16:43:14.04154885-04:00",
                "EnableIPv6": False,
                "Labels": {},
                "Driver": "bridge",
                "Attachable": False,
                "ConfigOnly": False,
                "Internal": False,
                "ConfigFrom": {"Network": ""},
                "Options": {
                    "com.docker.network.bridge.enable_icc": "true",
                    "com.docker.network.driver.mtu": "1500",
                },
                "IPAM": {
                    "Config": [{"Subnet": "172.20.0.0/16", "Gateway": "172.20.0.1"}],
                    "Driver": "default",
                    "Options": {},
                },
                "Scope": "local",
                "Id": "2c7dfdeef407717c107041f6e1e53c3248cf688b78be1f346e4a1079e9da6570",
                "Containers": {},
            }
        )
        expected_result.append(
            {
                "c344cf82-783e-420e-9d02-30980e058ae5": {
                    "bridge": {
                        "aux_address": None,
                        "subnet": "172.20.0.0/16",
                        "internal": False,
                        "host_binding": None,
                        "docker_name": "rocknet01",
                        "icc": True,
                        "ip_masquerade": False,
                        "dgateway": "172.20.0.1",
                        "ip_range": None,
                    },
                    "ctype": "bridge",
                    "ipv6_addresses": None,
                    "ipv4_method": "manual",
                    "ipv6_method": None,
                    "ipv6_dns": None,
                    "name": "br-6088a34098e0",
                    "ipv4_addresses": "172.20.0.1/16",
                    "ipv6_gw": None,
                    "ipv4_dns": None,
                    "state": "activated",
                    "ipv6_dns_search": None,
                    "ipv4_gw": None,
                    "ipv4_dns_search": None,
                }
            }
        )

        # @todo: Add more types of connections, such as docker0, wifi, eth, veth, etc...

        # Cycle through each of the above parameter / run_command data sets.
        for con, o, e, r, dnet_o, dnet_inspect_o, expected in zip(
            con_name, out, err, rc, dnets_out, dnet_inspect_out, expected_result
        ):
            con_list = [con]
            self.mock_run_command.return_value = (o, e, r)
            self.mock_dnets.return_value = dnet_o
            self.mock_dnet_inspect.return_value = dnet_inspect_o
            returned = get_con_config(con_list)
            self.assertEqual(
                returned,
                expected,
                msg="Un-expected get_con_config() result:\n "
                "returned = {}.\n "
                "expected = {}.\n ".format(returned, expected),
            )

    def test_get_con_config_con_not_found(self):
        """
        Test get_con_config() if connection is not found / vanished.
        It should return an empty dict.
        """
        con_name = ["bogus-uuid"]
        expected_result = {}
        self.mock_run_command.side_effect = CommandException(
            err=["Error: bogus-uuid - no such connection profile.", ""],
            cmd=["/usr/bin/nmcli", "c", "show", "bogus-uuid"],
            out=[""],
            rc=10,
        )
        returned = get_dev_config(con_name)
        self.assertEqual(
            returned,
            expected_result,
            msg="Un-expected get_con_config() result:\n "
            "returned = ({}).\n "
            "expected = ({}).\n "
            "for con_name: {}".format(returned, expected_result, con_name),
        )

    def test_get_con_config_exception(self):
        """
        Test get_con_config() if nmcli returns error code != 10.
        It should raise an exception (CommandException).
        """
        con_name = ["bogus-uuid"]
        self.mock_run_command.side_effect = CommandException(
            err=["Error: bogus-uuid - no such connection profile.", ""],
            cmd=["/usr/bin/nmcli", "c", "show", "bogus-uuid"],
            out=[""],
            rc=1,
        )
        with self.assertRaises(CommandException):
            get_con_config(con_name)

    def test_enable_ip_forwarding(self):
        """enable_ip_forwarding() calls write with the correct contents
        Enable_ip_forwarding should write to /etc/sysctl.d/99-tailscale.conf
        with the following lines
          - net.ipv4.ip_forward = 1
          - net.ipv6.conf.all.forwarding = 1
        """
        priority = 99
        name = "tailscale"
        file_path = f"{SYSCTL_CONFD_PATH}{priority}-{name}.conf"
        m = mock_open()
        with patch("system.network.open", m):
            enable_ip_forwarding(name=name, priority=priority)

            # Test that the file was opened in 'w' mode
            m.assert_called_once_with(file_path, "w")

            # Test that 'write' was called with the correct content
            calls = [
                call("net.ipv4.ip_forward = 1\n"),
                call("net.ipv6.conf.all.forwarding = 1\n"),
            ]
            m().write.assert_has_calls(calls, any_order=False)

        # Test that run_command was called as expected
        self.mock_run_command.assert_called_once_with(
            [SYSCTL, "-p", file_path], log=True
        )

    def test_disable_ip_forwarding(self):
        """test proper call of os.remove() and final sysctl command"""
        # mock os.scandir()
        self.patch_os_scandir = patch("system.network.os.scandir")
        self.mock_os_scandir = self.patch_os_scandir.start()
        self.mock_os_scandir.return_value.__enter__.return_value = [
            MockDirEntry(
                name="99-tailscale.conf",
                path="/etc/sysctl.d/99-tailscale.conf",
                is_file=True,
            ),
            MockDirEntry(
                name="70-yast.conf", path="/etc/sysctl.d/70-yast.conf", is_file=True
            ),
        ]
        # mock os.remove()
        self.patch_os_remove = patch("system.network.os.remove")
        self.mock_os_remove = self.patch_os_remove.start()
        # mock run_command()
        self.mock_run_command.return_value = [""], [""], 0
        disable_ip_forwarding(name="tailscale")
        # test os.remove() was called
        self.mock_os_remove.assert_called_once_with("/etc/sysctl.d/99-tailscale.conf")
        cmd = [
            SYSCTL,
            "-w",
            "net.ipv4.ip_forward=0",
            "-w",
            "net.ipv6.conf.all.forwarding=0",
        ]
        # test run_command() was called
        self.mock_run_command.assert_called_once_with(cmd, log=True)
