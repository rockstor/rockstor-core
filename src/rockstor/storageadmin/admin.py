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

from django.contrib import admin
from storageadmin.models import (
    Disk,
    Pool,
    Share,
    Snapshot,
    IscsiTarget,
    SFTP,
    NFSExportGroup,
    NFSExport,
    SambaShare,
    SambaCustomConfig,
    PosixACLs,
    OauthApp,
)
from storageadmin.models.rockon import (
    RockOn,
    DImage,
    DContainer,
    DContainerLink,
    DContainerNetwork,
    DPort,
    DVolume,
    ContainerOption,
    DContainerArgs,
    DCustomConfig,
    DContainerEnv,
    DContainerDevice,
    DContainerLabel,
)
from storageadmin.models.user import User, Group

# https://docs.djangoproject.com/en/4.2/ref/contrib/admin/


class ShareAdminInline(admin.TabularInline):
    """
    Controls display of Share when displayed inline, e.g. in Pool detailed view.
    """

    model = Share
    fields = [
        "subvol_name",
        "size",
        "qgroup",
        "pqgroup",
        "compression_algo",
    ]
    list_per_page = 15


class SnapshotAdminInline(admin.TabularInline):
    """
    Controls display of Snapshot when displayed inline, e.g. in Share detailed view.
    """

    model = Snapshot
    fields = [
        "name",
        "size",
        "qgroup",
        "rusage",
        "eusage",
    ]
    list_per_page = 15


class IscsiTargetAdminInline(admin.TabularInline):
    """
    Controls display of IscsiTarget when displayed inline, e.g. in Share detailed view.
    """

    model = IscsiTarget
    fields = [
        "tname",
        "tid",
        "dev_name",
        "dev_size",
    ]
    list_per_page = 15


class SFTPAdminInline(admin.TabularInline):
    """
    Controls display of SFTP when displayed inline, e.g. in Share detailed view.
    """

    model = SFTP
    fields = [
        "editable",
    ]


@admin.register(SFTP)
class SFTPAdmin(admin.ModelAdmin):
    def parent_share_name(self, obj):
        if obj.share:
            return obj.share.name
        else:
            return None

    # Overview list
    list_display = ["parent_share_name", "editable"]
    list_per_page = 15
    # Detailed view
    fields = ["editable"]


class NFSExportAdminInline(admin.TabularInline):
    """
    Controls display of NFSExport when displayed inline, e.g. in Share & NFSExportGroup detailed view.
    """

    model = NFSExport
    fields = ["export_group", "mount"]


@admin.register(NFSExport)
class NFSExportAdmin(admin.ModelAdmin):
    def parent_share_name(self, obj):
        if obj.share:
            return obj.share.name
        else:
            return None

    # Overview list
    list_display = ["parent_share_name", "export_group", "mount"]
    list_per_page = 15
    # Detailed view
    fields = ["export_group", "share", "mount"]


@admin.register(NFSExportGroup)
class NFSExportGroupAdmin(admin.ModelAdmin):
    # Overview list
    list_display = [
        "host_str",
        "admin_host",
        "editable",
        "syncable",
        "mount_security",
        "nohide",
        "enabled",
    ]
    # Detailed view
    fields = [
        "host_str",
        "admin_host",
        ("editable", "syncable", "mount_security"),
        ("nohide", "enabled")
    ]
    inlines = [NFSExportAdminInline]


class DiskAdminInline(admin.TabularInline):
    """
    Controls display of Disk when displayed inline, e.g. in a Pool detailed view.
    """

    model = Disk
    fields = [
        "name",
        "devid",
        "size",
        "allocated",
        "model",
    ]
    list_per_page = 15


@admin.register(Disk)
class DiskAdmin(admin.ModelAdmin):
    def parent_pool_name(self, obj):
        if obj.pool:
            return obj.pool.name
        else:
            return None

    # Overview list
    list_display = [
        "name",
        "serial",
        "devid",
        "size",
        "allocated",
        "model",
        "parent_pool_name",
    ]
    # Detailed view
    fields = [
        ("name", "serial", "devid"),
        ("vendor", "model"),
        ("size", "allocated"),
        "btrfs_uuid",
        ("offline", "parted"),
        ("smart_available", "smart_enabled", "smart_options"),
        "role",
    ]


# Samba


class SambaShareAdminInline(admin.TabularInline):
    """
    Controls display of SambaShare when displayed inline, e.g. in Share detailed view.
    """

    model = SambaShare
    fields = [
        "path",
        "comment",
        "browsable",
        "read_only",
        "guest_ok",
        "time_machine",
        "shadow_copy",
        "snapshot_prefix",
    ]
    list_per_page = 15


