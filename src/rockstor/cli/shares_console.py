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
from rest_util import (api_call, print_share_info)

class SharesConsole(BaseConsole):

    def __init__(self, prompt):
        BaseConsole.__init__(self)
        self.parent_prompt = prompt
        self.greeting = ('%s Shares' % self.parent_prompt)
        self.prompt = ('%s>' % self.greeting)
        self.url = ('%sshares/' % BaseConsole.url)

    def do_list(self, args):
        """
        List brief information about all shares
        """
        share_info = api_call(self.url)
        print_share_info(share_info)

    def do_add(self, args):
        """
        To add a share

        add share_name -ppool_name -ssize
        """
        arg_fields = args.split()
        sname = arg_fields[0]
        input_data = {}
        for f in arg_fields[1:]:
            if(f[0:2] == '-p'):
                input_data['pool'] = f[2:]
            elif(f[0:2] == '-s'):
                input_data['size'] = f[2:]
            else:
                return self.do_help(args)
        if(len(input_data) != 2):
            return self.do_help(args)
        url = ('%s/%s/' % (self.url, sname))
        share_info = api_call(url, data=input_data, calltype='post')
        print_share_info(share_info)

    def do_resize(self, args):
        """
        To resize a share

        resize share_name new_size
        """
        try:
            fields = args.split()
            sname = fields[0]
            new_size = int(fields[1])
        except:
            return self.do_help(args)
        input_data = {'size': new_size,}
        url = ('%s/%s/' % (self.url, sname))
        share_info = api_call(url, data=input_data, calltype='put')
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
                sd_console.onecmd(' '.join(input_share[1:]))
            else:
                sd_console.cmdloop()
