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
from storageadmin.models import NetworkInterface

class Appliance(models.Model):
    """uuid is hostid-uid"""
    uuid = models.CharField(max_length=64, unique=True)
    ip = models.CharField(max_length=4096, unique=True)
    current_appliance = models.BooleanField(default=False)
    hostname = models.CharField(max_length=128, default='Rockstor')
    mgmt_port = models.IntegerField(default=443)
    client_id = models.CharField(max_length=100, null=True)
    client_secret = models.CharField(max_length=255, null=True)

    @property
    def ipaddr(self, *args, **kwargs):
        if (not self.current_appliance):
            return self.ip
        try:
            no = NetworkInterface.objects.get(itype='management')
            return no.ipaddr
        except NetworkInterface.DoesNotExist:
            try:
                return NetworkInterface.objects.all()[0].ipaddr
            except Exception, e:
                msg = ('Failed to grab the management IP of the appliance '
                       'due to an error: %s' % e.__str__())
                raise Exception(e)

    class Meta:
        app_label = 'storageadmin'
