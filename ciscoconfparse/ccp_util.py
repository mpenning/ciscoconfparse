from __future__  import absolute_import
import itertools
import socket
import time
import sys
import re
import os

if (sys.version_info>=(3, 0, 0,)):
    from collections.abc import MutableSequence
else:
    ## This syntax is not supported in Python 3...
    from collections import MutableSequence

from ciscoconfparse.protocol_values import ASA_TCP_PORTS, ASA_UDP_PORTS
from dns.exception import DNSException
from dns.resolver import Resolver
from dns import reversename, query, zone

if sys.version_info[0] < 3:
    from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
else:
    from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
""" ccp_util.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2014-2015, 2018-2019 David Michael Pennington

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

_IPV6_REGEX_STR = r"""(?!:::\S+?$)       # Negative Lookahead for 3 colons
 (?P<addr>                               # Begin a group named 'addr'
 (?P<opt1>{0}(?::{0}){{7}})              # no double colons, option 1
|(?P<opt2>(?:{0}:){{1}}(?::{0}){{1,6}})  # match fe80::1
|(?P<opt3>(?:{0}:){{2}}(?::{0}){{1,5}})  # match fe80:a::1
|(?P<opt4>(?:{0}:){{3}}(?::{0}){{1,4}})  # match fe80:a:b::1
|(?P<opt5>(?:{0}:){{4}}(?::{0}){{1,3}})  # match fe80:a:b:c::1
|(?P<opt6>(?:{0}:){{5}}(?::{0}){{1,2}})  # match fe80:a:b:c:d::1
|(?P<opt7>(?:{0}:){{6}}(?::{0}){{1,1}})  # match fe80:a:b:c:d:e::1
|(?P<opt8>:(?::{0}){{1,7}})              # leading double colons
|(?P<opt9>(?:{0}:){{1,7}}:)              # trailing double colons
|(?P<opt10>(?:::))                       # bare double colons (default route)
)                                        # End group named 'addr'
""".format(r'[0-9a-fA-F]{1,4}')
_IPV6_REGEX_STR_COMPRESSED1 = r"""(?!:::\S+?$)(?P<addr1>(?P<opt1_1>{0}(?::{0}){{7}})|(?P<opt1_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt1_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt1_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt1_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt1_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt1_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt1_8>:(?::{0}){{1,7}})|(?P<opt1_9>(?:{0}:){{1,7}}:)|(?P<opt1_10>(?:::)))""".format(
    r'[0-9a-fA-F]{1,4}')
_IPV6_REGEX_STR_COMPRESSED2 = r"""(?!:::\S+?$)(?P<addr2>(?P<opt2_1>{0}(?::{0}){{7}})|(?P<opt2_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt2_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt2_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt2_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt2_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt2_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt2_8>:(?::{0}){{1,7}})|(?P<opt2_9>(?:{0}:){{1,7}}:)|(?P<opt2_10>(?:::)))""".format(
    r'[0-9a-fA-F]{1,4}')
_IPV6_REGEX_STR_COMPRESSED3 = r"""(?!:::\S+?$)(?P<addr3>(?P<opt3_1>{0}(?::{0}){{7}})|(?P<opt3_2>(?:{0}:){{1}}(?::{0}){{1,6}})|(?P<opt3_3>(?:{0}:){{2}}(?::{0}){{1,5}})|(?P<opt3_4>(?:{0}:){{3}}(?::{0}){{1,4}})|(?P<opt3_5>(?:{0}:){{4}}(?::{0}){{1,3}})|(?P<opt3_6>(?:{0}:){{5}}(?::{0}){{1,2}})|(?P<opt3_7>(?:{0}:){{6}}(?::{0}){{1,1}})|(?P<opt3_8>:(?::{0}){{1,7}})|(?P<opt3_9>(?:{0}:){{1,7}}:)|(?P<opt3_10>(?:::)))""".format(
    r'[0-9a-fA-F]{1,4}')

_CISCO_RANGE_ATOM_STR = r"""\d+\s*\-*\s*\d*"""
_CISCO_RANGE_STR = r"""^(?P<line_prefix>[a-zA-Z\s]*)(?P<slot_prefix>[\d\/]*\d+\/)*(?P<range_text>(\s*{0})*)$""".format(
    _CISCO_RANGE_ATOM_STR)

_RGX_IPV6ADDR = re.compile(_IPV6_REGEX_STR, re.VERBOSE)

_RGX_IPV4ADDR = re.compile(r'^(?P<addr>\d+\.\d+\.\d+\.\d+)')
_RGX_IPV4ADDR_NETMASK = re.compile(r"""
     (?:
       ^(?P<addr0>\d+\.\d+\.\d+\.\d+)$
      |(?:^
         (?:(?P<addr1>\d+\.\d+\.\d+\.\d+))(?:\s+|\/)(?:(?P<netmask>\d+\.\d+\.\d+\.\d+))
       $)
      |^(?:\s*(?P<addr2>\d+\.\d+\.\d+\.\d+)(?:\/(?P<masklen>\d+))\s*)$
    )
    """, re.VERBOSE)

_RGX_CISCO_RANGE = re.compile(_CISCO_RANGE_STR)

def is_valid_ipv4_addr(input=""):
    """Check if this is a valid IPv4 string"""
    assert input!=""
    if _RGX_IPV4ADDR.search(input):
        return True
    return False

def is_valid_ipv6_addr(input=""):
    """Check if this is a valid IPv6 string"""
    assert input!=""
    if _RGX_IPV6ADDR.search(input):
        return True
    return False

## Emulate the old behavior of ipaddr.IPv4Network in Python2, which can use
##    IPv4Network with a host address.  Google removed that in Python3's 
##    ipaddress.py module
class IPv4Obj(object):
    """An object to represent IPv4 addresses and IPv4Networks.  When :class:`~ccp_util.IPv4Obj` objects are compared or sorted, shorter masks are greater than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses.

    Kwargs:
        - arg (str): A string containing an IPv4 address, and optionally a netmask or masklength.  The following address/netmask formats are supported: "10.1.1.1/24", "10.1.1.1 255.255.255.0", "10.1.1.1/255.255.255.0"

    Attributes:
        - network_object : An IPv4Network object
        - ip_object  : An IPv4Address object
        - ip : An IPv4Address object
        - as_binary_tuple (tuple): The address as a tuple of zero-padded binary strings
        - as_hex_tuple (tuple): The address as a tuple of zero-padded 8-bit hex strings
        - as_decimal (int): The ip address as a decimal integer
        - network : An IPv4Network object
        - network_object : An IPv4Network object
        - netmask (str): A string representing the netmask
        - prefixlen (int): An integer representing the length of the netmask
        - prefixlength (int): An integer representing the length of the netmask
        - broadcast (str): A string representing the broadcast address
        - hostmask (str): A string representing the hostmask
        - numhosts (int): An integer representing the number of hosts contained in the network

    Returns:
        - an instance of :class:`~ccp_util.IPv4Obj`.

