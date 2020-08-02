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
from storageadmin.models import Pool
from system.osi import run_command
from fs.btrfs import mount_root

BTRFS = "/usr/sbin/btrfs"


def main():
    for p in Pool.objects.all():
        try:
            print("Processing pool(%s)" % p.name)
            mnt_pt = mount_root(p)
            o, e, rc = run_command([BTRFS, "qgroup", "show", "-p", mnt_pt], throw=False)
            if rc != 0:
                print("Quotas not enabled on pool(%s). Skipping it." % p.name)
                continue

            qgroup_ids = []
            for l in o:
                if (
                    re.match("qgroupid", l) is not None
                    or re.match("-------", l) is not None
                ):
                    continue
                cols = l.strip().split()
                if len(cols) != 4:
                    print("Ignoring unexcepted line(%s)." % l)
                    continue
                if cols[3] == "---":
                    print("No parent qgroup for %s" % l)
                    continue
                qgroup_ids.append(cols[3])

            for q in qgroup_ids:
                print("relaxing the limit on qgroup %s" % q)
                run_command([BTRFS, "qgroup", "limit", "none", q, mnt_pt])

            print("Finished processing pool(%s)" % p.name)
        except Exception as e:
            print(
                "Exception while qgroup-maxout of Pool(%s): %s" % (p.name, e.__str__())
            )


if __name__ == "__main__":
    main()
