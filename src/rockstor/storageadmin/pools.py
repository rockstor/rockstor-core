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

import subprocess
import re

class Pool():

    def __init__(self, name, uuid, disks=[]):
        self.name = name
        self.uuid = uuid
        self.disks = disks

def list_pools():
    proc = subprocess.Popen(["/sbin/btrfs", "filesystem", "show"],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            shell=False)
    output, error = proc.communicate()
    output = output.split('\n')
    pools = {}
    for i in range(len(output)):
        line = output[i]
        if (re.match("Label:", line) is not None):
            l_fields = line.split()
            name = l_fields[1][1:-1]
            uuid = l_fields[3]
            pool = Pool(name=name, uuid=uuid)
            num_devices = int(output[i+1].split()[2])
            for j in range(num_devices):
                disk = output[i+2+j].split()[-1]
                pool.disks.append(disk)
            pools[name] = pool
    return pools

def create_pool():
    pass

def delete_pool():
    pass
