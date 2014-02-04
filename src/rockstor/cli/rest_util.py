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

    if (r.status_code != 200):
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
        r.raise_for_status()

    try:
        ret_val = r.json()
    except ValueError:
        ret_val = {}
    return ret_val

def print_pool_info(pool_info):
    if (pool_info is None or
        not isinstance(pool_info, dict) or
        len(pool_info) == 0):
        print('There are no pools in the system')
        return
    try:
        if ('count' not in pool_info):
            pool_info = [pool_info]
        else:
            pool_info = pool_info['results']
        print("List of pools in the system")
        print("--------------------------------------")
        print("Name\tSize\tUsage\tRaid")
        for p in pool_info:
            p['size'] = sizeof_fmt(p['size'])
            p['usage'] = sizeof_fmt(p['usage'])
            print('%s\t%s\t%s\t%s' %
                  (p['name'], p['size'], p['usage'], p['raid']))
    except Exception, e:
        print('Error rendering pool info')

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
                  (s['name'], s['size'], s['usage'], s['pool']['name']))
    except Exception, e:
        print('Error rendering share info')

def print_disk_info(disk_info):
    if (disk_info is None or
        not isinstance(disk_info, dict) or
        len(disk_info) == 0):
        print('There are no disks in the system')
        return
    try:
        if ('results' not in disk_info):
            #POST is used, don't do anything
            disk_info = disk_info
        elif ('count' not in disk_info):
            disk_info = [disk_info]
        else:
            disk_info = disk_info['results']
        print("List of disks in the system")
        print("--------------------------------------------")
        print("Name\tSize\tPool")
        for d in disk_info:
            d['size'] = sizeof_fmt(d['size'])
            print('%s\t%s\t%s' % (d['name'], d['size'], d['pool']))
    except Exception, e:
        print('Error rendering disk info')


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
