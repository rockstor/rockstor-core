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

import re
from shutil import move
from tempfile import mkstemp

from services import systemctl

SSHD_CONFIG = '/etc/ssh/sshd_config'

def update_sftp(input_list):
    """
    input list is a list of dictionaries. sample dictionary:
    {'user': 'rocky',
     'dir': '/mnt3/shareX',}

    """
    fo, npath = mkstemp()
    with open(SSHD_CONFIG) as sfo:
        for line in sfo.readlines():
            if (re.match('####BEGIN: Rockstor SFTP CONFIG####', line) is not
                None):
                fo.write(line)
                for entry in input_list:
                    fo.write('Match User %s\n' % entry['user'])
                    fo.write('\tChrootDirectory %s\n' % entry['dir'])
                    fo.write('\tForceCommand internal-sftp\n\n')
                fo.write('####END: Rockstor SFTP CONFIG####\n')
                break
            else:
                fo.write(line)
    move(npath, SSHD_CONFIG)
    return systemctl('sshd', 'reload')


