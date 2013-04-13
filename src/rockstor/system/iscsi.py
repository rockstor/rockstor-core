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

TGTADM_BIN = '/usr/sbin/tgtadm'
DD_BIN = '/bin/dd'

from osi import run_command


def create_target_device(tid, tname):
    cmd = [TGTADM_BIN, '--lld', 'iscsi', '--mode', 'target', '--op', 'new',
           '--tid', tid, '--targetname', tname]
    return run_command(cmd)

def add_logical_unit(tid, lun, dev_name):
    cmd = [TGTADM_BIN, '--lld', 'iscsi', '--mode', 'logicalunit', '--op',
           'new', '--tid', tid, '--lun', lun, '-b', dev_name]
    return run_command(cmd)

def ip_restrict(tid):
    """
    no restrictions at all
    """
    cmd = [TGTADM_BIN, '--lld', 'iscsi', '--mode', 'target', '--op', 'bind',
           '--tid', tid, '-I', 'ALL']
    return run_command(cmd)

def create_lun_file(dev_name, size):
    """
    size in MB
    """
    of = ('of=%s' % dev_name)
    count = ('count=%d' % size)
    cmd = [DD_BIN, 'if=/dev/zero', of, 'bs=1M', count]
    return run_command(cmd)

def export_iscsi(tid, tname, lun, dev_name, size):
    """
    main method that does everything to a share to make it available as a iscsi
    device. this should be called from the api view

    1. create the dev_name file with the given size using dd
    2. create target device
    3. add logical unit
    4. authentication??
    """
    create_lun_file(dev_name, size)
    create_target_device(tid, tname)
    add_logical_unit(tid, lun, dev_name)
    ip_restrict(tid)
