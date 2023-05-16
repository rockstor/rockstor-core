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

SYSTEMCTL = "/usr/bin/systemctl"
