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
from storageadmin.models import (NFSExport, NFSExportGroup, Disk)
from storageadmin.util import handle_exception
from system.osi import (refresh_nfs_exports, nfs4_mount_teardown)
from share_helpers import validate_share
from fs.btrfs import (mount_share, is_share_mounted)


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


def create_adv_nfs_export_input(exports, request):
    exports_d = {}
    for e in exports:
        fields = e.split()
        if (len(fields) < 2):
            e_msg = ('Invalid exports input -- %s' % e)
            handle_exception(Exception(e_msg), request)
        share = fields[0].split('/')[-1]
        s = validate_share(share, request)
        mnt_pt = ('%s%s' % (settings.MNT_PT, s.name))
        if (not is_share_mounted(s.name)):
            pool_device = Disk.objects.filter(pool=s.pool)[0].name
            mount_share(s, pool_device, mnt_pt)
        exports_d[fields[0]] = []
        for f in fields[1:]:
            cf = f.split('(')
            if (len(cf) != 2 or cf[1][-1] != ')'):
                e_msg = ('Invalid exports input -- %s. offending '
                         'section: %s' % (e, f))
                handle_exception(Exception(e_msg), request)
            exports_d[fields[0]].append(
                {'client_str': cf[0], 'option_list': cf[1][:-1],
                 'mnt_pt': ('%s%s' % (settings.MNT_PT, share))})
    return exports_d


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
        'admin_host': None,
        }
    if ('host_str' in request.data):
        options['host_str'] = request.data['host_str']
    if ('mod_choice' in request.data and
        (request.data['mod_choice'] == 'ro' or
         request.data['mod_choice'] == 'rw')):
        options['editable'] = request.data['mod_choice']
    if ('sync_choice' in request.data and
        (request.data['sync_choice'] == 'sync' or
         request.data['sync_choice'] == 'async')):
        options['syncable'] = request.data['sync_choice']
    if ('admin_host' in request.data and
        len(request.data['admin_host']) > 0):
        options['admin_host'] = request.data['admin_host']
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
        e_msg = ('A lower level error occured while refreshing NFS exports. '
                 'Error: %s. This could be due to invalid input. '
                 'If so, correct your input and try again.' % e)
        logger.exception(e)
        handle_exception(Exception(e_msg), request)
