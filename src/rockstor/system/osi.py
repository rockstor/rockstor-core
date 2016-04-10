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
from socket import inet_ntoa
from struct import pack
from exceptions import CommandException
import hashlib
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


HOSTS_FILE = '/etc/hosts'
MKDIR = '/bin/mkdir'
RMDIR = '/bin/rmdir'
CHMOD = '/bin/chmod'
MOUNT = '/bin/mount'
UMOUNT = '/bin/umount'
EXPORTFS = '/usr/sbin/exportfs'
RESTART = '/sbin/restart'
SERVICE = '/sbin/service'
HOSTID = '/usr/bin/hostid'
DEFAULT_MNT_DIR = '/mnt2/'
SHUTDOWN = '/usr/sbin/shutdown'
GRUBBY = '/usr/sbin/grubby'
CAT = '/usr/bin/cat'
UDEVADM = '/usr/sbin/udevadm'
GREP = '/usr/bin/grep'
NMCLI = '/usr/bin/nmcli'
HOSTNAMECTL = '/usr/bin/hostnamectl'
LSBLK = '/usr/bin/lsblk'
HDPARM = '/usr/sbin/hdparm'
SYSTEMCTL_BIN = '/usr/bin/systemctl'


def inplace_replace(of, nf, regex, nl):
    with open(of) as afo, open(nf, 'w') as tfo:
        replaced = [False, ] * len(regex)
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
            if (not replaced[i]):
                tfo.write(nl[i])


def run_command(cmd, shell=False, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, stdin=subprocess.PIPE, throw=True,
                log=False, input=None):
    try:
        cmd = map(str, cmd)
        p = subprocess.Popen(cmd, shell=shell, stdout=stdout, stderr=stderr,
                             stdin=stdin)
        out, err = p.communicate(input=input)
        out = out.split('\n')
        err = err.split('\n')
        rc = p.returncode
    except Exception, e:
        msg = ('Exception while running command(%s): %s' % (cmd, e.__str__()))
        raise Exception(msg)

    if (rc != 0):
        if (log):
            e_msg = ('non-zero code(%d) returned by command: %s. output: %s error:'
                     ' %s' % (rc, cmd, out, err))
            logger.error(e_msg)
        if (throw):
            raise CommandException(cmd, out, err, rc)
    return (out, err, rc)


def uptime():
    with open('/proc/uptime') as ufo:
        # todo check on readline here as reads a character at a time
        # todo xreadlines() reads one line at a time.
        return int(float(ufo.readline().split()[0]))


def def_kernel():
    kernel = None
    o, e, rc = run_command([GRUBBY, '--default-kernel'], throw=False)
    if (len(o) > 0):
        k_fields = o[0].split('/boot/vmlinuz-')
        if (len(k_fields) == 2):
            kernel = k_fields[1]
    return kernel


def kernel_info(supported_version):
    uname = os.uname()
    if (uname[2] != supported_version):
        e_msg = ('You are running an unsupported kernel(%s). Some features '
                 'may not work properly.' % uname[2])
        run_command([GRUBBY, '--set-default=/boot/vmlinuz-%s' % supported_version])
        e_msg = ('%s Please reboot and the system will '
                 'automatically boot using the supported kernel(%s)' %
                 (e_msg, supported_version))
        raise Exception(e_msg)
    return uname[2]


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
    fo, npath = mkstemp()
    with open(npath, 'w') as efo:
        shares = []
        for e in exports.keys():
            if (len(exports[e]) == 0):
                #  do share tear down at the end, only snaps here
                if (len(e.split('/')) == 4):
                    nfs4_mount_teardown(e)
                else:
                    shares.append(e)
                continue

            if (not is_mounted(e)):
                bind_mount(exports[e][0]['mnt_pt'], e)
            client_str = ''
            admin_host = None
            for c in exports[e]:
                run_command([EXPORTFS, '-i', '-o', c['option_list'],
                             '%s:%s' % (c['client_str'], e)])
                client_str = ('%s%s(%s) ' % (client_str, c['client_str'],
                                             c['option_list']))
                if ('admin_host' in c):
                    admin_host = c['admin_host']
            if (admin_host is not None):
                run_command([EXPORTFS, '-i', '-o', 'rw,no_root_squash',
                             '%s:%s' % (admin_host, e)])
                client_str = ('%s %s(rw,no_root_squash)' % (client_str,
                                                            admin_host))
            export_str = ('%s %s\n' % (e, client_str))
            efo.write(export_str)
        for s in shares:
            nfs4_mount_teardown(s)
    shutil.move(npath, '/etc/exports')
    return run_command([EXPORTFS, '-ra'])


