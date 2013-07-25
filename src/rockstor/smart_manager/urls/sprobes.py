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

from django.conf.urls.defaults import patterns, url
from smart_manager.views import (SmartManagerView, ServiceView, SProbeView,
                                 MemInfoView, NetStatView,
                                 DiskStatView, NFSDistribView,
                                 NFSDClientDistribView, NFSDShareDistribView,
                                 NFSDShareClientDistribView)


urlpatterns = patterns('',

    # Smart probes
    url(r'^$', SProbeView.as_view(), name='probe-view'),

    # Generic smart probes
    url(r'^diskstat/$', DiskStatView.as_view(),
        name='diskstat-view'),
    url(r'^meminfo/$', MemInfoView.as_view(),
        name='meminfo-view'),
    url(r'^netstat/$', NetStatView.as_view(),
        name='netstat-view'),

    # Advanced smart probes
    url(r'^nfs-distrib/$', NFSDistribView.as_view(), name='nfsdistrib-view'),
    url(r'^nfs-distrib/(?P<pid>[0-9]+)/$', NFSDistribView.as_view(),
        name='nfsdistrib-view'),
    url(r'^nfs-distrib/(?P<pid>[0-9]+)/(?P<command>[a-z]+)/$',
        NFSDistribView.as_view(), name='nfsdistrib-view'),

    url(r'^nfs-client-distrib/$', NFSDClientDistribView.as_view(),
        name='nfsclientdistrib-view'),
    url(r'^nfs-client-distrib/(?P<pid>[0-9]+)/$',
        NFSDClientDistribView.as_view(), name='nfsclientdistrib-view'),
    url(r'^nfs-client-distrib/(?P<pid>[0-9]+)/(?P<command>[a-z]+)/$',
        NFSDClientDistribView.as_view(), name='nfsclientdistrib-view'),

    url(r'^nfs-share-distrib/$', NFSDShareDistribView.as_view(),
        name='nfssharedistrib-view'),
    url(r'^nfs-share-distrib/(?P<pid>[0-9]+)/$',
        NFSDShareDistribView.as_view(), name='nfssharedistrib-view'),
    url(r'^nfs-share-distrib/(?P<pid>[0-9]+)/(?P<command>[a-z]+)/$',
        NFSDShareDistribView.as_view(), name='nfssharedistrib-view'),

    url(r'^nfs-share-client-distrib/$', NFSDShareClientDistribView.as_view(),
        name='nfsshareclientdistrib-view'),
    url(r'^nfs-share-client-distrib/(?P<pid>[0-9]+)/$',
        NFSDShareClientDistribView.as_view(),
        name='nfsshareclientdistrib-view'),
    url(r'^nfs-share-client-distrib/(?P<pid>[0-9]+)/(?P<command>[a-z]+)/$',
        NFSDShareClientDistribView.as_view(),
        name='nfsshareclientdistrib-view'),

)
