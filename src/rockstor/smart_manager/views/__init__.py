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
from smart_manager.views.sprobes import SProbeView  # noqa E501
from smart_manager.views.mem_info import MemInfoView  # noqa E501
from smart_manager.views.net_stat import NetStatView  # noqa E501
from smart_manager.views.disk_stat import DiskStatView  # noqa E501
from smart_manager.views.nfs_distrib import NFSDistribView  # noqa E501
from smart_manager.views.nfs_client_distrib import NFSDClientDistribView  # noqa E501
from smart_manager.views.nfs_share_distrib import NFSDShareDistribView  # noqa E501
from smart_manager.views.nfs_share_client_distrib import NFSDShareClientDistribView  # noqa E501
from smart_manager.views.cpu_util import CPUMetricView  # noqa E501
from smart_manager.views.nfs_uid_gid import NFSDUidGidDistributionView  # noqa E501
from smart_manager.views.load_avg import LoadAvgView  # noqa E501
from smart_manager.views.sprobe_metadata import SProbeMetadataView, SProbeMetadataDetailView  # noqa E501
from smart_manager.views.base_service import BaseServiceView, BaseServiceDetailView  # noqa E501
from smart_manager.views.nis_service import NISServiceView  # noqa E501
from smart_manager.views.samba_service import SambaServiceView  # noqa E501
from smart_manager.views.nfs_service import NFSServiceView  # noqa E501
from smart_manager.views.replication import ReplicaListView, ReplicaDetailView  # noqa E501
from smart_manager.views.replica_trail import ReplicaTrailListView, ReplicaTrailDetailView  # noqa E501
from smart_manager.views.replication_service import ReplicationServiceView  # noqa E501
from smart_manager.views.ntp_service import NTPServiceView  # noqa E501
from smart_manager.views.ldap_service import LdapServiceView  # noqa E501
from smart_manager.views.sftp_service import SFTPServiceView  # noqa E501
from smart_manager.views.tasktypes import TaskTypeView  # noqa E501
from smart_manager.views.task_scheduler import TaskSchedulerListView, TaskSchedulerDetailView  # noqa E501
from smart_manager.views.task_log import TaskLogView  # noqa E501
from smart_manager.views.replica_share import ReplicaShareListView, ReplicaShareDetailView  # noqa E501
from smart_manager.views.receive_trail import ReceiveTrailListView, ReceiveTrailDetailView  # noqa E501
from smart_manager.views.ts_service import TaskSchedulerServiceView  # noqa E501
from smart_manager.views.dc_service import DataCollectorServiceView  # noqa E501
from smart_manager.views.sm_service import ServiceMonitorView  # noqa E501
from smart_manager.views.snmp_service import SNMPServiceView  # noqa E501
from smart_manager.views.docker_service import DockerServiceView  # noqa E501
from smart_manager.views.smartd_service import SMARTDServiceView  # noqa E501
from smart_manager.views.nut_service import NUTServiceView  # noqa E501
from smart_manager.views.active_directory import ActiveDirectoryServiceView  # noqa E501
from smart_manager.views.receiver_pools import ReceiverPoolListView  # noqa E501
from smart_manager.views.ztaskd_service import ZTaskdServiceView  # noqa E501
from smart_manager.views.bootstrap_service import BootstrapServiceView  # noqa E501
from smart_manager.views.shellinaboxd_service import ShellInABoxServiceView  # noqa E501
from smart_manager.views.rockstor_service import RockstorServiceView  # noqa E501
from smart_manager.views.tailscaled_service import TailscaledServiceView  # noqa E501
