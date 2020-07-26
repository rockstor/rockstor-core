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
import re
from datetime import datetime
from django.utils.timezone import utc
from django.conf import settings
from storageadmin.models import Share, Snapshot, SFTP
from smart_manager.models import ShareUsage
from fs.btrfs import (
    mount_share,
    mount_snap,
    is_mounted,
    umount_root,
    shares_info,
    volume_usage,
    snaps_info,
    qgroup_create,
    update_quota,
    share_pqgroup_assign,
    qgroup_assign,
)
from storageadmin.util import handle_exception
from copy import deepcopy

import logging

logger = logging.getLogger(__name__)

NEW_ENTRY = True
UPDATE_TS = False
# The following model/db default setting is also used when quotas are disabled
# or when a Read-only state prevents creation of a new pqgroup.
PQGROUP_DEFAULT = settings.MODEL_DEFS["pqgroup"]


def helper_mount_share(share, mnt_pt=None):
    if not share.is_mounted:
        if mnt_pt is None:
            mnt_pt = "{}{}".format(settings.MNT_PT, share.name)
        mount_share(share, mnt_pt)


def validate_share(sname, request):
    try:
        return Share.objects.get(name=sname)
    except:
        e_msg = "Share with name ({}) does not exist.".format(sname)
        handle_exception(Exception(e_msg), request)


def sftp_snap_toggle(share, mount=True):
    for snap in Snapshot.objects.filter(share=share, uvisible=True):
        mnt_pt = "{}/{}/{}/.{}".format(
            settings.SFTP_MNT_ROOT, share.owner, share.name, snap.name
        )
        if mount and not is_mounted(mnt_pt):
            mount_snap(share, snap.name, snap.qgroup, mnt_pt)
        elif is_mounted(mnt_pt) and not mount:
            umount_root(mnt_pt)


def toggle_sftp_visibility(share, snap_name, snap_qgroup, on=True):
    if not SFTP.objects.filter(share=share).exists():
        return

    mnt_pt = "{}/{}/{}/.{}".format(
        settings.SFTP_MNT_ROOT, share.owner, share.name, snap_name
    )
    if on:
        if not is_mounted(mnt_pt):
            mount_snap(share, snap_name, snap_qgroup, mnt_pt)
    else:
        umount_root(mnt_pt)


