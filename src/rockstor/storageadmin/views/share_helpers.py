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

from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from storageadmin.models import (Share, Snapshot, SFTP)
from smart_manager.models import ShareUsage
from fs.btrfs import (mount_share, mount_snap, is_mounted,
                      umount_root, shares_info, volume_usage, snaps_info,
                      qgroup_create, update_quota)
from storageadmin.util import handle_exception

import logging
logger = logging.getLogger(__name__)


def helper_mount_share(share, mnt_pt=None):
    if not share.is_mounted:
        if mnt_pt is None:
            mnt_pt = ('%s%s' % (settings.MNT_PT, share.name))
        mount_share(share, mnt_pt)


def validate_share(sname, request):
    try:
        return Share.objects.get(name=sname)
    except:
        e_msg = ('Share with name: %s does not exist' % sname)
        handle_exception(Exception(e_msg), request)


def sftp_snap_toggle(share, mount=True):
    for snap in Snapshot.objects.filter(share=share, uvisible=True):
        mnt_pt = ('%s/%s/%s/.%s' % (settings.SFTP_MNT_ROOT,
                                    share.owner, share.name,
                                    snap.name))
        if (mount and not is_mounted(mnt_pt)):
            mount_snap(share, snap.name, mnt_pt)
        elif (is_mounted(mnt_pt) and not mount):
            umount_root(mnt_pt)


def toggle_sftp_visibility(share, snap_name, on=True):
    if (not SFTP.objects.filter(share=share).exists()):
        return

    mnt_pt = ('%s/%s/%s/.%s' % (settings.SFTP_MNT_ROOT, share.owner,
                                share.name, snap_name))
    if (on):
        if (not is_mounted(mnt_pt)):
            mount_snap(share, snap_name, mnt_pt)
    else:
        umount_root(mnt_pt)


def import_shares(pool, request):
    # Establish known shares/subvols within our db for the given pool:
    shares_in_db = [s_on_disk.name for s_on_disk in Share.objects.filter(pool=pool)]
    # Find the actual/current shares/subvols within the given pool:
    shares_on_disk = shares_info(pool)
    # Delete db Share object if it is no longer found on disk.
    for s_in_db in shares_in_db:
        if (s_in_db not in shares_on_disk):
            Share.objects.get(pool=pool, name=s_in_db).delete()
    for s_on_disk in shares_on_disk:
        if (s_on_disk in shares_in_db):
            share = Share.objects.get(name=s_on_disk)
            share.qgroup = shares_on_disk[s_on_disk]
            rusage, eusage, pqgroup_rusage, pqgroup_eusage = \
                volume_usage(pool, share.qgroup, share.pqgroup)
            ts = datetime.utcnow().replace(tzinfo=utc)
            if (rusage != share.rusage or eusage != share.eusage or
               pqgroup_rusage != share.pqgroup_rusage or
               pqgroup_eusage != share.pqgroup_eusage):
                share.rusage = rusage
                share.eusage = eusage
                share.pqgroup_rusage = pqgroup_rusage
                share.pqgroup_eusage = pqgroup_eusage
                su = ShareUsage(name=s_on_disk, r_usage=rusage, e_usage=eusage,
                                ts=ts)
                su.save()
            else:
                try:
                    su = ShareUsage.objects.filter(name=s_on_disk).latest('id')
                    su.ts = ts
                    su.count += 1
                except ShareUsage.DoesNotExist:
                    su = ShareUsage(name=s_on_disk, r_usage=rusage,
                                    e_usage=eusage, ts=ts)
                finally:
                    su.save()
            share.save()
            continue
        try:
            cshare = Share.objects.get(name=s_on_disk)
            cshares_d = shares_info(cshare.pool)
            if (s_on_disk in cshares_d):
                e_msg = ('Another pool(%s) has a Share with this same '
                         'name(%s) as this pool(%s). This configuration '
                         'is not supported. You can delete one of them '
                         'manually with this command: '
                         'btrfs subvol delete %s[pool name]/%s' %
                         (cshare.pool.name, s_on_disk, pool.name, settings.MNT_PT, s_on_disk))
                handle_exception(Exception(e_msg), request)
            else:
                cshare.pool = pool
                cshare.qgroup = shares_on_disk[s_on_disk]
                cshare.size = pool.size
                cshare.subvol_name = s_on_disk
                cshare.rusage, cshare.eusage,
                cshare.pqgroup_rusage, cshare.pqgroup_eusage = \
                    volume_usage(pool, cshare.qgroup, cshare.pqgroup)
                cshare.save()
        except Share.DoesNotExist:
            pqid = qgroup_create(pool)
            update_quota(pool, pqid, pool.size * 1024)
            nso = Share(pool=pool, qgroup=shares_on_disk[s_on_disk], pqgroup=pqid, name=s_on_disk,
                        size=pool.size, subvol_name=s_on_disk)
            nso.save()
        mount_share(nso, '%s%s' % (settings.MNT_PT, s_on_disk))


def import_snapshots(share):
    snaps_d = snaps_info('%s%s' % (settings.MNT_PT, share.pool.name),
                         share.name)
    snaps = [s.name for s in Snapshot.objects.filter(share=share)]
    for s in snaps:
        if (s not in snaps_d):
            Snapshot.objects.get(share=share, name=s).delete()
    for s in snaps_d:
        if (s in snaps):
            so = Snapshot.objects.get(share=share, name=s)
        else:
            so = Snapshot(share=share, name=s, real_name=s,
                          writable=snaps_d[s][1], qgroup=snaps_d[s][0])
        rusage, eusage = volume_usage(share.pool, snaps_d[s][0])
        ts = datetime.utcnow().replace(tzinfo=utc)
        if (rusage != so.rusage or eusage != so.eusage):
            so.rusage = rusage
            so.eusage = eusage
            su = ShareUsage(name=s, r_usage=rusage, e_usage=eusage, ts=ts)
            su.save()
        else:
            try:
                su = ShareUsage.objects.filter(name=s).latest('id')
                su.ts = ts
                su.count += 1
            except ShareUsage.DoesNotExist:
                su = ShareUsage(name=s, r_usage=rusage, e_usage=eusage,
                                ts=ts)
            finally:
                su.save()
        so.save()
