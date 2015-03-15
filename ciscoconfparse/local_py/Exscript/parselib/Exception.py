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
class LexerException(Exception):
    """
    Fallback exception that is called when the error type is not known.
    """
    pass

class CompileError(LexerException):
    """
    Raised during the compilation procedure if the template contained
    a syntax error.
    """
    pass

class ExecuteError(LexerException):
    """
    Raised during the execution of the compiled template whenever any
    error occurs.
    """
    pass