>>> from ciscoconfparse.ccp_util import IPv4Obj
>>> net = IPv4Obj('172.16.1.0/24')
>>> net
<IPv4Obj 172.16.1.0/24>
>>> net.ip
IPv4Address('172.16.1.0')
>>> net.ip + 1
IPv4Address('172.16.1.1')
>>> str(net.ip+1)
'172.16.1.1'
>>> net.network
IPv4Address('172.16.1.0')
>>> net.network_object
IPv4Network('172.16.1.0/24')
>>> str(net.network_object)
'172.16.1.0/24'
>>> net.prefixlen
24
>>> net.network_object.iterhosts()
<generator object iterhosts at 0x7f00bfcce730>
>>>
    """

    def __init__(self, arg='127.0.0.1/32', strict=False):

        #RGX_IPV4ADDR = re.compile(r'^(\d+\.\d+\.\d+\.\d+)')
        #RGX_IPV4ADDR_NETMASK = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)')

        self.arg = arg
        self.dna = "IPv4Obj"
        try:
            mm = _RGX_IPV4ADDR_NETMASK.search(arg)
        except TypeError:
            if getattr(arg, 'dna', '')=="IPv4Obj":
                ip_str = '{0}/{1}'.format(str(arg.ip_object), arg.prefixlen)
                self.network_object = IPv4Network(ip_str, strict=False)
                self.ip_object = IPv4Address(str(arg.ip_object))
                return None
            elif isinstance(arg, IPv4Network):
                self.network_object = arg
                self.ip_object = IPv4Address(str(arg).split('/')[0])
                return None
            elif isinstance(arg, IPv4Address):
                self.network_object = IPv4Network(str(arg)+'/32')
                self.ip_object = IPv4Address(str(arg).split('/')[0])
                return None
            else:
                raise ValueError(
                    "IPv4Obj doesn't understand how to parse {0}".format(arg))

        ERROR = "IPv4Obj couldn't parse '{0}'".format(arg)
        assert (not (mm is None)), ERROR

        mm_result = mm.groupdict()
        addr = mm_result['addr0'] or mm_result['addr1'] \
            or mm_result['addr2'] or '127.0.0.1'

        ## Normalize addr if we get zero-padded strings, i.e. 172.001.001.001
        addr = '.'.join([str(int(ii)) for ii in addr.split('.')])

        masklen = int(mm_result['masklen'] or 32)
        netmask = mm_result['netmask']
        if netmask:
            ## ALWAYS check for the netmask first
            self.network_object = IPv4Network(
                '{0}/{1}'.format(addr, netmask), strict=strict)
            self.ip_object = IPv4Address('{0}'.format(addr))
        else:
            self.network_object = IPv4Network(
                '{0}/{1}'.format(addr, masklen), strict=strict)
            self.ip_object = IPv4Address('{0}'.format(addr))

    def __repr__(self):
        return """<IPv4Obj {0}/{1}>""".format(
            str(self.ip_object), self.prefixlen)

    def __eq__(self, val):
        try:
            if self.network_object == val.network_object:
                return True
            return False
        except (Exception) as e:
            errmsg = "'{0}' cannot compare itself to '{1}': {2}".format(
                self.__repr__(), val, e)
            raise ValueError(errmsg)

    def __gt__(self, val):
        try:
            val_in_self = self.__contains__(val)
            val_nobj = getattr(val, 'network_object')
            self_nobj = getattr(self, 'network_object')
            val_dec = getattr(val, 'as_decimal')
            self_dec = getattr(self, 'as_decimal')

            if val_in_self:
                # Sort shorter masks as lower...
                return False
            elif self_nobj==val_nobj:
                return (self_dec > val_dec)
            else:
                return (self_nobj > val_nobj)
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(
                self.__repr__(), val)
            raise ValueError(errmsg)

    def __lt__(self, val):
        try:
            val_in_self = self.__contains__(val)
            val_nobj = getattr(val, 'network_object')
            self_nobj = getattr(self, 'network_object')
            val_dec = getattr(val, 'as_decimal')
            self_dec = getattr(self, 'as_decimal')

            if val_in_self:
                # Sort shorter masks as lower...
                return True
            elif self_nobj==val_nobj:
                return (self_dec < val_dec)
            else:
                return (self_nobj < val_nobj)
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(
                self.__repr__(), val)
            raise ValueError(errmsg)

    def __contains__(self, val):
        # Used for "foo in bar"... python calls bar.__contains__(foo)
        try:
            if (self.network_object.prefixlen == 0):
                return True
            elif self.network_object.prefixlen > val.network_object.prefixlen:
                # obvious shortcut... if this object's mask is longer than
                #    val, this object cannot contain val
                return False
            else:
                #return (val.network in self.network)
                return (self.network<=val.network) and \
                    (self.broadcast>=val.broadcast)

        except (Exception) as e:
            raise ValueError(
                "Could not check whether '{0}' is contained in '{1}': {2}".
                format(val, self, e))

    def __hash__(self):
        # Python3 needs __hash__()
        return hash(str(self.ip_object)) + hash(str(self.prefixlen))

    def __iter__(self):
        return self.network_object.__iter__()

    def __next__(self):
        ## For Python3 iteration...
        return self.network_object.__next__()

    def next(self):
        ## For Python2 iteration...
        return self.network_object.__next__()

    @property
    def ip(self):
        """Returns the address as an IPv4Address object."""
        return self.ip_object

    @property
    def netmask(self):
        """Returns the network mask as an IPv4Address object."""
        return self.network_object.netmask

    @property
    def prefixlen(self):
        """Returns the length of the network mask as an integer."""
        return self.network_object.prefixlen

    @property
    def prefixlength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    @property
    def broadcast(self):
        """Returns the broadcast address as an IPv4Address object."""
        if sys.version_info[0] < 3:
            return self.network_object.broadcast
        else:
            return self.network_object.broadcast_address

    @property
    def network(self):
        """Returns an IPv4Network object, which represents this network.
        """
        if sys.version_info[0] < 3:
            return self.network_object.network
        else:
            ## The ipaddress module returns an "IPAddress" object in Python3...
            return IPv4Network('{0}'.format(self.network_object.compressed))

    @property
    def hostmask(self):
        """Returns the host mask as an IPv4Address object."""
        return self.network_object.hostmask

    @property
    def version(self):
        """Returns the version of the object as an integer.  i.e. 4"""
        return 4

    @property
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if sys.version_info[0] < 3:
            return self.network_object.numhosts
        else:
            return 2**(32 - self.network_object.prefixlen)

    @property
    def as_decimal(self):
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.ip).split('.')
        num_strings.reverse()  # reverse the order
        return sum(
            [int(num) * (256**idx) for idx, num in enumerate(num_strings)])

    @property
    def as_zeropadded(self):
        """Returns the IP address as a zero-padded string (useful when sorting)"""
        num_strings = str(self.ip).split('.')
        return '.'.join(
            ['{0:03}'.format(int(num)) for num in num_strings])

    @property
    def as_zeropadded_network(self):
        """Returns the IP network as a zero-padded string (useful when sorting)"""
        num_strings = str(self.network).split('.')
        return '.'.join(
            ['{0:03}'.format(int(num)) for num in num_strings])

    @property
    def as_binary_tuple(self):
        """Returns the IP address as a tuple of zero-padded binary strings"""
        return tuple(['{0:08b}'.format(int(num)) for num in \
            str(self.ip).split('.')])

    @property
    def as_hex_tuple(self):
        """Returns the IP address as a tuple of zero-padded hex strings"""
        return tuple(['{0:02x}'.format(int(num)) for num in \
            str(self.ip).split('.')])

    @property
    def is_multicast(self):
        """Returns a boolean for whether this is a multicast address"""
        return self.network_object.is_multicast

    @property
    def is_private(self):
        """Returns a boolean for whether this is a private address"""
        return self.network_object.is_private

    @property
    def is_reserved(self):
        """Returns a boolean for whether this is a reserved address"""
        return self.network_object.is_reserved


## Emulate the old behavior of ipaddr.IPv6Network in Python2, which can use
##    IPv6Network with a host address.  Google removed that in Python3's 
##    ipaddress.py module
class IPv6Obj(object):
    """An object to represent IPv6 addresses and IPv6Networks.  When :class:`~ccp_util.IPv6Obj` objects are compared or sorted, shorter masks are greater than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses.

    Kwargs:
        - arg (str): A string containing an IPv6 address, and optionally a netmask or masklength.  The following address/netmask formats are supported: "2001::dead:beef", "2001::dead:beef/64",

    Attributes:
        - network_object : An IPv6Network object
        - ip_object  : An IPv6Address object
        - ip : An IPv6Address object
        - as_binary_tuple (tuple): The ipv6 address as a tuple of zero-padded binary strings
        - as_decimal (int): The ipv6 address as a decimal integer
        - as_hex_tuple (tuple): The ipv6 address as a tuple of zero-padded 8-bit hex strings
        - network (str): A string representing the network address
        - netmask (str): A string representing the netmask
        - prefixlen (int): An integer representing the length of the netmask
        - broadcast: raises `NotImplementedError`; IPv6 doesn't use broadcast
        - hostmask (str): A string representing the hostmask
        - numhosts (int): An integer representing the number of hosts contained in the network

    Returns:
        - an instance of :class:`~ccp_util.IPv6Obj`.

    """

    def __init__(self, arg='::1/128', strict=False):

        #arg= _RGX_IPV6ADDR_NETMASK.sub(r'\1/\2', arg) # mangle IOS: 'addr mask'
        self.arg = arg
        self.dna = "IPv6Obj"

        try:
            mm = _RGX_IPV6ADDR.search(arg)
        except TypeError:
            if getattr(arg, 'dna', '')=="IPv6Obj":
                ip_str = '{0}/{1}'.format(str(arg.ip_object), arg.prefixlen)
                self.network_object = IPv6Network(ip_str, strict = False)
                self.ip_object = IPv6Address(str(arg.ip_object))
                return None
            elif isinstance(arg, IPv6Network):
                self.network_object = arg
                self.ip_object = IPv6Address(str(arg).split('/')[0])
                return None
            elif isinstance(arg, IPv6Address):
                self.network_object = IPv6Network(str(arg)+'/128')
                self.ip_object = IPv6Address(str(arg).split('/')[0])
                return None
            else:
                raise ValueError(
                    "IPv6Obj doesn't understand how to parse {0}".format(arg))

        assert (not (mm is None)), "IPv6Obj couldn't parse {0}".format(arg)
        self.network_object = IPv6Network(arg, strict=strict)
        self.ip_object = IPv6Address(mm.group(1))

# 'address_exclude', 'compare_networks', 'hostmask', 'ipv4_mapped', 'iter_subnets', 'iterhosts', 'masked', 'max_prefixlen', 'netmask', 'network', 'numhosts', 'overlaps', 'prefixlen', 'sixtofour', 'subnet', 'supernet', 'teredo', 'with_hostmask', 'with_netmask', 'with_prefixlen'

    def __repr__(self):
        return """<IPv6Obj {0}/{1}>""".format(
            str(self.ip_object), self.prefixlen)

    def __eq__(self, val):
        try:
            if self.network_object == val.network_object:
                return True
            return False
        except (Exception) as e:
            errmsg = "'{0}' cannot compare itself to '{1}': {2}".format(
                self.__repr__(), val, e)
            raise ValueError(errmsg)

    def __gt__(self, val):
        try:
            val_in_self = self.__contains__(val)
            val_nobj = getattr(val, 'network_object')
            self_nobj = getattr(self, 'network_object')
            val_dec = getattr(val, 'as_decimal')
            self_dec = getattr(self, 'as_decimal')

            if val_in_self:
                # Sort shorter masks as higher...
                return False
            elif self_nobj==val_nobj:
                return (self_dec > val_dec)
            else:
                return (self_nobj > val_nobj)
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(
                self.__repr__(), val)
            raise ValueError(errmsg)

    def __lt__(self, val):
        try:
            val_in_self = self.__contains__(val)
            val_nobj = getattr(val, 'network_object')
            self_nobj = getattr(self, 'network_object')
            val_dec = getattr(val, 'as_decimal')
            self_dec = getattr(self, 'as_decimal')

            if val_in_self:
                # Sort shorter masks as higher...
                return True
            elif self_nobj==val_nobj:
                return (self_dec < val_dec)
            else:
                return (self_nobj < val_nobj)
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(
                self.__repr__(), val)
            raise ValueError(errmsg)

    def __contains__(self, val):
        # Used for "foo in bar"... python calls bar.__contains__(foo)
        try:
            if (self.network_object.prefixlen == 0):
                return True
            elif self.network_object.prefixlen > val.network_object.prefixlen:
                # obvious shortcut... if this object's mask is longer than
                #    val, this object cannot contain val
                return False
            else:
                #return (val.network in self.network)
                return (self.network<=val.network) and \
                    (self.broadcast>=val.broadcast)

        except (Exception) as e:
            raise ValueError(
                "Could not check whether '{0}' is contained in '{1}': {2}".
                format(val, self, e))

    def __hash__(self):
        # Python3 needs __hash__()
        return hash(str(self.ip_object)) + hash(str(self.prefixlen))

    def __iter__(self):
        return self.network_object.__iter__()

    def __next__(self):
        ## For Python3 iteration...
        return self.network_object.__next__()

    def next(self):
        ## For Python2 iteration...
        return self.network_object.__next__()

    @property
    def ip(self):
        """Returns the address as an IPv6Address object."""
        return self.ip_object

    @property
    def netmask(self):
        """Returns the network mask as an IPv6Address object."""
        return self.network_object.netmask

    @property
    def prefixlen(self):
        """Returns the length of the network mask as an integer."""
        return self.network_object.prefixlen

    @property
    def prefixlength(self):
        """Returns the length of the network mask as an integer."""
        return self.prefixlen

    @property
    def compressed(self):
        """Returns the IPv6 object in compressed form"""
        return self.network_object.compressed

    @property
    def exploded(self):
        """Returns the IPv6 object in exploded form"""
        return self.network_object.exploded

    @property
    def packed(self):
        """Returns the IPv6 object in packed form"""
        return self.network_object.packed

    @property
    def broadcast(self):
        raise NotImplementedError("IPv6 does not have broadcasts")

    @property
    def network(self):
        """Returns an IPv6Network object, which represents this network.
        """
        if sys.version_info[0] < 3:
            return self.network_object.network
        else:
            ## The ipaddress module returns an "IPAddress" object in Python3...
            return IPv6Network('{0}'.format(self.network_object.compressed))

    @property
    def hostmask(self):
        """Returns the host mask as an IPv6Address object."""
        return self.network_object.hostmask

    @property
    def version(self):
        """Returns the version of the object as an integer.  i.e. 4"""
        return 6

    @property
    def numhosts(self):
        """Returns the total number of IP addresses in this network, including broadcast and the "subnet zero" address"""
        if sys.version_info[0] < 3:
            return self.network_object.numhosts
        else:
            return 2**(128 - self.network_object.prefixlen)

    @property
    def as_decimal(self):
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.ip.exploded).split(':')
        num_strings.reverse()  # reverse the order
        return sum(
            [int(num, 16) * (256**idx) for idx, num in enumerate(num_strings)])

    @property
    def as_binary_tuple(self):
        """Returns the IPv6 address as a tuple of zero-padded 8-bit binary strings"""
        nested_list = [
            ['{0:08b}'.format(int(ii, 16)) for ii in [num[0:2], num[2:4]]]
            for num in str(self.ip.exploded).split(':')
        ]
        return tuple(itertools.chain(*nested_list))

    @property
    def as_hex_tuple(self):
        """Returns the IPv6 address as a tuple of zero-padded 8-bit hex strings"""
        nested_list = [
            ['{0:02x}'.format(int(ii, 16)) for ii in [num[0:2], num[2:4]]]
            for num in str(self.ip.exploded).split(':')
        ]
        return tuple(itertools.chain(*nested_list))

    @property
    def is_multicast(self):
        """Returns a boolean for whether this is a multicast address"""
        return self.network_object.is_multicast

    @property
    def is_private(self):
        """Returns a boolean for whether this is a private address"""
        return self.network_object.is_private

    @property
    def is_reserved(self):
        """Returns a boolean for whether this is a reserved address"""
        return self.network_object.is_reserved

    @property
    def is_link_local(self):
        """Returns a boolean for whether this is an IPv6 link-local address"""
        return self.network_object.is_link_local

    @property
    def is_site_local(self):
        """Returns a boolean for whether this is an IPv6 site-local address"""
        return self.network_object.is_site_local

    @property
    def is_unspecified(self):
        """Returns a boolean for whether this address is not otherwise 
        classified"""
        return self.network_object.is_unspecified

    @property
    def teredo(self):
        return self.network_object.teredo

    @property
    def sixtofour(self):
        return self.network_object.sixtofour


class L4Object(object):
    """Object for Transport-layer protocols; the object ensures that logical operators (such as le, gt, eq, and ne) are parsed correctly, as well as mapping service names to port numbers"""

    def __init__(self, protocol='', port_spec='', syntax=''):
        self.protocol = protocol
        self.port_list = list()
        self.syntax = syntax

        try:
            port_spec = port_spec.strip()
        except:
            port_spec = port_spec

        if syntax == 'asa':
            if protocol == 'tcp':
                ports = ASA_TCP_PORTS
            elif protocol == 'udp':
                ports = ASA_UDP_PORTS
            else:
                raise NotImplementedError(
                    "'{0}' is not supported: '{0}'".format(protocol))
        else:
            raise NotImplementedError("This syntax is unknown: '{0}'".format(
                syntax))

        if 'eq ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = [int(ports.get(port_str, port_str))]
        elif re.search(r'^\S+$', port_spec):
            # Technically, 'eq ' is optional...
            self.port_list = [int(ports.get(port_spec, port_spec))]
        elif 'range ' in port_spec:
            port_tmp = re.split('\s+', port_spec)[1:]
            self.port_list = range(
                int(ports.get(port_tmp[0], port_tmp[0])),
                int(ports.get(port_tmp[1], port_tmp[1])) + 1)
        elif 'lt ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = range(1, int(ports.get(port_str, port_str)))
        elif 'gt ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = range(
                int(ports.get(port_str, port_str)) + 1, 65535)
        elif 'neq ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            tmp = set(range(1, 65535))
            tmp.remove(int(port_str))
            self.port_list = sorted(tmp)

    def __eq__(self, val):
        if (self.protocol == val.protocol) and (
                self.port_list == val.port_list):
            return True
        return False

    def __repr__(self):
        return "<L4Object {0} {1}>".format(self.protocol, self.port_list)

class DNSResponse(object):
    """A universal DNS Response object

    Kwargs:
        - query_type (str): A string containing the DNS record to lookup
        - result_str (str): A string containing the DNS Response
        - input (str): The DNS query string
        - duration (float): The query duration in seconds 

    Attributes:
        - query_type (str): A string containing the DNS record to lookup
        - result_str (str): A string containing the DNS Response
        - input (str): The DNS query string
        - has_error (bool): Indicates the query resulted in an error when True
        - error_str (str): The error returned by dnspython
        - duration (float): The query duration in seconds 
        - preference (int): The MX record's preference (default: -1)

    Returns:
        A :class:`~ccp_util.DNSResponse` instance
