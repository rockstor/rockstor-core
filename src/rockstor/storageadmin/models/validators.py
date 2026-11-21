"""
Copyright (joint work) 2026 The Rockstor Project <https://rockstor.com>

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

import re
import ipaddress
from django.core.exceptions import ValidationError


def validate_nfs_host_str(value):
    error_count = 0
    host_regex = (
        r"^(([a-zA-Z0-9\*]|[a-zA-Z0-9\*][a-zA-Z0-9\-\*]*"
        r"[a-zA-Z0-9\*])\.)*([A-Za-z0-9\*]|[A-Za-z0-9\*]"
        r"[A-Za-z0-9\-\*]*[A-Za-z0-9\*])$"
    )
    if re.match(host_regex, value) is None:
        error_count += 1

    # ip networks, validate IP address (ipv4/6), incl. CIDR notation
    try:
        ipaddress.ip_network(value)
    except ValidationError:
        error_count += 1

    if error_count == 2:
        raise ValidationError("Invalid host string: %s" % value)


def validate_nfs_modify_str(value):
    if value != "ro" and value != "rw":
        raise ValidationError("Invalid mod choice. Possible options: ro, rw")


def validate_nfs_sync_choice(value):
    if value != "async" and value != "sync":
        msg = "Invalid sync choice. Possible options: async, sync"
        raise ValidationError(msg)
