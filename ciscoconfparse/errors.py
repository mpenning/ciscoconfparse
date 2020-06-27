from __future__ import absolute_import


class BaseError(Exception):
    def __init__(self, msg=""):
        super(BaseError, self).__init__(msg)
        self.msg = msg


class DynamicAddressException(Exception):
    """Throw this if you try to get an address object from a dhcp interface"""

    def __init__(self, msg=""):
        super(DynamicAddressException, self).__init__(msg)
        self.msg = msg