def hostid():
    """
    return the hostid of the machine
    """
    return run_command([HOSTID])


def config_network_device(name, dtype='ethernet', method='auto', ipaddr=None,
                          netmask=None, autoconnect='yes', gateway=None,
                          dns_servers=None):
    #1. delete any existing connections that are using the given device.
    show_cmd = [NMCLI, 'c', 'show']
    o, e, rc = run_command(show_cmd)
    for l in o:
        fields = l.strip().split()
        if (len(fields) > 3 and fields[-1] == name):
            #fields[-3] is the uuid of the connection
            run_command([NMCLI, 'c', 'delete', fields[-3]])
    #2. Add a new connection
    add_cmd = [NMCLI, 'c', 'add', 'type', dtype, 'con-name', name, 'ifname', name]
    if (method == 'manual'):
        add_cmd.extend(['ip4', '%s/%s' % (ipaddr, netmask)])
    if (gateway is not None and len(gateway.strip()) > 0):
        add_cmd.extend(['gw4', gateway])
    run_command(add_cmd)
    #3. modify with extra options like dns servers
    if (method == 'manual'):
        mod_cmd = [NMCLI, 'c', 'mod', name, ]
        if (dns_servers is not None and len(dns_servers.strip()) > 0):
            mod_cmd.extend(['ipv4.dns', dns_servers])
        if (autoconnect == 'no'):
            mod_cmd.extend(['connection.autoconnect', 'no'])
        if (len(mod_cmd) > 4):
            run_command(mod_cmd)
    run_command([NMCLI, 'c', 'up', name])
    #wait for the interface to be activated
    num_attempts = 0
    while True:
        state = get_net_config(name)[name].get('state', None)
        if (state != 'activated'):
            time.sleep(1)
            num_attempts += 1
        else:
            break
        if (num_attempts > 30):
            msg = ('Waited %s seconds for connection(%s) state to '
                   'be activated but it has not. Giving up. current state: %s'
                   % (num_attempts, name, state))
            raise Exception(msg)


def convert_netmask(bits):
    #convert netmask bits into ip representation
    bits = int(bits)
    mask = 0
    for i in xrange(32-bits,32):
        mask |= (1 << i)
    return inet_ntoa(pack('>I', mask))

