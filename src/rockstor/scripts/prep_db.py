"""
Copyright (joint work) 2024 The Rockstor Project <https://rockstor.com>

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

from smart_manager.models import Service
from storageadmin.models import Setup


def register_services() -> None:
    services = {
        "NFS": "nfs",
        "Samba": "smb",
        "NTP": "ntpd",
        "Active Directory": "active-directory",
        "LDAP": "ldap",
        "SFTP": "sftp",
        "Replication": "replication",
        "SNMP": "snmpd",
        "Rock-on": "docker",
        "S.M.A.R.T": "smartd",
        "NUT-UPS": "nut",
        "Collector": "rockstor-collector",
        # moving towards generic scheduling service name.
        "Scheduling": "scheduling",
        "Bootstrap": "rockstor-bootstrap",
        "Rockstor": "rockstor", # Service Gateway Interface (SGI) server.
        "Tailscale": "tailscaled",
    }


    for k, v in services.items():
        try:
            so = Service.objects.get(name=v)
            so.display_name = k
        except Service.DoesNotExist:
            so = Service(display_name=k, name=v)
        finally:
            so.save()
    for so in Service.objects.filter():
        if so.display_name not in services:
            so.delete()


def create_setup():
    setup = Setup.objects.all()
    if len(setup) == 0:
        s = Setup()
        s.save()


def main():
    create_setup()
    register_services()
