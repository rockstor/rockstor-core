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


from home import login_page, login_submit, logout_user, home  # noqa F401
from snapshot import SnapshotView  # noqa F401
from share import ShareListView, ShareDetailView, PoolShareListView  # noqa F401
from disk import DiskMixin, DiskListView, DiskDetailView  # noqa F401
from pool import PoolListView, PoolDetailView, get_usage_bound  # noqa F401
from command import CommandView  # noqa F401
from appliances import ApplianceListView, ApplianceDetailView  # noqa F401
from login import LoginView  # noqa F401
from user import UserListView, UserDetailView  # noqa F401
from dashboardconfig import DashboardConfigView  # noqa F401
from network import (
    NetworkDeviceListView,  # noqa F401
    NetworkConnectionListView,
    NetworkStateView,
    NetworkConnectionDetailView,
)
from pool_scrub import PoolScrubView  # noqa F401
from setup_user import SetupUserView  # noqa F401
from share_acl import ShareACLView  # noqa F401
from nfs_exports import (
    NFSExportGroupListView,
    NFSExportGroupDetailView,  # noqa F401
    AdvancedNFSExportView,
)  # noqa F401
from share_command import ShareCommandView  # noqa F401
from samba import SambaListView, SambaDetailView  # noqa F401
from sftp import SFTPListView, SFTPDetailView  # noqa F401
from oauth_app import OauthAppView  # noqa F401
from group import GroupListView, GroupDetailView  # noqa F401
from pool_balance import PoolBalanceView  # noqa F401
from tls_certificate import TLSCertificateView  # noqa F401
from rockon import RockOnView  # noqa F401
from rockon_id import RockOnIdView  # noqa F401
from rockon_container import RockOnContainerView  # noqa F401
from rockon_volume import RockOnVolumeView  # noqa F401
from rockon_port import RockOnPortView  # noqa F401
from rockon_custom_config import RockOnCustomConfigView  # noqa F401
from rockon_environment import RockOnEnvironmentView  # noqa F401
from rockon_device import RockOnDeviceView  # noqa F401
from rockon_labels import RockOnLabelView  # noqa F401
from disk_smart import DiskSMARTDetailView  # noqa F401
from config_backup import (
    ConfigBackupListView,
    ConfigBackupDetailView,  # noqa F401
    ConfigBackupUpload,
)  # noqa F401
from email_client import EmailClientView  # noqa F401
from update_subscription import (
    UpdateSubscriptionListView,  # noqa F401
    UpdateSubscriptionDetailView,
)  # noqa F401
from pincard import PincardView  # noqa F401
