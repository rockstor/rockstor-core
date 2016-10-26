"""
This plugin creates snapper pre and post snapshots upon modifications by yum.
"""

from os import readlink, getppid
from os.path import basename
from dbus import SystemBus, Interface, DBusException
from yum.plugins import PluginYumExit, TYPE_CORE
import logging

"""
Copyright (c) 2016 RockStor, Inc. <http://rockstor.com>
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

# Yum
requires_api_version = '2.7'
plugin_type = (TYPE_CORE,)

# Own global variables
snapper = None
description = ''
pre_number = None
important = []
cleanup = 'number'
userdata = {'important': 'no'}


def init_hook(conduit):
    """Set up global settings for the other hooks.
    """
    global important, description, snapper
    important = conduit.confList('main', 'important', [])
    description = 'yum(%s)' % basename(readlink('/proc/%d/exe' % getppid()))
    try:
        bus = SystemBus()
        snapper = Interface(bus.get_object('org.opensuse.Snapper',
                                           '/org/opensuse/Snapper'),
                            dbus_interface='org.opensuse.Snapper')
    except DBusException as e:
        message = 'Could not connect to snapperd:\n  %s' % e
        raise PluginYumExit(message)


def pretrans_hook(conduit):
    """Take a snapper pre snapshot, which is marked as important depending on
    patterns specified in yum_snapper.conf.
    """
    global userdata, pre_number
    transaction = conduit.getTsInfo()
    for name in {item.name for item in transaction}:
        if any(name.startswith(item) for item in important):
            userdata['important'] = 'yes'
            break
    try:
        logging.info('Creating pre snapshot')
        pre_number = snapper.CreatePreSnapshot('root', description, cleanup,
                                               userdata)
        logging.debug('Created pre snapshot %d' % pre_number)
    except DBusException as e:
        logging.error('Pre snapshot creation failed:')
        logging.error(' %s' % e)


def posttrans_hook(conduit):
    """Take a snapper post snapshot if the pre snapshot exists.
    """
    if pre_number:
        try:
            logging.info('Creating post snapshot')
            post_number = snapper.CreatePostSnapshot('root', pre_number, '',
                                                     cleanup, userdata)
            logging.debug('Created post snapshot %d' % post_number)
        except DBusException as e:
            logging.error('Post snapshot creation failed:')
            logging.error(' %s' % e)