def net_config_helper(name):
    config = {}
    o, e, rc = run_command([NMCLI, '-t', 'c', 'show', name], throw=False)
    if (rc == 10):
        return config
    for l in o:
        l = l.strip()
        if ('method' in config):
            if (config['method'] == 'auto'):
                #dhcp
                if (re.match('DHCP4.OPTION.*ip_address = .+', l) is not None):
                    config['ipaddr'] = l.split('= ')[1]
                elif (re.match('DHCP4.OPTION.*:domain_name_servers = .+', l) is not None):
                    config['dns_servers'] = l.split('= ')[1]
                elif (re.match('DHCP4.OPTION.*:subnet_mask = .+', l) is not None):
                    config['netmask'] = l.split('= ')[1]
                elif (re.match('IP4.GATEWAY:.+', l) is not None):
                    config['gateway'] = l.split(':')[1]

            elif (config['method'] == 'manual'):
                #manual
                if (re.match('IP4.ADDRESS', l) is not None):
                    kv_split = l.split(':')
                    if (len(kv_split) > 1):
                        vsplit = kv_split[1].split('/')
                    if (len(vsplit) > 0):
                        config['ipaddr'] = vsplit[0]
                    if (len(vsplit) > 1):
                        config['netmask'] = convert_netmask(vsplit[1])
                elif (re.match('ipv4.dns:.+', l) is not None):
                    config['dns_servers'] = l.split(':')[1]
                elif (re.match('ipv4.gateway:.+', l) is not None):
                    config['gateway'] = l.split(':')[1]

            else:
                raise Exception('Unknown ipv4.method(%s). ' % config['method'])

        if (re.match('connection.interface-name:', l) is not None):
            config['name'] = l.split(':')[1]
        elif (re.match('connection.autoconnect:', l) is not None):
            config['autoconnect'] = l.split(':')[1]
        elif (re.match('ipv4.method:.+', l) is not None):
            config['method'] = l.split(':')[1]

        if (re.match('GENERAL.DEVICES:.+', l) is not None):
            config['dname'] = l.split(':')[1]
        elif (re.match('connection.type:.+', l) is not None):
            config['ctype'] = l.split(':')[1]
        elif (re.match('GENERAL.STATE:.+', l) is not None):
            config['state'] = l.split(':')[1]

    if ('dname' in config):
        o, e, rc = run_command([NMCLI, '-t', '-f', 'all', 'd', 'show', config['dname'],])
        for l in o:
            l = l.strip()
            if (re.match('GENERAL.TYPE:.+', l) is not None):
                config['dtype'] = l.split(':')[1]
            elif (re.match('GENERAL.HWADDR:.+', l) is not None):
                config['mac'] = l.split('GENERAL.HWADDR:')[1]
            elif (re.match('CAPABILITIES.SPEED:.+', l) is not None):
                config['dspeed'] = l.split(':')[1]

    return config

def get_net_config(all=False, name=None):
    if (all):
        o, e, rc = run_command([NMCLI, '-t', 'd', 'show'])
        devices = []
        config = {}
        for i in range(len(o)):
            if (re.match('GENERAL.DEVICE:', o[i]) is not None and
                re.match('GENERAL.TYPE:', o[i+1]) is not None and
                o[i+1].strip().split(':')[1] == 'ethernet'):
                dname = o[i].strip().split(':')[1]
                config[dname] = {'dname': dname,
                                 'mac': o[i+2].strip().split('GENERAL.HWADDR:')[1],
                                 'name': o[i+5].strip().split('GENERAL.CONNECTION:')[1],
                                 'dtype': 'ethernet', }
        for device in config:
            config[device].update(net_config_helper(config[device]['name']))
            if (config[device]['name'] == '--'):
                config[device]['name'] = device
        return config
    return {name: net_config_helper(name),}




def update_issue(ipaddr):
    msg = ("\n\nYou can go to RockStor's webui by pointing your web browser"
           " to https://%s\n\n" % ipaddr)
    with open('/etc/issue', 'w') as ifo:
        ifo.write(msg)


def sethostname(hostname):
    return run_command([HOSTNAMECTL, 'set-hostname', hostname])


def gethostname():
    o, e, rc = run_command([HOSTNAMECTL, '--static'])
    return o[0]


def is_share_mounted(sname, mnt_prefix=DEFAULT_MNT_DIR):
    mnt_pt = mnt_prefix + sname
    return is_mounted(mnt_pt)


def is_mounted(mnt_pt):
    with open('/proc/mounts') as pfo:
        for line in pfo.readlines():
            if (re.search(' ' + mnt_pt + ' ', line) is not None):
                return True
    return False


