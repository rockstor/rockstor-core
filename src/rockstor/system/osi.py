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
import os
import subprocess
import shutil
import socket

from exceptions import CommandException

MKDIR = '/bin/mkdir'
RMDIR = '/bin/rmdir'
CHMOD = '/bin/chmod'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
EXPORTFS = '/usr/sbin/exportfs'
RESTART = '/sbin/restart'
EXPORT_DIR = '/export/'
SMB_CONFIG = '/etc/samba/smb.conf'
SERVICE = '/sbin/service'
HOSTID = '/usr/bin/hostid'
IFCONFIG = '/sbin/ifconfig'
NTPDATE = '/usr/sbin/ntpdate'


class Disk():

    def __init__(self, name, size, free, parted=False):
        self.name = name
        self.size = size
        self.free = free
        self.parted = parted

    def __repr__(self):
        return {'name': self.name,
                'size': self.size,
                'free': self.free,
                'parted': self.parted, }

def scan_disks(min_size):
    """
    min_size is in KB, so it is also number of blocks. Discard any disk with
    num_blocks < min_size
    """
    disks = {}
    with open('/proc/partitions') as pfo:
        for line in pfo.readlines():
            disk_fields = line.split()
            if (len(disk_fields) != 4):
                continue
            if (re.match('sd[a-z]+$|xvd[a-z]+$', disk_fields[3]) is not None):
                name = disk_fields[3]
                num_blocks = int(disk_fields[2]) # each block is 1KB
                if (num_blocks < min_size):
                    continue
                disk = Disk(name=name, size=num_blocks, free=num_blocks)
                disks[name] = disk.__repr__()
            elif (re.match('sd[a-z]+[0-9]+$|xvd[a-z]+[0-9]+$', disk_fields[3])
                  is not None):
                name = disk_fields[3][0:3]
                if (name in disks):
                    del(disks[name])
        return disks

def run_command(cmd, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, throw=True):
    p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr)
    out, err = p.communicate()
    out = out.split('\n')
    err = err.split('\n')
    rc = p.returncode
    if (throw and rc != 0):
        raise CommandException(out, err, rc)
    return (out, err, rc)

def uptime():
    with open('/proc/uptime') as ufo:
        return int(float(ufo.readline().split()[0]))

def create_tmp_dir(dirname):
    return run_command([MKDIR, '-p', dirname])

def rm_tmp_dir(dirname):
    return run_command([RMDIR, dirname])

def nfs4_mount_teardown(export_pt):
    """
    reverse of setup. cleanup when there are no more exports
    """
    if (os.path.exists(export_pt)):
        if (os.path.ismount(export_pt)):
            run_command([UMOUNT, export_pt])
        return run_command([RMDIR, export_pt])
    return True

def refresh_nfs_exports(exports):
    """
    input format:

    {'export_point': [{'client_str': 'www.example.com',
                       'option_list': 'rw,insecure,'
                       'mnt_pt': mnt_pt,},],
                       ...}

    if 'clients' is an empty list, then unmount and cleanup.
    """
    with open('/etc/exports', 'w') as efo:
        shares = []
        for e in exports.keys():
            if (len(exports[e]) == 0):
                #do share tear down at the end, only snaps here
                if (len(e.split('/')) == 4):
                    nfs4_mount_teardown(e)
                else:
                    shares.append(e)
                continue

            if (not os.path.ismount(e)):
                run_command([MKDIR, '-p', e])
                run_command([CHMOD, '-R', '777', e])
                run_command([MOUNT, '--bind', exports[e][0]['mnt_pt'], e])
            client_str = ''
            for c in exports[e]:
                client_str = ('%s%s(%s) ' % (client_str, c['client_str'],
                                             c['option_list']))
            export_str = ('%s %s\n' % (e, client_str))
            efo.write(export_str)
        for s in shares:
            nfs4_mount_teardown(s)
    return run_command([EXPORTFS, '-ra'])

