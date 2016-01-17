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
from tempfile import mkstemp
from shutil import move
import logging
from system.email_util import email_root
from exceptions import CommandException

logger = logging.getLogger(__name__)

SMART = '/usr/sbin/smartctl'
CAT = '/usr/bin/cat'
# enables reading file dumps of smartctl output instead of running smartctl
# currently hardwired to read from eg:- /root/smartdumps/smart-H--info.out
# default setting = False
TESTMODE = False


def info(device, test_mode=TESTMODE):
    """
    Retrieve matching properties found in smartctl -H --info output.
    Used to populate the Identity / general info tab by views/disk_smart.py
    :param device: disk device name
    :param test_mode: Not True causes cat from file rather than smartctl command
    :return: list of smart parameters extracted from device or test file
    """
    if not test_mode:
        o, e, rc = run_command([SMART, '-H', '--info', '/dev/%s' % device],
                               throw=False)
    else:  # we are testing so use a smartctl -H --info file dump instead
        o, e, rc = run_command([CAT, '/root/smartdumps/smart-H--info.out'],
                               throw=False)
    res = {}
    # List of string matches to look for in smartctrl -H --info output.
    # Note the "|" char allows for defining alternative matches ie A or B
    matches = ('Model Family:|Vendor:', 'Device Model:|Product:',
               'Serial Number:|Serial number:',
               'LU WWN Device Id:|Logical Unit id:',
               'Firmware Version:|Revision', 'User Capacity:',
               'Sector Size:|Logical block size:', 'Rotation Rate:',
               'Device is:', 'ATA Version is:',
               'SATA Version is:', 'Local Time is:',
               'SMART support is:.* Available',
               'SMART support is:.* Enabled',
               'SMART overall-health self-assessment|SMART Health Status:',)
    res = ['', ] * len(matches)
    version = ''
    for l in o:
        if (re.match('smartctl ', l) is not None):
            version = ' '.join(l.split()[1:4])
        for i in range(len(matches)):
            if (re.match(matches[i], l) is not None):
                res[i] = l.split(': ')[1].strip()
    res.insert(14, version)
    return res


def extended_info(device, test_mode=TESTMODE):
    """
    Retrieves a list of SMART attributes found from parsing smartctl -a output
    Mostly ATA / SATA as SCSI uses a free form syntax for this.
    Extracts all lines starting with ID# ATTRIBUTE_NAME and creates a dictionary
    of lists containing each lines column entries indexed in the dictionary via
    the Attribute name.
    :param device: disk device name
    :param testmode: Not True causes cat from file rather than smartctl command
    :return: dictionary of smart attributes extracted from device or test file
    """
    if not test_mode:
        o, e, rc = run_command([SMART, '-a', '/dev/%s' % device], throw=False)
    else:  # we are testing so use a smartctl -a file dump instead
        o, e, rc = run_command([CAT, '/root/smartdumps/smart-a.out'],
                               throw=False)
    attributes = {}
    for i in range(len(o)):
        if (re.match('Vendor Specific SMART Attributes with Thresholds:',
                     o[i]) is not None):
            if (len(o) > i + 1):
                if (re.match('ID# ATTRIBUTE_NAME', o[i + 1]) is not None):
                    for j in range(i + 2, len(o)):
                        if (o[j] == ''):
                            break
                        fields = o[j].strip().split()
                        if (len(fields) > 10):
                            fields[9] = ' '.join(fields[9:])
                        attributes[fields[1]] = fields[0:10]
    return attributes


def capabilities(device, test_mode=TESTMODE):
    """
    Retrieves a list of SMART capabilities found from parsing smartctl -c output
    ATA / SATA only.
    Extracts all capabilities and build a dictionary of lists containing
    ID, Name, Flag, and description for each capability found. The dictionary
    is indexed by the capability name.
    :param device: disk device name
    :param test_mode: Not True causes cat from file rather than smartctl command
    :return: dictionary of smart capabilities extracted from device or test file
    """
    if not test_mode:
        o, e, rc = run_command([SMART, '-c', '/dev/%s' % device])
    else:  # we are testing so use a smartctl -c file dump instead
        o, e, rc = run_command([CAT, '/root/smartdumps/smart-c.out'])
    cap_d = {}
    for i in range(len(o)):
        if (re.match('=== START OF READ SMART DATA SECTION ===',
                     o[i]) is not None):
            prev_line = None
            cur_cap = None
            cur_val = None
            for j in range(i + 2, len(o)):
                if (re.match('.*:\s+\(.*\)', o[j]) is not None):
                    cap = o[j][:o[j].index(':')]
                    flag = o[j][(o[j].index('(') + 1):o[j].index(')')].strip()
                    val = o[j][(o[j].index(')') + 1):].strip()
                    if (val == 'seconds.' or val == 'minutes.'):
                        val = '%s %s' % (flag, val)
                        flag = ''
                    if (prev_line is not None):
                        cap = '%s %s' % (prev_line, cap)
                        prev_line = None
                    cur_cap = cap
                    cap_d[cur_cap] = [flag, val]
                elif (re.match('\s', o[j]) is not None):
                    cap_d[cur_cap][1] += '\n'
                    cap_d[cur_cap][1] += o[j].strip()
                else:
                    prev_line = o[j].strip()
            break
    return cap_d


