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


from base_console import BaseConsole
from share_detail_console import ShareDetailConsole
from rest_util import (api_call, print_shares_info, print_share_info)

class SharesConsole(BaseConsole):

    def __init__(self, greeting):
        BaseConsole.__init__(self)
        self.greeting = greeting + ' Shares';
        self.prompt = self.greeting + '> '
        self.url = ('%sshares' % BaseConsole.url)

    def do_list(self, args):
        url = self.url
        if (args is not None):
            url = ('%s%s' % (self.url, args))
        shares_info = api_call(url)
        print_shares_info(shares_info)

    def help_list(self):
        print """
        %(c)sDisplay information about shares on the appliance%(e)s
        
        %(c)sUsage%(e)s
        %(c)slist%(e)s [%(u)sshare_name%(e)s]
        
        %(c)sExamples%(e)s
        Display details of all shares:     %(c)slist%(e)s
        Details of a single share: %(c)slist%(e)s myshare
        """ % BaseConsole.c_params

    def do_add(self, args):
        arg_fields = args.split()
        if (len(arg_fields) < 3):
            error = ('3 arguments expected. %d given' % len(arg_fields))
            return self.help_wrapper(error, 'add')

        multiplier = 1024
        num = None
        try:
            num = int(arg_fields[2])
        except:
            if (len(arg_fields[2]) > 2):
                try:
                    num = int(arg_fields[2][:-2])
                except:
                    error = ('Invalid size parameter: %s' % arg_fields[2])
                    return self.help_wrapper(error, 'add')
                suffix = arg_fields[2][-2:].lower()
                if (suffix == 'mb'):
                    multiplier = multiplier ** 1
                elif (suffix == 'gb'):
                    multiplier = multiplier ** 2
                elif (suffix == 'tb'):
                    multiplier = multiplier ** 3
                elif (suffix == 'pb'):
                    multiplier = multiplier ** 4
                else:
                    error = ('Invalid size suffix: %s. must be one of '
                             'MB, GB, TB or PB' % suffix)
                    return self.help_wrapper(error, 'add')
            else:
                error = 'Invalid size parameter: %s' % arg_fields[2]
                return self.help_wrapper(error, 'add')
        size = num * multiplier
        input_data = {
		'sname': arg_fields[0],
		'pool' : arg_fields[1],
                      'size': size,}
        #url = ('%s/%s' % (self.url, arg_fields[0]))
        url = self.url
        share_info = api_call(url, data=input_data, calltype='post')
        print_share_info(share_info)

    def help_add(self):
        print """
        %(c)sCreate a new share%(e)s
        
        %(c)sUsage%(e)s
        %(c)sadd%(e)s %(u)sshare_name%(e)s %(u)spool_name%(e)s %(u)ssize%(e)s

        %(c)sParameters%(e)s
        %(u)sshare_name%(e)s    Intended name of the share.
        %(u)spool_name%(e)s     Pool in which to create the share. The pool should
                      exist in order to create shares.
        %(u)ssize%(e)s          Intended size of the share. An integer with
                      an optional suffix(MB, GB, TB, PB). When no suffix is
                      given, MB is presumed.

        Examples:
        To create a 20 GB share in a valid pool called pool0.
        %(c)sadd%(e)s share1234 pool0 20GB

        To create a 100 MB share in a valid pool called mypool.
        %(c)sadd%(e)s share100 mypool 100
        """ % BaseConsole.c_params

    def do_resize(self, args):
        try:
            fields = args.split()
            sname = fields[0]
            new_size = int(fields[1])
        except:
            return self.do_help(args)
        input_data = {'size': new_size,}
        url = ('%s/%s' % (self.url, sname))
        share_info = api_call(url, data=input_data, calltype='put')
        print_share_info(share_info)

    def help_resize(self):
        print """
        %(c)sResize a share%(e)s
        
        %(c)sUsage%(e)s
        %(c)sresize%(e)s %(u)sshare_name%(e)s %(u)snew_size%(e)s

        %(c)sParameters%(e)s
        %(u)sshare_name%(e)s    A valid share to resize
        %(u)snew_size%(e)s      The new size of the share after resize.

        %(c)sExamples%(e)s
        Resize a share called myshare to 100GB
        %(c)sresize%(e)s myshare 100GB
        """ % BaseConsole.c_params

    def do_clone(self, args):
        fields = args.split()
        input_data = {'name': fields[1],}
        url = ('%s/%s/clone' % (self.url, fields[0]))
        print api_call(url, data=input_data, calltype='post')

    def help_clone(self):
        print """
        %(c)sClone a share%(e)s
        
        %(c)sUsage%(e)s
        %(c)sclone%(e)s %(u)sshare_name%(e)s %(u)sclone_name%(e)s
        """ % BaseConsole.c_params

    def do_rollback(self, args):
        """
        Rollback a share to the state of one of it's snapshots.

        rollback <share_name> <snap_name>
        """
        fields = args.split()
        input_data = {'name': fields[1],}
        url = ('%s/%s/rollback' % (self.url, fields[0]))
        print api_call(url, data=input_data, calltype='post')

    def do_change_op(self, args):
        """
        To change ownership and permissions

        change_op share_name owner group perms
        """
        fields = args.split()
        input_data = {'owner': fields[1],
                      'group': fields[2],
                      'perms': fields[3],}
        url = ('%s%s/acl' % (self.url, fields[0]))
        share_info = api_call(url, data=input_data, calltype='post')
        print_share_info(share_info)

    def do_delete(self, args):
        """
        Delete a share
        """
        pass

    def do_disable(self, args):
        """
        Disable a share. Mark of deletion, but don't quite delete.
        """
        pass

    def do_enable(self, args):
        """
        Enable a previously disabled share
        """
        pass

    def do_share(self, args):
        """
        To go to a share console: share share_name
        """
        input_share = args.split()
        if (len(input_share) > 0):
            sd_console = ShareDetailConsole(self.greeting, input_share[0])
            if (len(input_share) > 1):
                return sd_console.onecmd(' '.join(input_share[1:]))
            return sd_console.cmdloop()