def get_md_members(device_name, test=None):
    """
    Returns the md members from a given device, if the given device is not an
    md device or the udevadm info command returns a non 0 (error) then the an
    empty string is returned.
    Example lines to parse from udevadmin:-
    E: MD_DEVICE_sda_DEV=/dev/sda
    E: MD_DEVICE_sda_ROLE=0
    E: MD_DEVICE_sdb_DEV=/dev/sdb
    E: MD_DEVICE_sdb_ROLE=1
    Based on the get_disk_serial function.
    N.B. may be deprecated on scan_disks move to udevadmin, or integrated.
    Could consider parsing "mdadm --detail /dev/md1" instead
    :param device_name: eg md126 or md0p2
    :param test: if test is not None then it's contents is used in lieu of
    udevadm output.
    :return: String of all members listed in udevadm info --name=device_name
    example: "[2]-/dev/sda[0]-/dev/sdb[1]-raid1" = 2 devices with level info
    """
    line_fields = []
    # if non md device then return empty string
    if re.match('md', device_name) is None:
        return ''
    members_string = ''
    if test is None:
        out, err, rc = run_command([UDEVADM, 'info', '--name=' + device_name],
                                   throw=False)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return empty string
        return ''
    # search output of udevadmin to find all current md members.
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().replace('=', ' ').split()
        # fast replace of '=' with space so split() can divide all fields
        # example original line "E: ID_SERIAL_SHORT=S1D5NSAF111111K"
        # less than 3 fields are of no use so just in case:-
        if len(line_fields) < 3:
            continue
        # catch the lines that begin with MD_DEVICE or MD_LEVEL
        if (re.match('MD_DEVICE|MD_LEVEL', line_fields[1]) is not None):
            # add this entries value (3rd column) to our string
            if len(line_fields[2]) == 1:
                # Surround single digits with square brackets ie the number of
                # members and the member index (assumes max 9 md members)
                members_string += '[' + line_fields[2] + '] '
            else:
                if re.match('/dev', line_fields[2]) is not None:
                    # We have a dev name so put it's serial in our string.
                    members_string += get_disk_serial(line_fields[2])
                else:
                    # > 1 char value that doesn't start with /dev, so raid level
                    members_string += line_fields[2]
    return members_string


def get_disk_serial(device_name, test=None):
    """
    Returns the serial number of device_name using udevadm to match that
    returned by lsblk. N.B. udevadm has been observed to return the following:-
    ID_SCSI_SERIAL  rarely seen
    ID_SERIAL_SHORT  often seen
    ID_SERIAL        thought to always be seen (see note below)
    N.B. if used in this order the serial is most likely to resemble that shown
    on the device label as well as that returned by the lsblk. ID_SERIAL seems
    always to appear but is sometimes accompanied by one or both of the others.
    When ID_SERIAL is accompanied by ID_SERIAL_SHORT the short variant is
    closer to lsblk and physical label. When they are both present the
    ID_SERIAL appears to be a combination of the model and the ID_SERIAL_SHORT
    ---------
    Additional personality added for md devices ie md0p1 or md126, these devices
    have no serial so we search for their MD_UUID and use that instead.
    :param device_name: eg sda
    :param test:
    :return: 12345678901234567890
    """
    serial_num = ''
    md_device = False
    line_fields = []
    if test is None:
        out, err, rc = run_command([UDEVADM, 'info', '--name=' + device_name],
                                   throw=False)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return empty string
        return ''
    # set flag for md personality if need be
    if re.match('md', device_name) is not None:
        md_device = True
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().replace('=', ' ').split()
        # fast replace of '=' with space so split() can divide all fields
        # example original line "E: ID_SERIAL_SHORT=S1D5NSAF111111K"
        # less than 3 fields are of no use so just in case:-
        if len(line_fields) < 3:
            continue
        # if we have an md device then just look for it's MD_UUID as the serial
        if md_device:
            # md device so search for MD_UUID
            if line_fields[1] == 'MD_UUID':
                serial_num = line_fields[2]
                # we have found our md serial equivalent so break to return
                break
            else:  # we are md_device but haven't found our MD_UUID line
                # move to next line of output and skip serial cascade search
                continue
        if line_fields[1] == 'ID_SCSI_SERIAL':
            # we have an instance of SCSI_SERIAL being more reliably unique
            # when present than SERIAL_SHORT or SERIAL so overwrite whatever
            # we have and look no further by breaking out of the search loop
            serial_num = line_fields[2]
            break
        elif line_fields[1] == 'ID_SERIAL_SHORT':
            # SERIAL_SHORT is better than SERIAL so just overwrite whatever we
            # have so far with SERIAL_SHORT
            serial_num = line_fields[2]
        else:
            if line_fields[1] == 'ID_SERIAL':
                # SERIAL is sometimes our only option but only use it if we
                # have found nothing else.
                if serial_num == '':
                    serial_num = line_fields[2]
    # should return one of the following in order of priority
    # SCSI_SERIAL, SERIAL_SHORT, SERIAL
    return serial_num