class SambaCustomConfigAdminInline(admin.TabularInline):
    """
    Controls display of SambaCustomConfig when displayed inline, e.g. in SambaShare detailed view.
    """

    model = SambaCustomConfig


class PosixACLsAdminInline(admin.TabularInline):
    """
    Controls display of SambaCustomConfig when displayed inline, e.g. in SambaShare detailed view.
    """

    model = PosixACLs


@admin.register(SambaShare)
class SambaShareAdmin(admin.ModelAdmin):
    def parent_share_name(self, obj):
        if obj.share:
            return obj.share.name
        else:
            return None

    def has_custom_config(self, obj) -> bool:
        if SambaCustomConfig.objects.filter(smb_share=obj).exists():
            return True
        else:
            return False

    # has_custom_config.boolean = True
    # Overview list
    list_display = [
        "path",
        "comment",
        "browsable",
        "read_only",
        "guest_ok",
        "time_machine",
        "shadow_copy",
        "snapshot_prefix",
        "has_custom_config",
        "parent_share_name",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        ("share", "path"),
        "comment",
        ("browsable", "read_only", "guest_ok", "time_machine"),
        ("shadow_copy", "snapshot_prefix"),
    ]
    inlines = [SambaCustomConfigAdminInline, PosixACLsAdminInline]


@admin.register(SambaCustomConfig)
class SambaCustomConfigAdmin(admin.ModelAdmin):
    def parent_sambashare_path(self, obj):
        if obj.smb_share:
            return obj.smb_share.path
        else:
            return None

    def parent_sambashare_sharename(self, obj):
        if obj.smb_share.share:
            return obj.smb_share.share.name
        else:
            return None

    # Overview list
    list_display = [
        "parent_sambashare_path",
        "parent_sambashare_sharename",
        "custom_config",
    ]


@admin.register(IscsiTarget)
class IscsiTargetAdmin(admin.ModelAdmin):
    def parent_share_name(self, obj):
        if obj.share:
            return obj.share.name
        else:
            return None

    # Overview list
    list_display = [
        "tname",
        "tid",
        "dev_name",
        "dev_size",
        "parent_share_name",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        "share",
        ("tname", "tid"),
        ("dev_name", "dev_size"),
    ]


@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    # model = Share
    # The following fails with no Snapshots on a given Share
    # list_display = [field.name for field in Share._meta.get_fields()]
    def parent_pool_name(self, obj):
        if obj.pool:
            return obj.pool.name
        else:
            return None

    # Overview list
    list_display = [
        "name",
        "id",
        "size",
        "subvol_name",
        "uuid",
        "owner",
        "group",
        "perms",
        "qgroup",
        "pqgroup",
        "replica",
        "compression_algo",
        "rusage",
        "eusage",
        "parent_pool_name",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        ("name", "subvol_name"),
        ("owner", "group", "perms"),
        ("qgroup", "pqgroup"),
        "size",
        ("rusage", "eusage"),
        ("pqgroup_rusage", "pqgroup_eusage"),
        "compression_algo",
        "uuid",
        "replica",
    ]
    inlines = [
        SnapshotAdminInline,
        SambaShareAdminInline,
        SFTPAdminInline,
        NFSExportAdminInline,
        IscsiTargetAdminInline,
    ]


@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    def parent_share_name(self, obj):
        if obj.share:
            return obj.share.name
        else:
            return None

    # Overview list
    list_display = [
        "name",
        "size",
        "qgroup",
        "rusage",
        "eusage",
        "parent_share_name",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        ("name", "real_name"),
        "qgroup",
        "size",
        "snap_type",
        ("rusage", "eusage"),
        ("writable", "uvisible"),
    ]


@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    # Overview list
    list_display = [
        "name",
        "uuid",
        "size",
        "raid",
        "toc",
        "compression",
        "mnt_options",
        "role",
    ]
    list_per_page = 15
    inlines = [DiskAdminInline, ShareAdminInline]


# Rock-ons
Rockon_Models = (
    RockOn,
    DImage,
    DContainer,
    DContainerLink,
    DContainerNetwork,
    DPort,
    DVolume,
    ContainerOption,
    DContainerArgs,
    DCustomConfig,
    DContainerEnv,
    DContainerDevice,
    DContainerLabel,
)
admin.site.register(Rockon_Models)

# User/Group models
admin.site.register((User, Group, OauthApp))
