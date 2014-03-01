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

from django.conf.urls import patterns, include, url
from storageadmin.views import (SetupWizardView, LoginView,
                                SupportView, DashboardConfigView,
                                SetupUserView, NFSExportGroupView,
                                SambaView, SFTPView, PluginView,
                                InstalledPluginView)
import os.path

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
    url(r'^setup_user$', SetupUserView.as_view(), name='setupwizard'),
    url(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': site_media }),
    url(r'^css/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': css_doc_root }),
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': js_doc_root }),
    url(r'^img/(?P<path>.*)$', 'django.views.static.serve',
            { 'document_root': img_doc_root }),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # REST API
    url(r'^api/login', LoginView.as_view(), name='login-api-view'),
    (r'^api/appliances', include('storageadmin.urls.appliances')),
    (r'^api/commands/', include('storageadmin.urls.commands')),
    (r'^api/disks', include('storageadmin.urls.disks')),
    (r'^api/network', include('storageadmin.urls.network')),
    (r'^api/pools', include('storageadmin.urls.pools')),
    (r'^api/shares', include('storageadmin.urls.share')),
    (r'^api/users/', include('storageadmin.urls.users')),
    (r'^api/support', include('storageadmin.urls.support')),
    url(r'^api/nfs-exports$', NFSExportGroupView.as_view()),
    url(r'^api/nfs-exports/(?P<export_id>\d+)$', NFSExportGroupView.as_view()),
    url(r'^api/samba$', SambaView.as_view()),
    url(r'^api/samba/(?P<id>\d+)$', SambaView.as_view()),
    url(r'^api/sftp$', SFTPView.as_view()),
    url(r'^api/sftp/(?P<id>\d+)$', SFTPView.as_view()),
    # Dashboard config
    url(r'^api/dashboardconfig/$', DashboardConfigView.as_view(), name='dashboardconfig-view'),
    url(r'^api/plugins', PluginView.as_view(), name='plugin-view'),
    url(r'^api/installed_plugins', InstalledPluginView.as_view(), name='installed-plugin-view'),

    (r'^api/sm/services/', include('smart_manager.urls.services')),
    (r'^api/sm/sprobes/', include('smart_manager.urls.sprobes')),
    (r'^api/sm/tasks/', include('smart_manager.urls.tasks')),
    (r'^api/sm/replicas/', include('smart_manager.urls.replicas')),

    # Backup Plugin
    (r'^api/plugin/backup/', include('backup.urls')),
)


