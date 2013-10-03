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

from django.conf import settings
from storageadmin.models import (Share, NFSExport)


def client_input(export):
    ci = {'client_str': export.host_str,
          'option_list': ('%s,%s,%s,no_root_squash' %
                          (export.editable, export.syncable,
                           export.mount_security))}
    if (export.nohide):
        ci['option_list'] = ('%s,nohide' % ci['option_list'])
    ci['mnt_pt'] = export.mount.replace(settings.NFS_EXPORT_ROOT,
                                        settings.MNT_PT)
    return ci

def create_nfs_export_input(cur_export):
    exports = {}
    for e in NFSExport.objects.all():
        e_list = []
        export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, e.share.name))
        if (e.nohide):
            snap_name = e.mount.split(e.share.name + '_')[-1]
            export_pt = ('%s/%s' % (export_pt, snap_name))
            if (e.share.id == cur_export.share.id and
                cur_export.enabled is False):
                exports[export_pt] = []
                continue

        if (export_pt in exports):
            e_list = exports[export_pt]

        if (cur_export.id == e.id):
            if (cur_export.enabled is True):
                e_list.append(client_input(cur_export))
        else:
            e_list.append(client_input(e))
        exports[export_pt] = e_list
    return exports
