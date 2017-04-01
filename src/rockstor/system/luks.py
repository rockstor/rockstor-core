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

import re
from system.osi import run_command
import logging

logger = logging.getLogger(__name__)

CRYPTSETUP = '/usr/sbin/cryptsetup'


def get_luks_container_dev(mapped_device_name, test=None):
    """
    Returns the parent device of an open LUKS container, ie if passed:
    /dev/mapper/luks-b8f89d97-f135-450f-9620-80a9fb421403
    it would return the following example device name string:
    /dev/sda3
    So /dev/sda3 is the LUKS container that once opened is mapped as our
    device_name in /dev/mapper
    :param mapped_device_name: any mapped device name accepted by cryptsetup,
    ie starting with "/dev/mapper/"
    :param test: if not None then it's contents is considered as substitute
    for the output of the cryptsetup command that is otherwise executed.
    :return: Empty string on any error or a device with path
    """
    # if non luks device then return empty string
    if re.match('/dev/mapper/luks-', mapped_device_name) is None:
        return ''
    container_dev = ''
    if test is None:
        out, err, rc = run_command([CRYPTSETUP, 'status' + mapped_device_name],
                                   throw=False)
    else:
        # test mode so process test instead of cryptsetup output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return empty string
        return ''
    # search output of cryptsetup to find a line such as the following:
    #   device:  /dev/sda3
    for line in out:
        if line == '':
            continue
        # get line fields
        line_fields = line.split()
        # less than 2 fields are of no use so just in case:-
        if len(line_fields) < 2:
            continue
        if re.match('device:', line_fields[0]) is not None:
            # we have our line match so return it's second member
            logger.debug('get_luks_container_dev return = %s' % line_fields[1])
            return line_fields[1]
    return container_dev

