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
class ExscriptException(Exception):
    pass

class FailException(ExscriptException):
    """
    This exception type is used if the "fail" command was used in a template.
    """
    pass

class PermissionError(ExscriptException):
    """
    Raised if an insecure function was called when the parser is in secure
    mode.
    """
    pass