def get_virtio_disk_serial(device_name):
    """
    N.B. this function is deprecated by get_disk_serial
    Returns the serial number of device_name virtio disk eg /dev/vda
    Returns empty string if cat /sys/block/vda/serial command fails
    Note no serial entry in /sys/block/sda/ for real or KVM sata drives
    :param device_name: eg vda
    :return: 12345678901234567890

    Note maximum length of serial number reported = 20 chars
    But longer serial numbers can be specified in the VM XML spec file.
    The virtio block device is itself limited to 20 chars ie:-
    https://github.com/qemu/qemu/blob/
    a9392bc93c8615ad1983047e9f91ee3fa8aae75f/include/standard-headers/
    linux/virtio_blk.h
    #define VIRTIO_BLK_ID_BYTES 20  /* ID string length */

    This process may not deal well with spaces in the serial number
    but VMM does not allow this.
    """
    dev_path = ('/sys/block/%s/serial' % device_name)
    out, err, rc = run_command([CAT, dev_path], throw=False)
    if (rc != 0):
        return ''
    # our out list has one element that is the serial number, like ['11111111111111111111']
    return out[0]


def system_shutdown():
    return run_command([SHUTDOWN, '-h', 'now'])


def system_reboot():
    return run_command([SHUTDOWN, '-r', 'now'])


def md5sum(fpath):
    # return the md5sum of the given file
    if (not os.path.isfile(fpath)):
        return None
    md5 = hashlib.md5()
    with open(fpath) as tfo:
        for l in tfo.readlines():
            md5.update(l)
    return md5.hexdigest()


def get_base_device(device, test_mode=False):
    """
    Helper function that returns the full path of the base device of a partition
    or if given a base device then will return it's full path,
    ie
    input sda3 output /dev/sda
    input sda output /dev/sda
    Works as a function of lsblk list order ie base devices first. So we return
    the first start of line match to our supplied device name with the pattern
    as the first element in lsblk's output and the match target as our device.
    :param device: device name as per db entry, ie as returned from scan_disks
    :param test_mode: Not True causes cat from file rather than smartctl command
    :return: base_dev: single item list containing the root device's full path
    ie device = sda3 the base_dev = /dev/sda or [''] if no lsblk entry was found
    to match.
    """
    base_dev = ['', ]
    if not test_mode:
        out, e, rc = run_command([LSBLK])
    else:
        out, e, rc = run_command([CAT, '/root/smartdumps/lsblk.out'])
    # now examine the output from lsblk line by line
    for line in out:
        line_fields = line.split()
        if len(line_fields) < 1:
            # skip empty lines
            continue
        if re.match(line_fields[0], device):
            # We have found a device string match to our device so record it.
            base_dev[0] = '/dev/' + line_fields[0]
            break
    # Return base_dev ie [''] or first character matches to line start in lsblk.
    return base_dev



