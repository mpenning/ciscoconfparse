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
Wrapper around the ipv4 and ipv6 modules to handle both, ipv4 and ipv6.
"""
from Exscript.util import ipv4
from Exscript.util import ipv6

def is_ip(string):
    """
    Returns True if the given string is an IPv4 or IPv6 address, False
    otherwise.

    @type  string: string
    @param string: Any string.
    @rtype:  bool
    @return: True if the string is an IP address, False otherwise.
    """
    return ipv4.is_ip(string) or ipv6.is_ip(string)

def _call_func(funcname, ip, *args):
    if ipv4.is_ip(ip):
        return ipv4.__dict__[funcname](ip, *args)
    elif ipv6.is_ip(ip):
        return ipv6.__dict__[funcname](ip, *args)
    raise ValueError('neither ipv4 nor ipv6: ' + repr(ip))

def normalize_ip(ip):
    """
    Transform the address into a fixed-length form, such as:

        192.168.0.1 -> 192.168.000.001
        1234::A -> 1234:0000:0000:0000:0000:0000:0000:000a

    @type  ip: string
    @param ip: An IP address.
    @rtype:  string
    @return: The normalized IP.
    """
    return _call_func('normalize_ip', ip)

def clean_ip(ip):
    """
    Cleans the ip address up, useful for removing leading zeros, e.g.::

        192.168.010.001 -> 192.168.10.1
        1234:0000:0000:0000:0000:0000:0000:000A -> 1234::a

    @type  ip: string
    @param ip: An IP address.
    @rtype:  string
    @return: The cleaned up IP.
    """
    return _call_func('clean_ip', ip)
