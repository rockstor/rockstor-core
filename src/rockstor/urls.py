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
from storageadmin.views import (SetupUserView, LoginView, DashboardConfigView,
                                NFSExportGroupListView,
                                NFSExportGroupDetailView, SambaListView,
                                SambaDetailView, SFTPListView, SFTPDetailView,
                                AdvancedNFSExportView, OauthAppView,
                                TLSCertificateView, SnapshotView,
                                ConfigBackupListView, ConfigBackupDetailView,
                                ConfigBackupUpload, EmailClientView)
import os.path
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

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

urlpatterns = patterns(
    '',
    url(r'^$', 'storageadmin.views.home', name='home'),
    url(r'^login_page$', 'storageadmin.views.login_page'),
    url(r'^login_submit$',
        'storageadmin.views.login_submit'),
    url(r'^logout_user$', 'storageadmin.views.logout_user'),
    url(r'^home$', 'storageadmin.views.home', name='home'),
    url(r'^setup_user$', SetupUserView.as_view()),
    url(r'^site_media/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': site_media}),
    url(r'^css/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': css_doc_root}),
    url(r'^js/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': js_doc_root}),
    url(r'^img/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': img_doc_root}),

    url(r'^o/', include('oauth2_provider.urls',
                        namespace='oauth2_provider',)),
    # REST API
    url(r'^api/login', LoginView.as_view()),
    (r'^api/appliances',
     include('storageadmin.urls.appliances')),
    (r'^api/commands/',
     include('storageadmin.urls.commands')),
    (r'^api/disks', include('storageadmin.urls.disks')),
    (r'^api/network', include('storageadmin.urls.network')),
    (r'^api/pools', include('storageadmin.urls.pools')),
    (r'^api/shares', include('storageadmin.urls.share')),
    (r'^api/snapshots', SnapshotView.as_view()),
    (r'^api/users', include('storageadmin.urls.users')),
    (r'^api/groups', include('storageadmin.urls.groups')),
    url(r'^api/nfs-exports$', NFSExportGroupListView.as_view()),
    url(r'^api/nfs-exports/(?P<export_id>\d+)$',
        NFSExportGroupDetailView.as_view()),
    url(r'^api/adv-nfs-exports$',
        AdvancedNFSExportView.as_view()),
    url(r'^api/samba$', SambaListView.as_view()),
    url(r'^api/samba/(?P<smb_id>\d+)$',
        SambaDetailView.as_view()),
    url(r'^api/sftp$', SFTPListView.as_view()),
    url(r'^api/sftp/(?P<id>\d+)$', SFTPDetailView.as_view()),
    # Dashboard config
    url(r'^api/dashboardconfig$',
        DashboardConfigView.as_view()),
    url(r'^api/oauth_app$', OauthAppView.as_view()),
    url(r'^api/oauth_app/(?P<id>\d+)$',
        OauthAppView.as_view()),
    (r'^api/sm/services/',
     include('smart_manager.urls.services')),
    (r'^api/sm/sprobes/',
     include('smart_manager.urls.sprobes')),
    (r'^api/sm/tasks/',
     include('smart_manager.urls.tasks')),
    (r'^api/sm/replicas/',
     include('smart_manager.urls.replicas')),

    # Certificate URL
    (r'^api/certificate', TLSCertificateView.as_view()),
    (r'^api/rockons',
     include('storageadmin.urls.rockons')),

    # Config Backup
    url(r'^api/config-backup$', ConfigBackupListView.as_view()),
    url(r'^api/config-backup/(?P<backup_id>\d+)$',
        ConfigBackupDetailView.as_view()),
    url(r'^api/config-backup/file-upload$',
        ConfigBackupUpload.as_view()),
    url(r'^api/email$', EmailClientView.as_view()),
    url(r'^api/email/(?P<command>.*)$', EmailClientView.as_view()),
    # Pincard
    url(r'^api/pincardmanager',
        include('storageadmin.urls.pincard')),
    # update subscription
    (r'^api/update-subscriptions',
     include('storageadmin.urls.update_subscription')),
)
