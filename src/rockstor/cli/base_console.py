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

import cmd
import readline


class BaseConsole(cmd.Cmd):

    url = "https://localhost/api/"

    # ansi colors
    (
        BLACK,
        RED,
        GREEN,
        YELLOW,
        BLUE,
        MAGENTA,
        CYAN,
        LIGHT_GRAY,
        DARK_GRAY,
        BRIGHT_RED,
        BRIGHT_GREEN,
        BRIGHT_YELLOW,
        BRIGHT_BLUE,
        BRIGHT_MAGENTA,
        BRIGHT_CYAN,
        WHITE,
    ) = range(16)

    # ansi escape sequences
    c = "\x1b[38;5;%dm" % (GREEN)  # set color
    u = "\x1b[4m"  # set underscore
    e = "\x1b[0m"  # end formatting
    c_params = {"c": c, "u": u, "e": e}

    def __init__(self):
        cmd.Cmd.__init__(self)

    def do_exit(self, args):
        return -1

    def help_exit(self):
        s = (
            """
        %(c)sExit from this console%(e)s

        To exit from this console: %(c)sexit%(e)s

        """
            % BaseConsole.c_params
        )
        print(s)

    def do_EOF(self, args):
        print("")
        return self.do_exit(args)

    def preloop(self):
        cmd.Cmd.preloop(self)

    def do_hist(self, args):
        for i in range(readline.get_current_history_length()):
            print(readline.get_history_item(i))

    def help_hist(self):
        s = (
            """
        %(c)sHistory of commands in this session%(e)s
        """
            % BaseConsole.c_params
        )
        print(s)

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
        print("%sError%s: %s" % BaseConsole.c, BaseConsole.e, error)
        print("====================================")
        print("Documentation for %s" % args)
        return self.do_help(args)

    def print_help(self, synopsis, cmd, args=[], params={}, examples={}):
        """@synopsys: One line synopsis of the command @cmd: command name @args: a
        list of arguments accepted by the command @params: a dictionary of
        parameter(key) and description(value) pairs @examples: a dictionary of
        example explanation(key) and invocation(value) pairs

        """
        cmd_args = [
            "%s%s%s" % (BaseConsole.c_params["u"], a, BaseConsole.c_params["e"],)
            for a in args
        ]
        cmd_str = "%s%s%s %s" % (
            BaseConsole.c_params["c"],
            cmd,
            BaseConsole.c_params["e"],
            " ".join(cmd_args),
        )
        params_list = [
            "\t%s%s%s\t%s"
            % (BaseConsole.c_params["u"], p, BaseConsole.c_params["e"], params[p])
            for p in params
        ]
        e_list = [
            "\t%s\n\t%s%s%s %s\n"
            % (
                e,
                BaseConsole.c_params["c"],
                cmd,
                BaseConsole.c_params["e"],
                examples[e],
            )
            for e in examples
        ]
        cur_params = {
            "snps": synopsis,
            "cmd": cmd_str,
            "params": "\n".join(params_list),
            "examples": "\n".join(e_list),
        }
        cur_params.update(BaseConsole.c_params)
        print("\t%(c)s%(snps)s%(e)s\n\n\tInvocation\n\t%(cmd)s\n" % cur_params)
        if len(params) > 0:
            print("\tParameters\n%(params)s\n" % cur_params)
        if len(examples) > 0:
            print("\tExamples\n%(examples)s" % cur_params)
