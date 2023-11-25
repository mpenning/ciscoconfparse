r""" errors.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2018-2019 David Michael Pennington at Samsung Data Services

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""


class BaseError(Exception):
    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class PythonOptimizeException(BaseError):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class RequirementFailure(BaseError):
    """Raise this error instead of using assert foo in non-test code"""

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class ListItemMissingAttribute(Exception):
    """Raise this error if a list() item is missing a required attribute."""

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class ListItemTypeError(Exception):
    """Raise this error if a list() contains more than one object type"""

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class DNSLookupError(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class DNSTimeoutError(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class DuplicateMember(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class DynamicAddressException(Exception):
    """Throw this if you try to get an address object from a dhcp interface"""

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidCiscoInterface(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidCiscoEthernetTrunkAction(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidCiscoEthernetVlan(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidMember(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidParameters(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidCiscoRange(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidShellVariableMapping(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class InvalidTypecast(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class NoRegexMatch(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class MismatchedType(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class UnexpectedType(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg


class UntypedError(Exception):

    def __init__(self, msg=""):
        super().__init__(msg)
        self.msg = msg
