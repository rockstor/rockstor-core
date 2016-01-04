#!/usr/bin/env python
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
            'rcli = cli.rock_cli:main',
            'prep_db = scripts.prep_db:main',
            'replicad = smart_manager.replication.listener_broker:main',
            'mgmt_ip = scripts.mgmt_ip:main',
            'pwreset = scripts.pwreset:main',
            'backup-plugin = backup.scheduler:main',
            'initrock = scripts.initrock:main',
            'data-collector = smart_manager.data_collector:main',
            'docker-wrapper = scripts.docker_wrapper:main',
            'ovpn-initpki = scripts.ovpn_util:initpki',
            'ovpn-client-gen = scripts.ovpn_util:client_gen',
            'ovpn-client-print = scripts.ovpn_util:client_retrieve',
            'qgroup-clean = scripts.qgroup_clean:main',
            'qgroup-maxout-limit = scripts.qgroup_maxout_limit:main',
            'rockon-json = scripts.rockon_util:main',
            'flash-optimize = scripts.flash_optimize:main',
            'st-snapshot = scripts.scheduled_tasks.snapshot:main',
            'st-pool-scrub = scripts.scheduled_tasks.pool_scrub:main',
            'delete-api-key = scripts.delete_api_key:main',
            'bootstrap = scripts.bootstrap:main',
            'send-replica = scripts.scheduled_tasks.send_replica:main',
        ],
    },

    install_requires=[
        'django == 1.6.11',
        'distribute >= 0.6.35',
        'URLObject == 2.1.1',
        'djangorestframework == 3.1.1',
        'pytz == 2014.3',
        'django-pipeline == 1.2.23',
        'requests == 1.1.0',
        'pyzmq == 15.0.0',
        'South == 1.0.2',
        'psycopg2 == 2.6',
        'django-oauth-toolkit == 0.9.0',
        'six == 1.7.3',
        'django-ztask == 0.1.5',
        'mock == 1.0.1',
        'coverage',
        'gevent-socketio',
        'psycogreen',
        'psutil == 3.3.0',
    ]

)