"""
    def __init__(self, query_type="", result_str="", input="", duration=0.0):
        self.query_type = query_type
        self.result_str = result_str
        self.input = input
        self.duration = duration  # Query duration in seconds

        self.has_error = False
        self.error_str = ""
        self.preference = -1   # MX Preference

    def __str__(self):
        return self.result_str

    def __repr__(self):
        if not self.has_error:
            return '<DNSResponse "{0}" result_str="{1}">'.format(
                self.query_type, self.result_str)
        else:
            return '<DNSResponse "{0}" error="{1}">'.format(
                self.query_type, self.error_str)

def dns_query(input="", query_type="", server="", timeout=2.0):
    """A unified IPv4 & IPv6 DNS lookup interface; this is essentially just a wrapper around dnspython's API.  When you query a PTR record, you can use an IPv4 or IPv6 address (which will automatically be converted into an in-addr.arpa name.  This wrapper only supports a subset of DNS records: 'A', 'AAAA', 'CNAME', 'MX', 'NS', 'PTR', and 'TXT'

    Kwargs:
        - input (str): A string containing the DNS record to lookup
        - query_type (str): A string containing the DNS record type (SOA not supported)
        - server (str): A string containing the fqdn or IP address of the dns server
        - timeout (float): DNS lookup timeout duration (default: 2.0 seconds)

    Returns:
        A set() of :class:`~ccp_util.DNSResponse` instances

