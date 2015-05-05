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

SMART = '/usr/sbin/smartctl'


def info(device):
    #get smart info of the device, such as availability
    o, e, rc = run_command([SMART, '-H', '--info', '/dev/%s' % device], throw=False)
    res = {}
    matches = ('Model Family:', 'Device Model:', 'Serial Number:',
               'LU WWN Device Id:', 'Firmware Version:', 'User Capacity:',
               'Sector Size:', 'Rotation Rate:', 'Device is:', 'ATA Version is:',
               'SATA Version is:', 'Local Time is:', 'SMART support is: Available',
               'SMART support is: Enabled', 'SMART overall-health self-assessment',)
    res = ['',] * len(matches)
    version = ''
    for l in o:
        if (re.match('smartctl ', l) is not None):
            version = ' '.join(l.split()[1:4])
        for i in range(len(matches)):
            if (re.match(matches[i], l) is not None):
                res[i] = l.split(': ')[1].strip()
    res.insert(14, version)
    return res

def extended_info(device):
    #o, e, rc = run_command([SMART, '-a', '/dev/%s' % device])
    o = ['smartctl 6.2 2013-07-26 r3841 [x86_64-linux-3.18.1-1.el7.elrepo.x86_64] (local build)', 'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org', '', '=== START OF INFORMATION SECTION ===', 'Model Family:     Western Digital Red (AF)', 'Device Model:     WDC WD20EFRX-68EUZN0', 'Serial Number:    WD-WCC4M5DW94Y5', 'LU WWN Device Id: 5 0014ee 25fca64f1', 'Firmware Version: 80.00A80', 'User Capacity:    2,000,398,934,016 bytes [2.00 TB]', 'Sector Sizes:     512 bytes logical, 4096 bytes physical', 'Rotation Rate:    5400 rpm', 'Device is:        In smartctl database [for details use: -P show]', 'ATA Version is:   ACS-2 (minor revision not indicated)', 'SATA Version is:  SATA 3.0, 6.0 Gb/s (current: 3.0 Gb/s)', 'Local Time is:    Sun Apr 26 14:14:42 2015 CDT', 'SMART support is: Available - device has SMART capability.', 'SMART support is: Enabled', '', '=== START OF READ SMART DATA SECTION ===', 'SMART overall-health self-assessment test result: PASSED', '', 'General SMART Values:', 'Offline data collection status:  (0x00)\tOffline data collection activity', '\t\t\t\t\twas never started.', '\t\t\t\t\tAuto Offline Data Collection: Disabled.', 'Self-test execution status:      (   0)\tThe previous self-test routine completed', '\t\t\t\t\twithout error or no self-test has ever ', '\t\t\t\t\tbeen run.', 'Total time to complete Offline ', 'data collection: \t\t(26760) seconds.', 'Offline data collection', 'capabilities: \t\t\t (0x7b) SMART execute Offline immediate.', '\t\t\t\t\tAuto Offline data collection on/off support.', '\t\t\t\t\tSuspend Offline collection upon new', '\t\t\t\t\tcommand.', '\t\t\t\t\tOffline surface scan supported.', '\t\t\t\t\tSelf-test supported.', '\t\t\t\t\tConveyance Self-test supported.', '\t\t\t\t\tSelective Self-test supported.', 'SMART capabilities:            (0x0003)\tSaves SMART data before entering', '\t\t\t\t\tpower-saving mode.', '\t\t\t\t\tSupports SMART auto save timer.', 'Error logging capability:        (0x01)\tError logging supported.', '\t\t\t\t\tGeneral Purpose Logging supported.', 'Short self-test routine ', 'recommended polling time: \t (   2) minutes.', 'Extended self-test routine', 'recommended polling time: \t ( 270) minutes.', 'Conveyance self-test routine', 'recommended polling time: \t (   5) minutes.', 'SCT capabilities: \t       (0x703d)\tSCT Status supported.', '\t\t\t\t\tSCT Error Recovery Control supported.', '\t\t\t\t\tSCT Feature Control supported.', '\t\t\t\t\tSCT Data Table supported.', '', 'SMART Attributes Data Structure revision number: 16', 'Vendor Specific SMART Attributes with Thresholds:', 'ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE', '  1 Raw_Read_Error_Rate     0x002f   200   200   051    Pre-fail  Always       -       0', '  3 Spin_Up_Time            0x0027   168   167   021    Pre-fail  Always       -       4566', '  4 Start_Stop_Count        0x0032   100   100   000    Old_age   Always       -       65', '  5 Reallocated_Sector_Ct   0x0033   200   200   140    Pre-fail  Always       -       0', '  7 Seek_Error_Rate         0x002e   200   200   000    Old_age   Always       -       0', '  9 Power_On_Hours          0x0032   099   099   000    Old_age   Always       -       1066', ' 10 Spin_Retry_Count        0x0032   100   253   000    Old_age   Always       -       0', ' 11 Calibration_Retry_Count 0x0032   100   253   000    Old_age   Always       -       0', ' 12 Power_Cycle_Count       0x0032   100   100   000    Old_age   Always       -       65', '192 Power-Off_Retract_Count 0x0032   200   200   000    Old_age   Always       -       44', '193 Load_Cycle_Count        0x0032   200   200   000    Old_age   Always       -       626', '194 Temperature_Celsius     0x0022   111   105   000    Old_age   Always       -       36', '196 Reallocated_Event_Count 0x0032   200   200   000    Old_age   Always       -       0', '197 Current_Pending_Sector  0x0032   200   200   000    Old_age   Always       -       0', '198 Offline_Uncorrectable   0x0030   100   253   000    Old_age   Offline      -       0', '199 UDMA_CRC_Error_Count    0x0032   200   200   000    Old_age   Always       -       0', '200 Multi_Zone_Error_Rate   0x0008   200   200   000    Old_age   Offline      -       0', '', 'SMART Error Log Version: 1', 'No Errors Logged', '', 'SMART Self-test log structure revision number 1', 'Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error', '# 1  Short offline       Completed without error       00%      1065         -', '# 2  Short offline       Completed without error       00%      1065         -', '# 3  Short offline       Completed without error       00%      1062         -', '# 4  Extended offline    Completed without error       00%      1055         -', '# 5  Extended offline    Aborted by host               90%      1050         -', '# 6  Short offline       Completed without error       00%      1049         -', '# 7  Short offline       Completed without error       00%       952         -', '', 'SMART Selective self-test log data structure revision number 1', ' SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS', '    1        0        0  Not_testing', '    2        0        0  Not_testing', '    3        0        0  Not_testing', '    4        0        0  Not_testing', '    5        0        0  Not_testing', 'Selective self-test flags (0x0):', '  After scanning selected spans, do NOT read-scan remainder of disk.', 'If Selective self-test is pending on power-up, resume after 0 minute delay.', '', '']
    attributes = {}
    for i in range(len(o)):
        if (re.match('Vendor Specific SMART Attributes with Thresholds:', o[i]) is not None):
            if (len(o) > i + 1):
                if (re.match('ID# ATTRIBUTE_NAME', o[i+1]) is not None):
                    for j in range(i+2, len(o)):
                        if (o[j] == ''):
                            break
                        fields = o[j].strip().split()
                        if (len(fields) > 10):
                            fields[9] = ' '.join(fields[9:])
                        attributes[fields[1]] = fields[0:10]
    return attributes