def error_logs(device, test_mode=TESTMODE):
    """
    Retrieves a parsed list of SMART errors from the output of smartctl -l error
    May be empty if no errors, also returns a raw output of the error log itself
    :param device: disk device name
    :param test_mode: Not True causes cat from file rather than smartctl command
    :return: summary: dictionary of lists containing details of error. Index is
    error number.
    :return: log_l: A list containing each line in turn of the error log.
    """
    if not test_mode:
        smart_command = [SMART, '-l', 'error', '/dev/%s' % device]
        o, e, rc = run_command(smart_command, throw=False)
    else:
        o, e, rc = run_command([CAT, '/root/smartdumps/smart-l-error.out'],
                           throw=False)
    # As we mute exceptions when calling the above command we should at least
    # examine what we have as return code (rc); 64 has been seen when the error
    # log contains errors but otherwise executes successfully so we catch this.
    overide_rc = 64
    e_msg = 'Drive /dev/%s has logged S.M.A.R.T errors. Please view ' \
                 'the Error logs tab for this device.' % device
    screen_return_codes(e_msg, overide_rc, o, e, rc, smart_command)
    ecode_map = {
        'ABRT' : 'Command ABoRTed',
        'AMNF' : 'Address Mark Not Found',
        'CCTO' :  'Command Completion Timed Out',
        'EOM' : 'End Of Media',
        'ICRC' : 'Interface Cyclic Redundancy Code (CRC) error',
        'IDNF' : 'IDentity Not Found',
        'ILI' : '(packet command-set specific)',
        'MC' : 'Media Changed',
        'MCR' : 'Media Change Request',
        'NM' : 'No Media',
        'obs' : 'obsolete',
        'TK0NF' : 'TracK 0 Not Found',
        'UNC' : 'UNCorrectable Error in Data',
        'WP' : 'Media is Write Protected',
    }
    summary = {}
    log_l = []
    for i in range(len(o)):
        if (re.match('=== START OF READ SMART DATA SECTION ===',
                     o[i]) is not None):
            err_num = None
            lifetime_hours = None
            state = None
            etype = None
            details = None
            for j in range(i + 1, len(o)):
                log_l.append(o[j])
                if (re.match('Error ', o[j]) is not None):
                    fields = o[j].split()
                    err_num = fields[1]
                    if ('lifetime:' in fields):
                        lifetime_hours = int(fields[fields.index('lifetime:')+1])
                if (re.match('When the command that caused the error occurred, the device was', o[j].strip()) is not None):
                    state = o[j].strip().split('the device was ')[1]
                if (re.search('Error: ', o[j]) is not None):
                    e_substr = o[j].split('Error: ')[1]
                    e_fields = e_substr.split()
                    etype = e_fields[0]
                    if (etype in ecode_map):
                        etype = ecode_map[etype]
                    details = ' '.join(e_fields[1:]) if (len(e_fields) > 1) else None
                    summary[err_num] = list([lifetime_hours, state, etype, details])
                    err_num = lifetime_hours = state = etype = details = None
    print ('summary_d %s' % summary)
    return (summary, log_l)