def is_rotational(device_name, test=None):
    """
    When given a device_name a udevadmin lookup takes place to look for either:
    E: ID_ATA_ROTATION_RATE_RPM non zero or ID_ATA_FEATURE_SET_AAM
    AAM = Automatic Acoustic Mamanement - ie head speed / noise tradeoff
    If neither is found for then the device is assumed to be non
    rotational. This method appears more reliable than
    "cat /sys/block/sda/queue/rotational"
    and "lsblk -d -o name,rota" which will both often report usb sticks as
    1 = rotational.
    N.B. we use --query=property and so have only 2 fields rather than 3 and
    no spaces, only '=' this simplifies the parsing required.
    :param device: list containing device name eg ['/dev/sda']
    :return: True if rotational, false if error or unknown.
    """
    rotational = False  # until we find otherwise
    logger.debug('is_rotational called with the following %s', device_name)
    if test is None:
        # todo consider changing back to throw=False for production.
        out, err, rc = run_command([UDEVADM, 'info', '--query=property',
                                    '--name=' + device_name[0]], throw=True)
    else:
        # test mode so process test instead of udevadmin output
        out = test
        rc = 0
    if rc != 0:  # if return code is an error return False
        return False
    # search output of udevadm to find signs of rotational media
    for line in out:
        if line == '':
            continue
        # nonlocal line_fields
        line_fields = line.strip().split('=')
        # example original line "ID_ATA_FEATURE_SET_AAM=1"
        # less than 2 fields are of no use so just in case:-
        if len(line_fields) < 2:
            continue
        if line_fields[0] == 'ID_ATA_ROTATION_RATE_RPM':
            # we have a rotation rate entry
            if line_fields[1] != 0:
                # non zero rotation so flag and look no further
                rotational = True
                break
        if line_fields[0] == 'ID_ATA_FEATURE_SET_AAM':
            # we have an Automatic Acoustic Managment entry
            if line_fields[1] != 0:
                # a non zero AAM entry so flag and look no further
                rotational = True
                break
    return rotational


def get_disk_power_status(device_name):
    """
    When given a disk name such as that stored in the db ie sda
    we return it's current power state via hdparm -C /dev/<disk>
    Possible states are:
    unknown - command not supported by disk
    active/idle - normal operation
    standby - low power mode, ie drive motor not active ie -y will do this
    sleeping - lowest power mode, completely shut down ie -Y will do this
    N.B. -C shouldn't spin up a drive in standby but has been reported to wake
    a drive from sleeping but we aren't going to invoke sleeping as pretty much
    any request will wake a fully sleeping drive.
    Drives in 'sleeping' mode typically require a hard or soft reset before
    becoming available for use, the kernel does this automatically however.
    :param device_name: disk name as stored in db / Disk model eg sda
    :return: single word sting of state as indicated by hdparm -C /dev/<disk>
    and if we encounter an error line in the output we return unknown.
    """
    # if we use the -C -q switches then we have only one line of output:
    # hdparm -C -q /dev/sda
    # drive state is:  active/idle
    # in some instances an error can be returned even with rc=0, we ignore this
    # ie SG_IO: bad/missing sense data, sb[]:  70 00 05 00 00 00 00 0a ......
    # We may want to ignore / return unknown when len(err) != 1
    out, err, rc = run_command([HDPARM, '-C', '-q', '/dev/%s' % device_name],
                               throw=False)
    # if len(err) != 1:
    #     logger.debug('hdparm has output to standard error of %s', err)
    if len(out) > 0:
        fields = out[0].split()
        # our line of interest has 4 fields when split by spaces, see above.
        if (len(fields) == 4):
            return fields[3]
    return 'unknown'


