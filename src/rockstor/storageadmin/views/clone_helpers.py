"""
Copyright (c) 2012-2020 Rockstor, Inc. <http://rockstor.com>
This file is part of Rockstor.

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

from storageadmin.models import Share, Snapshot
from storageadmin.util import handle_exception
from fs.btrfs import (
    add_clone,
    share_id,
    update_quota,
    mount_share,
    qgroup_create,
    set_property,
    remove_share,
    share_pqgroup_assign,
    is_subvol,
)
from rest_framework.response import Response
from storageadmin.serializers import ShareSerializer
import re
import shutil
from django.conf import settings
from system.osi import run_command

# The following model/db default setting is also used when quotas are disabled.
PQGROUP_DEFAULT = settings.MODEL_DEFS["pqgroup"]


def create_repclone(share, request, logger, snapshot):
    """
    Variant of create_clone but where the share already exists and is to be
    supplanted by a snapshot which is effectively moved into the shares prior
    position, both in the db and on the file system. This is achieved thus:
    Unmount target share - (via remove_share()).
    Btrfs subvol delete target share (via remove_share()).
    Remove prior target share mount point (dir).
    Move snap source to target share's former location (becomes share on disk).
    Update existing target share db entry with source snap's qgroup / usage.
    Remove source snap's db entry: updated share db entry makes it redundant.
    Remount share (which now represents the prior snap's subvol relocated).
    :param share: Share object to be supplanted
    :param request:
    :param logger: Logger object to reference
    :param snapshot: Source snapshot/quirk share object to supplant target.
    :return: response of serialized share (in it's updated form)
    """
    try:
        logger.info(
            "Supplanting share ({}) with "
            "snapshot ({}).".format(share.name, snapshot.name)
        )
        # We first strip our snapshot.name of any path as when we encounter the
        # initially created receive subvol it is identified as a share with a
        # snapshots location as it's subvol name (current quirk of import sys).
        # E.g. first receive subvol/share-in-snapdir name example:
        # ".snapshots/C583C37F-...1712B_sharename/sharename_19_replication_1".
        # Subsequent more regular snapshots (in db as such) are named thus:
        # "sharename_19_replication_2" or "sharename_19_replication_2" and on.
        # The 19 in the above names is the generation of the replication task.
        #
        # Normalise source name across initial quirk share & subsequent snaps.
        source_name = snapshot.name.split("/")[-1]
        # Note in the above we have to use Object.name for polymorphism, but
        # our share is passed by it's subvol (potential fragility point).
        snap_path = "{}/.snapshots/{}/{}".format(
            share.pool.mnt_pt, share.name, source_name
        ).replace("//", "/")
        # e.g. for above: /mnt2/poolname/.snapshots/sharename/snapname
        # or /.snapshots/sharename/snapname for system pool shares
        share_path = ("{}/{}".format(share.pool.mnt_pt, share.name)).replace("//", "/")
        # e.g. for above: /mnt2/poolname/sharename or /sharename for system pool shares
        # Passed db snap assured by caller but this does not guarantee on disk.
        if not is_subvol(snap_path):
            raise Exception(
                "Subvol with path ({}) does not exist. Aborting "
                "replacement of share with path ({}).".format(snap_path, share_path)
            )
        # unmounts and then subvol deletes our on disk share
        remove_share(share.pool, share.name, PQGROUP_DEFAULT)
        # Remove read only flag on our snapshot subvol
        set_property(snap_path, "ro", "false", mount=False)
        # Ensure removed share path is clean, ie remove mount point.
        run_command(["/usr/bin/rm", "-rf", share_path], throw=False)
        # Now move snapshot to prior shares location. Given both a share and
        # a snapshot are subvols, we effectively promote the snap to a share.
        logger.info(
            "Moving snapshot ({}) to prior share's pool location ({})".format(
                snap_path, share_path
            )
        )
        shutil.move(snap_path, share_path)
        # This should have re-established our just removed subvol.
        # Supplant share db info with snap info to reflect new on disk state.
        share.qgroup = snapshot.qgroup
        share.rusage = snapshot.rusage
        share.eusage = snapshot.eusage
        share.save()
        # delete our now redundant snapshot/quirky share db entry
        snapshot.delete()
        # update our share's quota
        update_quota(share.pool, share.pqgroup, share.size * 1024)
        # mount our newly supplanted share
        # We independently mount all shares, data pool or system pool, in /mnt2/name
        mnt_pt = "{}{}".format(settings.MNT_PT, share.name)
        mount_share(share, mnt_pt)
        return Response(ShareSerializer(share).data)
    except Exception as e:
        handle_exception(e, request)


def create_clone(share, new_name, request, logger, snapshot=None):
    # if snapshot is None, create clone of the share.
    # If it's not, then clone it.
    if re.match(settings.SHARE_REGEX + "$", new_name) is None:
        e_msg = (
            "Clone name is invalid. It must start with a letter and can "
            "contain letters, digits, _, . and - characters."
        )
        handle_exception(Exception(e_msg), request)
    if Share.objects.filter(name=new_name).exists():
        e_msg = "Another share with name ({}) already exists.".format(new_name)
        handle_exception(Exception(e_msg), request)
    if Snapshot.objects.filter(share=share, name=new_name).exists():
        e_msg = (
            "Snapshot with name ({}) already exists for the "
            "share ({}). Choose a different name."
        ).format(new_name, share.name)
        handle_exception(Exception(e_msg), request)

    try:
        share_name = share.subvol_name
        snap = None
        if snapshot is not None:
            snap = snapshot.real_name
        add_clone(share.pool, share_name, new_name, snapshot=snap)
        snap_id = share_id(share.pool, new_name)
        qgroup_id = "0/{}".format(snap_id)
        pqid = qgroup_create(share.pool)
        new_share = Share(
            pool=share.pool,
            qgroup=qgroup_id,
            pqgroup=pqid,
            name=new_name,
            size=share.size,
            subvol_name=new_name,
        )
        new_share.save()
        if pqid != PQGROUP_DEFAULT:
            update_quota(new_share.pool, pqid, new_share.size * 1024)
            share_pqgroup_assign(pqid, new_share)
        # Mount our new clone share.
        # We independently mount all shares, data pool or system pool, in /mnt2/name
        mnt_pt = "{}{}".format(settings.MNT_PT, new_name)
        mount_share(new_share, mnt_pt)
        return Response(ShareSerializer(new_share).data)
    except Exception as e:
        handle_exception(e, request)
