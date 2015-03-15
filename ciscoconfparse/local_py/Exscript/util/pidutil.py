# Copyright (C) 2007-2011 Samuel Abels.
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
Handling PID (process id) files.
"""
import os
import logging
import fcntl
import errno

def read(path):
    """
    Returns the process id from the given file if it exists, or None
    otherwise. Raises an exception for all other types of OSError
    while trying to access the file.

    @type  path: str
    @param path: The name of the pidfile.
    @rtype:  int or None
    @return: The PID, or none if the file was not found.
    """
    # Try to read the pid from the pidfile.
    logging.info("Checking pidfile '%s'", path)
    try:
        return int(open(path).read())
    except IOError, (code, text):
        if code == errno.ENOENT: # no such file or directory
            return None
        raise

def isalive(path):
    """
    Returns True if the file with the given name contains a process
    id that is still alive.
    Returns False otherwise.

    @type  path: str
    @param path: The name of the pidfile.
    @rtype:  bool
    @return: Whether the process is alive.
    """
    # try to read the pid from the pidfile
    pid = read(path)
    if pid is None:
        return False

    # Check if a process with the given pid exists.
    try:
        os.kill(pid, 0) # Signal 0 does not kill, but check.
    except OSError, (code, text):
        if code == errno.ESRCH: # No such process.
            return False
    return True

def kill(path):
    """
    Kills the process, if it still exists.

    @type  path: str
    @param path: The name of the pidfile.
    """
    # try to read the pid from the pidfile
    pid = read(path)
    if pid is None:
        return

    # Try to kill the process.
    logging.info("Killing PID %s", pid)
    try:
        os.kill(pid, 9)
    except OSError, (code, text):
        # re-raise if the error wasn't "No such process"
        if code != errno.ESRCH:
            raise

def write(path):
    """
    Writes the current process id to the given pidfile.

    @type  path: str
    @param path: The name of the pidfile.
    """
    pid = os.getpid()
    logging.info("Writing PID %s to '%s'", pid, path)
    try:
        pidfile = open(path, 'wb')
        # get a non-blocking exclusive lock
        fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        # clear out the file
        pidfile.seek(0)
        pidfile.truncate(0)
        # write the pid
        pidfile.write(str(pid))
    finally:
        try:
            pidfile.close()
        except:
            pass

def remove(path):
    """
    Deletes the pidfile if it exists.

    @type  path: str
    @param path: The name of the pidfile.
    """
    logging.info("Removing pidfile '%s'", path)
    try:
        os.unlink(path)
    except IOError:
        pass
