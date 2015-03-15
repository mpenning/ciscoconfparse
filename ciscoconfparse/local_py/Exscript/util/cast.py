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
Handy shortcuts for converting types.
"""
import re
import Exscript

def to_list(item):
    """
    If the given item is iterable, this function returns the given item.
    If the item is not iterable, this function returns a list with only the
    item in it.

    @type  item: object
    @param item: Any object.
    @rtype:  list
    @return: A list with the item in it.
    """
    if hasattr(item, '__iter__'):
        return item
    return [item]

def to_host(host, default_protocol = 'telnet', default_domain = ''):
    """
    Given a string or a Host object, this function returns a Host object.

    @type  host: string|Host
    @param host: A hostname (may be URL formatted) or a Host object.
    @type  default_protocol: str
    @param default_protocol: Passed to the Host constructor.
    @type  default_domain: str
    @param default_domain: Appended to each hostname that has no domain.
    @rtype:  Host
    @return: The Host object.
    """
    if host is None:
        raise TypeError('None can not be cast to Host')
    if hasattr(host, 'get_address'):
        return host
    if default_domain and not '.' in host:
        host += '.' + default_domain
    return Exscript.Host(host, default_protocol = default_protocol)

def to_hosts(hosts, default_protocol = 'telnet', default_domain = ''):
    """
    Given a string or a Host object, or a list of strings or Host objects,
    this function returns a list of Host objects.

    @type  hosts: string|Host|list(string)|list(Host)
    @param hosts: One or more hosts or hostnames.
    @type  default_protocol: str
    @param default_protocol: Passed to the Host constructor.
    @type  default_domain: str
    @param default_domain: Appended to each hostname that has no domain.
    @rtype:  list[Host]
    @return: A list of Host objects.
    """
    return [to_host(h, default_protocol, default_domain)
            for h in to_list(hosts)]

def to_regex(regex, flags = 0):
    """
    Given a string, this function returns a new re.RegexObject.
    Given a re.RegexObject, this function just returns the same object.

    @type  regex: string|re.RegexObject
    @param regex: A regex or a re.RegexObject
    @type  flags: int
    @param flags: See Python's re.compile().
    @rtype:  re.RegexObject
    @return: The Python regex object.
    """
    if regex is None:
        raise TypeError('None can not be cast to re.RegexObject')
    if hasattr(regex, 'match'):
        return regex
    return re.compile(regex, flags)

def to_regexs(regexs):
    """
    Given a string or a re.RegexObject, or a list of strings or
    re.RegexObjects, this function returns a list of re.RegexObjects.

    @type  regexs: str|re.RegexObject|list(str|re.RegexObject)
    @param regexs: One or more regexs or re.RegexObjects.
    @rtype:  list(re.RegexObject)
    @return: A list of re.RegexObjects.
    """
    return [to_regex(r) for r in to_list(regexs)]
