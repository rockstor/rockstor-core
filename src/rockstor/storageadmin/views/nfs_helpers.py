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
from storageadmin.models import (Share, NFSExport, NFSExportGroup)
from storageadmin.util import handle_exception
from system.osi import (refresh_nfs_exports, nfs4_mount_teardown)

def client_input(export):
    eg = export.export_group
    ci = {'client_str': eg.host_str,
          'option_list': ('%s,%s,%s' % (eg.editable, eg.syncable,
                                        eg.mount_security))}
    if (eg.nohide):
        ci['option_list'] = ('%s,nohide' % ci['option_list'])
    ci['mnt_pt'] = export.mount.replace(settings.NFS_EXPORT_ROOT,
                                        settings.MNT_PT)
    if (eg.admin_host is not None):
        ci['admin_host'] = eg.admin_host
    return ci

def create_nfs_export_input(exports):
    exports_d = {}
    for e in exports:
        e_list = []
        export_pt = ('%s%s' % (settings.NFS_EXPORT_ROOT, e.share.name))
        if (e.export_group.nohide):
            snap_name = e.mount.split('/')[-1]
            export_pt = ('%s/%s' % (export_pt, snap_name))
        if (export_pt in exports_d):
            e_list = exports_d[export_pt]
        e_list.append(client_input(e))
        exports_d[export_pt] = e_list
    return exports_d

def parse_options(request):
    options = {
        'host_str': '*',
        'editable': 'ro',
        'syncable': 'async',
        'mount_security': 'insecure',
        }
    if ('host_str' in request.DATA):
        options['host_str'] = request.DATA['host_str']
    if ('mod_choice' in request.DATA):
        options['editable'] = request.DATA['mod_choice']
    if ('sync_choice' in request.DATA):
        options['syncable'] = request.DATA['sync_choice']
    if ('admin_host' in request.DATA):
        options['admin_host'] = request.DATA['admin_host']
    return options

def dup_export_check(share, host_str, request, export_id=None):
    for e in NFSExport.objects.filter(share=share):
        if (e.export_group.host_str == host_str):
            if (e.export_group.id == export_id):
                continue
            e_msg = ('An export already exists for the host string: %s' %
                     host_str)
            handle_exception(Exception(e_msg), request)

def validate_export_group(export_id, request):
    try:
        return NFSExportGroup.objects.get(id=export_id)
    except:
        e_msg = ('NFS export with id: %d does not exist' % export_id)
        handle_exception(Exception(e_msg), request)

def refresh_wrapper(exports, request, logger):
    try:
        refresh_nfs_exports(exports)
    except Exception, e:
        e_msg = ('Unable to delete the export because it is in use.'
                 ' Try again Later')
        logger.exception(e)
        handle_exception(Exception(e_msg), request)

def teardown_wrapper(export_pt, request, logger):
    try:
        nfs4_mount_teardown(export_pt)
    except Exception, e:
        e_msg = ('Unable to delete the export(%s) because it is '
                 'in use' % (export_pt))
        logger.exception(e)
        handle_exception(Exception(e_msg), request)
