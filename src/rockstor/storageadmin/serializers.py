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

from rest_framework import serializers
from storageadmin.models import (
    Disk,
    Pool,
    Share,
    Snapshot,
    NFSExport,
    SambaShare,
    IscsiTarget,
    Appliance,
    SupportCase,
    DashboardConfig,
    NetworkDevice,
    NetworkConnection,
    User,
    PoolScrub,
    Setup,
    NFSExportGroup,
    SFTP,
    AdvancedNFSExport,
    OauthApp,
    Group,
    PoolBalance,
    SambaCustomConfig,
    TLSCertificate,
    RockOn,
    DContainer,
    DVolume,
    DPort,
    DCustomConfig,
    DContainerEnv,
    DContainerDevice,
    DContainerLabel,
    DContainerNetwork,
    SMARTAttribute,
    SMARTCapability,
    SMARTInfo,
    SMARTErrorLog,
    SMARTErrorLogSummary,
    SMARTTestLog,
    SMARTTestLogDetail,
    SMARTIdentity,
    ConfigBackup,
    EmailClient,
    UpdateSubscription,
)
from django.contrib.auth.models import User as DjangoUser


class DiskInfoSerializer(serializers.ModelSerializer):
    pool_name = serializers.CharField()
    power_state = serializers.CharField()
    hdparm_setting = serializers.CharField()
    apm_level = serializers.CharField()
    temp_name = serializers.CharField()
    target_name = serializers.CharField()
    io_error_stats = serializers.CharField()

    class Meta:
        model = Disk
        fields = "__all__"


class PoolInfoSerializer(serializers.ModelSerializer):
    disks = DiskInfoSerializer(many=True, source="disk_set")
    free = serializers.IntegerField()
    reclaimable = serializers.IntegerField()
    mount_status = serializers.CharField()
    is_mounted = serializers.BooleanField()
    quotas_enabled = serializers.BooleanField()
    has_missing_dev = serializers.BooleanField()
    dev_stats_ok = serializers.BooleanField()
    dev_missing_count = serializers.IntegerField()
    redundancy_exceeded = serializers.BooleanField()
    data_raid = serializers.CharField()
    metadata_raid = serializers.CharField()


    class Meta:
        model = Pool
        fields = "__all__"


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot
        fields = "__all__"


class NFSExportSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source="share_name")
    share_id = serializers.CharField()

    class Meta:
        model = NFSExport
        fields = "__all__"


class NFSExportGroupSerializer(serializers.ModelSerializer):
    exports = NFSExportSerializer(many=True, source="nfsexport_set")

    class Meta:
        model = NFSExportGroup
        fields = "__all__"


class AdvancedNFSExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvancedNFSExport
        fields = "__all__"



class SUserSerializer(serializers.ModelSerializer):

    ALLOWED_CHOICES = (("yes", "yes"), ("no", "no"), ("otp", "otp"))
    groupname = serializers.CharField()
    managed_user = serializers.BooleanField(default=True)
    has_pincard = serializers.BooleanField(default=False)
    pincard_allowed = serializers.ChoiceField(choices=ALLOWED_CHOICES, default="no")

    class Meta:
        model = User
        fields = "__all__"


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    suser = SUserSerializer(source="suser")

    class Meta:
        model = DjangoUser
        fields = ("username", "is_active", "suser")


class SambaCustomConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SambaCustomConfig
        fields = "__all__"


class SambaShareSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source="share_name")
    share_id = serializers.CharField()
    admin_users = SUserSerializer(many=True)
    custom_config = SambaCustomConfigSerializer(
        many=True, source="sambacustomconfig_set"
    )

    class Meta:
        model = SambaShare
        fields = "__all__"



class IscsiSerializer(serializers.ModelSerializer):
    class Meta:
        model = IscsiTarget
        fields = "__all__"


class SharePoolSerializer(serializers.ModelSerializer):
    size_gb = serializers.FloatField()

    class Meta:
        model = Share
        fields = "__all__"


