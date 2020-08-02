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
from sprobes import SProbeView  # noqa E501
from mem_info import MemInfoView  # noqa E501
from net_stat import NetStatView  # noqa E501
from disk_stat import DiskStatView  # noqa E501
from nfs_distrib import NFSDistribView  # noqa E501
from nfs_client_distrib import NFSDClientDistribView  # noqa E501
from nfs_share_distrib import NFSDShareDistribView  # noqa E501
from nfs_share_client_distrib import NFSDShareClientDistribView  # noqa E501
from cpu_util import CPUMetricView  # noqa E501
from nfs_uid_gid import NFSDUidGidDistributionView  # noqa E501
from load_avg import LoadAvgView  # noqa E501
from sprobe_metadata import SProbeMetadataView, SProbeMetadataDetailView  # noqa E501
from base_service import BaseServiceView, BaseServiceDetailView  # noqa E501
from nis_service import NISServiceView  # noqa E501
from samba_service import SambaServiceView  # noqa E501
from nfs_service import NFSServiceView  # noqa E501
from replication import ReplicaListView, ReplicaDetailView  # noqa E501
from replica_trail import ReplicaTrailListView, ReplicaTrailDetailView  # noqa E501
from replication_service import ReplicationServiceView  # noqa E501
from ntp_service import NTPServiceView  # noqa E501
from ldap_service import LdapServiceView  # noqa E501
from sftp_service import SFTPServiceView  # noqa E501
from tasktypes import TaskTypeView  # noqa E501
from task_scheduler import TaskSchedulerListView, TaskSchedulerDetailView  # noqa E501
from task_log import TaskLogView  # noqa E501
from replica_share import ReplicaShareListView, ReplicaShareDetailView  # noqa E501
from receive_trail import ReceiveTrailListView, ReceiveTrailDetailView  # noqa E501
from ts_service import TaskSchedulerServiceView  # noqa E501
from dc_service import DataCollectorServiceView  # noqa E501
from sm_service import ServiceMonitorView  # noqa E501
from snmp_service import SNMPServiceView  # noqa E501
from docker_service import DockerServiceView  # noqa E501
from smartd_service import SMARTDServiceView  # noqa E501
from nut_service import NUTServiceView  # noqa E501
from active_directory import ActiveDirectoryServiceView  # noqa E501
from receiver_pools import ReceiverPoolListView  # noqa E501
from ztaskd_service import ZTaskdServiceView  # noqa E501
from bootstrap_service import BootstrapServiceView  # noqa E501
from shellinaboxd_service import ShellInABoxServiceView  # noqa E501
from rockstor_service import RockstorServiceView  # noqa E501
