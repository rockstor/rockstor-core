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
from storageadmin.models import Disk, Pool, Share, Snapshot
from storageadmin.models.rockon import RockOn, DImage, DContainer, DContainerLink, DContainerNetwork, DPort, DVolume, ContainerOption, DContainerArgs, DCustomConfig, DContainerEnv, DContainerDevice, DContainerLabel
from storageadmin.models.user import User, Group
# https://docs.djangoproject.com/en/4.2/ref/contrib/admin/

@admin.register(Disk)
class DiskAdmin(admin.ModelAdmin):
    pass

@admin.register(Pool)
class PoolAdmin(admin.ModelAdmin):
    pass

@admin.register(Share)
class ShareAdmin(admin.ModelAdmin):
    pass

@admin.register(Snapshot)
class SnapshotAdmin(admin.ModelAdmin):
    pass

# Rock-ons
Rockon_Models = (RockOn, DImage, DContainer, DContainerLink, DContainerNetwork, DPort, DVolume, ContainerOption, DContainerArgs, DCustomConfig, DContainerEnv, DContainerDevice, DContainerLabel)
admin.site.register(Rockon_Models)

# User/Group models
admin.site.register((User, Group))