class ShareSerializer(serializers.ModelSerializer):
    snapshots = SnapshotSerializer(many=True, source="snapshot_set")
    pool = PoolInfoSerializer()
    nfs_exports = NFSExportSerializer(many=True, source="nfsexport_set")
    mount_status = serializers.CharField()
    is_mounted = serializers.BooleanField()
    pqgroup_exist = serializers.BooleanField()

    class Meta:
        model = Share
        fields = "__all__"


class ApplianceSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source="ipaddr")

    class Meta:
        model = Appliance
        fields = "__all__"


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportCase
        fields = "__all__"


class DashboardConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardConfig
        fields = "__all__"


class NetworkDeviceSerializer(serializers.ModelSerializer):
    cname = serializers.CharField()
    dev_name = serializers.CharField()

    class Meta:
        model = NetworkDevice
        fields = "__all__"


class NetworkConnectionSerializer(serializers.ModelSerializer):
    ctype = serializers.CharField()
    mtu = serializers.IntegerField()
    team_profile = serializers.CharField()
    bond_profile = serializers.CharField()
    docker_name = serializers.CharField()
    user_dnet = serializers.BooleanField()
    docker_options = serializers.DictField()

    class Meta:
        model = NetworkConnection
        fields = "__all__"


class PoolScrubSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolScrub
        fields = "__all__"


class PoolBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolBalance
        fields = "__all__"


class SetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setup
        fields = "__all__"


class SFTPSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source="share_name")
    share_id = serializers.CharField()

    class Meta:
        model = SFTP
        fields = "__all__"


class OauthAppSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField()
    client_secret = serializers.CharField()
    is_internal = serializers.BooleanField()

    class Meta:
        model = OauthApp
        fields = "__all__"


class TLSCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TLSCertificate
        fields = "__all__"


class RockOnSerializer(serializers.ModelSerializer):
    ui_port = serializers.IntegerField()
    ui_publish = serializers.BooleanField()
    host_network = serializers.BooleanField()

    class Meta:
        model = RockOn
        fields = "__all__"


class RockOnContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = DContainer
        fields = "__all__"


class RockOnVolumeSerializer(serializers.ModelSerializer):
    share_name = serializers.CharField()

    class Meta:
        model = DVolume
        fields = "__all__"


class RockOnPortSerializer(serializers.ModelSerializer):
    container_name = serializers.CharField()

    class Meta:
        model = DPort
        fields = "__all__"


class RockOnCustomConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DCustomConfig
        fields = "__all__"


class RockOnEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DContainerEnv
        fields = "__all__"


class RockOnDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = DContainerDevice
        fields = "__all__"


class RockOnLabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = DContainerLabel
        fields = "__all__"


class RockOnNetworkSerializer(serializers.ModelSerializer):
    docker_name = serializers.CharField()
    container_name = serializers.CharField()

    class Meta:
        model = DContainerNetwork
        fields = "__all__"


class SMARTCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTCapability
        fields = "__all__"


class SMARTAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTAttribute
        fields = "__all__"


class SMARTErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTErrorLog
        fields = "__all__"


class SMARTErrorLogSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTErrorLogSummary
        fields = "__all__"


class SMARTTestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTTestLog
        fields = "__all__"


class SMARTTestLogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTTestLogDetail
        fields = "__all__"


class SMARTIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTIdentity
        fields = "__all__"


class SMARTInfoSerializer(serializers.ModelSerializer):
    capabilities = SMARTCapabilitySerializer(many=True)
    attributes = SMARTAttributeSerializer(many=True)
    errorlog = SMARTErrorLogSerializer(many=True)
    errorlogsummary = SMARTErrorLogSummarySerializer(many=True)
    identity = SMARTIdentitySerializer()
    testlog = SMARTTestLogSerializer(many=True)
    testlogdetail = SMARTTestLogDetailSerializer(many=True)

    class Meta:
        model = SMARTInfo
        fields = "__all__"


class ConfigBackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigBackup
        fields = "__all__"


class EmailClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailClient
        fields = "__all__"



class UpdateSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateSubscription
        fields = "__all__"
