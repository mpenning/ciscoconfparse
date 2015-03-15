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
from Exscript.util        import ipv4
from Exscript.stdlib.util import secure_function

@secure_function
def in_network(scope, prefixes, destination, default_pfxlen = [24]):
    """
    Returns True if the given destination is in the network range that is
    defined by the given prefix (e.g. 10.0.0.1/22). If the given prefix
    does not have a prefix length specified, the given default prefix length
    is applied. If no such prefix length is given, the default length is
    /24.

    If a list of prefixes is passed, this function returns True only if
    the given destination is in ANY of the given prefixes.

    @type  prefixes: string
    @param prefixes: A prefix, or a list of IP prefixes.
    @type  destination: string
    @param destination: An IP address.
    @type  default_pfxlen: int
    @param default_pfxlen: The default prefix length.
    @rtype:  True
    @return: Whether the given destination is in the given network.
    """
    needle = ipv4.ip2int(destination[0])
    for prefix in prefixes:
        network, pfxlen = ipv4.parse_prefix(prefix, default_pfxlen[0])
        mask            = ipv4.pfxlen2mask_int(pfxlen)
        if needle & mask == ipv4.ip2int(network) & mask:
            return [True]
    return [False]

@secure_function
def mask(scope, ips, mask):
    """
    Applies the given IP mask (e.g. 255.255.255.0) to the given IP address
    (or list of IP addresses) and returns it.

    @type  ips: string
    @param ips: A prefix, or a list of IP prefixes.
    @type  mask: string
    @param mask: An IP mask.
    @rtype:  string
    @return: The network(s) that result(s) from applying the mask.
    """
    mask = ipv4.ip2int(mask[0])
    return [ipv4.int2ip(ipv4.ip2int(ip) & mask) for ip in ips]

@secure_function
def mask2pfxlen(scope, masks):
    """
    Converts the given IP mask(s) (e.g. 255.255.255.0) to prefix length(s).

    @type  masks: string
    @param masks: An IP mask, or a list of masks.
    @rtype:  string
    @return: The prefix length(s) that result(s) from converting the mask.
    """
    return [ipv4.mask2pfxlen(mask) for mask in masks]

@secure_function
def pfxlen2mask(scope, pfxlen):
    """
    Converts the given prefix length(s) (e.g. 30) to IP mask(s).

    @type  pfxlen: int
    @param pfxlen: An IP prefix length.
    @rtype:  string
    @return: The mask(s) that result(s) from converting the prefix length.
    """
    return [ipv4.pfxlen2mask(pfx) for pfx in pfxlen]

@secure_function
def network(scope, prefixes):
    """
    Given a prefix, this function returns the corresponding network address.

    @type  prefixes: string
    @param prefixes: An IP prefix.
    @rtype:  string
    @return: The network address(es) of the prefix length(s).
    """
    return [ipv4.network(pfx) for pfx in prefixes]

@secure_function
def broadcast(scope, prefixes):
    """
    Given a prefix, this function returns the corresponding broadcast address.

    @type  prefixes: string
    @param prefixes: An IP prefix.
    @rtype:  string
    @return: The broadcast address(es) of the prefix length(s).
    """
    return [ipv4.broadcast(pfx) for pfx in prefixes]

@secure_function
def pfxmask(scope, ips, pfxlen):
    """
    Applies the given prefix length to the given ips, resulting in a
    (list of) IP network addresses.

    @type  ips: string
    @param ips: An IP address, or a list of IP addresses.
    @type  pfxlen: int
    @param pfxlen: An IP prefix length.
    @rtype:  string
    @return: The mask(s) that result(s) from converting the prefix length.
    """
    mask = ipv4.pfxlen2mask_int(pfxlen[0])
    return [ipv4.int2ip(ipv4.ip2int(ip) & mask) for ip in ips]

@secure_function
def remote_ip(scope, local_ips):
    """
    Given an IP address, this function calculates the remaining available
    IP address under the assumption that it is a /30 network.
    In other words, given one link net address, this function returns the
    other link net address.

    @type  local_ips: string
    @param local_ips: An IP address, or a list of IP addresses.
    @rtype:  string
    @return: The other IP address of the link address pair.
    """
    return [ipv4.remote_ip(ip) for ip in local_ips]
