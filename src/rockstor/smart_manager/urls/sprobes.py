"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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

#from django.conf.urls import patterns, urls
from django.urls import include, re_path
from smart_manager.views import (
    MemInfoView,
    NetStatView,
    DiskStatView,
    NFSDistribView,
    NFSDClientDistribView,
    NFSDShareDistribView,
    NFSDShareClientDistribView,
    CPUMetricView,
    NFSDUidGidDistributionView,
    LoadAvgView,
    SProbeMetadataView,
    SProbeMetadataDetailView,
)


urlpatterns = [
    # Smart probes
    re_path(r"^$", SProbeView.as_view(), name="probe-view"),
    re_path(r"^metadata$", SProbeMetadataView.as_view(), name="probe-view"),
    re_path(
        r"^metadata/(?P<pid>[0-9]+)$",
        SProbeMetadataDetailView.as_view(),
        name="probe-view",
    ),
    # Generic smart probes
    re_path(r"^diskstat/$", DiskStatView.as_view(), name="diskstat-view"),
    re_path(r"^meminfo/$", MemInfoView.as_view(), name="meminfo-view"),
    re_path(r"^netstat/$", NetStatView.as_view(), name="netstat-view"),
    re_path(r"^cpumetric/$", CPUMetricView.as_view(), name="cpumetric-view"),
    re_path(r"^loadavg$", LoadAvgView.as_view(), name="loadavg-view"),
    # Advanced smart probes
    re_path(r"^nfs-1$", NFSDistribView.as_view(), name="nfsdistrib-view"),
    re_path(r"^nfs-1/(?P<pid>[0-9]+)$", NFSDistribView.as_view(), name="nfsdistrib-view"),
    re_path(
        r"^nfs-1/(?P<pid>[0-9]+)/(?P<command>[a-z]+)$",
        NFSDistribView.as_view(),
        name="nfsdistrib-view",
    ),
    re_path(r"^nfs-2$", NFSDClientDistribView.as_view(), name="nfsclientdistrib-view"),
    re_path(
        r"^nfs-2/(?P<pid>[0-9]+)$",
        NFSDClientDistribView.as_view(),
        name="nfsclientdistrib-view",
    ),
    re_path(
        r"^nfs-2/(?P<pid>[0-9]+)/(?P<command>[a-z]+)$",
        NFSDClientDistribView.as_view(),
        name="nfsclientdistrib-view",
    ),
    re_path(r"^nfs-3$", NFSDShareDistribView.as_view(), name="nfssharedistrib-view"),
    re_path(
        r"^nfs-3/(?P<pid>[0-9]+)$",
        NFSDShareDistribView.as_view(),
        name="nfssharedistrib-view",
    ),
    re_path(
        r"^nfs-3/(?P<pid>[0-9]+)/(?P<command>[a-z]+)$",
        NFSDShareDistribView.as_view(),
        name="nfssharedistrib-view",
    ),
    re_path(
        r"^nfs-4$",
        NFSDShareClientDistribView.as_view(),
        name="nfsshareclientdistrib-view",
    ),
    re_path(
        r"^nfs-4/(?P<pid>[0-9]+)$",
        NFSDShareClientDistribView.as_view(),
        name="nfsshareclientdistrib-view",
    ),
    re_path(
        r"^nfs-4/(?P<pid>[0-9]+)/(?P<command>[a-z]+)$",
        NFSDShareClientDistribView.as_view(),
        name="nfsshareclientdistrib-view",
    ),
    re_path(r"^nfs-5$", NFSDUidGidDistributionView.as_view(), name="nfsuidgid-view"),
    re_path(
        r"^nfs-5/(?P<pid>[0-9]+)$",
        NFSDUidGidDistributionView.as_view(),
        name="nfsuidgid-view",
    ),
    re_path(
        r"^nfs-5/(?P<pid>[0-9]+)/(?P<command>[a-z]+)$",
        NFSDUidGidDistributionView.as_view(),
        name="nfsuidgid-view",
    ),
]
