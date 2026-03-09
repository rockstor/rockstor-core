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

from os import stat, stat_result
from stat import S_IMODE

from huey.api import Task
from huey.contrib.djhuey import db_task, HUEY
from rest_framework.response import Response
from django.db import transaction
from storageadmin.models import Share
from storageadmin.serializers import ShareSerializer
from fs.btrfs import mount_share, get_property
from storageadmin.util import handle_exception
from storageadmin.views import ShareListView
from storageadmin.views.scheduling_helpers import is_pending_task
from system.acl import acl_change_manager, chown_or_chmod_active
from system.users import user_name, group_name


class ShareACLView(ShareListView):
    @transaction.atomic
    def post(self, request, sid):
        with self._handle_exception(request):
            share = Share.objects.get(id=sid)
            current_taskid = share.taskid
            mnt_pt = share.mnt_pt
            # Sanity check on current_taskid - ignore if no evidence of ongoing task.
            if current_taskid is not None:
                hi = HUEY
                task_status = "unknown"
                # Enqueue tasks are pending pre execution.
                # There is a 1 to 3 second "pending" status for Huey tasks
                if is_pending_task(hi, current_taskid):
                    task_status = "pending"
                # Executing tasks are no longer pending.
                # Huey has limitations on feedback regarding executing tasks.
                # I.e. task_status = hi.result(current_taskid, preserve = True)
                # Returns None for both ongoing and non-existent task ids.
                # See: https://github.com/coleifer/huey/issues/488
                # CHECK FOR ONGOING RELATED ACTIVITY
                if chown_or_chmod_active(mnt_pt=mnt_pt):
                    task_status = "running"
                if task_status != "unknown":
                    e_msg = f"Change task, status ({task_status}), found for ({share.name}): task id ({current_taskid}) should complete in a few minutes."
                    handle_exception(Exception(e_msg), request)
            # OWNER, GROUP, AND PERMISSIONS UPDATE.
            # Get the on disk subvol info.
            was_unmounted: bool = False
            if not share.is_mounted:
                was_unmounted = True
                # Filesystem rights access/changes require a mounted filesystem/subvol.
                mount_share(share, mnt_pt)
            share_stat: stat_result = stat(mnt_pt)
            subvol_owner = user_name(share_stat.st_uid)
            subvol_group = group_name(share_stat.st_gid)
            subvol_perms = oct(S_IMODE(share_stat.st_mode))[2:].zfill(3)
            # Establish the requested owner, group, perms, defaulting to on disk info.
            options: dict[str, str | bool] = {
                "owner": request.data.get("owner", subvol_owner),
                "group": request.data.get("group", subvol_group),
                "perms": request.data.get("perms", subvol_perms),
                # Owner and group recursive (unimplemented in Web-UI)
                "orecursive": request.data.get("orecursive", True),
                # Permissions recursive (unimplemented in Web-UI)
                "precursive": request.data.get("precursive", True),
            }
            # Align Share DB with requested owner, group, perms: if required.
            changed_fields: list[str] = []
            if share.owner != options["owner"]:
                share.owner = options["owner"]
                changed_fields.append("owner")
            if share.group != options["group"]:
                share.group = options["group"]
                changed_fields.append("group")
            if share.perms != options["perms"]:
                share.perms = options["perms"]
                changed_fields.append("perms")
            # COMPRESSION SETTING FROM DISK
            # Opportunistically update DB Share.compression_algo.
            compression: str = get_property(mnt_pt, "compression")
            if share.compression_algo != compression:
                share.compression_algo = compression
                changed_fields.append("compression_algo")
            # TASK INVOCATION
            task_result_handle: Task = acl_change_manager(
                mnt_pt,
                owner=options["owner"],
                group=options["group"],
                og_recursive=options["orecursive"],
                perms=options["perms"],
                p_recursive=options["precursive"],
                was_unmounted=was_unmounted,
            )
            # Store above task ID in Share; overwriting any "unknown" (orphaned) value.
            share.taskid = task_result_handle.id
            changed_fields.append("taskid")
            share.save(update_fields=changed_fields)
            return Response(ShareSerializer(share).data)


@db_task()
def clear_taskid(taskid: str | None = None):
    """
    Find Share with matching taskid to clear and update DB.
    Called by @HUEY.signal(SIGNAL_COMPLETE) task_completed(signal, task) for relevant
    tasks.
    """
    if taskid is None:
        return None
    try:
        # Assumes there can be only one Share with this taskid.
        share = Share.objects.get(taskid=taskid)
    except Share.DoesNotExist:
        return None
    share.taskid = None
    share.save(update_fields=["taskid"])
    return None
