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

import ipaddress
import re

from django.core.exceptions import ValidationError


def validate_nfs_host_str(value: str) -> None:
    """
    Validate NFS export client host specifications:
    1. Check for most permissive
    2. IP-related variants
    3. Actual host string variants (netgroups and standard/wildcard hostnames)

    Return None if valid, else raise ValidationError.
    """
    if not value or not isinstance(value, str):
        raise ValidationError(f"Invalid host string: {value}")

    # 1. Every source host is allowed
    if value == "*":
        return

    # 2. Single IPs, CIDR, IP/netmask
    # Reject IPv6 zone IDs
    if "%" in value:
        raise ValidationError(f"Invalid host string: {value}")
    try:
        # strict=False for set host bits
        net_ip = ipaddress.ip_network(value, strict=False)
        # Special case: do not allow inverse hostmasks
        if "/" in value:
            _, suffix = value.split("/", 1)
            if not suffix.isdigit() and suffix != str(net_ip.netmask):
                raise ValidationError(f"Invalid host string: {value}")
        return
    except ValueError:
        pass

    # 3. String-based evaluation
    # Netgroups
    if re.match(r"^@[a-zA-Z0-9_.-]+$", value):
        return

    # Hostnames & wildcard domains (prevent all-numeric, so invalid IPs fail)
    host_regex = (
        r"^(([a-zA-Z0-9\*]|[a-zA-Z0-9\*][a-zA-Z0-9\-\*]*"
        r"[a-zA-Z0-9\*])\.)*([A-Za-z\*]|[A-Za-z\*]"
        r"[A-Za-z0-9\-\*]*[A-Za-z0-9\*])$"
    )

    if re.match(host_regex, value):
        return

    raise ValidationError(f"Invalid host string: {value}")


def validate_nfs_modify_str(value: str) -> None:
    """
    Validate read-only (ro) or read-write (rw) as only viable options.
    Return None if valid, else raise ValidationError.
    """
    if value not in ("ro", "rw"):
        raise ValidationError("Invalid mode choice. Possible options: ro, rw")


def validate_nfs_sync_choice(value: str) -> None:
    """
    Validate NFS sync choices as either async or sync only.
    Return None if valid, else raise ValidationError.
    """
    if value not in ("async", "sync"):
        raise ValidationError("Invalid sync choice. Possible options: async, sync")