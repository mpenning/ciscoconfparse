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
Network related error types.
"""

class ProtocolException(Exception):
    """
    Default exception that is thrown on most protocol related errors.
    """
    pass

class TimeoutException(ProtocolException):
    """
    An exception that is thrown if the connected host did not
    respond for too long.
    """
    pass

class ExpectCancelledException(ProtocolException):
    """
    An exception that is thrown if Protocol.cancel_expect()
    was called.
    """
    pass

class DriverReplacedException(ProtocolException):
    """
    An exception that is thrown if the protocol driver
    was switched during a call to expect().
    """
    pass

class LoginFailure(ProtocolException):
    """
    An exception that is thrown if the response of a connected host looked
    like it was trying to signal a login error during the authentication
    procedure.
    """
    pass

class InvalidCommandException(ProtocolException):
    """
    An exception that is thrown if the response of a connected host contained
    a string that looked like an error.
    """
    pass