def test_logs(device, test_mode=TESTMODE):
    """
    Retrieves information from SMART Self-Test logs held by the drive.
    Creates a dictionary of previous test info, indexed by test number and a
    list containing the remaining log info, each line is an item in the list.
    :param device: disk device name
    :param test_mode: Not True causes cat from file rather than smartctl command
    :return: test_d as a dictionary of summarized test
    """
    if not test_mode:
        smart_command = [SMART, '-l', 'selftest', '-l', 'selective', '/dev/%s'
                         % device]
        o, e, rc = run_command(smart_command, throw=False)
    else:
        o, e, rc = run_command(
            [CAT, '/root/smartdumps/smart-l-selftest-l-selective.out'])
    # A return code of 128 (non zero so run_command raises an exception) has
    # been seen when executing this command. Strange as it means
    # "Invalid argument to exit" anyway if we silence the throw of a generic
    # non 0 exception we can catch the 128, akin to 64 catch in error_logs().
    # N.B. no official list of rc = 128 in /usr/include/sysexits.h
    overide_rc = 128
    e_msg = 'run_command(%s) returned an error of %s. This has undetermined ' \
            'meaning. Please view the Self-Test Logs tab for this device.' \
            % (smart_command, overide_rc)
    screen_return_codes(e_msg, overide_rc, o, e, rc, smart_command)
    test_d = {}
    log_l = []
    for i in range(len(o)):
        if (re.match('SMART Self-test log structure revision number',
                     o[i]) is not None):
            log_l.append(o[i])
            if (len(o) > (i + 1)):
                if (re.match('Num  Test_Description    Status',
                             o[i + 1]) is not None):
                    for j in range(i + 2, len(o)):
                        if (re.match('# ', o[j]) is not None):
                            fields = re.split(r'\s\s+', o[j].strip()[2:])
                            fields[3] = 100 - int(fields[3][:-1])
                            test_d[fields[0]] = fields[1:]
                        else:
                            log_l.append(o[j])
    return (test_d, log_l)


def run_test(device, test):
    # start a smart test(short, long or conveyance)
    return run_command([SMART, '-t', test, '/dev/%s' % device])


def available(device, test_mode=TESTMODE):
    """
    Returns boolean pair: true if SMART support is available on the device and
    true if SMART support is enabled.
    Used by update_disk_state in views/disk.py to assess smart status
    :param device:
    :return: available (boolean), enabled (boolean)
    """
    if not test_mode:
        o, e, rc = run_command([SMART, '--info', ('/dev/%s' % device)])
    else:  # we are testing so use a smartctl --info file dump instead
        o, e, rc = run_command([CAT, '/root/smartdumps/smart--info.out'])
    a = False
    e = False
    for i in o:
        # N.B. .* in pattern match to allow for multiple spaces
        if (re.match('SMART support is:.* Available', i) is not None):
            a = True
        if (re.match('SMART support is:.* Enabled', i) is not None):
            e = True
    return a, e


def toggle_smart(device, enable=False):
    switch = 'on' if (enable) else 'off'
    # enable SMART support of the device
    return run_command([SMART, '--smart=%s' % switch, '/dev/%s' % device])


def update_config(config):
    SMARTD_CONFIG = '/etc/smartmontools/smartd.conf'
    ROCKSTOR_HEADER = '###BEGIN: Rockstor smartd config. DO NOT EDIT BELOW THIS LINE###'
    fo, npath = mkstemp()
    with open(SMARTD_CONFIG) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            if (re.match('DEVICESCAN', line) is not None):
                # comment out this line, if not, smartd ignores everything else
                tfo.write('#%s' % line)
            elif (re.match(ROCKSTOR_HEADER, line) is None):
                tfo.write(line)
            else:
                break
        tfo.write('%s\n' % ROCKSTOR_HEADER)
        for l in config.split('\n'):
            tfo.write('%s\n' % l)

    return move(npath, SMARTD_CONFIG)


def screen_return_codes(msg_on_hit, return_code_target, o, e, rc, command):
    """
    Provides a central mechanism to screen return codes from executing smart
    commands. This is required as some non zero return codes would otherwise
    trigger a generic exception clause in our general purpose run_command.
    If the target return code is seen then email root with the message
    provided, otherwise raise a generic exception with the command information.
    N.B. May be done better by acting as a SMART run_command wrapper (Future).
    :param msg_on_hit: message used to email root
    :param return_code_target: return code to screen for
    :param o: the output from the command when it was run
    :param e: the error from the command when it was run
    :param rc: the return code from running the command
    """
    # if our return code is our target then log with our message and email root
    # with the same.
    if rc == return_code_target:
        logger.error(msg_on_hit)
        email_root('S.M.A.R.T error', msg_on_hit)
    # In all other non zero (error) instances we raise an exception as normal.
    elif rc != 0:
        e_msg = ('non-zero code(%d) returned by command: %s output: '
                 '%s error: %s' % (rc, command, o, e))
        logger.error(e_msg)
        raise CommandException(('%s' % command), o, e, rc)
