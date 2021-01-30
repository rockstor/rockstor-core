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

from django.conf.urls import include, url
from django.views.static import serve
from django.conf import settings

from smart_manager.views import (
    BaseServiceView,
    SProbeView,
    TaskSchedulerListView,
    ReplicaListView,
)
from storageadmin.views import (
    SetupUserView,
    LoginView,
    DashboardConfigView,
    NFSExportGroupListView,
    NFSExportGroupDetailView,
    SambaListView,
    SambaDetailView,
    SFTPListView,
    SFTPDetailView,
    AdvancedNFSExportView,
    OauthAppView,
    TLSCertificateView,
    SnapshotView,
    ConfigBackupListView,
    ConfigBackupDetailView,
    ConfigBackupUpload,
    EmailClientView,
    home,
    login_page,
    login_submit,
    logout_user,
    ShareListView,
    PoolListView,
    ApplianceListView,
    ApplianceDetailView,
    DiskListView,
    NetworkStateView,
    UserListView,
    GroupListView,
    GroupDetailView,
    UserDetailView,
    PincardView,
    UpdateSubscriptionListView,
    RockOnView,
)
import os.path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

site_media = os.path.join(os.path.dirname(__file__), "site_media")
css_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/css")
img_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/img")
js_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/js")

# TODO move to path() and re_path() introduced in Django 2.0.
#  url() is to be deprecated, as of 2.0 it's a link to re_path()
urlpatterns = [
    url(r"^$", home, name="home"),
    url(r"^login_page$", login_page, name="login_page"),
    url(r"^login_submit$", login_submit, name="login_submit"),
    url(r"^logout_user$", logout_user, name="logout_user"),
    url(r"^home$", home, name="home"),
    url(r"^setup_user$", SetupUserView.as_view()),
    # https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-files-uploaded-by-a-user-during-development
    url(r"^site_media/(?P<path>.*)$", serve, {"document_root": site_media}),
    url(r"^css/(?P<path>.*)$", serve, {"document_root": css_doc_root}),
    url(r"^js/(?P<path>.*)$", serve, {"document_root": js_doc_root}),
    url(r"^img/(?P<path>.*)$", serve, {"document_root": img_doc_root}),
    url(r"^o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    # REST API
    url(r"^api/login", LoginView.as_view()),
    url(r"^api/appliances$", ApplianceListView.as_view()),
    url(r"^api/appliances/(?P<appid>\d+)$", ApplianceDetailView.as_view()),
    url(r"^api/commands/", include("storageadmin.urls.commands")),
    url(r"^api/disks$", DiskListView.as_view()),
    url(r"^api/disks/", include("storageadmin.urls.disks")),
    url(r"^api/network$", NetworkStateView.as_view()),
    url(r"^api/network/", include("storageadmin.urls.network")),
    url(r"^api/pools$", PoolListView.as_view(), name="pool-view"),
    url(r"^api/pools/", include("storageadmin.urls.pools")),
    url(r"^api/shares$", ShareListView.as_view(), name="share-view"),
    url(r"^api/shares/", include("storageadmin.urls.share")),
    url(r"^api/snapshots", SnapshotView.as_view()),
    url(r"^api/users$", UserListView.as_view()),
    url(
        r"^api/users/(?P<username>%s)$" % settings.USERNAME_REGEX,
        UserDetailView.as_view(),
    ),
    url(r"^api/groups$", GroupListView.as_view()),
    url(
        r"^api/groups/(?P<groupname>%s)$" % settings.USERNAME_REGEX,
        GroupDetailView.as_view(),
    ),
    url(r"^api/nfs-exports$", NFSExportGroupListView.as_view()),
    url(r"^api/nfs-exports/(?P<export_id>\d+)$", NFSExportGroupDetailView.as_view()),
    url(r"^api/adv-nfs-exports$", AdvancedNFSExportView.as_view()),
    url(r"^api/samba$", SambaListView.as_view()),
    url(r"^api/samba/(?P<smb_id>\d+)$", SambaDetailView.as_view()),
    url(r"^api/sftp$", SFTPListView.as_view()),
    url(r"^api/sftp/(?P<id>\d+)$", SFTPDetailView.as_view()),
    # Dashboard config
    url(r"^api/dashboardconfig$", DashboardConfigView.as_view()),
    url(r"^api/oauth_app$", OauthAppView.as_view()),
    url(r"^api/oauth_app/(?P<id>\d+)$", OauthAppView.as_view()),
    url(r"^api/sm/services$", BaseServiceView.as_view()),
    url(r"^api/sm/services/", include("smart_manager.urls.services")),
    url(r"^api/sm/sprobes$", SProbeView.as_view(), name="probe-view"),
    url(r"^api/sm/sprobes/", include("smart_manager.urls.sprobes")),
    url(r"^api/sm/tasks$", TaskSchedulerListView.as_view()),
    url(r"^api/sm/tasks/", include("smart_manager.urls.tasks")),
    url(r"^api/sm/replicas$", ReplicaListView.as_view(), name="replica-view"),
    url(r"^api/sm/replicas/", include("smart_manager.urls.replicas")),
    # Certificate url
    url(r"^api/certificate", TLSCertificateView.as_view()),
    url(r"^api/rockons$", RockOnView.as_view()),
    url(r"^api/rockons/", include("storageadmin.urls.rockons")),
    # Config Backup
    url(r"^api/config-backup$", ConfigBackupListView.as_view()),
    url(r"^api/config-backup/(?P<backup_id>\d+)$", ConfigBackupDetailView.as_view()),
    url(r"^api/config-backup/file-upload$", ConfigBackupUpload.as_view()),
    url(r"^api/email$", EmailClientView.as_view()),
    url(r"^api/email/(?P<command>.*)$", EmailClientView.as_view()),
    # Pincard
    url(
        r"^api/pincardmanager/(?P<command>create|reset)/(?P<user>\w+)$",
        PincardView.as_view(),
    ),
    # update subscription
    url(r"^api/update-subscriptions$", UpdateSubscriptionListView.as_view()),
    url(
        r"^api/update-subscriptions/", include("storageadmin.urls.update_subscription")
    ),
]
