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
                                 NetworkInterface, User, PoolScrub, Setup,
                                 NFSExportGroup, SFTP)
from django.contrib.auth.models import User as DjangoUser

class DiskInfoSerializer(serializers.ModelSerializer):
    pool_name = serializers.CharField(source='pool_name')
    class Meta:
        model = Disk

class PoolInfoSerializer(serializers.ModelSerializer):
    disks = DiskInfoSerializer(source='disk_set')
    usage = serializers.IntegerField(source='cur_usage')
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
    exports = NFSExportSerializer(source='nfsexport_set')
    class Meta:
        model = NFSExportGroup

class SambaShareSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')
    class Meta:
        model = SambaShare

class IscsiSerializer(serializers.ModelSerializer):
    class Meta:
        model = IscsiTarget

class ShareSerializer(serializers.ModelSerializer):
    snapshots = SnapshotSerializer(source='snapshot_set')
    pool = PoolInfoSerializer(source='pool')
    nfs_exports = NFSExportSerializer(source='nfsexport_set')
    smb_shares = SambaShareSerializer(source='sambashare_set')
    usage = serializers.IntegerField(source='cur_usage')

    class Meta:
        model = Share

class ApplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appliance

class SUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User

class UserSerializer(serializers.ModelSerializer):
    suser = SUserSerializer(source='suser')
    class Meta:
        model = DjangoUser
        fields = ('username', 'is_active', 'suser')

class SupportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportCase

class DashboardConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardConfig

class NetworkInterfaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NetworkInterface

class PoolScrubSerializer(serializers.ModelSerializer):
    class Meta:
        model = PoolScrub

class SetupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Setup

class SFTPSerializer(serializers.ModelSerializer):
    share = serializers.CharField(source='share_name')
    class Meta:
        model = SFTP
