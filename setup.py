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
        #'URLObject == 2.1.1',
        #'chardet == 2.3.0',
        #'distribute >= 0.6.35',
        #'django == 1.8.16',
        #'django-oauth-toolkit == 0.9.0',
        #'django-pipeline == 1.6.9',
        #'huey == 2.3.0',
        #'djangorestframework == 3.1.1',
        #'python-engineio == 2.3.2',  # Revisit version post 3.0.0
        #'gevent == 1.1.2',
        #'gevent-websocket == 0.9.5',
        #'mock == 1.0.1',
        #'psutil == 3.3.0',
        #'psycogreen == 1.0',
        #'psycopg2 == 2.7.4',
        #'python-socketio == 1.6.0',
        #'pytz == 2014.3',
        #'pyzmq == 15.0.0',
        #'requests == 1.1.0',
        #'six == 1.14.0',  # 1.14.0 (15 Jan 2020) Python 2/3 compat lib
        #'distro',
        #'django-braces == 1.13.0',  # 1.14.0 (30 Dec 2019) needs Django 1.11.0+
        'asgiref == 3.5.0',
        'backports.zoneinfo == 0.2.1',
        'bidict == 0.22.0',
        'certifi == 2021.10.8',
        'cffi == 1.15.0',
        'chardet == 4.0.0',
        'charset-normalizer == 2.0.12',
        'cryptography == 36.0.2',
        'Deprecated == 1.2.13',
        'distro == 1.7.0',
        'Django == 4.0.3',
        'django-braces == 1.15.0',
        'django-oauth-toolkit == 1.7.1',
        'django-pipeline == 2.0.8',
        'djangorecipe == 2.2.1',
        'djangorestframework == 3.13.1',
        'gevent == 21.12.0',
        'gevent-websocket == 0.10.1',
        'greenlet == 1.1.2',
        'huey == 2.4.3',
        'idna == 3.3',
        'jwcrypto == 1.0',
        'mock == 4.0.3',
        'oauthlib == 3.2.0',
        'psutil == 5.9.0',
        'psycogreen == 1.0.2',
        'psycopg2 == 2.9.3',
        # 'psycopg2-binary==2.9.3,
        'pycparser == 2.21',
        'python-engineio == 4.3.1',
        'python-socketio == 5.5.2',
        'pytz == 2022.1',
        'pyzmq == 22.3.0',
        'requests == 2.27.1',
        'sqlparse == 0.4.2',
        'urllib3 == 1.26.9',
        'URLObject == 2.4.3',
        'wrapt == 1.14.0',
        'zc.buildout == 2.13.7',
        'zc.recipe.egg == 2.0.7',
        'zope.event == 4.5.0',
        'zope.interface == 5.4.0',
    ]

)