def import_shares(pool, request):
    # Establish known shares/subvols within our db for the given pool:
    shares_in_pool_db = [s.name for s in Share.objects.filter(pool=pool)]
    # Find the actual/current shares/subvols within the given pool:
    # Limited to Rockstor relevant subvols ie shares and clones.
    shares_in_pool = shares_info(pool)
    # List of pool's share.pqgroups so we can remove inadvertent duplication.
    # All pqgroups are removed when quotas are disabled, combined with a part
    # refresh we could have duplicates within the db.
    share_pqgroups_used = []
    # Delete db Share object if it is no longer found on disk.
    for s_in_pool_db in shares_in_pool_db:
        if s_in_pool_db not in shares_in_pool:
            logger.debug(
                "Removing, missing on disk, share db entry ({}) from "
                "pool ({}).".format(s_in_pool_db, pool.name)
            )
            Share.objects.get(pool=pool, name=s_in_pool_db).delete()
    # Check if each share in pool also has a db counterpart.
    for s_in_pool in shares_in_pool:
        logger.debug("---- Share name = {}.".format(s_in_pool))
        if s_in_pool in shares_in_pool_db:
            logger.debug("Updating pre-existing same pool db share entry.")
            # We have a pool db share counterpart so retrieve and update it.
            share = Share.objects.get(name=s_in_pool, pool=pool)
            # Initially default our pqgroup value to db default of '-1/-1'
            # This way, unless quotas are enabled, all pqgroups will be
            # returned to db default.
            pqgroup = PQGROUP_DEFAULT
            if share.pool.quotas_enabled:
                # Quotas are enabled on our pool so we can validate pqgroup.
                if (
                    share.pqgroup == pqgroup
                    or not share.pqgroup_exist
                    or share.pqgroup in share_pqgroups_used
                ):
                    # we have a void '-1/-1' or non existent pqgroup or
                    # this pqgroup has already been seen / used in this pool.
                    logger.debug(
                        "#### replacing void, non-existent, or duplicate pqgroup."
                    )
                    pqgroup = qgroup_create(pool)
                    if pqgroup != PQGROUP_DEFAULT:
                        update_quota(pool, pqgroup, share.size * 1024)
                        share_pqgroup_assign(pqgroup, share)
                else:
                    # Our share's pqgroup looks OK so use it.
                    pqgroup = share.pqgroup
                # Record our use of this pqgroup to spot duplicates later.
                share_pqgroups_used.append(deepcopy(share.pqgroup))
            if share.pqgroup != pqgroup:
                # we need to update our share.pqgroup
                share.pqgroup = pqgroup
                share.save()
            share.qgroup = shares_in_pool[s_in_pool]
            rusage, eusage, pqgroup_rusage, pqgroup_eusage = volume_usage(
                pool, share.qgroup, pqgroup
            )
            if (
                rusage != share.rusage
                or eusage != share.eusage
                or pqgroup_rusage != share.pqgroup_rusage
                or pqgroup_eusage != share.pqgroup_eusage
            ):
                share.rusage = rusage
                share.eusage = eusage
                share.pqgroup_rusage = pqgroup_rusage
                share.pqgroup_eusage = pqgroup_eusage
                update_shareusage_db(s_in_pool, rusage, eusage)
            else:
                update_shareusage_db(s_in_pool, rusage, eusage, UPDATE_TS)
            share.save()
            continue
        try:
            logger.debug("No prior entries in scanned pool trying all pools.")
            # Test (Try) for an existing system wide Share db entry.
            cshare = Share.objects.get(name=s_in_pool)
            # Get a list of Rockstor relevant subvols (ie shares and clones)
            # for the prior existing db share entry's pool.
            cshares_d = shares_info(cshare.pool)
            if s_in_pool in cshares_d:
                e_msg = (
                    "Another pool ({}) has a share with this same "
                    "name ({}) as this pool ({}). This configuration "
                    "is not supported. You can delete one of them "
                    "manually with the following command: "
                    '"btrfs subvol delete {}[pool name]/{}" WARNING this '
                    "will remove the entire contents of that "
                    "subvolume."
                ).format(
                    cshare.pool.name, s_in_pool, pool.name, settings.MNT_PT, s_in_pool
                )
                handle_exception(Exception(e_msg), request)
            else:
                # Update the prior existing db share entry previously
                # associated with another pool.
                logger.debug("Updating prior db entry from another pool.")
                cshare.pool = pool
                cshare.qgroup = shares_in_pool[s_in_pool]
                cshare.size = pool.size
                cshare.subvol_name = s_in_pool
                (
                    cshare.rusage,
                    cshare.eusage,
                    cshare.pqgroup_rusage,
                    cshare.pqgroup_eusage,
                ) = volume_usage(pool, cshare.qgroup, cshare.pqgroup)
                cshare.save()
                update_shareusage_db(s_in_pool, cshare.rusage, cshare.eusage)
        except Share.DoesNotExist:
            logger.debug("Db share entry does not exist - creating.")
            # We have a share on disk that has no db counterpart so create one.
            # Retrieve new pool quota id for use in db Share object creation.
            # As the replication receive share is 'special' we tag it as such.
            replica = False
            share_name = s_in_pool
            if re.match(".snapshot", s_in_pool) is not None:
                # We have an initial replication share, non snap in .snapshots.
                # We could change it's name here but still a little mixing
                # of name and subvol throughout project.
                replica = True
                logger.debug(
                    "Initial receive quirk-subvol found: Importing "
                    "as share and setting replica flag."
                )
            qid = shares_in_pool[s_in_pool]
            pqid = qgroup_create(pool)
            if pqid != PQGROUP_DEFAULT:
                update_quota(pool, pqid, pool.size * 1024)
                qgroup_assign(qid, pqid, pool.mnt_pt)
            rusage, eusage, pqgroup_rusage, pqgroup_eusage = volume_usage(
                pool, qid, pqid
            )
            nso = Share(
                pool=pool,
                qgroup=qid,
                pqgroup=pqid,
                name=share_name,
                size=pool.size,
                subvol_name=s_in_pool,
                rusage=rusage,
                eusage=eusage,
                pqgroup_rusage=pqgroup_rusage,
                pqgroup_eusage=pqgroup_eusage,
                replica=replica,
            )
            nso.save()
            update_shareusage_db(s_in_pool, rusage, eusage)
            mount_share(nso, "{}{}".format(settings.MNT_PT, s_in_pool))


def import_snapshots(share):
    snaps_d = snaps_info(share.pool.mnt_pt, share.name)
    snaps = [s.name for s in Snapshot.objects.filter(share=share)]
    for s in snaps:
        if s not in snaps_d:
            logger.debug(
                "Removing, missing on disk, snapshot db entry ({}) "
                "from share ({}).".format(s, share.name)
            )
            Snapshot.objects.get(share=share, name=s).delete()
    for s in snaps_d:
        if s in snaps:
            so = Snapshot.objects.get(share=share, name=s)
        else:
            logger.debug(
                "Adding, missing in db, on disk snapshot ({}) "
                "against share ({}).".format(s, share.name)
            )
            so = Snapshot(
                share=share,
                name=s,
                real_name=s,
                writable=snaps_d[s][1],
                qgroup=snaps_d[s][0],
            )
        rusage, eusage = volume_usage(share.pool, snaps_d[s][0])
        if rusage != so.rusage or eusage != so.eusage:
            so.rusage = rusage
            so.eusage = eusage
            update_shareusage_db(s, rusage, eusage)
        else:
            update_shareusage_db(s, rusage, eusage, UPDATE_TS)
        so.save()


def update_shareusage_db(subvol_name, rusage, eusage, new_entry=True):
    """
    Creates a new share/subvol db usage entry, or updates an existing one with
    a new time stamp and count increment.
    The 'create new entry' mode is expected to be faster.
    :param subvol_name: share/subvol name
    :param rusage: Referenced/shared usage
    :param eusage: Exclusive usage
    :param new_entry: If True create a new entry with the passed params,
    otherwise attempt to update the latest (by id) entry with time and count.
    """
    ts = datetime.utcnow().replace(tzinfo=utc)
    if new_entry:
        su = ShareUsage(name=subvol_name, r_usage=rusage, e_usage=eusage, ts=ts)
        su.save()
    else:
        try:
            su = ShareUsage.objects.filter(name=subvol_name).latest("id")
            su.ts = ts
            su.count += 1
        except ShareUsage.DoesNotExist:
            su = ShareUsage(name=subvol_name, r_usage=rusage, e_usage=eusage, ts=ts)
        finally:
            su.save()
