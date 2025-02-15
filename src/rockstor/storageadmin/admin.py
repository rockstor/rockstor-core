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
    model = IscsiTarget
    fields = [
        "tname",
        "tid",
        "dev_name",
        "dev_size",
    ]
    list_per_page = 15


class SFTPAdminInline(admin.TabularInline):
    model = SFTP
    fields = [
        "editable",
    ]


@admin.register(SFTP)
class SFTPAdmin(admin.ModelAdmin):
    # Overview list
    list_display = ["share_name", "share_id", "editable"]
    list_per_page = 15
    # Detailed view
    fields = ["editable"]


class NFSExportAdminInline(admin.TabularInline):
    model = NFSExport
    fields = ["export_group", "mount"]


@admin.register(NFSExport)
class NFSExportAdmin(admin.ModelAdmin):
    # Overview list
    list_display = ["share_name", "share_id", "export_group", "mount"]
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
        ("nohide", "enabled"),
    ]
    inlines = [NFSExportAdminInline]


class DiskAdminInline(admin.TabularInline):
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
    # Overview list
    list_display = [
        "name",
        "target_name",
        "temp_name",
        "serial",
        "devid",
        "size",
        "allocated",
        "model",
        "power_state",
        "hdparm_setting",
        "apm_level",
        "io_error_stats",
        "pool_name",
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


class SambaShareAdminInline(admin.TabularInline):
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
    model = SambaCustomConfig


class PosixACLsAdminInline(admin.TabularInline):
    model = PosixACLs


class DVolumeAdminInline(admin.TabularInline):
    model = DVolume


@admin.register(DVolume)
class DVolumeAdmin(admin.ModelAdmin):
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = [
        "label",
        "parent_container_name",
        "description",
        "min_size",
        "uservol",
        "dest_dir",
        "share_name",
    ]
    # Detailed view
    fields = [
        ("container", "share"),
        "label",
        "description",
        (
            "uservol",
            "dest_dir",
            "min_size",
        ),
    ]


class DPortAdminInline(admin.TabularInline):
    model = DPort


@admin.register(DPort)
class DPortAdmin(admin.ModelAdmin):
    # Similar to DVolumeAdmin
    # Overview list
    list_display = [
        "label",
        "container_name",
        "description",
        "hostp",
        "hostp_default",
        "containerp",
        "protocol",
        "uiport",
        "publish",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        ("description", "label"),
        ("hostp", "hostp_default", "containerp"),
        ("uiport", "publish", "protocol"),
    ]


class DContainerAdminInline(admin.TabularInline):
    model = DContainer


class ContainerOptionAdminInline(admin.TabularInline):
    model = ContainerOption


@admin.register(ContainerOption)
class ContainerOptionAdmin(admin.ModelAdmin):
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = ["parent_container_name", "name", "val"]
    # Detailed view
    fields = [("name", "val")]


class DContainerArgsAdminInline(admin.TabularInline):
    model = DContainerArgs


@admin.register(DContainerArgs)
class DContainerArgsAdmin(admin.ModelAdmin):
    # Essentially identical to ContainerOptionAdmin
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = ["parent_container_name", "name", "val"]
    # Detailed view
    fields = [("name", "val")]


class DContainerLabelAdminInline(admin.TabularInline):
    model = DContainerLabel


@admin.register(DContainerLabel)
class DContainerLabelAdmin(admin.ModelAdmin):
    # Almost identical to DContainerArgs (-name + key)
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = ["parent_container_name", "key", "val"]
    # Detailed view
    fields = [("key", "val")]


class DContainerEnvAdminInline(admin.TabularInline):
    model = DContainerEnv


@admin.register(DContainerEnv)
class DContainerEnvAdmin(admin.ModelAdmin):
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = [
        "parent_container_name",
        "label",
        "key",
        "val",
        "description",
    ]
    # Detailed view
    fields = [
        "label",
        "description",
        ("key", "val"),
    ]


class DContainerDeviceAdminInline(admin.TabularInline):
    model = DContainerDevice


@admin.register(DContainerDevice)
class DContainerDeviceAdmin(admin.ModelAdmin):
    # Almost identical to DContainerEnvAdmin (i.e. dev/key fields)
    def parent_container_name(self, obj):
        if obj.container:
            return obj.container.name
        else:
            return None

    # Overview list
    list_display = [
        "parent_container_name",
        "label",
        "dev",
        "val",
        "description",
    ]
    # Detailed view
    fields = [
        "label",
        "description",
        ("dev", "val"),
    ]


class DContainerLinkAdminInline(admin.TabularInline):
    # https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin.fk_name
    fk_name = "destination"  # Specify which ForeignKey/OneToOne use use.
    model = DContainerLink


@admin.register(DContainerLink)
class DContainerLinkAdmin(admin.ModelAdmin):
    def parent_source_container_name(self, obj):
        if obj.source:
            return obj.source.name
        else:
            return None

    def parent_destination_container_name(self, obj):
        if obj.destination:
            return obj.destination.name
        else:
            return None

    # Overview list
    list_display = [
        "name",
        "parent_source_container_name",
        "parent_destination_container_name",
    ]
    # Detailed view
    fields = ["name", ("source", "destination")]


class DContainerNetworkAdminInline(admin.TabularInline):
    # https://docs.djangoproject.com/en/4.2/ref/contrib/admin/#django.contrib.admin.InlineModelAdmin.fk_name
    fk_name = "container"  # Specify which ForeignKey/OneToOne use use.
    model = DContainerNetwork


@admin.register(DContainerNetwork)
class DContainerNetworkAdmin(admin.ModelAdmin):
    # Overview list
    list_display = [
        "docker_name",
        "container_name",
    ]
    # Detailed view
    fields = [("container", "connection")]


@admin.register(DContainer)
class DContainerAdmin(admin.ModelAdmin):
    def parent_rockon_name(self, obj):
        if obj.rockon:
            return obj.rockon.name
        else:
            return None

    def parent_dimage_name(self, obj):
        if obj.dimage:
            return obj.dimage.name
        else:
            return None

    def has_options(self, obj) -> bool:
        if ContainerOption.objects.filter(container=obj).exists():
            return True
        else:
            return False

    def has_args(self, obj) -> bool:
        if DContainerArgs.objects.filter(container=obj).exists():
            return True
        else:
            return False

    def has_env(self, obj) -> bool:
        if DContainerEnv.objects.filter(container=obj).exists():
            return True
        else:
            return False

    def has_device(self, obj) -> bool:
        if DContainerDevice.objects.filter(container=obj).exists():
            return True
        else:
            return False

    def has_label(self, obj) -> bool:
        if DContainerLabel.objects.filter(container=obj).exists():
            return True
        else:
            return False

    def has_network(self, obj) -> bool:
        if DContainerNetwork.objects.filter(container=obj).exists():
            return True
        else:
            return False

    has_options.boolean = True
    has_args.boolean = True
    has_env.boolean = True
    has_device.boolean = True
    has_label.boolean = True
    has_network.boolean = True
    # Overview list
    list_display = [
        "name",
        "parent_rockon_name",
        "parent_dimage_name",
        "has_options",
        "has_args",
        "has_env",
        "has_device",
        "has_label",
        "has_network",
        "launch_order",
        "uid",
    ]
    list_per_page = 15
    # Detailed view
    fields = [
        "name",
        ("rockon", "dimage"),
        "launch_order",
        "uid",
    ]
    inlines = [
        ContainerOptionAdminInline,
        DPortAdminInline,
        DContainerArgsAdminInline,
        DContainerEnvAdminInline,
        DContainerDeviceAdminInline,
        DContainerLabelAdminInline,
        DContainerLinkAdminInline,
        DContainerNetworkAdminInline,
    ]


class DCustomConfigAdminInline(admin.TabularInline):
    model = DCustomConfig


@admin.register(DCustomConfig)
class DCustomConfigAdmin(admin.ModelAdmin):
    def parent_rockon_name(self, obj):
        if obj.rockon:
            return obj.rockon.name
        else:
            return None

    # Overview list
    list_display = [
        "parent_rockon_name",
        "label",
        "key",
        "val",
        "description",
    ]
    # Detailed view
    fields = [
        "label",
        "description",
        ("key", "val"),
    ]


@admin.register(RockOn)
class RockOnAdmin(admin.ModelAdmin):
    # Overview list
    list_display = [
        "name",
        "description",
        "version",
        "ui_publish",
        "ui_port",
        "state",
        "status",
        "host_network",
    ]
    list_per_page = 10
    # Detailed view
    fields = [
        ("name", "version", "website"),
        "description",
        "more_info",
        ("ui", "https", "volume_add_support"),
        ("state", "status", "taskid", "link"),
    ]
    inlines = [DContainerAdminInline, DCustomConfigAdminInline]


@admin.register(SambaShare)
class SambaShareAdmin(admin.ModelAdmin):
    def has_custom_config(self, obj) -> bool:
        if SambaCustomConfig.objects.filter(smb_share=obj).exists():
            return True
        else:
            return False

    has_custom_config.boolean = True
    # Overview list
    list_display = [
        "path",
        "comment",
        "admin_users",
        "browsable",
        "read_only",
        "guest_ok",
        "time_machine",
        "shadow_copy",
        "snapshot_prefix",
        "has_custom_config",
        "share_name",
        "share_id",
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
        "subvol_name",
        "mnt_pt",
        "mount_status",
        "size",
        # "size_gb",
        "uuid",
        "owner",
        "group",
        "perms",
        "qgroup",
        "pqgroup",
        "pqgroup_exist",
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
        DVolumeAdminInline,
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
        "mnt_pt",
        "mount_status",
        "raid",
        "data_raid",
        "metadata_raid",
        "quotas_enabled",
        "uuid",
        "size",
        "free",
        # "toc",
        "compression",
        "mnt_options",
        "role",
        "has_missing_dev",
        "redundancy_exceeded",
    ]
    list_per_page = 15
    inlines = [DiskAdminInline, ShareAdminInline]


# Rock-ons
Rockon_Models = (DImage,)
admin.site.register(Rockon_Models)

# User/Group models
admin.site.register((User, Group, OauthApp))