def set_disk_spindown(device, spindown_time):
    """
    Takes a value to be used with hdparm -S to set disk spindown time for the
    device specified.
    Executes hdparm -S spindown_time and ensures the systemd script to do the
    same on boot is also updated. Note we do not restart the systemd service
    to enact these changes in order to keep keep our drive intervention to a
    minimum.
    :param device: The name of a disk device as used in the db ie sda
    :param spindown_time: String received from settings form ie "20 minutes"
    :return:
    """
    # hdparm -S work on for example /dev/sda3 so base_dev may be redundant.
    # todo lighten by removing base_dev
    base_dev = get_base_device(device)
    # md devices result in [''] from get_base_device so do nothing and return
    # todo look to using system/osi get_md_members(device_name, test=None)
    # todo with md devices and then treat each in turn.
    if len(base_dev[0]) == 0:
        return True;
    # Don't spin down non rotational devices, skip all and return True.
    if is_rotational(base_dev) is not True:
        logger.debug('skipping hdparm -S as device not confirmed as rotational')
        return True;
    # setup hdparm command
    hdparm_command = [HDPARM, '-q', '-S', '%s' % spindown_time, '%s' % get_dev_byid_name(base_dev[0])]
    logger.debug('proposed hdparm command = %s', hdparm_command)

    update_hdparm_service(hdparm_command)

    return run_command(hdparm_command)


def get_dev_byid_name(device_name):
    """
    When given a standard dev name eg sda will return the /dev/disk/by-id
    name, or None if error or no name available.
    Works by querying udev via udevadm info --query=property --name device_name
    The first line of which (DEVLINKS) is examined and parsed for the first
    entry which has been found to be the /dev/disk/by-id symlink to our
    device_name eg:
    DEVLINKS=/dev/disk/by-id/ata-QEMU_HARDDISK_QM00005
    /dev/disk/by-path/pci-0000:00:05.0-ata-1.0
    In the above example we have the by-id name made from type, model and serial
    and a second by-path entry which is not used here.
    N.B. As the subsystem of the device is embeded in the by-id name a drive's
    by-id path will change if for example it is plugged in via usb rather than
    ata subsystem.
    :param device_name: eg sda but can also be /dev/sda or even the by-id name
    but only if the full path is specified with by-id
    :return: None if error or no DEVLINKS entry found or the full path to this
    given device_name.
    """
    out, err, rc = run_command(
        [UDEVADM, 'info', '--query=property', '--name', str(device_name)],
        throw=False)
    if len(out) > 0:
        # the output has at least one line
        # split this line by '=' and ' ' chars
        fields = out[0].replace('=', ' ').split()
        if len(fields) > 1:
            # we have at least 2 fields in this line
            if fields[0] == 'DEVLINKS':
                # return the first value directly after DEVLINKS
                return fields[1]
    # if no DEVLINKS value found or an error occurred.
    return None

def get_devname_old(device_name):
    """
    Depricated / prior version of get_devname()
    Returns the value of DEVNAME as reported by udevadm when supplied with a
    legal device name ie a full path by-id or full path by-path ie any DEVLINKS.
    Also works when supplied with eg "sda"
    Primarily intended to retrieve the full path device name from a full path
    by-id name or an abbreviated DEVNAME eg sda.
    N.B. this is a partner function to get_dev_byid_name(device_name)
    Works by sampling the second line of udevadm and confirming it begins with
    DEVNAME, then returning the value found after the '=' char.
    example line:
    DEVNAME=/dev/sda
    :param device_name: sda, /dev/sda, full path by-id or by-path
    :return: Full path of device name eg /dev/sda or None if error or no DEVNAME
    found
    """
    out, err, rc = run_command(
        [UDEVADM, 'info', '--query=property', '--name', str(device_name)],
        throw=False)
    if len(out) > 1:
        # the output has at least two lines
        # split the second line by the '=' char
        fields = out[1].split('=')
        if len(fields) > 1:
            # we have at least 2 fields in this line
            if fields[0] == 'DEVNAME':
                # return the first value directly after DEVNAME
                return fields[1]
    # if no DEVNAME value found or an error occurred.
    return None


