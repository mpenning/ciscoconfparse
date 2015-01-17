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

            self_prefixlen = self.network_object.prefixlen
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

            self_prefixlen = self.network_object.prefixlen
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
