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
from sprobes import SProbeView
from mem_info import MemInfoView
from net_stat import NetStatView
from disk_stat import DiskStatView
from nfs_distrib import NFSDistribView
from nfs_client_distrib import NFSDClientDistribView
from nfs_share_distrib import NFSDShareDistribView
from nfs_share_client_distrib import NFSDShareClientDistribView
from cpu_util import CPUMetricView
from nfs_uid_gid import NFSDUidGidDistributionView
from load_avg import LoadAvgView
from sprobe_metadata import (SProbeMetadataView, SProbeMetadataDetailView)
from base_service import (BaseServiceView, BaseServiceDetailView)
from nis_service import NISServiceView
from samba_service import SambaServiceView
from nfs_service import NFSServiceView
from replication import (ReplicaListView, ReplicaDetailView)
from replica_trail import (ReplicaTrailListView, ReplicaTrailDetailView)
from replication_service import ReplicationServiceView
from ntp_service import NTPServiceView
from ldap_service import LdapServiceView
from sftp_service import SFTPServiceView
from tasktypes import TaskTypeView
from task_scheduler import (TaskSchedulerListView, TaskSchedulerDetailView)
from task_log import TaskLogView
from replica_share import (ReplicaShareListView, ReplicaShareDetailView)
from receive_trail import (ReceiveTrailListView, ReceiveTrailDetailView)
from ts_service import TaskSchedulerServiceView
from dc_service import DataCollectorServiceView
from sm_service import ServiceMonitorView
from afp_service import AFPServiceView
from snmp_service import SNMPServiceView
from docker_service import DockerServiceView
from smartd_service import SMARTDServiceView
from nut_service import NUTServiceView
from active_directory import ActiveDirectoryServiceView
from receiver_pools import ReceiverPoolListView
from ztaskd_service import ZTaskdServiceView
from bootstrap_service import BootstrapServiceView
from shellinaboxd_service import ShellInABoxServiceView
from rockstor_service import RockstorServiceView
