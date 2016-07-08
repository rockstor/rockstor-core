"""
Copyright (c) 2012-2016 RockStor, Inc. <http://rockstor.com>
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

from osi import run_command
from services import service_status
import shutil
from tempfile import mkstemp
import re

SHELL_CONFIG = '/etc/sysconfig/shellinaboxd'
SYSTEMCTL = '/usr/bin/systemctl'

def update_shell_config(shelltype='LOGIN', css='white-on-black'):

    npath = mkstemp()
    with open(npath, 'w') as tfo:
        #Write shellinaboxd default config
        tfo.write('USER=root\n')
        tfo.write('GROUP=root\n')
        tfo.write('CERTDIR=/var/lib/shellinabox\n')
        tfo.write('PORT=4200\n')
        #Add config customization for css and shelltype
        #IMPORTANT
        #--localhost-only to block shell direct access and because behind nginx
        #--disable-ssl because already on rockstor ssl
        #--no-beep to avoid sounds and possible crashes under FF - see man pages
        tfo.write('OPTS="--no-beep --localhost-only --disable-ssl --css %s.css -s /:%s"' % 
                 (css, shelltype))

    shutil.move(npath, SHELL_CONFIG)


def restart_shell():

    #simply restart shellinaboxd service
    
    return run_command([SYSTEMCTL, 'restart', 'shellinaboxd'])

def status():
    
    return service_status('shellinaboxd')
