"""
Copyright (c) 2012-2023 Rockstor, Inc. <https://rockstor.com>
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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

# constants.py

"""This module defines system-level constants."""
"""Take care to minimise import in this module, to guard against circular dependency."""

MKDIR = "/usr/bin/mkdir"
RMDIR = "/usr/bin/rmdir"
DEFAULT_MNT_DIR = "/mnt2/"
MOUNT = "/usr/bin/mount"
UMOUNT = "/usr/bin/umount"

USERMOD = "/usr/sbin/usermod"
LDD = "/usr/bin/ldd"

SYSTEMCTL = "/usr/bin/systemctl"

# Works in Leap 15.4 (systemd-249.16-150400.8.28.3) and Tumbleweed (systemd-253.4-2.1)
UDEVADM = "/usr/bin/udevadm"
SHUTDOWN = "/sbin/shutdown"

TAILSCALE = "/usr/bin/tailscale"

# Major block device number:str to ignore (commonality ordered):
# https://www.kernel.org/doc/Documentation/admin-guide/devices.txt
# 7: Loopback
# 11: SCSI CD-ROM
# 2: Floppy disks
BLOCK_DEV_EXCLUDE: list[str] = ["7", "11", "2"]