def capabilities(device):
    #such information as which tests does the device supported_services
    #o, e, rc = run_command([SMART, '-c', device])
    o = ['smartctl 6.2 2013-07-26 r3841 [x86_64-linux-3.18.1-1.el7.elrepo.x86_64] (local build)', 'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org', '', '=== START OF READ SMART DATA SECTION ===', 'General SMART Values:', 'Offline data collection status:  (0x00)\tOffline data collection activity', '\t\t\t\t\twas never started.', '\t\t\t\t\tAuto Offline Data Collection: Disabled.', 'Self-test execution status:      (   0)\tThe previous self-test routine completed', '\t\t\t\t\twithout error or no self-test has ever ', '\t\t\t\t\tbeen run.', 'Total time to complete Offline ', 'data collection: \t\t(26760) seconds.', 'Offline data collection', 'capabilities: \t\t\t (0x7b) SMART execute Offline immediate.', '\t\t\t\t\tAuto Offline data collection on/off support.', '\t\t\t\t\tSuspend Offline collection upon new', '\t\t\t\t\tcommand.', '\t\t\t\t\tOffline surface scan supported.', '\t\t\t\t\tSelf-test supported.', '\t\t\t\t\tConveyance Self-test supported.', '\t\t\t\t\tSelective Self-test supported.', 'SMART capabilities:            (0x0003)\tSaves SMART data before entering', '\t\t\t\t\tpower-saving mode.', '\t\t\t\t\tSupports SMART auto save timer.', 'Error logging capability:        (0x01)\tError logging supported.', '\t\t\t\t\tGeneral Purpose Logging supported.', 'Short self-test routine ', 'recommended polling time: \t (   2) minutes.', 'Extended self-test routine', 'recommended polling time: \t ( 270) minutes.', 'Conveyance self-test routine', 'recommended polling time: \t (   5) minutes.', 'SCT capabilities: \t       (0x703d)\tSCT Status supported.', '\t\t\t\t\tSCT Error Recovery Control supported.', '\t\t\t\t\tSCT Feature Control supported.', '\t\t\t\t\tSCT Data Table supported.', '', '']
    cap_d = {}
    for i in range(len(o)):
        if (re.match('=== START OF READ SMART DATA SECTION ===', o[i]) is not None):
            prev_line = None
            cur_cap = None
            cur_val = None
            for j in range(i+2, len(o)):
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

