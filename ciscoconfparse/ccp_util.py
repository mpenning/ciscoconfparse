from collections import MutableSequence
try:
    from itertools import takewhile, count
    from itertools import izip as zip
except:
    pass
import sys
import re
import os

from protocol_values import ASA_TCP_PORTS, ASA_UDP_PORTS

try:
    if sys.version_info[0]<3:
        from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
    else:
        from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
except:
    sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "local_py"))
    # re: modules usage... thank you Delnan
    # http://stackoverflow.com/a/5027393
    if (sys.version_info[0]<3) and \
        (bool(sys.modules.get('ipaddr', False)) is False):
        # Relative import path referenced to this directory
        from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
    elif (sys.version_info[0]==3) and \
        (bool(sys.modules.get('ipaddress', False)) is False):
        # Relative import path referenced to this directory
        from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

""" ccp_util.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2014-2015 David Michael Pennington

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

RGX_IPV4ADDR = re.compile(r'^(\d+\.\d+\.\d+\.\d+)')
RGX_IPV4ADDR_NETMASK = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)')

## Emulate the old behavior of ipaddr.IPv4Network in Python2, which can use
##    IPv4Network with a host address.  Google removed that in Python3's 
##    ipaddress.py module
class IPv4Obj(object):
    """An object to represent IPv4 addresses and IPv4Networks.  When :class:`~ccp_util.IPv4Obj` objects are compared or sorted, shorter masks are greater than longer masks. After comparing mask length, numerically higher IP addresses are greater than numerically lower IP addresses.

    Kwargs:
        - arg (str): A string containing an IPv4 address, and optionally a netmask or masklength.  The following address/netmask formats are supported: "10.1.1.1/24", "10.1.1.1 255.255.255.0", "10.1.1.1/255.255.255.0"

    Attributes:
        - network_object : An IPv4Network object
        - ip_object  : An IPAddress object
        - ip : An IPAddress object
        - network (str): A string representing the network address
        - netmask (str): A string representing the netmask
        - prefixlen (int): An integer representing the length of the netmask
        - broadcast (str): A string representing the broadcast address
        - hostmask (str): A string representing the hostmask
        - numhosts (int): An integer representing the number of hosts contained in the network

    Returns:
        - an instance of :class:`~ccp_util.IPv4Obj`.

    """
    def __init__(self, arg='127.0.0.1/32', strict=False):

        RGX_IPV4ADDR = re.compile(r'^(\d+\.\d+\.\d+\.\d+)')
        RGX_IPV4ADDR_NETMASK = re.compile(r'(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)')

        arg = RGX_IPV4ADDR_NETMASK.sub(r'\1/\2', arg) # mangle IOS: 'addr mask'
        self.arg = arg
        mm = RGX_IPV4ADDR.search(arg)
        assert (not (mm is None)), "IPv4Obj couldn't parse {0}".format(arg)
        self.network_object = IPv4Network(arg, strict=strict)
        self.ip_object = IPv4Address(mm.group(1))


    def __repr__(self):
        return """<IPv4Obj {0}/{1}>""".format(str(self.ip_object), self.prefixlen)
    def __eq__(self, val):
        try:
            if self.network_object==val.network_object:
                return True
            return False
        except (Exception) as e:
            errmsg = "'{0}' cannot compare itself to '{1}': {2}".format(self.__repr__(), val, e)
            raise ValueError(errmsg)

    def __gt__(self, val):
        try:
            val_prefixlen = int(getattr(val, 'prefixlen'))
            val_nobj = getattr(val, 'network_object')

            self_nobj = self.network_object
            if (self.network_object.prefixlen<val_prefixlen):
                # Sort shorter masks as higher...
                return True
            elif (self.network_object.prefixlen>val_prefixlen):
                return False
            elif (self_nobj>val_nobj):
                # If masks are equal, rely on Google's sorting...
                return True
            return False
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(self.__repr__(), val)
            raise ValueError(errmsg)

    def __lt__(self, val):
        try:
            val_prefixlen = int(getattr(val, 'prefixlen'))
            val_nobj = getattr(val, 'network_object')

            self_nobj = self.network_object
            if (self.network_object.prefixlen>val_prefixlen):
                # Sort shorter masks as lower...
                return True
            elif (self.network_object.prefixlen<val_prefixlen):
                return False
            elif (self_nobj<val_nobj):
                # If masks are equal, rely on Google's sorting...
                return True
            return False
        except:
            errmsg = "{0} cannot compare itself to '{1}'".format(self.__repr__(), val)
            raise ValueError(errmsg)

    def __contains__(self, val):
        # Used for "foo in bar"... python calls bar.__contains__(foo)
        try:
            if (self.network_object.prefixlen==0):
                return True
            elif self.network_object.prefixlen>val.network_object.prefixlen:
                # obvious shortcut... if this object's mask is longer than
                #    val, this object cannot contain val
                return False
            else:
                #return (val.network in self.network)
                return (self.network<=val.network) and \
                    (self.broadcast>=val.broadcast)

        except (Exception) as e:
            raise ValueError("Could not check whether '{0}' is contained in '{1}': {2}".format(val, self, e))

    def __hash__(self):
        # Python3 needs __hash__()
        return hash(str(self.ip_object))+hash(str(self.prefixlen))

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
    def broadcast(self):
        """Returns the broadcast address as an IPv4Address object."""
        if sys.version_info[0]<3:
            return self.network_object.broadcast
        else:
            return self.network_object.broadcast_address

    @property
    def network(self):
        """Returns an IPv4Network object, which represents this network.
        """
        if sys.version_info[0]<3:
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
        if sys.version_info[0]<3:
            return self.network_object.numhosts
        else:
            return 2**(32-self.network_object.prefixlen)

    @property
    def as_decimal(self):
        """Returns the IP address as a decimal integer"""
        num_strings = str(self.ip).split('.')
        num_strings.reverse()  # reverse the order
        return sum([int(num)*(256**idx) for idx, num in enumerate(num_strings)])

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

        if syntax=='asa':
            if protocol=='tcp':
                ports = ASA_TCP_PORTS
            elif protocol=='udp':
                ports = ASA_UDP_PORTS
            else:
                raise NotImplementedError("'{0}' is not supported: '{0}'".format(protocol))
        else:
            raise NotImplementedError("This syntax is unknown: '{0}'".format(syntax))

        if 'eq ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = [int(ports.get(port_str, port_str))]
        elif re.search(r'^\S+$', port_spec):
            # Technically, 'eq ' is optional...
            self.port_list = [int(ports.get(port_spec, port_spec))]
        elif 'range ' in port_spec:
            port_tmp = re.split('\s+', port_spec)[1:]
            self.port_list = range(int(ports.get(port_tmp[0], port_tmp[0])), 
                int(ports.get(port_tmp[1], port_tmp[1])) + 1)
        elif 'lt ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = range(1, int(ports.get(port_str, port_str)))
        elif 'gt ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            self.port_list = range(int(ports.get(port_str, port_str)) + 1, 65535)
        elif 'neq ' in port_spec:
            port_str = re.split('\s+', port_spec)[-1]
            tmp = set(range(1, 65535))
            tmp.remove(int(port_str))
            self.port_list = sorted(tmp)

    def __eq__(self, val):
        if (self.protocol==val.protocol) and (self.port_list==val.port_list):
            return True
        return False

    def __repr__(self):
        return "<L4Object {0} {1}>".format(self.protocol, self.port_list)

class DelimitedMatches(MutableSequence):
    """A list which specifies how delimited matches should be processed; 
    all matches start at index=0, and terminate either at the end of the 
    delimted sequence in question, or at the corresponding value of break_arg.

    This list supports a shorthand 'hack' for certain special values:

    - k:i means ignore anything at this position (defaults to "__ignore__")
    - k:m means match anything at this position (defaults to "__match__")
    - k:b means break match iteration at this position (defaults to "__break__")

    *Any other value* in the list will be processed locally by the method receiving 
    the DelimitedMatch instance in question.  Only certain methods support delimited
    matches at this time.
    """
    def __init__(self, match_shim=None, ignore_arg="__ignore__", 
        break_arg="__break__", match_arg="__match__", 
        unknown_arg="__unknown__", substr_arg="__substr__"):

        super(DelimitedMatches, self).__init__()

        self.dna = "DelimitedMatches"
        self.ignore_arg = ignore_arg
        self.break_arg = break_arg
        self.match_arg = match_arg
        self.unknown_arg = unknown_arg
        self.substr_arg = substr_arg
        self._result = False         # Is this a result value?
        self.overflow = False        # Was there an overflow?
        self.overflow_index = -1     # Point where overflow occured

        if getattr(match_shim, 'append', ''):
            self._match_list = [self._match_expansion(ii) 
                for ii in match_shim]
            self._result_list = [unknown_arg for ii in range(0, 
                len(self._match_list))]
        elif (match_shim is None):
            self._match_list = list()
            self._result_list = list()
        else:
            raise ValueError("DelimtedMatches() requires a list")

    @property
    def match_indicies(self):
        """Return the indicies where a match is required"""
        match_indicies = [idx for idx, val in 
                zip(count(), self._match_list) if val==self.match_arg]
        return match_indicies

    @property
    def matched_indicies(self):
        """Return the indicies where a match happened"""
        return list(takewhile(lambda x: self._result_list[x]!=self.unknown_arg, 
            self.match_indicies))

    @property
    def number_unmatched_elements(self):
        """Return the number of unmatched elements"""
        if self._result and self.overflow:
            return len(filter(lambda x: x==self.match_arg, 
                self._match_list[self.overflow_index:]))
        elif self._result and not self.overflow:
            return len(self.match_indicies) - len(self.matched_indicies)
        else:
            return 0

    @property
    def all_matched(self):
        """Return a boolean for whether all matches occured"""
        if self._result and len(self.match_indicies)>0 \
            and (self.number_unmatched_elements==0):
            return True
        else:
            return False

    @property
    def result(self):
        return self._result

    @property
    def match_list(self):
        return self._match_list

    @property
    def result_list(self):
        """Return the list of results"""
        return self._result_list

    @property
    def _list(self):
        if self._result:
            return tuple(self._result_list)
        else:
            return self._match_list

    def _match_expansion(self, arg):
        ## k:i  => __ignore__
        ## k:m  => __match__
        ## k:b  => __break__
        return arg.replace('k:i', self.ignore_arg).replace('k:b', 
            self.break_arg).replace('k:m', self.match_arg)

    def __len__(self):
        return len(self._list)

    def __getitem__(self, ii):
        return self._list[ii]

    def __delitem__(self, ii):
        if not self._result:
            del self._match_list[ii]
            del self._result_list[ii]
        else:
            raise AttributeError("Cannot delete a DelimitedMatches result")

    def __setitem__(self, ii, val):
        if not self._result:
            self._match_list[ii] = self._match_expansion(val)
            self._result_list[ii] = self.unknown_arg
            return self._list[ii]
        else:
            raise AttributeError("Cannot modify a DelimitedMatches result")

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        if self._result:
            return """<DelimitedMatches result {}>""".format(str(self._list))
        else:
            return """<DelimitedMatches match {}>""".format(str(self._list))

    def insert(self, ii, val):
        if not self._result:
            self._match_list.insert(ii, self._match_expansion(val))
            self._result_list.insert(ii, self.unknown_arg)
        else:
            raise AttributeError("Cannot insert in a DelimitedMatches result")

    def append(self, val):
        if not self._result:
            list_idx = len(self._list)
            self._match_list.insert(list_idx, self._match_expansion(val))
            self._result_list.insert(list_idx, self.unknown_arg)
        else:
            raise AttributeError("Cannot append to a DelimitedMatches result")
