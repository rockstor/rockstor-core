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
  description='Smart Powerful Storage Solution',
  author='RockStor, Inc.',
  author_email='help@rockstor.com',

  packages=['storageadmin', 'smart_manager',],
  package_dir={'': 'src/rockstor'},
  entry_points={
        'console_scripts': [
            'sm = smart_manager.smd:main',
            'rcli = cli.rock_cli:main',
            'prep_db = prep_db:main',
            'replicad = smart_manager.replication.scheduler:main',
            ],
        },

  dependency_links = ['http://rockstor.com/downloads/gevent-socketio-0.3.6.tgz'],

  install_requires=[
    'django == 1.4.3',
    'distribute >= 0.6.35',
    'URLObject == 2.1.1',
    'djangorestframework == 2.1.15',
    'pytz',
    'django-pipeline == 1.2.23',
    'socketIO-client == 0.3',
    'gevent-socketio == 0.3.6',
    'requests == 1.1.0',
    'pyzmq == 13.0.0',
    'South == 0.7.6',
  ]
)
