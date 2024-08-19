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

from rest_framework import serializers, pagination
from .models import (
    CPUMetric,
    LoadAvg,
    MemInfo,
    ServiceStatus,
    SProbe,
    NFSDCallDistribution,
    NFSDClientDistribution,
    NFSDShareDistribution,
    DiskStat,
    NetStat,
    NFSDShareClientDistribution,
    NFSDUidGidDistribution,
    TaskDefinition,
    Task,
    Replica,
    ReplicaTrail,
    ReplicaShare,
    ReceiveTrail,
    Service,
)
from smart_manager.taplib.probe_config import TapConfig


class CPUMetricSerializer(serializers.ModelSerializer):
    class Meta:
        model = CPUMetric
        fields = "__all__"


class LoadAvgSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoadAvg
        fields = ("uptime",)


class MemInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MemInfo
        fields = "__all__"


class DiskStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = DiskStat
        fields = "__all__"


class NetStatSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetStat
        fields = "__all__"


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = "__all__"


class ServiceStatusSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    display_name = serializers.CharField()
    config = serializers.CharField()

    class Meta:
        model = ServiceStatus
        fields = "__all__"


class SProbeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SProbe
        fields = "__all__"


# TODO: Do we need this class anymore? Only used in advanced_sprobe
class PaginatedSProbe(pagination.PageNumberPagination):
    class Meta:
        object_serializer_class = SProbeSerializer


class NFSDCallDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDCallDistribution
        fields = "__all__"


class NFSDClientDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDClientDistribution
        fields = "__all__"


class NFSDShareDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDShareDistribution
        fields = "__all__"


class NFSDShareClientDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDShareClientDistribution
        fields = "__all__"


class NFSDUidGidDistributionSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFSDUidGidDistribution
        fields = "__all__"


class SProbeConfigSerializer(serializers.Serializer):
    uuid = serializers.CharField(max_length=100)
    sdetail = serializers.CharField(max_length=4096)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.uuid = attrs.get("uuid", instance.uuid)
            instance.sdetail = attrs.get("sdetail", instance.sdetail)
            return instance
        return TapConfig(**attrs)


class TaskDefinitionSerializer(serializers.ModelSerializer):
    share_name = serializers.CharField()
    pool_name = serializers.CharField()

    class Meta:
        model = TaskDefinition
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = Task
        fields = "__all__"


class TaskType(object):
    def __init__(self, name, detail):
        self.name = name
        self.detail = detail


class TaskTypeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    detail = serializers.CharField(max_length=255)

    def restore_object(self, attrs, instance=None):
        if instance is not None:
            instance.name = attrs.get("name", instance.name)
            instance.detail = attrs.get("detail", instance.detail)
            return instance
        return TaskType(**attrs)


class ReplicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Replica
        fields = "__all__"


class ReplicaTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplicaTrail
        fields = "__all__"


class ReplicaShareSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReplicaShare
        fields = "__all__"


class ReceiveTrailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReceiveTrail
        fields = "__all__"
