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
import os
from Exscript.stdlib.util import secure_function

def chmod(scope, filename, mode):
    """
    Changes the permissions of the given file (or list of files)
    to the given mode. You probably want to use an octal representation
    for the integer, e.g. "chmod(myfile, 0644)".

    @type  filename: string
    @param filename: A filename.
    @type  mode: int
    @param mode: The access permissions.
    """
    for file in filename:
        os.chmod(file, mode[0])
    return True

def clear(scope, filename):
    """
    Clear the contents of the given file. The file is created if it does
    not exist.

    @type  filename: string
    @param filename: A filename.
    """
    file = open(filename[0], 'w')
    file.close()
    return True

@secure_function
def exists(scope, filename):
    """
    Returns True if the file with the given name exists, False otherwise.
    If a list of files is given, the function returns True only if ALL of
    the files exist.

    @type  filename: string
    @param filename: A filename.
    @rtype:  bool
    @return: The operating system of the remote device.
    """
    return [os.path.exists(f) for f in filename]

def mkdir(scope, dirname, mode = None):
    """
    Creates the given directory (or directories). The optional access
    permissions are set to the given mode, and default to whatever
    is the umask on your system defined.

    @type  dirname: string
    @param dirname: A filename, or a list of dirnames.
    @type  mode: int
    @param mode: The access permissions.
    """
    for dir in dirname:
        if mode is None:
            os.makedirs(dir)
        else:
            os.makedirs(dir, mode[0])
    return True

def read(scope, filename):
    """
    Reads the given file and returns the result.
    The result is also stored in the built-in __response__ variable.

    @type  filename: string
    @param filename: A filename.
    @rtype:  string
    @return: The content of the file.
    """
    file  = open(filename[0], 'r')
    lines = file.readlines()
    file.close()
    scope.define(__response__ = lines)
    return lines

def rm(scope, filename):
    """
    Deletes the given file (or files) from the file system.

    @type  filename: string
    @param filename: A filename, or a list of filenames.
    """
    for file in filename:
        os.remove(file)
    return True

def write(scope, filename, lines, mode = ['a']):
    """
    Writes the given string into the given file.
    The following modes are supported:

      - 'a': Append to the file if it already exists.
      - 'w': Replace the file if it already exists.

    @type  filename: string
    @param filename: A filename.
    @type  lines: string
    @param lines: The data that is written into the file.
    @type  mode: string
    @param mode: Any of the above listed modes.
    """
    file = open(filename[0], mode[0])
    file.writelines(['%s\n' % line.rstrip() for line in lines])
    file.close()
    return True
