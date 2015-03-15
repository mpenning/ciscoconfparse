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
from Exscript.stdlib.util import secure_function

@secure_function
def replace(scope, strings, source, dest):
    """
    Returns a copy of the given string (or list of strings) in which all
    occurrences of the given source are replaced by the given dest.

    @type  strings: string
    @param strings: A string, or a list of strings.
    @type  source: string
    @param source: What to replace.
    @type  dest: string
    @param dest: What to replace it with.
    @rtype:  string
    @return: The resulting string, or list of strings.
    """
    return [s.replace(source[0], dest[0]) for s in strings]

@secure_function
def tolower(scope, strings):
    """
    Returns the given string in lower case.

    @type  strings: string
    @param strings: A string, or a list of strings.
    @rtype:  string
    @return: The resulting string, or list of strings in lower case.
    """
    return [s.lower() for s in strings]
