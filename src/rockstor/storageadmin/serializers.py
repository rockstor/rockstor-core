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

from rest_framework import serializers
from storageadmin.models import (Disk, Pool, Share, Snapshot, NFSExport,
                                 SambaShare, IscsiTarget, Appliance,
                                 SupportCase, DashboardConfig,
                                 NetworkDevice, NetworkConnection, User, PoolScrub, Setup,
                                 NFSExportGroup, SFTP, AdvancedNFSExport,
                                 OauthApp, NetatalkShare, Group, PoolBalance,
                                 SambaCustomConfig, TLSCertificate, RockOn,
                                 DVolume, DPort, DCustomConfig, DContainerEnv,
                                 SMARTAttribute, SMARTCapability, SMARTInfo,
                                 SMARTErrorLog, SMARTErrorLogSummary,
                                 SMARTTestLog, SMARTTestLogDetail,
                                 SMARTIdentity, ConfigBackup, EmailClient,
                                 UpdateSubscription)
from django.contrib.auth.models import User as DjangoUser


class DiskInfoSerializer(serializers.ModelSerializer):
    pool_name = serializers.CharField()
    power_state = serializers.CharField()
    hdparm_setting = serializers.CharField()
    apm_level = serializers.CharField()
    temp_name = serializers.CharField()
    class Meta:
        model = Disk


class PoolInfoSerializer(serializers.ModelSerializer):
    disks = DiskInfoSerializer(many=True, source='disk_set')
    free = serializers.IntegerField()
    reclaimable = serializers.IntegerField()

    class Meta:
        model = Pool


class SnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = Snapshot


class NFSExportSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')

    class Meta:
        model = NFSExport


class NFSExportGroupSerializer(serializers.ModelSerializer):
    exports = NFSExportSerializer(many=True, source='nfsexport_set')

    class Meta:
        model = NFSExportGroup


class AdvancedNFSExportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdvancedNFSExport


class SUserSerializer(serializers.ModelSerializer):
    
    ALLOWED_CHOICES = (
        ('yes', 'yes'),
        ('no', 'no'),
        ('otp', 'otp')
        )
    groupname = serializers.CharField()
    managed_user = serializers.BooleanField(default=True)
    has_pincard = serializers.BooleanField(default=False)
    pincard_allowed = serializers.ChoiceField(choices=ALLOWED_CHOICES, default='no')

    class Meta:
        model = User


class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group


class UserSerializer(serializers.ModelSerializer):
    suser = SUserSerializer(source='suser')

    class Meta:
        model = DjangoUser
        fields = ('username', 'is_active', 'suser')


class SambaCustomConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = SambaCustomConfig


class SambaShareSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')
    admin_users = SUserSerializer(many=True)
    custom_config = SambaCustomConfigSerializer(many=True,
                                                source='sambacustomconfig_set')

    class Meta:
        model = SambaShare


class IscsiSerializer(serializers.ModelSerializer):
    class Meta:
        model = IscsiTarget


class SharePoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Share


class ShareSerializer(serializers.ModelSerializer):
    snapshots = SnapshotSerializer(many=True, source='snapshot_set')
    pool = PoolInfoSerializer()
    nfs_exports = NFSExportSerializer(many=True, source='nfsexport_set')

    class Meta:
        model = Share


class ApplianceSerializer(serializers.ModelSerializer):
    ip = serializers.CharField(source='ipaddr')

    class Meta:
        model = Appliance


class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportCase


class DashboardConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardConfig


class NetworkDeviceSerializer(serializers.ModelSerializer):
    cname = serializers.CharField()

    class Meta:
        model = NetworkDevice


class NetworkConnectionSerializer(serializers.ModelSerializer):
    ctype = serializers.CharField()
    team_profile = serializers.CharField()
    bond_profile = serializers.CharField()

    class Meta:
        model = NetworkConnection


class PoolScrubSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolScrub


class PoolBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolBalance


class SetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setup


class SFTPSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')

    class Meta:
        model = SFTP


class OauthAppSerializer(serializers.ModelSerializer):
    client_id = serializers.CharField()
    client_secret = serializers.CharField()

    class Meta:
        model = OauthApp


class NetatalkShareSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')

    class Meta:
        model = NetatalkShare


class TLSCertificateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TLSCertificate


class RockOnSerializer(serializers.ModelSerializer):
    ui_port = serializers.IntegerField()

    class Meta:
        model = RockOn


class RockOnVolumeSerializer(serializers.ModelSerializer):
    share_name = serializers.CharField()

    class Meta:
        model = DVolume


class RockOnPortSerializer(serializers.ModelSerializer):
    class Meta:
        model = DPort


class RockOnCustomConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DCustomConfig

class RockOnEnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DContainerEnv

class SMARTCapabilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTCapability


class SMARTAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTAttribute


class SMARTErrorLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTErrorLog


class SMARTErrorLogSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTErrorLogSummary


class SMARTTestLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTTestLog


class SMARTTestLogDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTTestLogDetail


class SMARTIdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SMARTIdentity


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


class ConfigBackupSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigBackup


class EmailClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailClient


class UpdateSubscriptionSerializer(serializers.ModelSerializer):

    class Meta:
        model = UpdateSubscription
