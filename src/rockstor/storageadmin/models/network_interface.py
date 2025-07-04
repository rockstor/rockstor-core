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
along with this program. If not, see <http://www.gnu.org/licenses/>.
"""

import json
from django.db import models

# This is the key abstraction for network configuration that is user
# configurable in Rockstor.  user can add, delete or modify connections which
# results in CRUD ops on this model and also on other models linked to this
# one, such as NetworkInterface, EthernetConnection etc..
class NetworkConnection(models.Model):
    # Wired connection 1, Team-team0 etc..
    name = models.CharField(max_length=256, null=True)
    # uuid generated by NM
    uuid = models.CharField(max_length=256, unique=True)
    # active (== GENERAL.STATE: activated in nmcli), could also be activating
    # or blank(assumed inactive) -- subtle distinction compared to state of
    # NetworkInterface
    state = models.CharField(max_length=64, null=True)

    # whether or not to automatically connect when underlying resources are
    # available.
    autoconnect = models.BooleanField(default=True)

    # manual or dhcp
    ipv4_method = models.CharField(max_length=64, null=True)
    # comma separated strings of ip/nm_bits. typically just one ip/nm. eg:
    # 192.168.1.5/24
    ipv4_addresses = models.CharField(max_length=1024, null=True)
    # there can only be one ipv4 gateway. eg: 192.168.1.1
    ipv4_gw = models.CharField(max_length=64, null=True)
    # comma separated strings of one or more dns addresses. eg: "8.8.8.8
    # 8.8.4.4"
    ipv4_dns = models.CharField(max_length=256, null=True)
    # comma separated strings of one or more dns search domains. eg:
    # rockstor.com
    ipv4_dns_search = models.CharField(max_length=256, null=True)

    # not clear yet on ipv6 stuff.
    ipv6_method = models.CharField(max_length=1024, null=True)
    ipv6_addresses = models.CharField(max_length=1024, null=True)
    ipv6_gw = models.CharField(max_length=64, null=True)
    ipv6_dns = models.CharField(max_length=256, null=True)
    ipv6_dns_search = models.CharField(max_length=256, null=True)

    # slave connections have a master. eg: team
    master = models.ForeignKey("NetworkConnection", null=True, on_delete=models.CASCADE)

    @property
    def ipaddr(self):
        if self.ipv4_addresses is None:
            return None
        return self.ipv4_addresses.split(",")[0].split("/")[0]

    @property
    def mtu(self):
        if self.ethernetconnection_set.count() > 0:
            eco = self.ethernetconnection_set.first()
            try:
                return int(eco.mtu)
            except ValueError:
                pass
        return 1500

    @property
    def ctype(self):
        if self.ethernetconnection_set.count() > 0:
            return "ethernet"
        if self.teamconnection_set.count() > 0:
            return "team"
        if self.bondconnection_set.count() > 0:
            return "bond"
        if self.bridgeconnection_set.count() > 0:
            return "bridge"
        return None

    @property
    def team_profile(self):
        profile = None
        try:
            tco = self.teamconnection_set.first()
            config_d = json.loads(tco.config)
            profile = config_d["runner"]["name"]
        except:
            pass
        finally:
            return profile

    @property
    def bond_profile(self):
        profile = None
        try:
            bco = self.bondconnection_set.first()
            config_d = json.loads(bco.config)
            profile = config_d["mode"]
        except:
            pass
        finally:
            return profile

    @property
    def docker_name(self):
        dname = None
        if self.bridgeconnection_set.count() > 0:
            brco = self.bridgeconnection_set.first()
            dname = brco.docker_name
        return dname

    @property
    def user_dnet(self):
        """
        Returns True if the docker network is a rocknet (defined by the user).
        Used by rockons.js to list available rocknets available for connection.
        :return: Boolean
        """
        user_dnet = None
        if self.bridgeconnection_set.count() > 0:
            brco = self.bridgeconnection_set.first()
            user_dnet = brco.usercon
            if user_dnet:
                user_dnet = True
        return user_dnet

    @property
    def docker_options(self):
        """
        Gather all connection's settings in a dict to be displayed in the UI connection form
        needed to edit an existing docker network connection.
        :return:
        """
        docker_options = {}
        if self.bridgeconnection_set.count() > 0:
            brco = self.bridgeconnection_set.first()
            connected_containers = []
            if brco.dcontainernetwork_set.filter(connection=brco.id).count() > 0:
                for i in range(
                    brco.dcontainernetwork_set.filter(connection=brco.id).count()
                ):
                    cname = (
                        brco.dcontainernetwork_set.filter(connection=brco.id)
                        .order_by("id")[i]
                        .container_name
                    )
                    rname = (
                        brco.dcontainernetwork_set.filter(connection=brco.id)
                        .order_by("id")[i]
                        .container.rockon.name
                    )
                    connected_containers.append("{} ({})".format(cname, rname))
            docker_options["aux_address"] = brco.aux_address
            docker_options["dgateway"] = brco.dgateway
            docker_options["host_binding"] = brco.host_binding
            docker_options["icc"] = brco.icc
            docker_options["internal"] = brco.internal
            docker_options["ip_masquerade"] = brco.ip_masquerade
            docker_options["ip_range"] = brco.ip_range
            docker_options["subnet"] = brco.subnet
            docker_options["containers"] = connected_containers
        return docker_options

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']



# network interfaces/devices are auto detected from the system via "nmcli d
# show" They are not "directly" user configurable. but their attributes are
# refreshed in two ways 1. when user configures a NetworkConnection and inturn
# NetworkInterface is changed, eg: state.  2. When changes at the system level
# are picked up.
class NetworkDevice(models.Model):
    # enp0s3, lo etc..
    name = models.CharField(max_length=256, unique=True)
    # ethernet, infiniband etc..
    dtype = models.CharField(max_length=100, null=True)
    mac = models.CharField(max_length=100, null=True)
    connection = models.ForeignKey(
        NetworkConnection, null=True, on_delete=models.SET_NULL
    )
    # active (== GENERAL.STATE: activated in nmcli), could also be activating
    # or blank(assumed inactive)
    state = models.CharField(max_length=64, null=True)
    mtu = models.CharField(max_length=64, null=True)

    @property
    def cname(self):
        if self.connection is None:
            return None
        return self.connection.name

    @property
    def dev_name(self):
        """
        Return the user-friendly docker_name as device name for bridge connections
        to be displayed in the network widget on the dashboard.
        :return:
        """
        if (self.dtype == "bridge") and (self.connection is not None):
            return self.connection.docker_name
        return self.name

    class Meta:
        app_label = "storageadmin"
        ordering = ['-id']


# This is the most common of connection types that uses NetworkInterface of
# dtype=ethernet
class EthernetConnection(models.Model):
    connection = models.ForeignKey(NetworkConnection, null=True, on_delete=models.CASCADE)
    mac = models.CharField(max_length=64, null=True)
    cloned_mac = models.CharField(max_length=64, null=True)
    mtu = models.CharField(max_length=64, null=True)

    class Meta:
        app_label = "storageadmin"


class TeamConnection(models.Model):
    connection = models.ForeignKey(NetworkConnection, null=True, on_delete=models.CASCADE)
    # eg: Team1
    name = models.CharField(max_length=64, null=True)
    # json config.
    config = models.CharField(max_length=2048, null=True)

    class Meta:
        app_label = "storageadmin"


class BondConnection(models.Model):
    connection = models.ForeignKey(NetworkConnection, null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=64, null=True)
    # at the NM level it's not json like in team config, but we could convert
    # it for consistency.
    config = models.CharField(max_length=2048, null=True)

    class Meta:
        app_label = "storageadmin"


class BridgeConnection(models.Model):
    connection = models.ForeignKey(NetworkConnection, null=True, on_delete=models.CASCADE)
    docker_name = models.CharField(max_length=64, null=True)
    usercon = models.BooleanField(default=False)
    aux_address = models.CharField(max_length=2048, null=True)
    dgateway = models.CharField(max_length=64, null=True)
    host_binding = models.CharField(max_length=64, null=True)
    icc = models.BooleanField(default=False)
    internal = models.BooleanField(default=False)
    ip_masquerade = models.BooleanField(default=False)
    ip_range = models.CharField(max_length=64, null=True)
    subnet = models.CharField(max_length=64, null=True)

    class Meta:
        app_label = "storageadmin"
