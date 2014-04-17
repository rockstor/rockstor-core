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


import requests
import time
import json
import settings
from storageadmin.exceptions import RockStorAPIException
from functools import wraps
from base_console import BaseConsole

auth_params = {'apikey': 'adminapikey'}

def api_error(console_func):
    @wraps(console_func)
    def arg_wrapper(a1, a2):
        try:
            return console_func(a1, a2)
        except RockStorAPIException, e:
            print ('Operation failed due to the following error returned '
                   'from the server:')
            print ('-----------------------------------------')
            print e.detail
            print ('-----------------------------------------')
            return -1
    return arg_wrapper

def api_call(url, data=None, calltype='get', headers=None, save_error=True):
    call = getattr(requests, calltype)
    try:
        if (headers is not None):
            if (headers['content-type'] == 'application/json'):
                r = call(url, verify=False, params=auth_params,
                         data=json.dumps(data), headers=headers)
            else:
                r = call(url, verify=False, params=auth_params, data=data,
                         headers=headers)
        else:
            r = call(url, verify=False, params=auth_params, data=data)
    except requests.exceptions.ConnectionError:
        print('Error connecting to Rockstor. Is it running?')
        return {}

    if (r.status_code == 404):
        msg = ('Invalid api end point: %s' % url)
        print msg
        raise RockStorAPIException(detail=msg)

    if (r.status_code != 200):
        print r.text
        try:
            error_d = json.loads(r.text)
            if ('detail' in error_d):
                raise RockStorAPIException(detail=error_d['detail'])

            if (settings.DEBUG is True and save_error is True):
                cur_time = str(int(time.time()))
                err_file = '/tmp/err-%s.html' % cur_time
                with open(err_file, 'w') as efo:
                    for line in r.text.split('\n'):
                        efo.write('%s\n' % line)
                    print('Error detail is saved at %s' % err_file)
        except ValueError:
            raise RockStorAPIException(detail='Internal Server Error')
        r.raise_for_status()

    try:
        ret_val = r.json()
    except ValueError:
        ret_val = {}
    return ret_val

def print_pools_info(pools_info):
    if (pools_info is None or
        not isinstance(pools_info, dict) or
        len(pools_info) == 0):
        print('There are no pools on the appliance.')
        return
    try:
        if ('count' not in pools_info):
            pools_info = [pools_info]
        else:
            pools_info = pools_info['results']
        print("%(c)sPools on the appliance\n%(e)s" % BaseConsole.c_params)
        print("Name\tSize\tUsage\tRaid")
        for p in pools_info:
            print_pool_info(p)
    except Exception, e:
        print('Error rendering pool info')

def print_pool_info(p, header=False):
    try:
        if header:
            print "%(c)sPool info%(e)s\n" % BaseConsole.c_params
            print("Name\tSize\tUsage\tRaid")
        p['size'] = sizeof_fmt(p['size'])
        p['usage'] = sizeof_fmt(p['usage'])
        print('%s%s%s\t%s\t%s\t%s' % (BaseConsole.c, p['name'], 
            BaseConsole.e, p['size'], p['usage'], p['raid']))
    except Exception, e:
        print e
        print('Error printing pool info')

def print_scrub_status(pool_name, scrub_info):
    try:
        print '%sScrub status for %s%s' % (BaseConsole.c, pool_name,
                BaseConsole.e);
        kb_scrubbed = None
        if ('kb_scrubbed' in scrub_info):
            kb_scrubbed = scrub_info['kb_scrubbed']
        status = scrub_info['status']
        print '%sStatus%s:  %s' % (BaseConsole.c, BaseConsole.e, status)
        if (status == 'finished'):
            print '%sKB Scrubbed%s:  %s' % (BaseConsole.c, BaseConsole.e, 
                    kb_scrubbed)
    except Exception, e:
        print e
        print('Error printing scrub status')

def print_share_info(share_info):
    if (share_info is None or
        not isinstance(share_info, dict) or
        len(share_info) == 0):
        print('There are no shares in the system')
        return
    try:
        if ('count' not in share_info):
            share_info = [share_info]
        else:
            share_info = share_info['results']
        print("List of shares in the system")
        print("---------------------------------------")
        print("Name\tSize(KB)\tUsage(KB)\tPool")
        for s in share_info:
            print('%s\t%s\t%s\t%s' %
                  (s['name'], s['size'], s['r_usage'], s['pool']['name']))
    except Exception, e:
        print e
        print('Error rendering share info')

def print_disks_info(disks_info):
    if (disks_info is None or
        not isinstance(disks_info, dict) or
        len(disks_info) == 0):
        print('There are no disks on the appliance.')
        return
    try:
        if ('results' not in disks_info):
            #POST is used, don't do anything
            disks_info = disks_info
        elif ('count' not in disks_info):
            disks_info = [disks_info]
        else:
            disks_info = disks_info['results']
        print("%sDisks on this Rockstor appliance%s\n" % (BaseConsole.u,
            BaseConsole.e))
        print("Name\tSize\tPool")
        for d in disks_info:
            print_disk_info(d)
    except Exception, e:
        print('Error rendering disk info')

def print_disk_info(d, header=False):
    try:
        if header:
            print "%(u)sDisk info%(e)s\n" % BaseConsole.c_params
            print("Name\tSize\tPool")
        d['size'] = sizeof_fmt(d['size'])
        print('%s%s%s\t%s\t%s' % (BaseConsole.c, d['name'],
            BaseConsole.e, d['size'], d['pool_name']))
    except Exception, e:
        print e
        print('Error printing disk info')

def print_export_info(export_info):
    if (export_info is None or
        not isinstance(export_info, dict) or
        len(export_info) == 0):
        print('There are no exports for this share')
        return
    export_info = [export_info]
    print("List of exports for the share")
    print("----------------------------------------")
    print("Id\tMount\tClient\tReadable\tSyncable\tEnabled")
    for e in export_info:
        print('%s\t%s\t%s\t%s\t%s\t%s' %
              (e['id'], e['mount'], e['host_str'], e['editable'],
               e['syncable'], e['enabled']))


def sizeof_fmt(num):
    for x in ['K','M','G','T','P','E']:
        if (num < 0.00):
            num = 0
            break
        if (num < 1024.00):
            break
        else:
            num /= 1024.00
            x = 'Z'
    return ("%3.2f%s" % (num, x))
