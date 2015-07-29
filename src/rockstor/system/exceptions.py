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


class CommandException(Exception):

    def __init__(self, cmd, out, err, rc):
        self.cmd = cmd
        self.out = out
        self.err = err
        self.rc = rc

    def __str__(self):
        return ('Error running a command. cmd = %s. rc = %d. stdout = %s. '
                'stderr = %s' % (self.cmd, self.rc, self.out, self.err))


class NonBTRFSRootException(Exception):

    def __init__(self, err):
        self.err = err

    def __str__(self):
        return repr(self.err)
