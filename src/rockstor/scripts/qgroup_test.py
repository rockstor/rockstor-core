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
import os
import re
from storageadmin.models import Share
from system.osi import run_command
from fs.btrfs import share_usage
from cli.api_wrapper import APIWrapper
from storageadmin.exceptions import RockStorAPIException
import random

BTRFS = "/usr/sbin/btrfs"


def create_share(aw, sname, pool, size=1024 * 1024):
    try:
        url = "shares"
        data = {
            "pool": pool,
            "size": size,
            "sname": sname,
        }
        headers = {
            "content-type": "application/json",
        }
        return aw.api_call(
            url, data=data, calltype="post", headers=headers, save_error=False
        )
    except RockStorAPIException as e:
        if e.detail == ("Share(%s) already exists. Choose a different name" % sname):
            print(e.detail)
            return
        raise e


def resize_share(aw, sname, new_size):
    so = Share.objects.get(name=sname)
    url = "shares/%s" % sname
    data = {
        "size": new_size,
    }
    headers = {
        "content-type": "application/json",
    }
    aw.api_call(url, data=data, calltype="put", headers=headers, save_error=False)
    print("Share(%s) resized. Old size: %d New size: %d" % (sname, so.size, new_size))


def fill_up_share(pname, sname, chunk=(1024 * 1024 * 2)):
    so = Share.objects.get(name=sname)
    rusage, eusage = share_usage(so.pool, so.qgroup)
    print("Writing to Share(%s) until quota is exceeded." % sname)
    print("Share(%s) Size: %d Usage: %d" % (sname, so.size, rusage))
    spath = "/mnt2/%s/%s" % (pname, sname)
    file_indices = sorted(
        [int(f.split("-")[1]) for f in os.listdir(spath)], reverse=True
    )
    counter = 0
    if len(file_indices) > 0:
        counter = file_indices[0] + 1
    quota_exceeded = False
    while not quota_exceeded:
        fname = "%s/file-%d" % (spath, counter)
        one_mb = "s" * chunk
        try:
            with open(fname, "w") as ofo:
                for i in range(100):
                    ofo.write(one_mb)
        except IOError as e:
            if re.search("Disk quota exceeded", e.__str__()) is not None:
                print(e.__str__())
                quota_exceeded = True
            else:
                raise e

        run_command(["/usr/bin/sync"])
        rusage, eusage = share_usage(so.pool, so.qgroup)
        print("Share(%s) Size: %d Usage: %d" % (sname, so.size, rusage))
        counter += 1


def remove_random_files(pname, sname):
    so = Share.objects.get(name=sname)
    rusage, eusage = share_usage(so.pool, so.qgroup)
    print("Share(%s) usage before file removal: %d" % (sname, rusage))
    spath = "/mnt2/%s/%s" % (pname, sname)
    flist = os.listdir(spath)
    random.shuffle(flist)
    rnum = random.randint(0, len(flist))
    for i in range(rnum):
        os.remove("%s/%s" % (spath, flist[i]))
    run_command(["/usr/bin/sync"])
    rusage, eusage = share_usage(so.pool, so.qgroup)
    print("Share(%s) usage after removing %d files: %d" % (sname, rnum, rusage))


def main():
    if len(sys.argv) == 1:
        sys.exit("Usage: %s <pool name>" % sys.argv[0])
    pname = sys.argv[1]
    sname = "qgroup-test-share1"
    size = 1024 * 1024  # 1 GiB
    aw = APIWrapper()
    print("Share(%s) created. Size: %d" % (sname, size))

    fill_up_share(pname, sname)
    # expand Share and fillup. repeat 3 times
    for i in range(3):
        size += 1024 * 512
        resize_share(aw, sname, size)
        fill_up_share(pname, sname)

    # remove random files and fillup. repeat 3 times.
    for i in range(3):
        # expand a bit so we can actually remove some files.
        size += 1024 * 128
        resize_share(aw, sname, size)
        remove_random_files(pname, sname)
        fill_up_share(pname, sname)

    # remove random files, shrink the pool by half of free'd capacity, fill
    # up. repeat 3 times
    for i in range(3):
        # expand a bit so we can actually remove files.
        size += 1024 * 128
        resize_share(aw, sname, size)
        remove_random_files(pname, sname)
        so = Share.objects.get(name=sname)
        rusage, eusage = share_usage(so.pool, so.qgroup)
        free_space = so.size - rusage
        print("Free space on Share(%s): %d" % (sname, free_space))
        size -= int(free_space / 2)
        resize_share(aw, sname, size)
        fill_up_share(pname, sname)

    aw.api_call("shares/%s" % sname, calltype="delete", save_error=False)
    print("Share(%s) deleted." % sname)


if __name__ == "__main__":
    main()