>>> from ciscoconfparse.ccp_util import dns_query
>>> dns_query('www.pennington.net', "A", "4.2.2.2")
set([<DNSResponse "A" result_str="65.19.187.2">])
>>> answer = dns_query('www.pennington.net', 'A', '4.2.2.2')
>>> str(answer.pop())
'65.19.187.2'
>>>
    """

    valid_records = set(['A', 'AAAA', 'AXFR', 'CNAME', 'MX', 'NS', 'PTR', 
        'TXT'])
    query_type = query_type.upper()
    assert query_type in valid_records
    assert server!=""
    assert float(timeout)>0
    assert input != ""
    intput = input.strip()
    retval = set([])
    resolver = Resolver()
    resolver.server = [socket.gethostbyname(server)]
    resolver.timeout = float(timeout)
    resolver.lifetime = float(timeout)
    start = time.time()
    if (query_type=="A") or (query_type=="AAAA"):
        try:
            answer = resolver.query(input, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    duration=duration,
                    input=input, result_str = str(result.address))
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, 
                    duration=duration, query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    elif query_type=="AXFR":
        """This is a hack: return text of zone transfer, instead of axfr objs"""
        _zone = zone.from_xfr(query.xfr(server, input, lifetime=timeout))
        return [_zone[node].to_text(node) for node in _zone.nodes.keys()]
    elif query_type=="CNAME":
        try:
            answer = resolver.query(input, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    duration=duration, 
                    input=input, result_str = str(result.target))
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, duration=duration,
                    query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    elif query_type=="MX":
        try:
            answer = resolver.query(input, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    input=input, result_str = str(result.target))
                response.preference = int(result.preference)
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, duration=duration,
                    query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    elif query_type=="NS":
        try:
            answer = resolver.query(input, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    duration=duration,
                    input=input, result_str = str(result.target))
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, 
                    duration=duration, query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    elif query_type=="PTR":
        if is_valid_ipv4_addr(input) or is_valid_ipv6_addr(input):
            inaddr = reversename.from_address(input)
        elif 'in-addr.arpa' in input.lower():
            inaddr = input
        else:
            raise ValueError('Cannot query PTR record for "{0}"'.format(input))

        try:
            answer = resolver.query(inaddr, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    duration=duration,
                    input=inaddr, result_str = str(result.target))
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, 
                    duration=duration,
                    query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    elif query_type=="TXT":
        try:
            answer = resolver.query(input, query_type)
            duration = time.time() - start
            for result in answer:
                response = DNSResponse(query_type=query_type, 
                    duration=duration,
                    input=inaddr, result_str = str(result.strings))
                retval.add(response)
        except DNSException as e:
                duration = time.time() - start
                response = DNSResponse(input=input, 
                    duration=duration, query_type=query_type)
                response.has_error = True
                response.error_str = e
                retval.add(response)
    return retval

def dns_lookup(input, timeout=3, server=''):
    """Perform a simple DNS lookup, return results in a dictionary"""
    resolver = Resolver()
    resolver.timeout = float(timeout)
    resolver.lifetime = float(timeout)
    if server:
        resolver.nameservers = [server]
    try:
        records = resolver.query(input, 'A')
        return {
            'addrs': [ii.address for ii in records],
            'error': '',
            'name': input,
        }
    except DNSException as e:
        return {
            'addrs': [],
            'error': repr(e),
            'name': input,
        }


def dns6_lookup(input, timeout=3, server=''):
    """Perform a simple DNS lookup, return results in a dictionary"""
    resolver = Resolver()
    resolver.timeout = float(timeout)
    resolver.lifetime = float(timeout)
    if server:
        resolver.nameservers = [server]
    try:
        records = resolver.query(input, 'AAAA')
        return {
            'addrs': [ii.address for ii in records],
            'error': '',
            'name': input,
        }
    except DNSException as e:
        return {
            'addrs': [],
            'error': repr(e),
            'name': input,
        }


_REVERSE_DNS_REGEX = re.compile(r'^\s*\d+\.\d+\.\d+\.\d+\s*$')

def reverse_dns_lookup(input, timeout=3, server=''):
    """Perform a simple reverse DNS lookup, return results in a dictionary"""
    assert _REVERSE_DNS_REGEX.search(
        input), "Invalid address format: '{0}'".format(input)
    resolver = Resolver()
    resolver.timeout = float(timeout)
    resolver.lifetime = float(timeout)
    if server:
        resolver.nameservers = [server]
    try:
        tmp = input.strip().split('.')
        tmp.reverse()
        inaddr = '.'.join(tmp) + ".in-addr.arpa"
        records = resolver.query(inaddr, 'PTR')
        return {
            'name': records[0].to_text(),
            'lookup': inaddr,
            'error': '',
            'addr': input,
        }
    except DNSException as e:
        return {
            'addrs': [],
            'lookup': inaddr,
            'error': repr(e),
            'name': input,
        }


class CiscoRange(MutableSequence):
    """Explode Cisco ranges into a list of explicit items... examples below...

