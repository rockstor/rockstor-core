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


class NetStat(models.Model):

    device = models.CharField(max_length=100)
    kb_rx = models.FloatField()
    packets_rx = models.FloatField()
    errs_rx = models.FloatField()
    drop_rx = models.IntegerField()
    fifo_rx = models.IntegerField()
    frame = models.IntegerField()
    compressed_rx = models.IntegerField()
    multicast_rx = models.IntegerField()

    kb_tx = models.FloatField()
    packets_tx = models.IntegerField()
    errs_tx = models.IntegerField()
    drop_tx = models.IntegerField()
    fifo_tx = models.IntegerField()
    colls = models.IntegerField()
    carrier = models.IntegerField()
    compressed_tx = models.IntegerField()
    ts = models.DateTimeField()


    class Meta:
        app_label = 'smart_manager'