def refresh_smb_config(exports, clean_config):
    shutil.copyfile(clean_config, SMB_CONFIG)
    with open(SMB_CONFIG, 'a') as sfo:
        for e in exports:
            sfo.write('[%s]\n' % e.share.name)
            sfo.write('    comment = %s\n' % e.comment)
            sfo.write('    path = %s\n' % e.path)
            sfo.write('    browsable = %s\n' % e.browsable)
            sfo.write('    read only = %s\n' % e.read_only)
            sfo.write('    create mask = %s\n' % e.create_mask)
    return True

def restart_samba():
    """
    call whenever config is updated
    """
    smbd_cmd = [SERVICE, 'smb', 'restart']
    return run_command(smbd_cmd)

def hostid():
    """
    return the hostid of the machine
    """
    return run_command([HOSTID])

def restart_network():
    """
    restart network service
    """
    cmd = [SERVICE, 'network', 'restart']
    return run_command(cmd)

def network_devices():
    """
    return all network devices on the system
    """
    devices = os.listdir('/sys/class/net')
    if ('lo' in devices):
        devices.remove('lo')
    return devices

def get_mac_addr(interface):
    """
    return the mac address of the given interface
    """
    ifile = ('/sys/class/net/%s/address' % interface)
    with open(ifile) as ifo:
        return ifo.readline().strip()

def get_ip_addr(interface):
    """
    useful when the interface gets ip from a dhcp server
    """
    out, err, rc = run_command([IFCONFIG, interface])
    line2 = out[1].strip()
    if (re.match('inet addr', line2) is not None):
        return line2.split()[1].split(':')[1]
    return '0.0.0.0'

def config_network_device(name, mac, ipaddr, netmask):
    config_script = ('/etc/sysconfig/network-scripts/ifcfg-%s' % name)
    with open(config_script, 'w') as cfo:
        cfo.write('DEVICE="%s"\n' % name)
        cfo.write('HWADDR="%s"\n' % mac)
        cfo.write('BOOTPROTO="static"\n')
        cfo.write('ONBOOT="yes"\n')
        cfo.write('IPADDR="%s"\n' % ipaddr)
        cfo.write('NETMASK="%s"\n' % netmask)

def char_strip(line, char='"'):
    if (line[0] == char and line[-1] == char):
        return line[1:-1]
    return line

def get_net_config(device_name):
    config = {'name': device_name,
              'bootproto': None,
              'onboot': None,
              'network': None,
              'netmask': None,
              'ipaddr': None,}
    config['mac'] = get_mac_addr(device_name)
    try:
        config_script = ('/etc/sysconfig/network-scripts/ifcfg-%s' %
                         device_name)
        with open(config_script) as cfo:
            for l in cfo.readlines():
                if (re.match('BOOTPROTO', l) is not None):
                    config['bootproto'] = char_strip(l.strip().split('=')[1])
                elif (re.match('ONBOOT', l) is not None):
                    config['onboot'] = char_strip(l.strip().split('=')[1])
                elif (re.match('IPADDR', l) is not None):
                    config['ipaddr'] = char_strip(l.strip().split('=')[1])
                elif (re.match('NETMASK', l) is not None):
                    config['netmask'] = char_strip(l.strip().split('=')[1])
                elif (re.match('NETWORK', l) is not None):
                    config['network'] = char_strip(l.strip().split('=')[1])
        if (config['bootproto'] == 'dhcp'):
            config['ipaddr'] = get_ip_addr(device_name)
    except:
        pass
    finally:
        return config

def set_networking(hostname, default_gw):
    with open('/etc/sysconfig/network', 'w') as nfo:
        nfo.write('NETWORKING=yes\n')
        nfo.write('HOSTNAME=%s\n' % hostname)
        nfo.write('GATEWAY=%s\n' % default_gw)

def set_nameservers(servers):
    with open('/etc/resolv.conf', 'w') as rfo:
        for s in servers:
            rfo.write('nameserver %s\n' % s)

def set_ntpserver(server):
    return run_command([NTPDATE, server])
