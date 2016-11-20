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


from home import (login_page, login_submit, logout_user, home)
from snapshot import SnapshotView
from share import (ShareListView, ShareDetailView, PoolShareListView)
from disk import (DiskMixin, DiskListView, DiskDetailView)
from pool import (PoolListView, PoolDetailView, get_usage_bound)
from command import CommandView
from appliances import (ApplianceListView, ApplianceDetailView)
from login import LoginView
from user import (UserListView, UserDetailView)
from dashboardconfig import DashboardConfigView
from network import (NetworkDeviceListView,
                     NetworkConnectionListView, NetworkStateView,
                     NetworkConnectionDetailView)
from pool_scrub import PoolScrubView
from setup_user import SetupUserView
from share_acl import ShareACLView
from nfs_exports import (NFSExportGroupListView, NFSExportGroupDetailView,
                         AdvancedNFSExportView)
from share_command import ShareCommandView
from samba import (SambaListView, SambaDetailView)
from sftp import (SFTPListView, SFTPDetailView)
from oauth_app import OauthAppView
from netatalk import (NetatalkListView, NetatalkDetailView)
from group import (GroupListView, GroupDetailView)
from pool_balance import PoolBalanceView
from tls_certificate import TLSCertificateView
from rockon import RockOnView
from rockon_id import RockOnIdView
from rockon_volume import RockOnVolumeView
from rockon_port import RockOnPortView
from rockon_custom_config import RockOnCustomConfigView
from rockon_environment import RockOnEnvironmentView
from disk_smart import DiskSMARTDetailView
from config_backup import (ConfigBackupListView, ConfigBackupDetailView,
                           ConfigBackupUpload)
from email_client import EmailClientView
from update_subscription import (UpdateSubscriptionListView,
                                 UpdateSubscriptionDetailView)