def error_logs(device):
    #o, e, rc = run_command([SMART, '-l', 'error', device])
    o = ['smartctl 6.2 2013-07-26 r3841 [x86_64-linux-3.13.0-49-generic] (local build)', 'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org', '', '=== START OF READ SMART DATA SECTION ===', 'SMART Error Log Version: 1', 'ATA Error Count: 6 (device log contains only the most recent five errors)', '\tCR = Command Register [HEX]', '\tFR = Features Register [HEX]', '\tSC = Sector Count Register [HEX]', '\tSN = Sector Number Register [HEX]', '\tCL = Cylinder Low Register [HEX]', '\tCH = Cylinder High Register [HEX]', '\tDH = Device/Head Register [HEX]', '\tDC = Device Command Register [HEX]', '\tER = Error register [HEX]', '\tST = Status register [HEX]', 'Powered_Up_Time is measured from power on, and printed as', 'DDd+hh:mm:SS.sss where DD=days, hh=hours, mm=minutes,', 'SS=sec, and sss=millisec. It "wraps" after 49.710 days.', '', 'Error 6 occurred at disk power-on lifetime: 8503 hours (354 days + 7 hours)', '  When the command that caused the error occurred, the device was active or idle.', '', '  After command completion occurred, registers were:', '  ER ST SC SN CL CH DH', '  -- -- -- -- -- -- --', '  40 51 00 ff ff ff 0f  Error: UNC at LBA = 0x0fffffff = 268435455', '', '  Commands leading to the command that caused the error were:', '  CR FR SC SN CL CH DH DC   Powered_Up_Time  Command/Feature_Name', '  -- -- -- -- -- -- -- --  ----------------  --------------------', '  60 00 08 ff ff ff 4f 00      00:00:48.499  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:00:48.498  READ FPDMA QUEUED', '  27 00 00 00 00 00 e0 00      00:00:48.497  READ NATIVE MAX ADDRESS EXT [OBS-ACS-3]', '  ec 00 00 00 00 00 a0 00      00:00:48.495  IDENTIFY DEVICE', '  ef 03 45 00 00 00 a0 00      00:00:48.495  SET FEATURES [Set transfer mode]', '', 'Error 5 occurred at disk power-on lifetime: 8503 hours (354 days + 7 hours)', '  When the command that caused the error occurred, the device was active or idle.', '', '  After command completion occurred, registers were:', '  ER ST SC SN CL CH DH', '  -- -- -- -- -- -- --', '  40 51 00 ff ff ff 0f  Error: UNC at LBA = 0x0fffffff = 268435455', '', '  Commands leading to the command that caused the error were:', '  CR FR SC SN CL CH DH DC   Powered_Up_Time  Command/Feature_Name', '  -- -- -- -- -- -- -- --  ----------------  --------------------', '  60 00 00 ff ff ff 4f 00      00:00:45.637  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:00:45.637  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:00:40.638  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:00:40.635  READ FPDMA QUEUED', '  60 00 20 ff ff ff 4f 00      00:00:35.958  READ FPDMA QUEUED', '', 'Error 4 occurred at disk power-on lifetime: 8431 hours (351 days + 7 hours)', '  When the command that caused the error occurred, the device was active or idle.', '', '  After command completion occurred, registers were:', '  ER ST SC SN CL CH DH', '  -- -- -- -- -- -- --', '  40 51 00 ff ff ff 0f  Error: UNC at LBA = 0x0fffffff = 268435455', '', '  Commands leading to the command that caused the error were:', '  CR FR SC SN CL CH DH DC   Powered_Up_Time  Command/Feature_Name', '  -- -- -- -- -- -- -- --  ----------------  --------------------', '  60 00 08 ff ff ff 4f 00      00:01:26.686  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:01:26.684  READ FPDMA QUEUED', '  27 00 00 00 00 00 e0 00      00:01:26.684  READ NATIVE MAX ADDRESS EXT [OBS-ACS-3]', '  ec 00 00 00 00 00 a0 00      00:01:26.682  IDENTIFY DEVICE', '  ef 03 45 00 00 00 a0 00      00:01:26.682  SET FEATURES [Set transfer mode]', '', 'Error 3 occurred at disk power-on lifetime: 8431 hours (351 days + 7 hours)', '  When the command that caused the error occurred, the device was active or idle.', '', '  After command completion occurred, registers were:', '  ER ST SC SN CL CH DH', '  -- -- -- -- -- -- --', '  40 51 00 ff ff ff 0f  Error: UNC at LBA = 0x0fffffff = 268435455', '', '  Commands leading to the command that caused the error were:', '  CR FR SC SN CL CH DH DC   Powered_Up_Time  Command/Feature_Name', '  -- -- -- -- -- -- -- --  ----------------  --------------------', '  60 00 20 ff ff ff 4f 00      00:01:24.067  READ FPDMA QUEUED', '  60 00 08 ff ff ff 4f 00      00:01:24.063  READ FPDMA QUEUED', '  60 00 20 ff ff ff 4f 00      00:01:23.321  READ FPDMA QUEUED', '  60 00 08 ff ff ff 4f 00      00:01:23.317  READ FPDMA QUEUED', '  60 00 20 ff ff ff 4f 00      00:01:23.286  READ FPDMA QUEUED', '', 'Error 2 occurred at disk power-on lifetime: 8431 hours (351 days + 7 hours)', '  When the command that caused the error occurred, the device was active or idle.', '', '  After command completion occurred, registers were:', '  ER ST SC SN CL CH DH', '  -- -- -- -- -- -- --', '  40 51 00 ff ff ff 0f  Error: UNC at LBA = 0x0fffffff = 268435455', '', '  Commands leading to the command that caused the error were:', '  CR FR SC SN CL CH DH DC   Powered_Up_Time  Command/Feature_Name', '  -- -- -- -- -- -- -- --  ----------------  --------------------', '  60 00 08 ff ff ff 4f 00      00:00:45.011  READ FPDMA QUEUED', '  60 00 00 ff ff ff 4f 00      00:00:45.009  READ FPDMA QUEUED', '  27 00 00 00 00 00 e0 00      00:00:45.008  READ NATIVE MAX ADDRESS EXT [OBS-ACS-3]', '  ec 00 00 00 00 00 a0 00      00:00:45.007  IDENTIFY DEVICE', '  ef 03 45 00 00 00 a0 00      00:00:45.006  SET FEATURES [Set transfer mode]', '', '', '']
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
        if (re.match('=== START OF READ SMART DATA SECTION ===', o[i]) is not None):
            err_num = None
            lifetime_hours = None
            state = None
            etype = None
            details = None

            for j in range(i+1, len(o)):
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

