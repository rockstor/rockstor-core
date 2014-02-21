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
from tempfile import mkstemp
import time
from exceptions import (CommandException, NonBTRFSRootException)

HOSTS_FILE = '/etc/hosts'
MKDIR = '/bin/mkdir'
RMDIR = '/bin/rmdir'
CHMOD = '/bin/chmod'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
EXPORTFS = '/usr/sbin/exportfs'
RESTART = '/sbin/restart'
SMB_CONFIG = '/etc/samba/smb.conf'
SERVICE = '/sbin/service'
HOSTID = '/usr/bin/hostid'
IFCONFIG = '/sbin/ifconfig'
NTPDATE = '/usr/sbin/ntpdate'
LVS = '/sbin/lvs'
VGS = '/sbin/vgs'
DD = '/bin/dd'
SFDISK = '/sbin/sfdisk'
IFUP = '/sbin/ifup'
IFDOWN = '/sbin/ifdown'
ROUTE = '/sbin/route'
SYSTEMCTL = '/usr/bin/systemctl'
YUM = '/usr/bin/yum'
AT = '/usr/bin/at'
DEFAULT_MNT_DIR = '/mnt2/'
RPM = '/usr/bin/rpm'

import logging
logger = logging.getLogger(__name__)

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

def inplace_replace(of, nf, regex, nl):
    with open(of) as afo, open(nf, 'w') as tfo:
        replaced = [False,] * len(regex)
        for l in afo.readlines():
            ireplace = False
            for i in range(0, len(regex)):
                if (re.match(regex[i], l) is not None):
                    tfo.write(nl[i])
                    replaced[i] = True
                    ireplace = True
                    break
            if (not ireplace):
                tfo.write(l)
        for i in range(0, len(replaced)):
            logger.info('regex: %s nl: %s replaced: %s' % (nf, regex, nl))
            if (not replaced[i]):
                tfo.write(nl[i])

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

def wipe_disk(disk):
    """
    removes partition table on a disk by dd'ing first 512 bytes
    """
    disk = ('/dev/%s' % disk)
    run_command([DD, 'if=/dev/zero', 'of=%s' % disk, 'bs=512', 'count=1'])
    return run_command([SFDISK, '-R', disk])

def root_disk():
    """
    returns the partition(s) used for /. Typically it's sda.
    """
    with open('/proc/mounts') as fo:
        for line in fo.readlines():
            fields = line.split()
            if (fields[1] == '/' and
                (fields[2] == 'ext4' or fields[2] == 'btrfs')):
                return fields[0][5:-1]
    msg = ('root filesystem is not BTRFS. During Rockstor installation, '
           'you must select BTRFS instead of LVM and other options for '
           'root filesystem. Please re-install Rockstor properly.')
    raise NonBTRFSRootException(msg)

def scan_disks(min_size):
    """
    min_size is in KB, so it is also number of blocks. Discard any disk with
    num_blocks < min_size
    """
    root = root_disk()
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
                name = disk_fields[3][0:-1]
                if (name in disks):
                    if (name == root):
                        del(disks[name])
                    else:
                        disks[name]['parted'] = True
        return disks

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
    if (is_mounted(export_pt)):
        run_command([UMOUNT, '-l', export_pt])
        for i in range(10):
            if (not is_mounted(export_pt)):
                return run_command([RMDIR, export_pt])
            time.sleep(1)
        run_command([UMOUNT, '-f', export_pt])
    if (os.path.exists(export_pt)):
        return run_command([RMDIR, export_pt])
    return True

def bind_mount(mnt_pt, export_pt):
    if (not is_mounted(export_pt)):
        run_command([MKDIR, '-p', export_pt])
        run_command([CHMOD, '-R', '777', export_pt])
        return run_command([MOUNT, '--bind', mnt_pt, export_pt])
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

            if (not is_mounted(e)):
                bind_mount(exports[e][0]['mnt_pt'], e)
            client_str = ''
            for c in exports[e]:
                client_str = ('%s%s(%s) ' % (client_str, c['client_str'],
                                             c['option_list']))
            export_str = ('%s %s\n' % (e, client_str))
            efo.write(export_str)
        for s in shares:
            nfs4_mount_teardown(s)
    return run_command([EXPORTFS, '-ra'])

