"""
Copyright (c) 2012-2020 RockStor, Inc. <http://rockstor.com>
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
import pwd
import cmd
import sys
import os
import readline

from base_console import BaseConsole
from setup_console import SetupConsole
from disks_console import DisksConsole
from pools_console import PoolsConsole
from shares_console import SharesConsole
from services_console import ServicesConsole
from sm_console import SMConsole
from support_console import SupportConsole
from network_console import NetworkConsole
from users_console import UsersConsole
from task_console import TaskConsole
from replication_console import ReplicationConsole
from backup_plugin_console import BackupPluginConsole
from rest_util import api_call
from nfs_export_console import NFSExportConsole
from api_keys import APIKeyConsole
from rest_util import set_token


ASCII_LOGO = """
 __   __   __        __  ___  __   __
|__) /  \ /  ` |__/ /__`  |  /  \ |__)
|  \ \__/ \__, |  \ .__/  |  \__/ |  \\
"""


class RockConsole(BaseConsole):
    def __init__(self, greeting="Rockstor"):
        self.user = pwd.getpwuid(os.getuid())[0]
        self.greeting = self.user + "@" + greeting
        self.prompt = self.greeting + "> "
        self.intro = (
            "%s\nWelcome to Rockstor. The Smart Open Storage Platform." % ASCII_LOGO
        )
        self.user_hist_file = os.path.expanduser("~") + "/.rcli.hist"
        try:
            readline.read_history_file(self.user_hist_file)
        except:
            pass
        finally:
            BaseConsole.__init__(self)

    def postloop(self):
        cmd.Cmd.postloop(self)
        print("Thanks for Rocking on the Console")
        try:
            readline.write_history_file(self.user_hist_file)
        except:
            print("Command history could not be saved")

    """
    Commands
    """

    def do_utcnow(self, args):
        """
        returns utc time on the server
        """
        url = "%scommands/utcnow" % BaseConsole.url
        print(api_call(url, calltype="post"))

    def do_uptime(self, args):
        """
        return uptime(in seconds) of the server
        """
        url = "%scommands/uptime" % BaseConsole.url
        print(api_call(url, calltype="post"))

    def do_bootstrap(self, args):
        """
        bootraps the storage state, mounts anything that needs to be mounted
        etc..
        """
        url = "%scommands/bootstrap" % BaseConsole.url
        print(api_call(url, calltype="post"))

    def do_shares(self, args):
        """
        Subconsole for share related operations.

        Go to shares subconsole:    shares
        Display list of shares:     shares list <share_name>
        Add a share:                shares add pool_name share_name
        Remove a share:             shares delete share_name
        share detail console:       shares share_name
        commands on a share:        shares share_name <input>
        """
        shares_console = SharesConsole(self.greeting)
        if len(args) == 0:
            return shares_console.cmdloop()
        return shares_console.onecmd(args)

    def do_pools(self, args):
        """
        Operations on pools can be done with this command.

        Go to pools subconsole:    pools
        Display the list of pools: pools list
        Add a pool:                pools add
        Remove a pool:             pools delete
        pool detail console:       pools pool_name
        commands on a pool:        pools pool_name <input>
        """
        pools_console = PoolsConsole(self.greeting)
        if len(args) == 0:
            pools_console.cmdloop()
        else:
            pools_console.onecmd(args)

    def do_disks(self, args):
        disks_console = DisksConsole(self.greeting)
        if len(args) == 0:
            disks_console.cmdloop()
        else:
            disks_console.onecmd(args)

    def help_disks(self):
        s = (
            """
        %(c)sPerform operations on disks.%(e)s

        Available commands:
        Go to disks subconsole:    %(c)sdisks%(e)s
        Display the list of disks: %(c)sdisks list%(e)s
        Scan for new disks:        %(c)sdisks scan%(e)s
        """
            % BaseConsole.c_params
        )
        print(s)

    def do_services(self, args):
        """
        Operations on all services can be done with this command.

        Display the list of services: services list
        service detail console:       services service_name
        nfs service console:          services nfs <commands>
        smb service console:          services smb <command>
        """
        services_console = ServicesConsole(self.greeting)
        if len(args) == 0:
            services_console.cmdloop()
        else:
            services_console.onecmd(args)

    def do_setup(self, args):
        """
        Temporary method to setup for dev purposes. to be deprecated later,
        perhaps.

        """
        setup_console = SetupConsole(self.greeting)
        if len(args) == 0:
            setup_console.cmdloop()
        else:
            setup_console.onecmd(args)

    def do_smart(self, args):
        """
        Smart manager console
        """
        sm_console = SMConsole(self.greeting)
        if len(args) == 0:
            sm_console.cmdloop()
        else:
            sm_console.onecmd(args)

    def do_support(self, args):
        """
        Support console
        """
        support_console = SupportConsole(self.greeting)
        if len(args) == 0:
            support_console.cmdloop()
        else:
            support_console.onecmd(args)

    def do_network(self, args):
        """
        Network console
        """
        network_console = NetworkConsole(self.greeting)
        if len(args) == 0:
            network_console.cmdloop()
        else:
            network_console.onecmd(args)

    def do_users(self, args):
        """
        Users console
        """
        users_console = UsersConsole(self.greeting)
        if len(args) == 0:
            users_console.cmdloop()
        else:
            users_console.onecmd(args)

    def do_tasks(self, args):
        """
        Task Scheduler Console
        """
        task_console = TaskConsole(self.greeting)
        if len(args) == 0:
            task_console.cmdloop()
        else:
            task_console.onecmd(args)

    def do_replication(self, args):
        """
        Replication console
        """
        rc = ReplicationConsole(self.greeting)
        if len(args) == 0:
            rc.cmdloop()
        else:
            rc.onecmd(args)

    def do_backup(self, args):
        """
        Backup plugin console
        """
        bc = BackupPluginConsole(self.greeting)
        if len(args) == 0:
            bc.cmdloop()
        else:
            bc.cmdloop(args)

    def do_nfs_exports(self, args):
        ne = NFSExportConsole(self.greeting)
        if len(args) == 0:
            ne.cmdloop()
        else:
            ne.cmdloop(args)

    def do_api_keys(self, args):
        ak = APIKeyConsole(self.greeting)
        if len(args) == 0:
            ak.cmdloop()
        else:
            ak.cmdloop(args)


def main():
    set_token()
    rc = RockConsole()
    if len(sys.argv) > 1:
        if sys.argv[1] == "-c":
            #  command is called remotely using ssh
            line = " ".join(sys.argv[2:])
        else:
            line = " ".join(sys.argv[1:])
        return rc.postcmd(rc.onecmd(line), line)
    else:
        return rc.cmdloop()
