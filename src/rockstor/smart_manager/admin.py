"""
Copyright (joint work) 2025 The Rockstor Project <https://rockstor.com>

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

from django.contrib import admin

from smart_manager.models import (
    CPUMetric,
    DiskStat,
    LoadAvg,
    MemInfo,
    NetStat,
    NFSDCallDistribution,
    NFSDClientDistribution,
    NFSDShareDistribution,
    NFSDUidGidDistribution,
    VmStat,
    SProbe,
    PoolUsage,
    Service,
    ServiceStatus,
    ShareUsage,
    Replica,
    ReplicaTrail,
    ReplicaShare,
    ReceiveTrail,
)


@admin.register(CPUMetric)
class CPUMetricAdmin(admin.ModelAdmin):
    list_display = ["name", "umode", "umode_nice", "smode", "idle", "ts"]
    list_per_page = 15


@admin.register(DiskStat)
class DiskStatAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "reads_completed",
        "reads_merged",
        "sectors_read",
        "ms_reading",
        "writes_completed",
        "writes_merged",
        "sectors_written",
        "ms_writing",
        "ios_progress",
        "ms_ios",
        "weighted_ios",
        "ts",
    ]
    list_per_page = 15


@admin.register(LoadAvg)
class LoadAvgAdmin(admin.ModelAdmin):
    list_display = [
        "load_1",
        "load_5",
        "load_15",
        "active_threads",
        "total_threads",
        "latest_pid",
        "idle_seconds",
        "ts",
        "uptime",
    ]
    list_per_page = 15


@admin.register(MemInfo)
class MemInfoAdmin(admin.ModelAdmin):
    list_display = [
        "total",
        "free",
        "buffers",
        "cached",
        "swap_total",
        "swap_free",
        "active",
        "inactive",
        "dirty",
        "ts",
    ]
    list_per_page = 15


@admin.register(NetStat)
class NetStatAdmin(admin.ModelAdmin):
    list_display = [
        "device",
        "kb_rx",
        "packets_rx",
        "errs_rx",
        "drop_rx",
        "fifo_rx",
        "frame",
        "compressed_rx",
        "multicast_rx",
        "kb_tx",
        "packets_tx",
        "errs_tx",
        "drop_tx",
        "fifo_tx",
        "colls",
        "carrier",
        "compressed_tx",
        "ts",
    ]
    list_per_page = 15


@admin.register(VmStat)
class VmStatAdmin(admin.ModelAdmin):
    list_display = ["free_pages", "ts"]
    list_per_page = 15


# NFSD monitoring start


class NFSDCallDistributionAdminInline(admin.TabularInline):
    model = NFSDCallDistribution


@admin.register(NFSDCallDistribution)
class NFSDCallDistributionAdmin(admin.ModelAdmin):
    list_display = [
        "rid",
        "ts",
        "num_lookup",
        "num_read",
        "num_write",
        "num_create",
        "num_commit",
        "num_remove",
        "sum_read",
        "sum_write",
    ]
    list_per_page = 15


class NFSDShareDistributionAdminInline(admin.TabularInline):
    model = NFSDShareDistribution


@admin.register(NFSDShareDistribution)
class NFSDShareDistributionAdmin(admin.ModelAdmin):
    # Same fields as NFSDCallDistributionAdmin + "share"
    list_display = [
        "rid",
        "ts",
        "share",
        "num_lookup",
        "num_read",
        "num_write",
        "num_create",
        "num_commit",
        "num_remove",
        "sum_read",
        "sum_write",
    ]
    list_per_page = 15


class NFSDUidGidDistributionAdminInline(admin.TabularInline):
    model = NFSDUidGidDistribution


@admin.register(NFSDUidGidDistribution)
class NFSDUidGidDistributionAdmin(admin.ModelAdmin):
    # Same fields as NFSDCallDistributionAdmin + "share" + "client" + "uid" + "gid"
    list_display = [
        "rid",
        "ts",
        "share",
        "client",
        "uid",
        "gid",
        "num_lookup",
        "num_read",
        "num_write",
        "num_create",
        "num_commit",
        "num_remove",
        "sum_read",
        "sum_write",
    ]
    list_per_page = 15


class NFSDClientDistributionAdminInline(admin.TabularInline):
    model = NFSDClientDistribution


@admin.register(NFSDClientDistribution)
class NFSDClientDistributionAdmin(admin.ModelAdmin):
    list_display = [
        "rid",
        "ts",
        "ip",
        "num_lookup",
        "num_read",
        "num_write",
        "num_create",
        "num_commit",
        "num_remove",
    ]
    list_per_page = 15


@admin.register(SProbe)
class SProbeAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "display_name",
        "smart",
        "state",
        "start",
        "end",
    ]
    list_per_page = 15
    inlines = [
        NFSDCallDistributionAdminInline,
        NFSDShareDistributionAdminInline,
        NFSDUidGidDistributionAdminInline,
        NFSDClientDistributionAdminInline,
    ]


# NFSD monitoring end


@admin.register(PoolUsage)
class PoolUsageAdmin(admin.ModelAdmin):
    list_display = [
        "pool",
        "ts",
        "free",
        "reclaimable",
        "count",
    ]
    list_per_page = 15


@admin.register(ShareUsage)
class ShareUsageAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "r_usage",
        "e_usage",
        "ts",
        "count",
    ]
    list_per_page = 15


class ServiceStatusAdminInline(admin.TabularInline):
    model = ServiceStatus


@admin.register(ServiceStatus)
class ServiceStatusAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "display_name",
        "service",
        "status",
        "config",
        "count",
        "ts",
    ]
    list_per_page = 17


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "display_name",
        "config",
    ]
    list_per_page = 17
    inlines = [ServiceStatusAdminInline]


# Share Replication start


class ReplicaTrailAdminInline(admin.TabularInline):
    model = ReplicaTrail


@admin.register(ReplicaTrail)
class ReplicaTrailAdmin(admin.ModelAdmin):
    """
    Counterpart to ReceiveTrailAdmin
    """

    list_display = [
        "replica",
        "snap_name",
        "kb_sent",
        "snapshot_created",
        "snapshot_failed",
        "send_pending",
        "send_succeeded",
        "send_failed",
        "end_ts",
        "status",
        "error",
    ]
    list_per_page = 15


@admin.register(Replica)
class ReplicaAdmin(admin.ModelAdmin):
    list_display = [
        "task_name",
        "share",
        "pool",
        "appliance",
        "dpool",
        "dshare",
        "enabled",
        "data_port",
        "meta_port",
        "ts",
        "crontab",
        "replication_ip",
    ]
    list_per_page = 15
    inlines = [ReplicaTrailAdminInline]


class ReceiveTrailAdminInline(admin.TabularInline):
    model = ReceiveTrail


@admin.register(ReceiveTrail)
class ReceiveTrailAdmin(admin.ModelAdmin):
    """
    Counterpart to ReplicaTrailAdmin
    """

    list_display = [
        "rshare",
        "snap_name",
        "kb_received",
        "receive_pending",
        "receive_succeeded",
        "receive_failed",
        "end_ts",
        "status",
        "error",
    ]
    list_per_page = 15


@admin.register(ReplicaShare)
class ReplicaShareAdmin(admin.ModelAdmin):
    list_display = [
        "share",
        "pool",
        "appliance",
        "src_share",
        "data_port",
        "meta_port",
        "ts",
    ]
    list_per_page = 15
    inlines = [ReceiveTrailAdminInline]


# Share Replication end



