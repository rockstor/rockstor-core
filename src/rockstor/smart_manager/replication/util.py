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

import time
from storageadmin.exceptions import RockStorAPIException
from storageadmin.models import Appliance, Share
from cli import APIWrapper
import logging

logger = logging.getLogger(__name__)


class ReplicationMixin(object):
    def validate_src_share(self, sender_uuid: str, sname: str):
        url = "https://"
        if self.raw is None:
            a = Appliance.objects.get(uuid=sender_uuid)
            url = f"{url}{a.ip}:{a.mgmt_port}"
            self.raw = APIWrapper(
                client_id=a.client_id, client_secret=a.client_secret, url=url
            )
        # TODO: update url to include senders shareId as sname is now invalid
        return self.raw.api_call(url=f"shares/{sname}")

    def update_replica_status(self, rtid: int, data):
        try:
            url = f"sm/replicas/trail/{rtid}"
            return self.law.api_call(url, data=data, calltype="put")
        except Exception as e:
            msg = f"Exception while updating replica({url}) status to {data['status']}: {e.__str__()}"
            raise Exception(msg)

    def disable_replica(self, rid: int):
        try:
            url = f"sm/replicas/{rid}"
            headers = {
                "content-type": "application/json",
            }
            return self.law.api_call(
                url,
                data={
                    "enabled": False,
                },
                calltype="put",
                save_error=False,
                headers=headers,
            )
        except Exception as e:
            msg = f"Exception while disabling replica({url}): {e.__str__()}"
            raise Exception(msg)

    def create_replica_trail(self, rid: int, snap_name: str):
        logger.debug(f"Replication create_replica_trail(rid={rid}, snap_name={snap_name})")
        url = f"sm/replicas/trail/replica/{rid}"
        return self.law.api_call(
            url,
            data={
                "snap_name": snap_name,
            },
            calltype="post",
            save_error=False,
        )

    def rshare_id(self, sname: str) -> int:
        url = f"sm/replicas/rshare/{sname}"
        rshare = self.law.api_call(url, save_error=False)
        return rshare["id"]

    def create_rshare(self, data) -> int:
        try:
            url = "sm/replicas/rshare"
            rshare = self.law.api_call(
                url, data=data, calltype="post", save_error=False
            )
            return rshare["id"]
        except RockStorAPIException as e:
            # Note replica_share.py post() generates this exception message.
            if e.detail == f"Replicashare({data['share']}) already exists.":  # noqa E501
                return self.rshare_id(data["share"])
            raise e

    def create_receive_trail(self, rid: int, data) -> int:
        url = f"sm/replicas/rtrail/rshare/{rid}"
        rt = self.law.api_call(url, data=data, calltype="post", save_error=False)
        return rt["id"]

    def update_receive_trail(self, rtid: int, data):
        url = f"sm/replicas/rtrail/{rtid}"
        try:
            return self.law.api_call(url, data=data, calltype="put", save_error=False)
        except Exception as e:
            msg = f"Exception while updating receive trail({url}): {e.__str__()}"
            raise Exception(msg)

    def prune_trail(self, url: str, days: int = 7):
        try:
            data = {
                "days": days,
            }
            return self.law.api_call(
                url, data=data, calltype="delete", save_error=False
            )
        except Exception as e:
            msg = f"Exception while pruning trail for url({url}): {e.__str__()}"
            raise Exception(msg)

    def prune_receive_trail(self, ro):
        url = f"sm/replicas/rtrail/rshare/{ro.id}"
        return self.prune_trail(url)

    def prune_replica_trail(self, ro):
        url = f"sm/replicas/trail/replica/{ro.id}"
        return self.prune_trail(url)

    def create_snapshot(self, sname: str, snap_name: str, snap_type="replication"):
        try:
            share = Share.objects.get(name=sname)
            url = f"shares/{share.id}/snapshots/{snap_name}"
            return self.law.api_call(
                url,
                data={
                    "snap_type": snap_type,
                },
                calltype="post",
                save_error=False,
            )
        except RockStorAPIException as e:
            # Note snapshot.py _create() generates this exception message.
            if (
                e.detail
                == f"Snapshot ({snap_name}) already exists for the share ({sname})."
            ):
                return logger.debug(e.detail)
            raise e

    def update_repclone(self, sname: str, snap_name: str):
        """
        Call the dedicated create_repclone via it's url to supplant our
        share with the given snapshot. Intended for use in receive.py to turn
        the oldest snapshot into an existing share via unmount, mv, mount
        cycle.
        :param sname: Existing share-name
        :param snap_name: Name of snapshot to supplant given share with.
        :return: False if there is a failure.
        """
        try:
            share = Share.objects.get(name=sname)
            url = f"shares/{share.id}/snapshots/{snap_name}/repclone"
            return self.law.api_call(url, calltype="post", save_error=False)
        except RockStorAPIException as e:
            # TODO: need to look further at the following as command repclone
            #  (snapshot.py post) catches Snapshot.DoesNotExist.
            #  and doesn't appear to call _delete_snapshot()
            # Note snapshot.py _delete_snapshot() generates this exception msg.
            if e.detail == f"Snapshot name ({snap_name}) does not exist.":
                logger.debug(e.detail)
                return False
            raise e

    def delete_snapshot(self, sname: str, snap_name: str):
        try:
            share = Share.objects.get(name=sname)
            url = f"shares/{share.id}/snapshots/{snap_name}"
            self.law.api_call(url, calltype="delete", save_error=False)
            return True
        except RockStorAPIException as e:
            # Note snapshot.py _delete_snapshot() generates this exception msg.
            if e.detail == f"Snapshot name ({snap_name}) does not exist.":
                logger.debug(e.detail)
                return False
            raise e

    def create_share(self, sname: str, pool: str):
        print(f"Replication 'create_share' called with sname {sname}, pool {pool}")
        try:
            url = "shares"
            data = {
                "pool": pool,
                "replica": True,
                "sname": sname,
            }
            headers = {
                "content-type": "application/json",
            }
            return self.law.api_call(
                url, data=data, calltype="post", headers=headers, save_error=False
            )
        except RockStorAPIException as e:
            # Note share.py post() generates this exception message.
            if e.detail == f"Share ({sname}) already exists. Choose a different name.":
                return logger.debug(e.detail)
            raise e

    def refresh_snapshot_state(self):
        try:
            return self.law.api_call(
                "commands/refresh-snapshot-state",
                data=None,
                calltype="post",
                save_error=False,
            )
        except Exception as e:
            logger.error(f"Exception while refreshing Snapshot state: {e.__str__()}")

    def refresh_share_state(self):
        try:
            return self.law.api_call(
                "commands/refresh-share-state",
                data=None,
                calltype="post",
                save_error=False,
            )
        except Exception as e:
            logger.error(f"Exception while refreshing Share state: {e.__str__()}")

    def humanize_bytes(
        self,
        num: int,
        units=(
            "Bytes",
            "KB",
            "MB",
            "GB",
        ),
    ):
        """
        Recursive routine to establish and then return the most appropriate
        num expression given the contents of units. Ie 1023 Bytes or 4096 KB
        :param num: Assumed to be in Byte units.
        :param units: list of units to recurse through
        :return: "1023 Bytes" or "4.28 KB" etc given num=1023 or num=4384 )
        """
        if num < 1024 or len(units) == 1:
            return f"{num:.2f} {units[0]}"
        return self.humanize_bytes(num / 1024, units[1:])

    def size_report(self, num: int, t0):
        t1 = time.time()
        dsize = self.humanize_bytes(float(num))
        drate = self.humanize_bytes(float(num / (t1 - t0)))
        return dsize, drate
