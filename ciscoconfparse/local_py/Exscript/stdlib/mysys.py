# Copyright (C) 2007-2010 Samuel Abels.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
import time
import sys
from subprocess import Popen, PIPE, STDOUT
from Exscript.stdlib.util import secure_function

def execute(scope, command):
    """
    Executes the given command locally.

    @type  command: string
    @param command: A shell command.
    """
    process = Popen(command[0],
                    shell     = True,
                    stdin     = PIPE,
                    stdout    = PIPE,
                    stderr    = STDOUT,
                    close_fds = True)
    scope.define(__response__ = process.stdout.read())
    return True

@secure_function
def message(scope, string):
    """
    Writes the given string to stdout.

    @type  string: string
    @param string: A string, or a list of strings.
    """
    sys.stdout.write(''.join(string) + '\n')
    return True

@secure_function
def wait(scope, seconds):
    """
    Waits for the given number of seconds.

    @type  seconds: int
    @param seconds: The wait time in seconds.
    """
    time.sleep(int(seconds[0]))
    return True