>>> from ciscoconfparse.ccp_util import CiscoRange
>>> CiscoRange('1-3,5,9-11,13')
<CiscoRange 1-3,5,9-11,13>
>>> CiscoRange('Eth1/1-3,7')
<CiscoRange Eth1/1-3,7>
>>> CiscoRange()
<CiscoRange none>
    """
    def __init__(self, text="", result_type=str):
        super(CiscoRange, self).__init__()
        self.text = text
        self.result_type = result_type
        if text:
            self.line_prefix, self.slot_prefix, self.range_text = self._parse_range_text()
            self._list = self._range()
        else:
            self.line_prefix = ""
            self.slot_prefix = ""
            self._list = list()

    def __repr__(self):
        if len(self._list)==0:
            return """<CiscoRange none>"""
        else:
            return """<CiscoRange {0}>""".format(self.compressed_str)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        del self._list[ii]

    def __setitem__(self, ii, val):
        return self._list[ii]

    def __str__(self):
        return self.__repr__()

    # Github issue #124
    def __eq__(self, other):
        assert hasattr(other, 'line_prefix')
        self_prefix_str = self.line_prefix + self.slot_prefix
        other_prefix_str = other.line_prefix + other.slot_prefix
        cmp1 = self_prefix_str.lower()==other_prefix_str.lower()
        cmp2 = sorted(self._list)==sorted(other._list)
        return cmp1 and cmp2

    def insert(self, ii, val):
        ## Insert something at index ii
        for idx, obj in enumerate(
                CiscoRange(
                    val, result_type=self.result_type)):
            self._list.insert(ii + idx, obj)

        # Prune out any duplicate entries, and sort...
        self._list = sorted(map(self.result_type, set(self._list)))
        return self

    def append(self, val):
        list_idx = len(self._list)
        self.insert(list_idx, val)
        return self

    def _parse_range_text(self):
        tmp = self.text.split(',')
        mm = _RGX_CISCO_RANGE.search(tmp[0])

        ERROR = "CiscoRange() couldn't parse '{0}'".format(self.text)
        assert (not (mm is None)), ERROR

        mm_result = mm.groupdict()
        line_prefix = mm_result.get('line_prefix', "") or ""
        slot_prefix = mm_result.get('slot_prefix', "") or ""
        if len(tmp[1:]) > 1:
            range_text = mm_result['range_text'] + ',' + ','.join(tmp[1:])
        elif len(tmp[1:]) == 1:
            range_text = mm_result['range_text'] + ',' + tmp[1]
        elif len(tmp[1:]) == 0:
            range_text = mm_result['range_text']
        return line_prefix, slot_prefix, range_text

    def _parse_dash_range(self, text):
        """Parse a dash Cisco range into a discrete list of items"""
        retval = list()
        for range_atom in text.split(','):
            try:
                begin, end = range_atom.split('-')
            except ValueError:
                ## begin and end are the same number
                begin, end = range_atom, range_atom
            begin, end = int(begin.strip()), int(end.strip()) + 1
            assert begin > -1
            assert end > begin
            retval.extend(range(begin, end))
        return list(set(retval))

    def _range(self):
        """Enumerate all values in the CiscoRange()"""

        def combine(arg):
            return self.line_prefix + self.slot_prefix + str(arg)

        return [self.result_type(ii) for ii in map(combine, self._parse_dash_range(self.range_text))]

    def remove(self, arg):
        remove_obj = CiscoRange(arg)
        for ii in remove_obj:
            try:
                ## Remove arg, even if duplicated... Ref Github issue #126
                while True:
                    index = self.index(self.result_type(ii))
                    self.pop(index)
            except ValueError:
                pass
        return self

    @property
    def as_list(self):
        return self._list

    ## Github issue #125
    @property
    def compressed_str(self):
        """Return a text string with a compressed csv of values