def get_devname(device_name, addPath=False):
    """
    Intended as a light and quicker way to retrieve a device name with or
    without path (default) from any legal udevadm --name parameter
    Simple wrapper around a call to:
    udevadm info --query=name device_name
    Works with device_name of eg sda /dev/sda /dev/disk/by-id/ and /dev/disk/
    If a device doesn't exist then udevadm returns multi work advise so if more
    than one word assume failure and return None.
    N.B. if given /dev/sdc3 or equivalent DEVLINKS this method will return sdc3
    if no path is requested.
    :param device_name: legal device name to --name in udevadmin
    :return: short device name ie sda (no path) or with path /dev/sda if addPath
    is True or None if multi word response from udevadm ie "Unknown device, .."
    """
    out, err, rc = run_command(
        [UDEVADM, 'info', '--query=name', '--name', str(device_name)],
        throw=False)
    if len(out) > 0:
        # we have at least a single line of output
        fields = out[0].split()
        if len(fields) == 1:
            # we have a single word output so return it with or without path
            if addPath:
                return '/dev/%s' % fields[0]
            # return the word (device name ie sda) without added /dev/
            return fields[0]
    # a non one word reply was received on the first line from udevadm or
    return None


def update_hdparm_service(hdparm_command_list, message='test_message'):
    """
    Updates or creates the /etc/systemd/system/rockstor-hdparm.service file for
    the device_name given.
    :param hdparm_command_list: list containing the hdparm command elements
    :param message: test message to follow hdparm command on next line
    :return: None or
    """
    edit_done = False
    do_edit = False
    clear_line_count = 0
    # get our by-id device name by extracting the last hdparm list item
    device_name_byid = hdparm_command_list[-1]
    # first create a temp file to use as our output until we are done editing.
    tfo, npath = mkstemp()
    # If there is already a rockstor-hdparm.service file then we use that
    # as our source file, otherwise use conf's empty template.
    if os.path.isfile('/etc/systemd/system/rockstor-hdparm.service'):
        infile = '/etc/systemd/system/rockstor-hdparm.service'
        update = True
    else:
        infile = ('%s/rockstor-hdparm.service' % settings.CONFROOT)
        update = False
    # Create our proposed temporary file based on the source file plus edits.
    with open(infile) as ino, open(npath, 'w') as outo:
        for line in ino.readlines(): # readlines reads whole file in one go.
            logger.debug('processing line with contents %s', line)
            if do_edit and edit_done and clear_line_count != 2:
                # We must have just edited an entry so we need to skip
                # a line as each entry consists of an ExecStart= line and a
                # remark line directly afterwards, but only if clear_line_count
                # doesn't indicate an addition.
                # reset our do_edit flag and continue
                do_edit = False
                continue
            if (re.match('ExecStart=', line) is not None) and not edit_done:
                # we have found a line beginning with "ExecStart="
                if update:
                    if device_name_byid == line.split()[-1]:
                        # matching device name entry so set edit flat
                        do_edit = True
                else:  # no update and ExecStart found so set edit flag
                    do_edit = True
            # process all lines with the following
            if line == '\n':  # empty line, or rather just a newline char
                    clear_line_count += 1
            if clear_line_count == 2 and not edit_done:
                    # we are looking at our second empty line and haven't yet
                    # achieved edit_done so do our edit / addition in this case.
                    do_edit = True
            if do_edit and not edit_done:
                outo.write('ExecStart=' + ' '.join(hdparm_command_list) + '\n')
                outo.write('# %s' % hdparm_command_list[-2] + '\n')
                edit_done = True
            # mechanism to skip a line if we have just done an edit
            if not (do_edit and edit_done and clear_line_count != 2):
                # if do-edit and edit_done are both true it means we have just
                # done a line replacement so we skip copying the original line
                # over to the target file, but only if clear_line_count also
                # !=2 as this would indicate an addition where we do need to
                # copy over the original files line.
                outo.write(line)
    # now copy our temp file over to our destination as we are done editing
    shutil.move(npath, '/etc/systemd/system/rockstor-hdparm.service')
    if update is not True:
        # then this is a fresh systemd instance so enable it
        # can't use systemctrl wrapper as circular then circular dependency
        # return systemctl('rockstor-hdparm', 'enable')
        # return run_command([SYSTEMCTL_BIN, 'enable', 'rockstor-hdparm'])
        return None
    return None


