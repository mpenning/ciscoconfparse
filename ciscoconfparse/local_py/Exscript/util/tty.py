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
TTY utilities.
"""
import os
import sys
import struct
from subprocess import Popen, PIPE

def _get_terminal_size(fd):
    try:
        import fcntl
        import termios
    except ImportError:
        return None
    s = struct.pack('HHHH', 0, 0, 0, 0)
    try:
        x = fcntl.ioctl(fd, termios.TIOCGWINSZ, s)
    except IOError: # Window size ioctl not supported.
        return None
    try:
        rows, cols, x_pixels, y_pixels = struct.unpack('HHHH', x)
    except struct.error:
        return None
    return rows, cols

def get_terminal_size(default_rows = 25, default_cols = 80):
    """
    Returns the number of lines and columns of the current terminal.
    It attempts several strategies to determine the size and if all fail,
    it returns (80, 25).

    @rtype:  int, int
    @return: The rows and columns of the terminal.
    """
    # Collect a list of viable input channels that may tell us something
    # about the terminal dimensions.
    fileno_list = []
    try:
        fileno_list.append(sys.stdout.fileno())
    except AttributeError:
        # Channel was redirected to an object that has no fileno()
        pass
    try:
        fileno_list.append(sys.stdin.fileno())
    except AttributeError:
        pass
    try:
        fileno_list.append(sys.stderr.fileno())
    except AttributeError:
        pass

    # Ask each channel for the terminal window size.
    for fd in fileno_list:
        try:
            rows, cols = _get_terminal_size(fd)
        except TypeError:
            # _get_terminal_size() returned None.
            pass
        else:
            return rows, cols

    # Try os.ctermid()
    try:
        fd = os.open(os.ctermid(), os.O_RDONLY)
    except AttributeError:
        # os.ctermid does not exist on Windows.
        pass
    except OSError:
        # The device pointed to by os.ctermid() does not exist.
        pass
    else:
        try:
            rows, cols = _get_terminal_size(fd)
        except TypeError:
            # _get_terminal_size() returned None.
            pass
        else:
            return rows, cols
        finally:
            os.close(fd)

    # Try `stty size`
    devnull = open(os.devnull, 'w')
    try:
        process = Popen(['stty', 'size'], stderr = devnull, stdout = PIPE)
    except OSError:
        pass
    else:
        errcode = process.wait()
        output  = process.stdout.read()
        devnull.close()
        try:
            rows, cols = output.split()
            return int(rows), int(cols)
        except (ValueError, TypeError):
            pass

    # Try environment variables.
    try:
        return tuple(int(os.getenv(var)) for var in ('LINES', 'COLUMNS'))
    except (ValueError, TypeError):
        pass

    # Give up.
    return default_rows, default_cols