def test_logs(device):
    #o, e, rc = run_command([SMART, '-l', 'selftest', '-l', 'selective', device])
    o = ['smartctl 6.2 2013-07-26 r3841 [x86_64-linux-3.18.1-1.el7.elrepo.x86_64] (local build)', 'Copyright (C) 2002-13, Bruce Allen, Christian Franke, www.smartmontools.org', '', '=== START OF READ SMART DATA SECTION ===', 'SMART Self-test log structure revision number 1', 'Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error', '# 1  Short offline       Completed without error       00%      1065         -', '# 2  Short offline       Completed without error       00%      1065         -', '# 3  Short offline       Completed without error       00%      1062         -', '# 4  Extended offline    Completed without error       00%      1055         -', '# 5  Extended offline    Aborted by host               90%      1050         -', '# 6  Short offline       Completed without error       00%      1049         -', '# 7  Short offline       Completed without error       00%       952         -', '', 'SMART Selective self-test log data structure revision number 1', ' SPAN  MIN_LBA  MAX_LBA  CURRENT_TEST_STATUS', '    1        0        0  Not_testing', '    2        0        0  Not_testing', '    3        0        0  Not_testing', '    4        0        0  Not_testing', '    5        0        0  Not_testing', 'Selective self-test flags (0x0):', '  After scanning selected spans, do NOT read-scan remainder of disk.', 'If Selective self-test is pending on power-up, resume after 0 minute delay.', '', '', '']
    test_d = {}
    log_l = []
    for i in range(len(o)):
        if (re.match('SMART Self-test log structure revision number', o[i]) is not None):
            log_l.append(o[i])
            if (len(o) > (i+1)):
                if (re.match('Num  Test_Description    Status', o[i+1]) is not None):
                    for j in range(i+2, len(o)):
                        if (re.match('# ', o[j]) is not None):
                            fields = re.split(r'\s\s+', o[j].strip()[2:])
                            fields[3] = 100 - int(fields[3][:-1])
                            test_d[fields[0]] = fields[1:]
                        else:
                            log_l.append(o[j])
    return (test_d, log_l)

def run_test(device, test):
    #start a smart test(short, long or conveyance)
    return run_command([SMART, '-t', test, '/dev/%s' % device])

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

def update_config(config):
    SMARTD_CONFIG = '/etc/smartmontools/smartd.conf'
    ROCKSTOR_HEADER = '###BEGIN: Rockstor smartd config. DO NOT EDIT BELOW THIS LINE###'
    fo, npath = mkstemp()
    with open(SMARTD_CONFIG) as sfo, open(npath, 'w') as tfo:
        for line in sfo.readlines():
            if (re.match(ROCKSTOR_HEADER, line) is None):
                tfo.write(line)
            else:
                break
        tfo.write('%s\n' % ROCKSTOR_HEADER)
        for l in config.split('\n'):
            tfo.write('%s\n' % l)

    return move(npath, SMARTD_CONFIG)
