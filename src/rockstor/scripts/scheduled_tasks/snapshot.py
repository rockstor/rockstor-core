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

import sys
import json
from datetime import datetime
import crontabwindow  # load crontabwindow module
from storageadmin.models import Share, Snapshot
from smart_manager.models import Task, TaskDefinition
from cli.api_wrapper import APIWrapper
from django.utils.timezone import utc
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def validate_snap_meta(meta):
    if type(meta) != dict:
        raise Exception("meta must be a dictionary, not %s" % type(meta))
    if "prefix" not in meta:
        raise Exception("prefix missing from meta. %s" % meta)
    if "share" not in meta:
        raise Exception("share missing from meta. %s" % meta)
    if meta["share"].isdigit():
        if not Share.objects.filter(id=meta["share"]).exists():
            raise Exception(
                "Non-existent Share id (%s) in meta. %s" % (meta["share"], meta)
            )
    else:
        # TODO: this else clause should be removed in #1854
        if not Share.objects.filter(name=meta["share"]).exists():
            raise Exception(
                "share ({}) in meta {} doesnt exist".format(meta["share"], meta)
            )
    if "max_count" not in meta:
        raise Exception("max_count missing from meta. %s" % meta)
    try:
        max_count = int(float(meta["max_count"]))
    except:
        raise Exception("max_count is not an integer. %s" % meta)
    if max_count < 1:
        raise Exception("max_count must atleast be 1, not %d" % max_count)
    if "visible" not in meta or type(meta["visible"]) != bool:
        meta["visible"] = False
    if "writable" not in meta or type(meta["writable"]) != bool:
        meta["writable"] = False
    return meta


# Deletes overflowing snapshots beyond max_count sorted by their id(implicitly
# create time). stop on first failure. Can be called safely with < max_count
# snapshots, just returns true in that case.
def delete(aw, share, snap_type, prefix, max_count):
    snapshots = Snapshot.objects.filter(
        share=share, snap_type=snap_type, name__startswith=prefix
    ).order_by("-id")
    for snap in snapshots[max_count:]:
        try:
            url = "shares/{}/snapshots/{}".format(share.id, snap.name)
            aw.api_call(url, data=None, calltype="delete", save_error=False)
        except Exception as e:
            logger.error(
                "Failed to delete old snapshots exceeding the "
                "maximum count(%d)" % max_count
            )
            logger.exception(e)
            return False
    return True


def main():
    tid = int(sys.argv[1])
    cwindow = sys.argv[2] if len(sys.argv) > 2 else "*-*-*-*-*-*"
    if crontabwindow.crontab_range(cwindow):
        # Performance note: immediately check task execution time/day window
        # range to avoid other calls
        tdo = TaskDefinition.objects.get(id=tid)
        stype = "task_scheduler"
        aw = APIWrapper()
        if tdo.task_type != "snapshot":
            logger.error("task_type(%s) is not snapshot." % tdo.task_type)
            return
        meta = json.loads(tdo.json_meta)
        validate_snap_meta(meta)

        # to keep backwards compatibility, allow for share to be either
        # name or id and migrate the metadata. To be removed in #1854
        try:
            share = Share.objects.get(id=meta["share"])
        except ValueError:
            share = Share.objects.get(name=meta["share"])
            meta["share"] = share.id
            tdo.json_meta = json.dumps(meta)
            tdo.save()

        max_count = int(float(meta["max_count"]))
        prefix = "%s_" % meta["prefix"]

        now = datetime.utcnow().replace(second=0, microsecond=0, tzinfo=utc)
        t = Task(task_def=tdo, state="started", start=now)

        snap_created = False
        t.state = "error"
        try:
            name = "%s_%s" % (
                meta["prefix"],
                datetime.now().strftime(settings.SNAP_TS_FORMAT),
            )
            url = "shares/{}/snapshots/{}".format(share.id, name)
            # only create a new snap if there's no overflow situation. This
            # prevents runaway snapshot creation beyond max_count+1.
            if delete(aw, share, stype, prefix, max_count):
                data = {
                    "snap_type": stype,
                    "uvisible": meta["visible"],
                    "writable": meta["writable"],
                }
                headers = {"content-type": "application/json"}
                aw.api_call(
                    url, data=data, calltype="post", headers=headers, save_error=False
                )
                logger.debug("created snapshot at %s" % url)
                t.state = "finished"
                snap_created = True
        except Exception as e:
            logger.error("Failed to create snapshot at %s" % url)
            logger.exception(e)
        finally:
            t.end = datetime.utcnow().replace(tzinfo=utc)
            t.save()

        # best effort pruning without erroring out. If deletion fails, we'll
        # have max_count+1 number of snapshots and it would be dealt with on
        # the next round.
        if snap_created:
            delete(aw, share, stype, prefix, max_count)
    else:
        logger.debug(
            "Cron scheduled task not executed because outside time/day window ranges"
        )


if __name__ == "__main__":
    # takes two arguments. taskdef object id and crontabwindow.
    main()