def rockstor_smb_config(fo, exports):
    fo.write('####BEGIN: Rockstor SAMBA CONFIG####\n')
    for e in exports:
        fo.write('[%s]\n' % e.share.name)
        fo.write('    comment = %s\n' % e.comment)
        fo.write('    path = %s\n' % e.path)
        fo.write('    browseable = %s\n' % e.browsable)
        fo.write('    read only = %s\n' % e.read_only)
        fo.write('    create mask = %s\n' % e.create_mask)
        fo.write('    guest ok = %s\n' % e.guest_ok)
        fo.write('    admin users = %s\n' % e.admin_users)
    fo.write('####END: Rockstor SAMBA CONFIG####\n')

def refresh_smb_config(exports):
    fh, npath = mkstemp()
    with open(SMB_CONFIG) as sfo, open(npath, 'w') as tfo:
        rockstor_section = False
        for line in sfo.readlines():
            if (re.match('####BEGIN: Rockstor SAMBA CONFIG####', line)
                is not None):
                rockstor_section = True
                rockstor_smb_config(tfo, exports)
                break
            else:
                tfo.write(line)
        if (rockstor_section is False):
            rockstor_smb_config(tfo, exports)
    shutil.move(npath, SMB_CONFIG)

def restart_samba():
    """
    call whenever config is updated
    """
    smbd_cmd = [SYSTEMCTL, 'restart', 'smb']
    return run_command(smbd_cmd)

def update_samba_discovery(ipaddr, clean_config):
    fo, npath = mkstemp()
    dest_file = '/etc/avahi/services/smb.service'
    regex = (' <name replace-wildcards="yes">')
    nl = (' <name replace-wildcards="yes">RockStor@%s</name>\n' % ipaddr,)
    inplace_replace(clean_config, npath, (regex,), nl)
    shutil.copy(npath, dest_file)
    run_command([CHMOD, '755', dest_file])
    return run_command([SYSTEMCTL, 'restart', 'avahi-daemon',])

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

def restart_network_interface(iname):
    """
    ifdown followed by ifup of a ethernet interface
    """
    run_command([IFDOWN, iname])
    return run_command([IFUP, iname])

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

def get_default_interface():
    """
    returns the interface configured with default gateway
    """
    out, err, rc = run_command([ROUTE])
    for line in out:
        fields = line.split()
        if (fields[0] == 'default'):
            return fields[-1]
    return None

def get_ip_addr(interface):
    """
    useful when the interface gets ip from a dhcp server
    """
    out, err, rc = run_command([IFCONFIG, interface])
    line2 = out[1].strip()
    if (re.match('inet ', line2) is not None):
        return line2.split()[1]
    return '0.0.0.0'

def config_network_device(name, mac, boot_proto='dhcp', ipaddr=None,
                          netmask=None, on_boot='yes', gateway=None):
    config_script = ('/etc/sysconfig/network-scripts/ifcfg-%s' % name)
    with open(config_script, 'w') as cfo:
        cfo.write('NAME="%s"\n' % name)
        cfo.write('TYPE="Ethernet"\n')
        cfo.write('HWADDR="%s"\n' % mac)
        cfo.write('BOOTPROTO="%s"\n' % boot_proto)
        cfo.write('ONBOOT="%s"\n' % on_boot)
        if (boot_proto == 'static'):
            cfo.write('IPADDR0="%s"\n' % ipaddr)
            cfo.write('NETMASK="%s"\n' % netmask)
            if (gateway is not None):
                cfo.write('GATEWAY0="%s"\n' % gateway)

def char_strip(line, char='"'):
    if (line[0] == char and line[-1] == char):
        return line[1:-1]
    return line

def parse_ifcfg(config_file, config_d):
    try:
        with open(config_file) as cfo:
            for l in cfo.readlines():
                if (re.match('BOOTPROTO', l) is not None):
                    config_d['bootproto'] = char_strip(l.strip().split('=')[1])
                elif (re.match('ONBOOT', l) is not None):
                    config_d['onboot'] = char_strip(l.strip().split('=')[1])
                elif (re.match('IPADDR', l) is not None):
                    config_d['ipaddr'] = char_strip(l.strip().split('=')[1])
                elif (re.match('NETMASK', l) is not None):
                    config_d['netmask'] = char_strip(l.strip().split('=')[1])
                elif (re.match('NETWORK', l) is not None):
                    config_d['network'] = char_strip(l.strip().split('=')[1])
                elif (re.match('NAME', l) is not None):
                    config_d['alias'] = char_strip(l.strip().split('=')[1])
        if (config_d['bootproto'] == 'dhcp'):
            config_d['ipaddr'] = get_ip_addr(config_d['name'])
    except:
        pass
    finally:
        return config_d

