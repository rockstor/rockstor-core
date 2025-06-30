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

from django.urls import include, re_path, path
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

from django.contrib import admin


site_media = os.path.join(os.path.dirname(__file__), "site_media")
css_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/css")
img_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/img")
js_doc_root = os.path.join(os.path.dirname(__file__), "/templates/storageadmin/js")

urlpatterns = [
    re_path(r"^$", home, name="home"),
    re_path(r"^login_page$", login_page, name="login_page"),
    re_path(r"^login_submit$", login_submit, name="login_submit"),
    re_path(r"^logout_user$", logout_user, name="logout_user"),
    re_path(r"^home$", home, name="home"),
    re_path(r"^setup_user$", SetupUserView.as_view()),
    # https://docs.djangoproject.com/en/1.10/howto/static-files/#serving-files-uploaded-by-a-user-during-development
    re_path(r"^site_media/(?P<path>.*)$", serve, {"document_root": site_media}),
    re_path(r"^css/(?P<path>.*)$", serve, {"document_root": css_doc_root}),
    re_path(r"^js/(?P<path>.*)$", serve, {"document_root": js_doc_root}),
    re_path(r"^img/(?P<path>.*)$", serve, {"document_root": img_doc_root}),
    re_path(r"^o/", include("oauth2_provider.urls", namespace="oauth2_provider")),
    # REST API
    re_path(r"^api/login", LoginView.as_view()),
    re_path(r"^api/appliances$", ApplianceListView.as_view()),
    re_path(r"^api/appliances/(?P<appid>\d+)$", ApplianceDetailView.as_view()),
    re_path(r"^api/commands/", include("storageadmin.urls.commands")),
    re_path(r"^api/disks$", DiskListView.as_view()),
    re_path(r"^api/disks/", include("storageadmin.urls.disks")),
    re_path(r"^api/network$", NetworkStateView.as_view()),
    re_path(r"^api/network/", include("storageadmin.urls.network")),
    re_path(r"^api/pools$", PoolListView.as_view(), name="pool-view"),
    re_path(r"^api/pools/", include("storageadmin.urls.pools")),
    re_path(r"^api/shares$", ShareListView.as_view(), name="share-view"),
    re_path(r"^api/shares/", include("storageadmin.urls.share")),
    re_path(r"^api/snapshots", SnapshotView.as_view()),
    re_path(r"^api/users$", UserListView.as_view()),
    re_path(
        r"^api/users/(?P<username>%s)$" % settings.USERNAME_REGEX,
        UserDetailView.as_view(),
    ),
    re_path(r"^api/groups$", GroupListView.as_view()),
    re_path(
        r"^api/groups/(?P<groupname>%s)$" % settings.USERNAME_REGEX,
        GroupDetailView.as_view(),
    ),
    re_path(r"^api/nfs-exports$", NFSExportGroupListView.as_view()),
    re_path(r"^api/nfs-exports/(?P<export_id>\d+)$", NFSExportGroupDetailView.as_view()),
    re_path(r"^api/adv-nfs-exports$", AdvancedNFSExportView.as_view()),
    re_path(r"^api/samba$", SambaListView.as_view()),
    re_path(r"^api/samba/(?P<smb_id>\d+)$", SambaDetailView.as_view()),
    re_path(r"^api/sftp$", SFTPListView.as_view()),
    re_path(r"^api/sftp/(?P<id>\d+)$", SFTPDetailView.as_view()),
    # Dashboard config
    re_path(r"^api/dashboardconfig$", DashboardConfigView.as_view()),
    re_path(r"^api/oauth_app$", OauthAppView.as_view()),
    re_path(r"^api/oauth_app/(?P<id>\d+)$", OauthAppView.as_view()),
    re_path(r"^api/sm/services$", BaseServiceView.as_view()),
    re_path(r"^api/sm/services/", include("smart_manager.urls.services")),
    re_path(r"^api/sm/sprobes$", SProbeView.as_view(), name="probe-view"),
    re_path(r"^api/sm/sprobes/", include("smart_manager.urls.sprobes")),
    re_path(r"^api/sm/tasks$", TaskSchedulerListView.as_view()),
    re_path(r"^api/sm/tasks/", include("smart_manager.urls.tasks")),
    re_path(r"^api/sm/replicas$", ReplicaListView.as_view(), name="replica-view"),
    re_path(r"^api/sm/replicas/", include("smart_manager.urls.replicas")),
    # Certificate url
    re_path(r"^api/certificate", TLSCertificateView.as_view()),
    re_path(r"^api/rockons$", RockOnView.as_view()),
    re_path(r"^api/rockons/", include("storageadmin.urls.rockons")),
    # Config Backup
    re_path(r"^api/config-backup$", ConfigBackupListView.as_view()),
    re_path(r"^api/config-backup/(?P<backup_id>\d+)$", ConfigBackupDetailView.as_view()),
    re_path(r"^api/config-backup/file-upload$", ConfigBackupUpload.as_view()),
    re_path(r"^api/email$", EmailClientView.as_view()),
    re_path(r"^api/email/(?P<command>.*)$", EmailClientView.as_view()),
    # Pincard
    re_path(
        r"^api/pincardmanager/(?P<command>create|reset)/(?P<user>\w+)$",
        PincardView.as_view(),
    ),
    # update subscription
    re_path(r"^api/update-subscriptions$", UpdateSubscriptionListView.as_view()),
    re_path(
        r"^api/update-subscriptions/", include("storageadmin.urls.update_subscription")
    ),
]

# Django Admin Docs
urlpatterns += [path('radmin/doc/', include('django.contrib.admindocs.urls'))]
# Django Admin
urlpatterns += [path("radmin/", admin.site.urls, name="admin")]
