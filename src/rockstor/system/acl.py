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

from osi import run_command

CHOWN = "/usr/bin/chown"
CHMOD = "/usr/bin/chmod"


def chown(share, owner, group=None, recursive=False):
    cmd = [
        CHOWN,
    ]
    if recursive is True:
        cmd.append("-R")
    if group is not None:
        owner = "%s:%s" % (owner, group)
    cmd.extend([owner, share])
    return run_command(cmd)


def chmod(share, perm_bits, recursive=False):
    cmd = [
        CHMOD,
    ]
    if recursive is True:
        cmd.append("-R")
    cmd.extend([perm_bits, share])
    return run_command(cmd)
