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

from smart_manager.models import Service
from storageadmin.models import Setup


def register_services():
    services = {
        "NFS": "nfs",
        "Samba": "smb",
        "NIS": "nis",
        "NTP": "ntpd",
        "Active Directory": "active-directory",
        "LDAP": "ldap",
        "SFTP": "sftp",
        "Replication": "replication",
        "SNMP": "snmpd",
        "Rock-on": "docker",
        "S.M.A.R.T": "smartd",
        "NUT-UPS": "nut",
        "ZTaskd": "ztask-daemon",
        "Bootstrap": "rockstor-bootstrap",
        "Shell In A Box": "shellinaboxd",
        "Rockstor": "rockstor",
    }

    # N.B. all other services have null as their default config with service.
    # Consider bringing shellinaboxd in line with this now default behaviour.
    services_configs = {
        "shellinaboxd": (
            '{"detach": false, "css": "white-on-black", ' '"shelltype": "LOGIN"}'
        )
    }

    for k, v in services.items():
        try:
            so = Service.objects.get(name=v)
            so.display_name = k
            # Apply any configuration defaults found in services_configs.
            if v in services_configs:
                so.config = services_configs[v]
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
