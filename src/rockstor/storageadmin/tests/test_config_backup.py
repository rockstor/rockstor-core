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
along with this program. If not, see <https://www.gnu.org/licenses/>.
"""
from unittest import mock
from unittest.mock import patch
from rest_framework import status

from storageadmin.models import ConfigBackup
from storageadmin.tests.test_api import APITestMixin
from storageadmin.views.config_backup import (
    get_sname,
    update_rockon_shares,
    validate_install_config,
    validate_update_config,
    validate_service_status,
    validate_taskdef_meta,
    validate_task_definitions,
)

"""
Fixture creation instructions:

System needs 2 non system pools:
- 'rock-pool', at any raid level.
- 'rock-pool2', at any raid level.

- Create 1 share named 'test_share01'
- Create 1 share named 'test_share02'

cd /opt/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin dumpdata storageadmin.pool storageadmin.share \
--natural-foreign --indent 4 > \
src/rockstor/storageadmin/fixtures/test_config_backup.json

To run the tests:
cd /opt/rockstor/src/rockstor
export DJANGO_SETTINGS_MODULE="settings"
poetry run django-admin test -v 2 -p test_config_backup.py
"""


class ConfigBackupTests(APITestMixin):
    fixtures = ["test_api.json", "test_config_backup.json"]
    BASE_URL = "/api/config-backup"
    sa_ml = [
        {
            "fields": {
                "status": "stopped",
                "website": "https://emby.media/",
                "volume_add_support": True,
                "name": "Emby server",
                "description": "Emby media server",
                "state": "installed",
                "version": "1.0",
                "link": "",
                "https": False,
                "ui": True,
                "icon": None,
                "more_info": "<h4>Adding media to Emby.</h4><p>You can add Shares(with media) to Emby from the settings wizard of this Rock-on. Then, from Emby WebUI, you can update and re-index your library.</p><p> Visit https://hub.docker.com/r/emby/embyserver for description of each option.",
            },
            "model": "storageadmin.rockon",
            "pk": 48,
        },
        {
            "fields": {
                "status": "stopped",
                "website": "https://hub.docker.com/r/linuxserver/mariadb/",
                "volume_add_support": True,
                "name": "MariaDB",
                "description": "MariaDB, relational database management system.",
                "state": "installed",
                "version": "1.0",
                "link": "",
                "https": False,
                "ui": False,
                "icon": None,
                "more_info": "<h4>Important locations</h4><p>Configuration file:<code>/config/custom.cnf</code></p> <p>Databases: <code>/config/databases</code></p> <p>Logs: <code>/config/log/mysql/</code></p>",
            },
            "model": "storageadmin.rockon",
            "pk": 58,
        },
        {
            "fields": {
                "status": "stopped",
                "website": "https://hub.docker.com/r/linuxserver/smokeping/",
                "volume_add_support": True,
                "name": "SmokePing",
                "description": "SmokePing is a network latency history monitor.",
                "state": "available",
                "version": "1.0",
                "link": "smokeping/smokeping.cgi",
                "https": False,
                "ui": True,
                "icon": None,
                "more_info": None,
            },
            "model": "storageadmin.rockon",
            "pk": 59,
        },
        {
            "fields": {
                "status": "exitcode: 137 error: ",
                "website": "",
                "volume_add_support": True,
                "name": "Alpine With AddStorage 2Ports",
                "description": "Alpine test Rock-on.",
                "state": "installed",
                "version": "1.0",
                "link": "",
                "https": False,
                "ui": True,
                "icon": None,
                "more_info": None,
            },
            "model": "storageadmin.rockon",
            "pk": 74,
        },
        {
            "fields": {
                "status": "exitcode: 137 error: ",
                "website": "",
                "volume_add_support": True,
                "name": "Alpine With AddStorage Single",
                "description": "Alpine test Rock-on.",
                "state": "installed",
                "version": "1.0",
                "link": "",
                "https": False,
                "ui": False,
                "icon": None,
                "more_info": None,
            },
            "model": "storageadmin.rockon",
            "pk": 75,
        },
        {
            "fields": {
                "launch_order": 1,
                "rockon": 48,
                "uid": None,
                "name": "embyserver",
                "dimage": 52,
            },
            "model": "storageadmin.dcontainer",
            "pk": 52,
        },
        {
            "fields": {
                "launch_order": 1,
                "rockon": 58,
                "uid": None,
                "name": "linuxserver-mariadb",
                "dimage": 62,
            },
            "model": "storageadmin.dcontainer",
            "pk": 62,
        },
        {
            "fields": {
                "launch_order": 1,
                "rockon": 59,
                "uid": None,
                "name": "SmokePing",
                "dimage": 63,
            },
            "model": "storageadmin.dcontainer",
            "pk": 63,
        },
        {
            "fields": {
                "launch_order": 1,
                "rockon": 74,
                "uid": None,
                "name": "alpine2p1",
                "dimage": 77,
            },
            "model": "storageadmin.dcontainer",
            "pk": 79,
        },
        {
            "fields": {
                "launch_order": 2,
                "rockon": 74,
                "uid": None,
                "name": "alpine2p2",
                "dimage": 77,
            },
            "model": "storageadmin.dcontainer",
            "pk": 80,
        },
        {
            "fields": {
                "launch_order": 1,
                "rockon": 75,
                "uid": None,
                "name": "alpinesingle",
                "dimage": 77,
            },
            "model": "storageadmin.dcontainer",
            "pk": 81,
        },
        {
            "fields": {
                "description": "Enter a valid GID of an existing user with permission to media shares to run Emby as.",
                "container": 52,
                "key": "GID",
                "val": "1000",
                "label": "GID",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 58,
        },
        {
            "fields": {
                "description": "Enter a comma-separated list of additional GIDs to run emby as",
                "container": 52,
                "key": "GIDLIST",
                "val": "100",
                "label": "GIDList",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 59,
        },
        {
            "fields": {
                "description": "Enter a valid UID to run MariaDB as. It must have full permissions to the share mapped in the previous step.",
                "container": 62,
                "key": "PUID",
                "val": "1000",
                "label": "UID to run MariaDB as.",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 71,
        },
        {
            "fields": {
                "description": "Enter a valid GID to use along with the above UID. It (or the above UID) must have full permissions to the share mapped in the previous step.",
                "container": 62,
                "key": "PGID",
                "val": "1000",
                "label": "GID to run MariaDB as.",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 72,
        },
        {
            "fields": {
                "description": "Enter a root password for the MariaDB server (minimum 4 characters).",
                "container": 62,
                "key": "MYSQL_ROOT_PASSWORD",
                "val": "mariadb",
                "label": "Root password.",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 73,
        },
        {
            "fields": {
                "description": "Enter a valid UID to run SmokePing as. It must have full permissions to all Shares mapped in the previous step.",
                "container": 63,
                "key": "PUID",
                "val": None,
                "label": "UID to run SmokePing as.",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 74,
        },
        {
            "fields": {
                "description": "Enter a valid GID to use along with the above UID. It(or the above UID) must have full permissions to all Shares mapped in the previous step.",
                "container": 63,
                "key": "PGID",
                "val": None,
                "label": "GID to run SmokePing as.",
            },
            "model": "storageadmin.dcontainerenv",
            "pk": 75,
        },
        {
            "fields": {"container": 52, "key": "embyserver", "val": "test3"},
            "model": "storageadmin.dcontainerlabel",
            "pk": 5,
        },
        {
            "fields": {"container": 62, "key": "linuxserver-mariadb", "val": "test4"},
            "model": "storageadmin.dcontainerlabel",
            "pk": 6,
        },
        {
            "fields": {"container": 81, "key": "alpinesingle", "val": "test2"},
            "model": "storageadmin.dcontainerlabel",
            "pk": 7,
        },
        {
            "fields": {"container": 79, "key": "alpine2p1", "val": "test1"},
            "model": "storageadmin.dcontainerlabel",
            "pk": 8,
        },
        {
            "fields": {
                "container": 52,
                "description": "Choose a Share for the Emby Server configuration. Eg: create a Share called emby-config for this purpose alone.",
                "uservol": False,
                "share": 15,
                "label": "Config Storage",
                "min_size": None,
                "dest_dir": "/config",
            },
            "model": "storageadmin.dvolume",
            "pk": 87,
        },
        {
            "fields": {
                "container": 52,
                "description": "Choose a Share with media content. Eg: create a Share called emby-media for this purpose alone or use an existing share. It will be available as /media inside Emby.",
                "uservol": False,
                "share": 13,
                "label": "Media Storage",
                "min_size": None,
                "dest_dir": "/media",
            },
            "model": "storageadmin.dvolume",
            "pk": 88,
        },
        {
            "fields": {
                "container": 62,
                "description": "Choose a share where the database should be stored. Eg: create a share called mariadb-server1 for this purpose alone. ",
                "uservol": False,
                "share": 10,
                "label": "Data Storage",
                "min_size": None,
                "dest_dir": "/config",
            },
            "model": "storageadmin.dvolume",
            "pk": 98,
        },
        {
            "fields": {
                "container": 63,
                "description": "Choose a Share for SmokePing Configuration Files",
                "uservol": False,
                "share": None,
                "label": "Config Storage",
                "min_size": None,
                "dest_dir": "/config",
            },
            "model": "storageadmin.dvolume",
            "pk": 99,
        },
        {
            "fields": {
                "container": 63,
                "description": "Choose a Share for SmokePing Data Files",
                "uservol": False,
                "share": None,
                "label": "Data location",
                "min_size": None,
                "dest_dir": "/data",
            },
            "model": "storageadmin.dvolume",
            "pk": 100,
        },
        {
            "fields": {
                "container": 79,
                "description": None,
                "uservol": True,
                "share": 14,
                "label": None,
                "min_size": None,
                "dest_dir": "/test_share10",
            },
            "model": "storageadmin.dvolume",
            "pk": 147,
        },
        {
            "fields": {
                "container": 80,
                "description": None,
                "uservol": True,
                "share": 14,
                "label": None,
                "min_size": None,
                "dest_dir": "/test_share10",
            },
            "model": "storageadmin.dvolume",
            "pk": 148,
        },
        {
            "fields": {
                "container": 81,
                "description": None,
                "uservol": True,
                "share": 10,
                "label": None,
                "min_size": None,
                "dest_dir": "/test_share09",
            },
            "model": "storageadmin.dvolume",
            "pk": 149,
        },
        {
            "fields": {
                "container": 52,
                "description": None,
                "uservol": True,
                "share": 9,
                "label": None,
                "min_size": None,
                "dest_dir": "/test_share08",
            },
            "model": "storageadmin.dvolume",
            "pk": 150,
        },
        {
            "fields": {
                "container": 62,
                "description": None,
                "uservol": True,
                "share": 8,
                "label": None,
                "min_size": None,
                "dest_dir": "/test_share07",
            },
            "model": "storageadmin.dvolume",
            "pk": 151,
        },
        {
            "fields": {
                "container": 52,
                "description": "Emby Server WebUI port. Suggested default: 8096",
                "hostp_default": 8096,
                "protocol": "tcp",
                "label": "WebUI port",
                "hostp": 8096,
                "uiport": True,
                "containerp": 8096,
            },
            "model": "storageadmin.dport",
            "pk": 68,
        },
        {
            "fields": {
                "container": 52,
                "description": "Emby Server HTTPS port. Suggested default: 8920",
                "hostp_default": 8920,
                "protocol": "tcp",
                "label": "HTTPS port",
                "hostp": 8920,
                "uiport": False,
                "containerp": 8920,
            },
            "model": "storageadmin.dport",
            "pk": 69,
        },
        {
            "fields": {
                "container": 62,
                "description": "MariaDB port. Suggested default: 3306",
                "hostp_default": 3306,
                "protocol": "tcp",
                "label": "MariaDB port",
                "hostp": 3306,
                "uiport": False,
                "containerp": 3306,
            },
            "model": "storageadmin.dport",
            "pk": 76,
        },
        {
            "fields": {
                "container": 63,
                "description": "SmokePing WebUI port. Suggested default: 7878",
                "hostp_default": 87,
                "protocol": "tcp",
                "label": "WebUI port",
                "hostp": 85,
                "uiport": True,
                "containerp": 80,
            },
            "model": "storageadmin.dport",
            "pk": 77,
        },
        {
            "fields": {
                "description": "<u>Optional:</u> path to hardware transcoding device (/dev/dri/renderD128). Leave blank if not needed.",
                "container": 52,
                "dev": "VAAPI",
                "val": "",
                "label": "VAAPI device",
            },
            "model": "storageadmin.dcontainerdevice",
            "pk": 1,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share01",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/257",
                "replica": False,
                "pqgroup": "2015/14",
                "owner": "root",
                "toc": "2019-11-06T16:02:01.830Z",
                "subvol_name": "test_share01",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 2,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share02",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/258",
                "replica": False,
                "pqgroup": "2015/15",
                "owner": "root",
                "toc": "2019-11-06T16:02:01.915Z",
                "subvol_name": "test_share02",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 3,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share03",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/259",
                "replica": False,
                "pqgroup": "2015/16",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.000Z",
                "subvol_name": "test_share03",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 4,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share04",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/260",
                "replica": False,
                "pqgroup": "2015/17",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.086Z",
                "subvol_name": "test_share04",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 5,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share05",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/261",
                "replica": False,
                "pqgroup": "2015/18",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.170Z",
                "subvol_name": "test_share05",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 6,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share06",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/262",
                "replica": False,
                "pqgroup": "2015/19",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.252Z",
                "subvol_name": "test_share06",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 7,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share07",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/263",
                "replica": False,
                "pqgroup": "2015/20",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.422Z",
                "subvol_name": "test_share07",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 8,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share08",
                "perms": "755",
                "pqgroup_rusage": 1925,
                "eusage": 1925,
                "rusage": 1925,
                "compression_algo": None,
                "qgroup": "0/264",
                "replica": False,
                "pqgroup": "2015/21",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.506Z",
                "subvol_name": "test_share08",
                "size": 5242880,
                "pqgroup_eusage": 1925,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 9,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share09",
                "perms": "755",
                "pqgroup_rusage": 115056,
                "eusage": 115056,
                "rusage": 115056,
                "compression_algo": None,
                "qgroup": "0/265",
                "replica": False,
                "pqgroup": "2015/22",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.588Z",
                "subvol_name": "test_share09",
                "size": 5242880,
                "pqgroup_eusage": 115056,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 10,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share11",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/267",
                "replica": False,
                "pqgroup": "2015/1",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.669Z",
                "subvol_name": "test_share11",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 11,
        },
        {
            "fields": {
                "group": "root",
                "name": "rockons_root",
                "perms": "755",
                "pqgroup_rusage": 2416,
                "eusage": 2416,
                "rusage": 2416,
                "compression_algo": None,
                "qgroup": "0/268",
                "replica": False,
                "pqgroup": "2015/4",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.750Z",
                "subvol_name": "rockons_root",
                "size": 5242880,
                "pqgroup_eusage": 2416,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 12,
        },
        {
            "fields": {
                "group": "root",
                "name": "emby-media",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/275",
                "replica": False,
                "pqgroup": "2015/10",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.836Z",
                "subvol_name": "emby-media",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 13,
        },
        {
            "fields": {
                "group": "root",
                "name": "test_share10",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": None,
                "qgroup": "0/266",
                "replica": False,
                "pqgroup": "2015/2",
                "owner": "root",
                "toc": "2019-11-06T16:02:02.922Z",
                "subvol_name": "test_share10",
                "size": 5242880,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 14,
        },
        {
            "fields": {
                "group": "root",
                "name": "emby-conf",
                "perms": "755",
                "pqgroup_rusage": 6543,
                "eusage": 6543,
                "rusage": 6543,
                "compression_algo": None,
                "qgroup": "0/274",
                "replica": False,
                "pqgroup": "2015/12",
                "owner": "root",
                "toc": "2019-11-06T16:02:03.008Z",
                "subvol_name": "emby-conf",
                "size": 5242880,
                "pqgroup_eusage": 6543,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 15,
        },
        {
            "fields": {
                "group": "root",
                "name": "home",
                "perms": "755",
                "pqgroup_rusage": 64,
                "eusage": 64,
                "rusage": 64,
                "compression_algo": None,
                "qgroup": "0/264",
                "replica": False,
                "pqgroup": "2015/2",
                "owner": "root",
                "toc": "2019-11-06T16:02:03.383Z",
                "subvol_name": "home",
                "size": 16767980,
                "pqgroup_eusage": 64,
                "pool": 3,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 16,
        },
        {
            "fields": {
                "group": "root",
                "name": "dropbox_test",
                "perms": "755",
                "pqgroup_rusage": 16,
                "eusage": 16,
                "rusage": 16,
                "compression_algo": "no",
                "qgroup": "0/498",
                "replica": False,
                "pqgroup": "2015/6",
                "owner": "root",
                "toc": "2019-11-06T16:02:03.179Z",
                "subvol_name": "dropbox_test",
                "size": 1048576,
                "pqgroup_eusage": 16,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 29,
        },
        {
            "fields": {
                "group": "root",
                "name": "drop-conf",
                "perms": "755",
                "pqgroup_rusage": 1146,
                "eusage": 1146,
                "rusage": 1146,
                "compression_algo": "no",
                "qgroup": "0/499",
                "replica": False,
                "pqgroup": "2015/13",
                "owner": "root",
                "toc": "2019-11-06T16:02:03.093Z",
                "subvol_name": "drop-conf",
                "size": 1048576,
                "pqgroup_eusage": 1146,
                "pool": 2,
                "uuid": None,
            },
            "model": "storageadmin.share",
            "pk": 30,
        },
    ]
    sm_ml = [
        {
            "fields": {
                "display_name": "Replication",
                "config": None,
                "name": "replication",
            },
            "model": "smart_manager.service",
            "pk": 1,
        },
        {
            "fields": {"display_name": "Samba", "config": None, "name": "smb"},
            "model": "smart_manager.service",
            "pk": 2,
        },
        {
            "fields": {"display_name": "NFS", "config": None, "name": "nfs"},
            "model": "smart_manager.service",
            "pk": 3,
        },
        {
            "fields": {"display_name": "NTP", "config": None, "name": "ntpd"},
            "model": "smart_manager.service",
            "pk": 5,
        },
        {
            "fields": {"display_name": "NIS", "config": None, "name": "nis"},
            "model": "smart_manager.service",
            "pk": 6,
        },
        {
            "fields": {"display_name": "LDAP", "config": None, "name": "ldap"},
            "model": "smart_manager.service",
            "pk": 7,
        },
        {
            "fields": {"display_name": "SFTP", "config": None, "name": "sftp"},
            "model": "smart_manager.service",
            "pk": 8,
        },
        {
            "fields": {"display_name": "Rockstor", "config": None, "name": "rockstor"},
            "model": "smart_manager.service",
            "pk": 9,
        },
        {
            "fields": {"display_name": "S.M.A.R.T", "config": None, "name": "smartd"},
            "model": "smart_manager.service",
            "pk": 10,
        },
        {
            "fields": {
                "display_name": "Active Directory",
                "config": None,
                "name": "active-directory",
            },
            "model": "smart_manager.service",
            "pk": 11,
        },
        {
            "fields": {"display_name": "NUT-UPS", "config": None, "name": "nut"},
            "model": "smart_manager.service",
            "pk": 12,
        },
        {
            "fields": {"display_name": "SNMP", "config": None, "name": "snmpd"},
            "model": "smart_manager.service",
            "pk": 13,
        },
        {
            "fields": {
                "display_name": "Rock-on",
                "config": '{"root_share": "rockons-root"}',
                "name": "docker",
            },
            "model": "smart_manager.service",
            "pk": 14,
        },
        {
            "fields": {
                "display_name": "Shell In A Box",
                "config": '{"detach": false, "css": "white-on-black", "shelltype": "LOGIN"}',
                "name": "shellinaboxd",
            },
            "model": "smart_manager.service",
            "pk": 15,
        },
        {
            "fields": {
                "display_name": "ZTaskd",
                "config": None,
                "name": "ztask-daemon",
            },
            "model": "smart_manager.service",
            "pk": 17,
        },
        {
            "fields": {
                "display_name": "Bootstrap",
                "config": None,
                "name": "rockstor-bootstrap",
            },
            "model": "smart_manager.service",
            "pk": 18,
        },
        {
            "fields": {
                "status": True,
                "count": 15,
                "ts": "2021-12-24T18:49:51.195Z",
                "service": 14,
            },
            "model": "smart_manager.servicestatus",
            "pk": 17,
        },
        {
            "fields": {
                "status": True,
                "count": 2,
                "ts": "2021-12-24T18:47:11.756Z",
                "service": 9,
            },
            "model": "smart_manager.servicestatus",
            "pk": 18,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.783Z",
                "service": 10,
            },
            "model": "smart_manager.servicestatus",
            "pk": 19,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.816Z",
                "service": 2,
            },
            "model": "smart_manager.servicestatus",
            "pk": 20,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.829Z",
                "service": 11,
            },
            "model": "smart_manager.servicestatus",
            "pk": 21,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.858Z",
                "service": 5,
            },
            "model": "smart_manager.servicestatus",
            "pk": 22,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.890Z",
                "service": 12,
            },
            "model": "smart_manager.servicestatus",
            "pk": 23,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:11.921Z",
                "service": 13,
            },
            "model": "smart_manager.servicestatus",
            "pk": 24,
        },
        {
            "fields": {
                "status": True,
                "count": 2,
                "ts": "2021-12-24T18:47:11.948Z",
                "service": 8,
            },
            "model": "smart_manager.servicestatus",
            "pk": 25,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.133Z",
                "service": 1,
            },
            "model": "smart_manager.servicestatus",
            "pk": 26,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.169Z",
                "service": 15,
            },
            "model": "smart_manager.servicestatus",
            "pk": 27,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.216Z",
                "service": 3,
            },
            "model": "smart_manager.servicestatus",
            "pk": 28,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.243Z",
                "service": 7,
            },
            "model": "smart_manager.servicestatus",
            "pk": 29,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.283Z",
                "service": 6,
            },
            "model": "smart_manager.servicestatus",
            "pk": 30,
        },
        {
            "fields": {
                "status": True,
                "count": 2,
                "ts": "2021-12-24T18:47:12.475Z",
                "service": 17,
            },
            "model": "smart_manager.servicestatus",
            "pk": 31,
        },
        {
            "fields": {
                "status": False,
                "count": 2,
                "ts": "2021-12-24T18:47:12.513Z",
                "service": 18,
            },
            "model": "smart_manager.servicestatus",
            "pk": 32,
        },
        {
            "fields": {
                "name": "snap_daily_ts01",
                "task_type": "snapshot",
                "json_meta": '{"writable": true, "visible": true, "prefix": "snap_daily_ts01", "share": "2", "max_count": "4"}',
                "enabled": False,
                "crontab": "42 3 * * *",
                "crontabwindow": "*-*-*-*-*-*",
            },
            "model": "smart_manager.taskdefinition",
            "pk": 1,
        },
        {
            "fields": {
                "name": "snap_daily_ts02",
                "task_type": "snapshot",
                "json_meta": '{"writable": true, "visible": true, "prefix": "snap_daily_ts02", "share": "33", "max_count": "4"}',
                "enabled": False,
                "crontab": "42 3 * * *",
                "crontabwindow": "*-*-*-*-*-*",
            },
            "model": "smart_manager.taskdefinition",
            "pk": 2,
        },
        {
            "fields": {
                "name": "snap_daily_ts04",
                "task_type": "snapshot",
                "json_meta": '{"writable": true, "visible": true, "prefix": "snap_daily_ts04", "share": "5", "max_count": "4"}',
                "enabled": False,
                "crontab": "42 3 * * *",
                "crontabwindow": "*-*-*-*-*-*",
            },
            "model": "smart_manager.taskdefinition",
            "pk": 3,
        },
        {
            "model": "smart_manager.taskdefinition",
            "pk": 4,
            "fields": {
                "name": "rockpool_scrub",
                "task_type": "scrub",
                "json_meta": '{"pool_name": "rock-pool", "pool": "2"}',
                "enabled": False,
                "crontab": "42 3 * * 5",
                "crontabwindow": "*-*-*-*-*-*",
            },
        },
        {
            "model": "smart_manager.taskdefinition",
            "pk": 5,
            "fields": {
                "name": "boguspool_scrub",
                "task_type": "scrub",
                "json_meta": '{"pool_name": "bogus-pool", "pool": "99"}',
                "enabled": False,
                "crontab": "42 3 * * 5",
                "crontabwindow": "*-*-*-*-*-*",
            },
        },
        {
            "model": "smart_manager.taskdefinition",
            "pk": 6,
            "fields": {
                "name": "rockpool2_scrub",
                "task_type": "scrub",
                "json_meta": '{"pool_name": "rock-pool2", "pool": "3"}',
                "enabled": False,
                "crontab": "42 3 * * 5",
                "crontabwindow": "*-*-*-*-*-*",
            },
        },
    ]

    @classmethod
    def setUpClass(cls):
        super(ConfigBackupTests, cls).setUpClass()

        # # Create RockOn objects as per fixture
        # cls.rockon_alpine_single = RockOn(id=73, name="Alpine With AddStorage Single")
        # cls.rockon_mariadb = RockOn(id=58, name="MariaDB")
        # cls.rockon_alpine_2ports = RockOn(id=75, name="Alpine With AddStorage 2Ports")
        # cls.rockon_emby = RockOn(id=74, name="Emby server")

        # TODO: may need to mock os.path.isfile

        cls.patch_backup_config = patch("storageadmin.views.config_backup.backup_config")
        cls.mock_backup_config = cls.patch_backup_config.start()
        cls.mock_backup_config.return_value = None

    @classmethod
    def tearDownClass(cls):
        super(ConfigBackupTests, cls).tearDownClass()

    @mock.patch(
        "storageadmin.views.config_backup.ConfigBackupDetailView._validate_input"
    )
    def test_valid_requests(self, mock_validate_input):
        # happy path POST
        response = self.client.post(self.BASE_URL)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        temp_configbackup = ConfigBackup(
            id=999, filename="backup-2019-11-07-110208.json.gz"
        )
        mock_validate_input.return_value = temp_configbackup
        # Happy path POST with restore command test restore .... backup with
        # id=1 is created when above post api call is made
        data = {"command": "restore"}
        response = self.client.post("{}/999".format(self.BASE_URL), data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

        # Happy path DELETE
        response = self.client.delete("{}/999".format(self.BASE_URL))
        self.assertEqual(response.status_code, status.HTTP_200_OK, msg=response.data)

    # TODO: 'module' object has no attribute 'views'
    #     when attempting to mock uploaded file content.
    # @mock.patch(storageadmin.views.config_backup.ConfigBackup)
    # def test_config_upload_file(self, mock_config_backup):
    #
    #     # happy path POST
    #     # so the following test throws:
    #     # 'FileUpload parse error - none of upload handlers can handle the
    #     # stream'
    #
    #     # we use a SimpleUploadedFile Object to act as our
    #     # ConfigBackup.config_backup (a models.fileField)
    #
    #     # setup fake zip file as models.FileField substitute in ConfigBackup
    #     fake_file = SimpleUploadedFile('file1.txt', b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #     # TODO: We also need to setup a content_type='text/plain' to test
    #     #     failure when file is not a zip file.
    #
    #     # override "config_backup = models.FileField" in super
    #     class MockConfigBackup(ConfigBackup):
    #         def __init__(self, **kwargs):
    #             self.config_backup = \
    #                 SimpleUploadedFile(self.filename, b"fake-file-contents",
    #                                    content_type="application/zip")
    #
    #         def save(self):
    #             pass
    #
    #     mock_config_backup.objects.get.side_effect = MockConfigBackup
    #
    #
    #     data = {'file-name': 'file1', 'file': 'file1.txt'}
    #     response = self.client.post('%s/file-upload' % self.BASE_URL,
    #                                 data=data)
    #     self.assertEqual(response.status_code,
    #                      status.HTTP_200_OK, msg=response.data)

    def test_get_sname(self):
        range_pks = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 29, 30]
        expected_snames = [
            "test_share01",
            "test_share02",
            "test_share03",
            "test_share04",
            "test_share05",
            "test_share06",
            "test_share07",
            "test_share08",
            "test_share09",
            "test_share11",
            "rockons_root",
            "emby-media",
            "test_share10",
            "emby-conf",
            "home",
            "dropbox_test",
            "drop-conf",
        ]

        for pk, sname in zip(range_pks, expected_snames):
            returned = get_sname(self.sa_ml, pk)
            self.assertEqual(
                returned,
                sname,
                msg="Un-expected get_sname() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(returned, sname),
            )

    # @mock.patch("storageadmin.views.config_backup.RockOn.objects")
    # def test_validate_rockons(self):
    #     # mock_rockon.filter.return_value = mock_rockon
    #     # mock_rockon.exists.return_value = False
    #     expected = {73: {'rname': 'Alpine With AddStorage Single', 'new_rid': 73},
    #                 58: {'rname': 'MariaDB', 'new_rid': 58},
    #                 75: {'rname': 'Alpine With AddStorage 2Ports', 'new_rid': 75},
    #                 74: {'rname': 'Emby server', 'new_rid': 74}}
    #
    #     returned = validate_rockons(self.sa_ml)
    #     self.assertEqual(
    #         returned,
    #         expected,
    #         msg="Un-expected validate_rockons() result:\n "
    #             "returned = {}.\n "
    #             "expected = {}.".format(returned, expected),
    #     )

    def test_update_rockon_shares(self):
        # cids = [52, 62, 81, 79, 80]
        # rids = [48, 58, 75, 74, 74]
        cid = [52]
        rid = [48]
        expected_rockons = [
            {
                48: {
                    "environment": {},
                    "rname": "Emby server",
                    "containers": [52],
                    "shares": {"emby-media": "/media", "emby-conf": "/config"},
                    "cc": {},
                    "new_rid": 48,
                    "devices": {},
                    "ports": {},
                },
                58: {
                    "environment": {},
                    "rname": "MariaDB",
                    "containers": [62],
                    "shares": {},
                    "cc": {},
                    "new_rid": 58,
                    "devices": {},
                    "ports": {},
                },
                75: {
                    "environment": {},
                    "rname": "Alpine With AddStorage Single",
                    "containers": [81],
                    "shares": {},
                    "cc": {},
                    "new_rid": 75,
                    "devices": {},
                    "ports": {},
                },
                74: {
                    "environment": {},
                    "rname": "Alpine With AddStorage 2Ports",
                    "containers": [79, 80],
                    "shares": {},
                    "cc": {},
                    "new_rid": 74,
                    "devices": {},
                    "ports": {},
                },
            }
        ]

        cid.append(62)
        rid.append(58)
        expected_rockons.append(
            {
                48: {
                    "environment": {},
                    "rname": "Emby server",
                    "containers": [52],
                    "shares": {},
                    "cc": {},
                    "new_rid": 48,
                    "devices": {},
                    "ports": {},
                },
                58: {
                    "environment": {},
                    "rname": "MariaDB",
                    "containers": [62],
                    "shares": {"test_share09": "/config"},
                    "cc": {},
                    "new_rid": 58,
                    "devices": {},
                    "ports": {},
                },
                75: {
                    "environment": {},
                    "rname": "Alpine With AddStorage Single",
                    "containers": [81],
                    "shares": {},
                    "cc": {},
                    "new_rid": 75,
                    "devices": {},
                    "ports": {},
                },
                74: {
                    "environment": {},
                    "rname": "Alpine With AddStorage 2Ports",
                    "containers": [79, 80],
                    "shares": {},
                    "cc": {},
                    "new_rid": 74,
                    "devices": {},
                    "ports": {},
                },
            }
        )

        cid.append(81)
        rid.append(75)
        expected_rockons.append(
            {
                48: {
                    "environment": {},
                    "rname": "Emby server",
                    "containers": [52],
                    "shares": {},
                    "cc": {},
                    "new_rid": 48,
                    "devices": {},
                    "ports": {},
                },
                58: {
                    "environment": {},
                    "rname": "MariaDB",
                    "containers": [62],
                    "shares": {},
                    "cc": {},
                    "new_rid": 58,
                    "devices": {},
                    "ports": {},
                },
                75: {
                    "environment": {},
                    "rname": "Alpine With AddStorage Single",
                    "containers": [81],
                    "shares": {},
                    "cc": {},
                    "new_rid": 75,
                    "devices": {},
                    "ports": {},
                },
                74: {
                    "environment": {},
                    "rname": "Alpine With AddStorage 2Ports",
                    "containers": [79, 80],
                    "shares": {},
                    "cc": {},
                    "new_rid": 74,
                    "devices": {},
                    "ports": {},
                },
            }
        )

        cid.append(79)
        rid.append(74)
        expected_rockons.append(
            {
                48: {
                    "environment": {},
                    "rname": "Emby server",
                    "containers": [52],
                    "shares": {},
                    "cc": {},
                    "new_rid": 48,
                    "devices": {},
                    "ports": {},
                },
                58: {
                    "environment": {},
                    "rname": "MariaDB",
                    "containers": [62],
                    "shares": {},
                    "cc": {},
                    "new_rid": 58,
                    "devices": {},
                    "ports": {},
                },
                75: {
                    "environment": {},
                    "rname": "Alpine With AddStorage Single",
                    "containers": [81],
                    "shares": {},
                    "cc": {},
                    "new_rid": 75,
                    "devices": {},
                    "ports": {},
                },
                74: {
                    "environment": {},
                    "rname": "Alpine With AddStorage 2Ports",
                    "containers": [79, 80],
                    "shares": {},
                    "cc": {},
                    "new_rid": 74,
                    "devices": {},
                    "ports": {},
                },
            }
        )

        cid.append(80)
        rid.append(74)
        expected_rockons.append(
            {
                48: {
                    "environment": {},
                    "rname": "Emby server",
                    "containers": [52],
                    "shares": {},
                    "cc": {},
                    "new_rid": 48,
                    "devices": {},
                    "ports": {},
                },
                58: {
                    "environment": {},
                    "rname": "MariaDB",
                    "containers": [62],
                    "shares": {},
                    "cc": {},
                    "new_rid": 58,
                    "devices": {},
                    "ports": {},
                },
                75: {
                    "environment": {},
                    "rname": "Alpine With AddStorage Single",
                    "containers": [81],
                    "shares": {},
                    "cc": {},
                    "new_rid": 75,
                    "devices": {},
                    "ports": {},
                },
                74: {
                    "environment": {},
                    "rname": "Alpine With AddStorage 2Ports",
                    "containers": [79, 80],
                    "shares": {},
                    "cc": {},
                    "new_rid": 74,
                    "devices": {},
                    "ports": {},
                },
            }
        )

        for c, r, out in zip(cid, rid, expected_rockons):
            rockons = {
                48: {
                    "rname": "Emby server",
                    "cc": {},
                    "devices": {},
                    "new_rid": 48,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [52],
                },
                58: {
                    "rname": "MariaDB",
                    "cc": {},
                    "devices": {},
                    "new_rid": 58,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [62],
                },
                75: {
                    "rname": "Alpine With AddStorage Single",
                    "cc": {},
                    "devices": {},
                    "new_rid": 75,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [81],
                },
                74: {
                    "rname": "Alpine With AddStorage 2Ports",
                    "cc": {},
                    "devices": {},
                    "new_rid": 74,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [79, 80],
                },
            }
            rockons = update_rockon_shares(c, self.sa_ml, r, rockons)
            self.assertEqual(
                rockons,
                out,
                msg="Un-expected update_rockon_shares() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(rockons, out),
            )

    def test_validate_install_config(self):
        # rids = [48, 58, 75, 74]
        rid = [48]
        out = [
            {
                48: {
                    "rname": "Emby server",
                    "cc": {},
                    "devices": {"VAAPI": ""},
                    "new_rid": 48,
                    "environment": {"GID": "1000", "GIDLIST": "100"},
                    "shares": {"emby-media": "/media", "emby-conf": "/config"},
                    "ports": {8096: 8096, 8920: 8920},
                    "containers": [52],
                },
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        ]

        rid.append(58)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {
                    "rname": "MariaDB",
                    "cc": {},
                    "devices": {},
                    "new_rid": 58,
                    "environment": {
                        "MYSQL_ROOT_PASSWORD": "mariadb",
                        "PUID": "1000",
                        "PGID": "1000",
                    },
                    "shares": {"test_share09": "/config"},
                    "ports": {3306: 3306},
                    "containers": [62],
                },
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        )

        rid.append(75)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {
                    "rname": "Alpine With AddStorage Single",
                    "cc": {},
                    "devices": {},
                    "new_rid": 75,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [81],
                },
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        )

        rid.append(74)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {
                    "rname": "Alpine With AddStorage 2Ports",
                    "cc": {},
                    "devices": {},
                    "new_rid": 74,
                    "environment": {},
                    "shares": {},
                    "ports": {},
                    "containers": [79, 80],
                },
            }
        )

        for r, o in zip(rid, out):
            rockons = {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
            rockons = validate_install_config(self.sa_ml, r, rockons)
            self.assertEqual(
                rockons,
                o,
                msg="Un-expected validate_install_config() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(rockons, o),
            )

    def test_validate_update_config(self):
        rid = [48]
        out = [
            {
                48: {
                    "rname": "Emby server",
                    "cc": {},
                    "labels": {"test3": "embyserver"},
                    "devices": {"VAAPI": ""},
                    "new_rid": 48,
                    "environment": {"GID": "1000", "GIDLIST": "100"},
                    "shares": {"/test_share08": "test_share08"},
                    "ports": {8096: 8096, 8920: 8920},
                    "containers": [52],
                },
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        ]

        rid.append(58)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {
                    "rname": "MariaDB",
                    "cc": {},
                    "labels": {"test4": "linuxserver-mariadb"},
                    "devices": {},
                    "new_rid": 58,
                    "environment": {
                        "MYSQL_ROOT_PASSWORD": "mariadb",
                        "PUID": "1000",
                        "PGID": "1000",
                    },
                    "shares": {"/test_share07": "test_share07"},
                    "ports": {3306: 3306},
                    "containers": [62],
                },
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        )

        rid.append(75)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {
                    "rname": "Alpine With AddStorage Single",
                    "cc": {},
                    "labels": {"test2": "alpinesingle"},
                    "devices": {},
                    "new_rid": 75,
                    "environment": {},
                    "shares": {"/test_share09": "test_share09"},
                    "ports": {},
                    "containers": [81],
                },
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
        )

        rid.append(74)
        out.append(
            {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {
                    "rname": "Alpine With AddStorage 2Ports",
                    "cc": {},
                    "labels": {"test1": "alpine2p1"},
                    "devices": {},
                    "new_rid": 74,
                    "environment": {},
                    "shares": {"/test_share10": "test_share10"},
                    "ports": {},
                    "containers": [79, 80],
                },
            }
        )

        for r, o in zip(rid, out):
            rockons = {
                48: {"rname": "Emby server", "new_rid": 48},
                58: {"rname": "MariaDB", "new_rid": 58},
                75: {"rname": "Alpine With AddStorage Single", "new_rid": 75},
                74: {"rname": "Alpine With AddStorage 2Ports", "new_rid": 74},
            }
            rockons = validate_install_config(self.sa_ml, r, rockons)
            rockons = validate_update_config(self.sa_ml, r, rockons)
            self.assertEqual(
                rockons,
                o,
                msg="Un-expected validate_update_config() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(rockons, o),
            )

    def test_validate_service_status(self):
        """
        Test correct parsing of sm_ml for two services:
        - docker service is set as ON below
        - shellinabox service is set as OFF below
        """
        services = {
            "docker": {"id": 14, "conf": {"config": {"root_share": "rockons-root"}}}
        }
        out = [True]

        services.update(
            {
                "shellinaboxd": {
                    "id": 15,
                    "conf": {
                        "config": {
                            "detach": False,
                            "css": "white-on-black",
                            "shelltype": "LOGIN",
                        }
                    },
                }
            }
        )
        out.append(False)

        for s, o in zip(services, out):
            ret = validate_service_status(self.sm_ml, services[s]["id"])
            self.assertEqual(
                ret,
                o,
                msg="Un-expected validate_service_status() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(ret, o),
            )

    def test_validate_taskdef_meta(self):
        """
        Input as per sm_ml above:
        The share in question is test_share01, which has:
          - an ID of 2 in sa_ml above
          - an ID of 3 in the test_config_backup.json fixture
        """
        task_type = ["snapshot"]  # list as will receive appends later on
        taskdef_meta = [
            {
                "writable": True,
                "visible": True,
                "prefix": "snap_daily_ts01",
                "share": "2",
                "max_count": "4",
            }
        ]
        out = [
            {
                "writable": True,
                "visible": True,
                "prefix": "snap_daily_ts01",
                "share": "3",
                "max_count": "4",
            }
        ]

        task_type.append("scrub")
        taskdef_meta.append({"pool_name": "rock-pool", "pool": "2"})
        out.append({"pool_name": "rock-pool", "pool": "2"})

        task_type.append("scrub")
        taskdef_meta.append({"pool_name": "rock-pool2", "pool": "3"})
        out.append({"pool_name": "rock-pool2", "pool": "4"})

        for t, m, o in zip(task_type, taskdef_meta, out):
            ret = validate_taskdef_meta(self.sa_ml, m, t)
            self.assertEqual(
                ret,
                o,
                msg="Unexpected validate_taskdef_meta() result:\n "
                "returned = {}.\n "
                "expected = {}.".format(ret, o),
            )

    def test_validate_task_definitions(self):
        """
        Test the correct parsing
        Snapshot:
        - valid metadata (snap_daily_ts01 in sm_ml)
        - invalid metadata: wrong share ID in backup file (snap_daily_ts02 in sm_ml)
        - invalid metadata: share does not exist on target system (snap_daily_ts04 in sm_ml)

        Scrub:
        - valid metadata: no pool ID change (rockpool_scrub in sm_ml)
        - valid metadata: with pool ID change (rockpool2_scrub in sm_ml)
        - invalid metadata: pool does not exist on target system (boguspool_scrub in sm_ml)
        """
        out = [
            {
                "task_type": "snapshot",
                "name": "snap_daily_ts01",
                "crontabwindow": "*-*-*-*-*-*",
                "enabled": False,
                "crontab": "42 3 * * *",
                "meta": {
                    "writable": True,
                    "visible": True,
                    "prefix": "snap_daily_ts01",
                    "share": "3",
                    "max_count": "4",
                },
            },
            {
                "task_type": "scrub",
                "name": "rockpool_scrub",
                "crontabwindow": "*-*-*-*-*-*",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {"pool_name": "rock-pool", "pool": "2"},
            },
            {
                "task_type": "scrub",
                "name": "rockpool2_scrub",
                "crontabwindow": "*-*-*-*-*-*",
                "enabled": False,
                "crontab": "42 3 * * 5",
                "meta": {"pool_name": "rock-pool2", "pool": "4"},
            },
        ]
        ret = validate_task_definitions(self.sm_ml, self.sa_ml)
        self.assertEqual(
            ret,
            out,
            msg="Unexpected validate_task_definitions() result:\n "
            "returned = {}.\n "
            "expected = {}.".format(ret, out),
        )
