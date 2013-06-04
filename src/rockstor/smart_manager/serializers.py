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

from rest_framework import serializers
from smart_manager.models import (CPUMetric, LoadAvg, MemInfo, ServiceStatus,
                                  SProbe, NFSDCallDistribution,
                                  NFSDClientDistribution)



class CPUMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPUMetric

class LoadAvgSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadAvg

class MemInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemInfo

class ServiceStatusSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='service.name')

    class Meta:
        model = ServiceStatus

class SProbeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SProbe

class NFSDCallDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDCallDistribution

class NFSDClientDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDClientDistribution
