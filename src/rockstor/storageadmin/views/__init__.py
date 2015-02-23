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
from share import ShareView
from pool import PoolView
from disk import DiskView
from command import CommandView
from share_iscsi import ShareIscsiView
from appliances import AppliancesView
from login import LoginView
from user import UserView
from support import SupportView
from dashboardconfig import DashboardConfigView
from share_nfs import ShareNFSView
from network import NetworkView
from pool_scrub import PoolScrubView
from setup_user import SetupUserView
from share_acl import ShareACLView
from nfs_exports import NFSExportGroupView
from share_command import ShareCommandView
from samba import SambaView
from sftp import SFTPView
from plugin import PluginView
from installed_plugin import InstalledPluginView
from adv_nfs_exports import AdvancedNFSExportView
from oauth_app import OauthAppView
from netatalk import NetatalkView
from group import GroupView
from pool_balance import PoolBalanceView
from rockon import RockOnView
from rockon_id import RockOnIdView