>>> from ciscoconfparse.ccp_util import CiscoRange
>>> range_obj = CiscoRange('1,3,5,6,7')
>>> range_obj.compressed_str
'1,3,5-7'
>>>
        """
        retval = list()
        prefix_str = self.line_prefix + self.slot_prefix

        # Build a list of integers (without prefix_str)
        input = list()
        for ii in self._list:
            try:
                unicode_ii = str(ii, 'utf-8') # Python2.7...
            except:
                unicode_ii = str(ii)
            ii = re.sub(r'^{0}(\d+)$'.format(prefix_str), '\g<1>', unicode_ii)
            input.append(int(ii))

        if len(input)==0: # Special case, handle empty list
            return ''

        # source - https://stackoverflow.com/a/51227915/667301
        input = sorted(list(set(input)))
        range_list = [input[0]]
        for ii in range(len(input)):
            if ii+1<len(input) and ii-1>-1:
                if (input[ii]-input[ii-1]==1) and (input[ii+1]-input[ii]==1):
                    if  range_list[-1]!='-':
                        range_list += ['-']
                    else:
                        range_list = range_list
                else:
                        range_list+=[input[ii]]
        if len(input)>1:
            range_list+=[input[len(input)-1]]

        # Build the return value from range_list...
        retval = prefix_str + str(range_list[0])
        for ii in range(1,len(range_list)):
            if str(type(range_list[ii]))!=str(type(range_list[ii-1])):
                retval += str(range_list[ii])
            else:
                retval += ',' + str(range_list[ii])

        return retval
