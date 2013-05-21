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
from disk import (DiskView, SystemDiskView)
from info import InfoView
from service import ServiceView
from setupwizard import SetupWizardView
from share_iscsi import ShareIscsiView
from appliances import AppliancesView
from login import LoginView
from socketio_service import RockStorMessageNamespace
from user import UserView
from share_samba import ShareSambaView
from support import SupportView
from dashboardconfig import DashboardConfigView
from share_nfs import ShareNFSView
from recipe import RecipeView
