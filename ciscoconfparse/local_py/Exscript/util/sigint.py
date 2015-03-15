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
"""
A class for catching SIGINT, such that CTRL+c works.
"""
import os
import sys
import signal

class SigIntWatcher(object):
    """
    This class solves two problems with multithreaded programs in Python:

      - A signal might be delivered to any thread and
      - if the thread that gets the signal is waiting, the signal
        is ignored (which is a bug).

    This class forks and catches sigint for Exscript.

    The watcher is a concurrent process (not thread) that waits for a
    signal and the process that contains the threads.
    Works on Linux, Solaris, MacOS, and AIX. Known not to work
    on Windows.
    """
    def __init__(self):
        """
        Creates a child process, which returns. The parent
        process waits for a KeyboardInterrupt and then kills
        the child process.
        """
        try:
            self.child = os.fork()
        except AttributeError:  # platforms that don't have os.fork
            pass
        except RuntimeError:
            pass # prevent "not holding the import lock" on some systems.
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            pid, status = os.wait()
        except KeyboardInterrupt:
            print '********** SIGINT RECEIVED - SHUTTING DOWN! **********'
            self.kill()
            sys.exit(1)
        sys.exit(status >> 8)

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError:
            pass
