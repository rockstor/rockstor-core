#!/usr/bin/env python
"""
Copyright (c) 2012-2017 RockStor, Inc. <http://rockstor.com>
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

from setuptools import setup

VERSION = '1.4.1'

setup(
    name='rockstor',
    version=VERSION,
    description='Store Smartly',
    author='RockStor, Inc.',
    author_email='support@rockstor.com',

    packages=['storageadmin', 'smart_manager', ],
    package_dir={'': 'src/rockstor'},
    entry_points={
        'console_scripts': [
            'backup-plugin = backup.scheduler:main',
            'backup-config = scripts.config_backup:main',
            'bootstrap = scripts.bootstrap:main',
            'data-collector = smart_manager.data_collector:main',
            'debug-mode = scripts.debugmode:main',
            'delete-api-key = scripts.delete_api_key:main',
            'delete-rockon = scripts.rockon_delete:delete_rockon',
            'docker-wrapper = scripts.docker_wrapper:main',
            'flash-optimize = scripts.flash_optimize:main',
            'initrock = scripts.initrock:main',
            'mnt-share = scripts.mount_share:mount_share',
            'ovpn-client-gen = scripts.ovpn_util:client_gen',
            'ovpn-client-print = scripts.ovpn_util:client_retrieve',
            'ovpn-initpki = scripts.ovpn_util:initpki',
            'prep_db = scripts.prep_db:main',
            'pwreset = scripts.pwreset:main',
            'qgroup-clean = scripts.qgroup_clean:main',
            'qgroup-maxout-limit = scripts.qgroup_maxout_limit:main',
            'qgroup-test = scripts.qgroup_test:main',
            'rcli = cli.rock_cli:main',
            'replicad = smart_manager.replication.listener_broker:main',
            'rockon-json = scripts.rockon_util:main',
            'send-replica = scripts.scheduled_tasks.send_replica:main',
            'st-pool-scrub = scripts.scheduled_tasks.pool_scrub:main',
            'st-snapshot = scripts.scheduled_tasks.snapshot:main',
            'st-system-power = scripts.scheduled_tasks.reboot_shutdown:main',
        ],
    },

    install_requires=[
        'URLObject == 2.1.1',
        'chardet == 2.3.0',
        'coverage',
        'distribute >= 0.6.35',
        'django == 1.8.16',
        'django-oauth-toolkit == 0.9.0',
        'django-pipeline == 1.6.9',
        'django-ztask == 0.1.5',
        'djangorestframework == 3.1.1',
        'python-engineio == 2.3.2',  # Revisit version post 3.0.0
        'gevent == 1.1.2',
        'gevent-websocket == 0.9.5',
        'mock == 1.0.1',
        'psutil == 3.3.0',
        'psycogreen == 1.0',
        'psycopg2 == 2.7.4',
        'python-socketio == 1.6.0',
        'pytz == 2014.3',
        'pyzmq == 15.0.0',
        'requests == 1.1.0',
        'six == 1.10.0',
        'distro',
    ]

)
