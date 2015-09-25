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

from django.db import models


class NetworkInterface(models.Model):
    #connection name. eg: eno1, enp4s0. same as device name
    name = models.CharField(max_length=100, null=True)
    #device name, if any
    dname = models.CharField(max_length=100, null=True)
    #device type, eg: ethernet
    dtype = models.CharField(max_length=64, null=True)
    #device speed capabilities. 1000 Mb/s etc..
    dspeed = models.CharField(max_length=64, null=True)
    #hw mac address, if any
    mac = models.CharField(max_length=100, null=True)
    #auto for dhcp and manual for static
    method = models.CharField(max_length=64, null=True)
    #automatically activate, on boot etc..
    autoconnect = models.CharField(max_length=8, null=True)
    #netmask in ip address format
    netmask = models.CharField(max_length=64, null=True)
    #IP address
    ipaddr = models.CharField(max_length=64, null=True)
    #not really implemented currently, but interfaces can be dedicated for
    #IO or manaagement.
    itype = models.CharField(max_length=100, default='io')
    #gateway address in IP address format
    gateway = models.CharField(max_length=64, null=True)
    #comma separated ip addresses
    dns_servers = models.CharField(max_length=1024, null=True)
    #connection type, ethernet or team
    ctype = models.CharField(max_length=64, null=True)
    #state of the connection. activated etc..
    state = models.CharField(max_length=64, null=True)


    class Meta:
        app_label = 'storageadmin'