def get_net_config_fedora(devices):

    config_list = []
    script_dir = ('/etc/sysconfig/network-scripts/')
    for d in devices:
        config = {'name': d,
                  'alias': d,
                  'bootproto': None,
                  'onboot': None,
                  'network': None,
                  'netmask': None,
                  'ipaddr': None,}
        config['mac'] = get_mac_addr(d)
        for f in os.listdir(script_dir):
            if (re.match('ifcfg-', f) is not None and
                f != 'ifcfg-lo'):
                full_path = ('%s/%s' % (script_dir, f))
                config = parse_ifcfg(full_path, config)
        config_list.append(config)
    return config_list

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

def update_issue(ipaddr):
    shutil.copyfile('/etc/issue.rockstor', '/etc/issue')
    msg = ("\n\nYou can go to RockStor's webui by pointing your web browser"
           " to https://%s\n\n" % ipaddr)
    with open('/etc/issue', 'a') as ifo:
        ifo.write(msg)

def current_version():
    out, err, rc = run_command([RPM, '-qi', 'rockstor'], throw=False)
    if (rc != 0):
        return '0.0-0'
    return ('%s-%s' % (out[1].split(':').strip(),
                       out[2].split(':').strip()))

    return
def update_check():
    out, err, rc = run_command([YUM, 'update', 'rockstor', '--changelog',
                                '--assumeno'], throw=False)
    if (rc == 1):
        #parse the output for the following information
        #1. what's the latest update version?
        #2. what are the updates?
        updates = []
        cur_version = None
        version = None
        for i in range(len(out)):
            if (re.match('---> Package rockstor.* updated', out[i])
                is not None):
                cur_version = out[i].split()[3].split(':')[1]
            if (re.match('---> Package rockstor.* be an update', out[i])
                is not None):
                version = out[i].split()[3].split(':')[1]
            if (re.match('ChangeLog for: ', out[i]) is not None):
                i = i + 1
                while True:
                    if (len(out) > i):
                        if (out[i+1] == ''):
                            break
                        updates.append(out[i+1])
                        i = i + 1
        if (version is None):
            version = cur_version
        return (cur_version, version, updates)
    #no update available
    out, err, rc = run_command([YUM, 'info', 'installed', 'rockstor'])
    version = ('%s-%s' % (out[4].split(': ')[1], out[5].split(': ')[1]))
    return (version, version, [])

def update_run():
    fh, npath = mkstemp()
    with open(npath, 'w') as atfo:
        atfo.write('%s stop rockstor\n' % SYSTEMCTL)
        atfo.write('%s -y update\n' % YUM)
        atfo.write('/bin/rm -f %s\n' % npath)
    run_command([SYSTEMCTL, 'start', 'atd'])
    out, err, rc = run_command([AT, '-f', npath, 'now + 1 minutes'])
    time.sleep(120)
    return out, err, rc

def sethostname(ip, hostname):
    """
    edit /etc/hosts file and /etc/hostname
    """
    fh, npath = mkstemp()
    with open(HOSTS_FILE) as hfo, open(npath, 'w') as tfo:
        for line in hfo.readlines():
            if (re.match(ip, line) is None):
                tfo.write(line)
        tfo.write('%s %s\n' % (ip, hostname))
    shutil.move(npath, HOSTS_FILE)

    with open('/etc/hostname', 'w') as hnfo:
        hnfo.write('%s\n' % hostname)

def is_share_mounted(sname, mnt_prefix=DEFAULT_MNT_DIR):
    mnt_pt = mnt_prefix + sname
    return is_mounted(mnt_pt)

def is_mounted(mnt_pt):
    with open ('/proc/mounts') as pfo:
        for line in pfo.readlines():
            if (re.search(' ' + mnt_pt + ' ', line) is not None):
                return True
    return False
