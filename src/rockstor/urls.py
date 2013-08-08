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

from django.conf.urls.defaults import patterns, include, url
from storageadmin.views import (DiskView, SystemDiskView, PoolView, ShareView,
                                SnapshotView, InfoView, SetupWizardView,
                                ShareIscsiView, AppliancesView, LoginView,
                                UserView, ShareSambaView, SupportView,
                                DashboardConfigView, ShareNFSView, NetworkView)
from smart_manager.views import (SmartManagerView, ServiceView, SProbeView,
                                 SProbeView2, MemInfoView, NetStatView,
                                 DiskStatView, NFSDistribView)

import os.path
import socketio.sdjango

site_media = os.path.join(
  os.path.dirname(__file__), 'site_media'
)
css_doc_root = os.path.join(
  os.path.dirname(__file__), '/templates/storageadmin/css'
)
img_doc_root = os.path.join(
  os.path.dirname(__file__), '/templates/storageadmin/img'
)
js_doc_root = os.path.join(
  os.path.dirname(__file__), '/templates/storageadmin/js'
)

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'storageadmin.views.home', name='home'),
    url(r'^login_page$', 'storageadmin.views.login_page', name='login_page'),
    url(r'^login_submit$', 'storageadmin.views.login_submit', name='login_submit'),
    url(r'^logout_user$', 'storageadmin.views.logout_user', name='logout_user'),
    url(r'^home$', 'storageadmin.views.home', name='home'),
    url(r'^setupwizard$', SetupWizardView.as_view(), name='setupwizard'),
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': site_media }),
    url(r'^css/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': css_doc_root }),
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': js_doc_root }),
    url(r'^img/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': img_doc_root }),

    # Socket.io
    url("^socket\.io", include(socketio.sdjango.urls)),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # REST API
    url(r'^api/login', LoginView.as_view(), name='login-api-view'),
    url(r'^api/appliances/$', AppliancesView.as_view(),
        name='appliances-view'),
    url(r'^api/appliances/(?P<id>\d+)$', AppliancesView.as_view(),
        name='appliances-view'),
    url(r'^api/tools/sysdisks', SystemDiskView.as_view(), name='sys-disk-view'),
    url(r'^api/tools/sysinfo', InfoView.as_view(), name='sys-info'),

    # Disks section
    url(r'^api/disks/$', DiskView.as_view(), name='disk-view'),
    url(r'^api/disks/(?P<dname>.*)/$', DiskView.as_view(), name='disk-view'),

    # Network section
    url(r'^api/network/$', NetworkView.as_view(), name='net-view'),
    url(r'^api/network/(?P<iname>[A-Za-z0-9]+)/$', NetworkView.as_view(),
        name='net-view'),

    # Pools section
    url(r'^api/pools/$', PoolView.as_view(), name='pool-view'),
    url(r'^api/pools/(?P<pname>[A-Za-z0-9_]+)/$', PoolView.as_view(),
        name='pool-view'),
    url(r'^api/pools/(?P<pname>[A-Za-z0-9_]+)/(?P<command>.*)/$',
        PoolView.as_view(), name='pool-view'),

    (r'^api/shares/', include('storageadmin.urls.share')),
    (r'^api/users/', include('storageadmin.urls.users')),


    url(r'^api/support/$', SupportView.as_view(), name='support-view'),
    url(r'^api/support/(?P<caseid>[0-9]+)/$', SupportView.as_view(), name='support-view'),

    # Dashboard config
    url(r'^api/dashboardconfig/$', DashboardConfigView.as_view(), name='dashboardconfig-view'),

    (r'^api/sm/services/', include('smart_manager.urls.services')),
    (r'^api/sm/sprobes/', include('smart_manager.urls.sprobes')),
)
