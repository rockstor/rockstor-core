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
from osi import run_command

SMART = '/usr/sbin/smartctl'


def info(device):
    #get smart info of the device, such as availability
    o, e, rc = run_command([SMART, '--info', device])

def capabilities(device):
    #such information as which tests does the device supported_services
    o, e, rc = run_command([SMART, '-c', device])

def run_test(device, test):
    #start a smart test(short, long or conveyance)
    o, e, rc = run_command([SMART, '-t', test, device])

def test_results(device, test):
    #get results of a specific test
    o, e, rc = run_command([SMART, '-l', test, device])

def available(device):
    #return true if SMART support is available on the device
    o, e, rc = run_command([SMART, '--info', ('/dev/%s' % device)])
    a = False
    e = False
    for i in o:
        if (re.match('SMART support is: Available', i) is not None):
            a = True
        if (re.match('SMART support is: Enabled', i) is not None):
            e = True
    return a, e

def toggle_smart(device, enable=False):
    switch = 'on' if (enable) else 'off'
    #enable SMART support of the device
    return run_command([SMART, '--smart=%s' % switch, '/dev/%s' % device])
