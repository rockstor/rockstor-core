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


class CPUMetric(models.Model):

    name = models.CharField(max_length=10)
    umode = models.IntegerField()
    umode_nice = models.IntegerField()
    smode = models.IntegerField()
    idle = models.IntegerField()
    ts = models.DateTimeField(auto_now=True)

class DiskStat(models.Model):

    name = models.CharField(max_length=3)
    reads_completed = models.IntegerField()
    reads_merged = models.IntegerField()
    sectors_read = models.IntegerField()
    ms_reading = models.IntegerField()
    writes_completed = models.IntegerField()
    writes_merged = models.IntegerField()
    sectors_written = models.IntegerField()
    ms_writing = models.IntegerField()
    ios_progress = models.IntegerField()
    ms_ios = models.IntegerField()
    weighted_ios = models.IntegerField()
    ts = models.DateTimeField(auto_now=True)

class LoadAvg(models.Model):

    load_1 = models.FloatField()
    load_5 = models.FloatField()
    load_15 = models.FloatField()
    active_threads = models.IntegerField()
    total_threads = models.IntegerField()
    latest_pid = models.IntegerField()
    ts = models.DateTimeField(auto_now=True)

class MemInfo(models.Model):

    total = models.IntegerField()
    free = models.IntegerField()
    ts = models.DateTimeField(auto_now=True)

class VmStat(models.Model):

    free_pages = models.IntegerField()
    ts = models.DateTimeField(auto_now=True)

class Service(models.Model):

    name = models.CharField(max_length=24, unique=True)
    registered = models.BooleanField(default=False)

class ServiceStatus(models.Model):

    service = models.ForeignKey(Service)
    status = models.BooleanField(default=False)
    ts = models.DateTimeField(auto_now=True)

class STap(models.Model):

    """
    tap module for hello world
    """
    start = models.DateTimeField(auto_now=True)
    end = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=16)
    name = models.CharField(max_length=32)

class HelloTapTS(models.Model):

    message = models.CharField(max_length=128)
    ts = models.DateTimeField(auto_now=True)

class IOStatsTap(models.Model):

    proc_name = models.CharField(max_length=128)
    num_open = models.IntegerField()
    num_read = models.IntegerField()
    sum_read = models.IntegerField()
    avg_read = models.IntegerField()
    num_write = models.IntegerField()
    sum_write = models.IntegerField()
    avg_write = models.IntegerField()
