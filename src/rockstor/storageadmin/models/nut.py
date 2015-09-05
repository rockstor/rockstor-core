"""
Copyright (c) 2012-2015 RockStor, Inc. <http://rockstor.com>
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

# __author__ = 'norman'


from django.db import models


class Nut(models.Model):
    # for /etc/ups/nut.conf ie mode
    # None, standalone, netserver, netclient
    nut_mode = models.CharField(max_length=1024)
    # for /etc/ups/ups.conf ie driver related
    ups_name = models.CharField(max_length=1024)
    ups_driver = models.CharField(max_length=1024, unique=True)
    ups_port = models.CharField(max_length=1024)
    ups_description = models.CharField(max_length=1024)
    ups_aux_options = models.CharField(max_length=1024)
    # for /etc/ups/upsd.users ie nut user config
    nut_user = models.CharField(max_length=1024)
    nut_user_pass = models.CharField(max_length=1024)
    nut_user_caps = models.CharField(max_length=1024)  # admin or upsmod
    # for /etc/ups/upsmon.conf
    nut_server = models.CharField(max_length=1024)  # nut_server name or ip

    class Meta:
        app_label = 'storageadmin'
