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

import cmd
import readline

class BaseConsole(cmd.Cmd):

    url = 'https://localhost/api/'

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_exit(self, args):
        """
        Exit from this console.

        To exit from this console: exit

        """
        return -1

    def do_EOF(self, args):
        print("")
        return self.do_exit(args)

    def preloop(self):
        cmd.Cmd.preloop(self)

    def do_hist(self, args):
        """
        History of commands in this session
        """
        for i in range(readline.get_current_history_length()):
            print readline.get_history_item(i)

    def do_shell(self, args):
        pass

    def precmd(self, line):
        return line

    def postcmd(self, stop, line):
        return stop

    def emptyline(self):
        """Do nothing on empty input line"""
        pass

    def default(self, line):
        """Called on an input line when the command prefix is not recognized.
           In that case we execute the line as Python code.
        """
        self.do_help(line)

    def help_wrapper(self, error, args):
        print('Error: %s' % error)
        print('====================================')
        print('Documentation for %s' % args)
        return self.do_help(args)
