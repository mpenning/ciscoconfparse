from __future__  import absolute_import
import traceback
import sys
import re
import os

from ciscoconfparse.errors import DynamicAddressException

from ciscoconfparse.ccp_util import _IPV6_REGEX_STR_COMPRESSED1, _IPV6_REGEX_STR_COMPRESSED2
from ciscoconfparse.ccp_util import _IPV6_REGEX_STR_COMPRESSED3
from ciscoconfparse.ccp_util import CiscoRange, IPv4Obj, IPv6Obj
from ciscoconfparse.ccp_abc import BaseCfgLine

### HUGE UGLY WARNING:
###   Anything in models_cisco.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and 
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality. 
###
###   Use models_cisco.py at your own risk.  You have been warned :-)
""" models_cisco.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2014-2019 David Michael Pennington

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

MAX_VLAN = 4094

##
##-------------  IOS Configuration line object
##


class IOSCfgLine(BaseCfgLine):
    """An object for a parsed IOS-style configuration line.  
    :class:`~models_cisco.IOSCfgLine` objects contain references to other 
    parent and child :class:`~models_cisco.IOSCfgLine` objects.

    .. note::

       Originally, :class:`~models_cisco.IOSCfgLine` objects were only 
       intended for advanced ciscoconfparse users.  As of ciscoconfparse 
       version 0.9.10, *all users* are strongly encouraged to prefer the 
       methods directly on :class:`~models_cisco.IOSCfgLine` objects.  
       Ultimately, if you write scripts which call methods on 
       :class:`~models_cisco.IOSCfgLine` objects, your scripts will be much 
       more efficient than if you stick strictly to the classic 
       :class:`~ciscoconfparse.CiscoConfParse` methods.

    Args:
        - text (str): A string containing a text copy of the IOS configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration. 
        - comment_delimiter (str): A string which is considered a comment for the configuration format.  Since this is for Cisco IOS-style configurations, it defaults to ``!``.

    Attributes:
        - text     (str): A string containing the parsed IOS configuration statement
        - linenum  (int): The line number of this configuration statement in the original config; default is -1 when first initialized.
        - parent (:class:`~models_cisco.IOSCfgLine()`): The parent of this object; defaults to ``self``.
        - children (list): A list of ``IOSCfgLine()`` objects which are children of this object.
        - child_indent (int): An integer with the indentation of this object's children
        - indent (int): An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
        - is_comment (bool): A boolean indicating whether this is a comment

    Returns:
        - An instance of :class:`~models_cisco.IOSCfgLine`.

    """

    def __init__(self, *args, **kwargs):
        """Accept an IOS line number and initialize family relationship
        attributes"""
        super(IOSCfgLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        ## Default object, for now
        return True

    @property
    def is_intf(self):
        # Includes subinterfaces
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_cisco.IOSCfgLine` is an interface; subinterfaces
        also return True.

        Returns:
            - bool.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sSerial')[0]
           >>> obj.is_intf
           True
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_intf
           True
           >>>
        """
        #intf_regex = r'^interface\s+(\S+.+)'
        #if self.re_match(intf_regex):
        if self.text[0:10] == 'interface ' and self.text[10] != ' ':
            return True
        return False

    @property
    def is_subintf(self):
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_cisco.IOSCfgLine` is a subinterface.

        Returns:
            - bool.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r'^interface\sSerial')[0]
           >>> obj.is_subintf
           False
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.is_subintf
           True
           >>>
        """
        intf_regex = r'^interface\s+(\S+?\.\d+)'
        if self.re_match(intf_regex):
            return True
        return False

    _VIRTUAL_INTF_REGEX_STR = r"""^interface\s+(Loopback|Vlan|Tunnel|Dialer|Virtual-Template|Port-Channel)"""
    _VIRTUAL_INTF_REGEX = re.compile(_VIRTUAL_INTF_REGEX_STR, re.I)

    @property
    def is_virtual_intf(self):
        if self.re_match(self._VIRTUAL_INTF_REGEX):
            return True
        return False

    @property
    def is_loopback_intf(self):
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_cisco.IOSCfgLine` is a loopback interface.

        Returns:
            - bool.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 11,14

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface Loopback0',
           ...     ' ip address 1.1.1.5 255.255.255.255',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r'^interface\sFast')[0]
           >>> obj.is_loopback_intf
           False
           >>> obj = parse.find_objects(r'^interface\sLoop')[0]
           >>> obj.is_loopback_intf
           True
           >>>
        """
        intf_regex = r'^interface\s+(\Soopback)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_ethernet_intf(self):
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_cisco.IOSCfgLine` is an ethernet interface.
        Any ethernet interface (10M through 10G) is considered an ethernet
        interface.

        Returns:
            - bool.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.is_ethernet_intf
           True
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_ethernet_intf
           False
           >>>
        """
        intf_regex = r'^interface\s+(.*?\Sthernet)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def in_portchannel(self):
        """Return a boolean indicating whether this port is configured in a port-channel

        """
        retval = self.re_match_iter_typed(
            r'^\s*channel-group\s+(\d+)', result_type=bool, default=False)
        return retval

    @property
    def portchannel_number(self):
        """Return an integer for the port-channel which it's configured in.  Return -1 if it's not configured in a port-channel

        """
        retval = self.re_match_iter_typed(
            r'^\s*channel-group\s+(\d+)', result_type=int, default=-1)
        return retval

    @property
    def is_portchannel(self):
        """Return a boolean indicating whether this port is a port-channel intf

        """
        return ('channel' in self.name.lower())


##
##-------------  IOS Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def


class BaseIOSIntfLine(IOSCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseIOSIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj('127.0.0.1/32', strict=False)

    def __repr__(self):
        if not self.is_switchport:
            try:
                ipv4_addr_object = self.ipv4_addr_object
            except DynamicAddressException:
                ipv4_addr_object = None

            if ipv4_addr_object is None:
                addr = "IPv4 dhcp"
            elif ipv4_addr_object == self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                ip = str(self.ipv4_addr_object.ip)
                prefixlen = str(self.ipv4_addr_object.prefixlen)
                addr = "{0}/{1}".format(ip, prefixlen)
            return "<%s # %s '%s' info: '%s'>" % (self.classname, self.linenum,
                                                  self.name, addr)
        else:
            return "<%s # %s '%s' info: 'switchport'>" % (
                self.classname, self.linenum, self.name)

    def _build_abbvs(self):
        """Build a set of valid abbreviations (lowercased) for the interface"""
        retval = set([])
        port_type_chars = self.port_type.lower()
        subinterface_number = self.subinterface_number
        for sep in ['', ' ']:
            for ii in range(1, len(port_type_chars) + 1):
                retval.add('{0}{1}{2}'.format(port_type_chars[0:ii], sep,
                                              subinterface_number))
        return retval

    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        return "default " + self.text

    @property
    def verbose(self):
        if not self.is_switchport:
            return "<%s # %s '%s' info: '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>" % (
                self.classname, self.linenum, self.text, self.ipv4_addr_object
                or "No IPv4", self.child_indent, len(self.children),
                self.family_endpoint)
        else:
            return "<%s # %s '%s' info: 'switchport' (child_indent: %s / len(children): %s / family_endpoint: %s)>" % (
                self.classname, self.linenum, self.text, self.child_indent,
                len(self.children), self.family_endpoint)

    @classmethod
    def is_object_for(cls, line="", re=re):
        return False

    ##-------------  Basic interface properties

    @property
    def abbvs(self):
        """A python set of valid abbreviations (lowercased) for the interface"""
        return self._build_abbvs()

    _INTF_NAME_RE_STR = r'^interface\s+(\S+[0-9\/\.\s]+)\s*'
    _INTF_NAME_REGEX = re.compile(_INTF_NAME_RE_STR)

    @property
    def name(self):
        """Return the interface name as a string, such as 'GigabitEthernet0/1'

        Returns:
            - str.  The interface name as a string, or '' if the object is not an interface.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20,23

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.name
           'FastEthernet1/0'
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.name
           'ATM2/0'
           >>> obj = parse.find_objects('^interface\sATM')[1]
           >>> obj.name
           'ATM2/0.100'
           >>>
        """
        if not self.is_intf:
            return ''
        name = self.re_match(self._INTF_NAME_REGEX).strip()
        return name

    @property
    def port(self):
        """Return the interface's port number

        Returns:
            - int.  The interface number.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.port
           0
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.port
           0
           >>>
        """
        return self.ordinal_list[-1]

    @property
    def port_type(self):
        """Return Loopback, ATM, GigabitEthernet, Virtual-Template, etc...

        Returns:
            - str.  The port type.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.port_type
           'FastEthernet'
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.port_type
           'ATM'
           >>>
        """
        port_type_regex = r'^interface\s+([A-Za-z\-]+)'
        return self.re_match(port_type_regex, group=1, default='')

    @property
    def ordinal_list(self):
        """Return a tuple of numbers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python tuple of integers: (2, 25).  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: (2, 0, 25).  This method strips all subinterface information in the returned value.

        Returns:
            - tuple.  A tuple of port numbers as integers.

        .. warning::

           ordinal_list should silently fail (returning an empty python list) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.ordinal_list
           (1, 0)
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.ordinal_list
           (2, 0)
           >>>
        """
        if not self.is_intf:
            return ()
        else:
            intf_number = self.interface_number
            if intf_number:
                return tuple([int(ii) for ii in intf_number.split('/')])
            else:
                return ()

    @property
    def interface_number(self):
        """Return a string representing the card, slot, port for this interface.  If you call interface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25'.  If you call interface_number on GigabitEthernet2/0/25.100 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.

        Returns:
            - string.

        .. warning::

           interface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.interface_number
           '1/0'
           >>> obj = parse.find_objects('^interface\sATM')[-1]
           >>> obj.interface_number
           '2/0'
           >>>
        """
        if not self.is_intf:
            return ""
        else:
            intf_regex = r'^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$'
            intf_number = self.re_match(intf_regex, group=1, default='')
            return intf_number

    @property
    def subinterface_number(self):
        """Return a string representing the card, slot, port for this interface or subinterface.  If you call subinterface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25.100'.  If you call interface_number on GigabitEthernet2/0/25 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.

        Returns:
            - string.

        .. warning::

           subinterface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.subinterface_number
           '1/0'
           >>> obj = parse.find_objects('^interface\sATM')[-1]
           >>> obj.subinterface_number
           '2/0.100'
           >>>
        """
        if not self.is_intf:
            return ""
        else:
            subintf_regex = r'^interface\s+[A-Za-z\-]+\s*(\d+.*?\.?\d?)(\s\S+)*\s*$'
            subintf_number = self.re_match(subintf_regex, group=1, default='')
            return subintf_number

    @property
    def description(self):
        """Return the current interface description string.

        """
        retval = self.re_match_iter_typed(
            r'^\s*description\s+(\S.+)$', result_type=str, default='')
        return retval

    @property
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(
            r'^\s*bandwidth\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r'^\s*delay\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_holdqueue_out(self):
        """Return the current hold-queue out depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r'^\s*hold-queue\s+(\d+)\s+out$', result_type=int, default=0)
        return retval

    @property
    def manual_holdqueue_in(self):
        """Return the current hold-queue in depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r'^\s*hold-queue\s+(\d+)\s+in$', result_type=int, default=0)
        return retval

    @property
    def manual_encapsulation(self):
        retval = self.re_match_iter_typed(
            r'^\s*encapsulation\s+(\S+)', result_type=str, default='')
        return retval

    @property
    def has_mpls(self):
        retval = self.re_match_iter_typed(
            r'^\s*(mpls\s+ip)$', result_type=bool, default=False)
        return retval

    @property
    def ipv4_addr_object(self):
        """Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj('127.0.0.1/32')"""
        try:
            return IPv4Obj('%s/%s' % (self.ipv4_addr, self.ipv4_netmask))
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except:
            return self.default_ipv4_addr_object

    @property
    def ipv4_network_object(self):
        """Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('127.0.0.1/32')"""
        return self.ip_network_object

    @property
    def ip_network_object(self):
        # Simplified on 2014-12-02
        try:
            return IPv4Obj(
                '{0}/{1}'.format(self.ipv4_addr, self.ipv4_netmask),
                strict=False)
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except (Exception) as e:
            return self.default_ipv4_addr_object

    @property
    def has_autonegotiation(self):
        if not self.is_ethernet_intf:
            return False
        elif self.is_ethernet_intf and (self.has_manual_speed or
                                        self.has_manual_duplex):
            return False
        elif self.is_ethernet_intf:
            return True
        else:
            raise ValueError

    @property
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r'^\s*speed\s+(\d+)$', result_type=bool, default=False)
        return retval

    @property
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r'^\s*duplex\s+(\S.+)$', result_type=bool, default=False)
        return retval

    @property
    def has_manual_carrierdelay(self):
        """Return a python boolean for whether carrier delay is manually configured on the interface"""
        return bool(self.manual_carrierdelay)

    @property
    def manual_carrierdelay(self):
        """Return the manual carrier delay (in seconds) of the interface as a python float. If there is no explicit carrier delay, return 0.0"""
        cd_seconds = self.re_match_iter_typed(
            r'^\s*carrier-delay\s+(\d+)$', result_type=float, default=0.0)
        cd_msec = self.re_match_iter_typed(
            r'^\s*carrier-delay\s+msec\s+(\d+)$',
            result_type=float,
            default=0.0)

        if (cd_seconds > 0.0):
            return cd_seconds
        elif (cd_msec > 0.0):
            return cd_msec / 1000.0
        else:
            return 0.0


    @property
    def has_manual_clock_rate(self):
        return bool(self.manual_clock_rate)

    @property
    def manual_clock_rate(self):
        """Return the clock rate of the interface as a python integer. If there is no explicit clock rate, return 0"""
        retval = self.re_match_iter_typed(
            r'^\s*clock\s+rate\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        """Returns a integer value for the manual MTU configured on an
        :class:`~models_cisco.IOSIntfLine` object.  Interfaces without a
        manual MTU configuration return 0.

        Returns:
            - integer.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' mtu 4470',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.manual_mtu
           0
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.manual_mtu
           4470
           >>>
        """
        retval = self.re_match_iter_typed(
            r'^\s*mtu\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_mpls_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r'^\s*mpls\s+mtu\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_ip_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r'^\s*ip\s+mtu\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_speed(self):
        retval = self.re_match_iter_typed(
            r'^\s*speed\s+(\d+)$', result_type=int, default=0)
        return retval

    @property
    def manual_duplex(self):
        retval = self.re_match_iter_typed(
            r'^\s*duplex\s+(\S.+)$', result_type=str, default='')
        return retval

    @property
    def has_manual_mtu(self):
        return bool(self.manual_mtu)

    @property
    def has_manual_mpls_mtu(self):
        return bool(self.manual_mpls_mtu)

    @property
    def has_manual_ip_mtu(self):
        return bool(self.manual_ip_mtu)

    @property
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r'^\s*(shut\S*)\s*$', result_type=bool, default=False)
        return retval

    @property
    def has_vrf(self):
        return bool(self.vrf)

    @property
    def vrf(self):
        retval = self.re_match_iter_typed(
            r'^\s*(ip\s+)*vrf\sforwarding\s(\S+)$', result_type=str, 
            group=2, default='')
        return retval

    @property
    def ip_addr(self):
        return self.ipv4_addr

    @property
    def ipv4_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r'^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+\s*$',
            result_type=str,
            default='')
        condition1 = self.re_match_iter_typed(
            r'^\s+ip\s+address\s+(dhcp)\s*$',
            result_type=str,
            default='')
        if condition1.lower()=='dhcp':
            error = "Cannot parse address from a dhcp interface: {0}".format(
                self.name)
            raise DynamicAddressException(error)
        else:
            return retval

    @property
    def ipv4_netmask(self):
        """Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r'^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)\s*$',
            result_type=str,
            default='')
        return retval

    @property
    def ipv4_masklength(self):
        """Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    def is_abbreviated_as(self, val):
        """Test whether `val` is a good abbreviation for the interface"""
        if val.lower() in self.abbvs:
            return True
        return False

    def in_ipv4_subnet(self, ipv4network=IPv4Obj('0.0.0.0/32', strict=False)):
        """Accept an argument for the :class:`~ccp_util.IPv4Obj` to be 
        considered, and return a boolean for whether this interface is within 
        the requested :class:`~ccp_util.IPv4Obj`.

        Kwargs:
           - ipv4network (:class:`~ccp_util.IPv4Obj`): An object to compare against IP addresses configured on this :class:`~models_cisco.IOSIntfLine` object.

        Returns:
            - bool if there is an ip address, or None if there is no ip address.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 21,23

           >>> from ciscoconfparse.ccp_util import IPv4Obj
           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface Serial1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     '!',
           ...     'interface ATM2/0',
           ...     ' no ip address',
           ...     '!',
           ...     'interface ATM2/0.100 point-to-point',
           ...     ' ip address 1.1.1.5 255.255.255.252',
           ...     ' pvc 0/100',
           ...     '  vbr-nrt 704 704',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sSerial')[0]
           >>> obj
           <IOSIntfLine # 1 'Serial1/0' info: '1.1.1.1/30'>
           >>> obj.in_ipv4_subnet(IPv4Obj('1.1.1.0/24', strict=False))
           True
           >>> obj.in_ipv4_subnet(IPv4Obj('2.1.1.0/24', strict=False))
           False
           >>>
        """
        if not (str(self.ipv4_addr_object.ip) == "127.0.0.1"):
            try:
                # Return a boolean for whether the interface is in that 
                #    network and mask
                return self.ipv4_network_object in ipv4network
            except (Exception) as e:
                raise ValueError(
                    "FATAL: %s.in_ipv4_subnet(ipv4network={0}) is an invalid arg: {1}".
                    format(ipv4network, e))
        else:
            return None

    def in_ipv4_subnets(self, subnets=None):
        """Accept a set or list of ccp_util.IPv4Obj objects, and return a boolean for whether this interface is within the requested subnets."""
        if (subnets is None):
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if (self.ipv4_addr_object in subnet):
                return tmp
        return tmp

    @property
    def has_no_icmp_unreachables(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr == ''):
            return False

        retval = self.re_match_iter_typed(
            r'^\s*no\sip\s(unreachables)\s*$', result_type=bool, default=False)
        return retval

    @property
    def has_no_icmp_redirects(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr == ''):
            return False

        retval = self.re_match_iter_typed(
            r'^\s*no\sip\s(redirects)\s*$', result_type=bool, default=False)
        return retval

    @property
    def has_no_ip_proxyarp(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        """Return a boolean for whether no ip proxy-arp is configured on the 
        interface.

        Returns:
            - bool.

        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 12

           >>> from ciscoconfparse.ccp_util import IPv4Obj
           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/0',
           ...     ' ip address 1.1.1.1 255.255.255.252',
           ...     ' no ip proxy-arp',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config, factory=True)
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.has_no_ip_proxyarp
           True
           >>>
        """

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr == ''):
            return False

        ## By default, Cisco IOS answers proxy-arp
        ## By default, Nexus disables proxy-arp
        ## By default, IOS-XR disables proxy-arp
        retval = self.re_match_iter_typed(
            r'^\s*no\sip\s(proxy-arp)\s*$', result_type=bool, default=False)
        return retval

    @property
    def has_ip_pim_dense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr == ''):
            return False

        retval = self.re_match_iter_typed(
            r'^\s*ip\spim\sdense-mode\s*$)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr == ''):
            return False

        retval = self.re_match_iter_typed(
            r'^\s*ip\spim\ssparse-mode\s*$)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def has_ip_pim_sparsedense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr == ''):
            return False

        retval = self.re_match_iter_typed(
            r'^\s*ip\spim\ssparse-dense-mode\s*$)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def manual_arp_timeout(self):
        """Return an integer with the current interface ARP timeout, if there isn't one set, return 0.  If there is no IP address, return -1"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr == ''):
            return -1

        ## By default, Cisco IOS defaults to 4 hour arp timers
        ## By default, Nexus defaults to 15 minute arp timers
        retval = self.re_match_iter_typed(
            r'^\s*arp\s+timeout\s+(\d+)\s*$', result_type=int, default=0)
        return retval

    @property
    def has_ip_helper_addresses(self):
        """Return a True if the intf has helper-addresses; False if not"""
        if len(self.ip_helper_addresses)>0:
            return True
        return False

    @property
    def ip_helper_addresses(self):
        """Return a list of IP helper-addresses"""
        retval = list()
        for child in self.children:
            if 'helper-address' in child.text:
                addr = child.re_match_typed('ip\s+helper-address\s+(\S+)')
                retval.append(addr)
        return retval

    @property
    def is_switchport(self):
        retval = self.re_match_iter_typed(
            r'^\s*(switchport)\s*', result_type=bool, default=False)
        return retval

    @property
    def has_manual_switch_access(self):
        retval = self.re_match_iter_typed(
            r'^\s*(switchport\smode\s+access)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    @property
    def manual_switch_trunk_encap(self):
        retval = self.re_match_iter_typed(
            r'^\s*(switchport\s+trunk\s+encap\s+(\S+))\s*$',
            result_type=str,
            default='')
        return retval

    @property
    def has_manual_switch_trunk(self):
        retval = self.re_match_iter_typed(
            r'^\s*(switchport\s+mode\s+trunk)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def has_switch_portsecurity(self):
        if not self.is_switchport:
            return False
        ## IMPORTANT: Cisco IOS will not enable port-security on the port
        ##    unless 'switch port-security' (with no other options)
        ##    is in the configuration
        retval = self.re_match_iter_typed(
            r'^\s*(switchport\sport-security)\s*$',
            result_type=bool,
            default=False)
        return retval

    @property
    def has_switch_stormcontrol(self):
        if not self.is_switchport:
            return False
        retval = self.re_match_iter_typed(
            r'^\s*(storm-control)\s*$', result_type=bool, default=False)
        return retval

    @property
    def has_dtp(self):
        if not self.is_switchport:
            return False

        ## Not using self.re_match_iter_typed, because I want to
        ##   be sure I build the correct API for regex_match is False, and
        ##   default value is True
        for obj in self.children:
            switch = obj.re_match(r'^\s*(switchport\snoneg\S*)\s*$')
            if not (switch is None):
                return False
        return True

    @property
    def access_vlan(self):
        """Return an integer with the access vlan number.  Return 1, if the switchport has no explicit vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0
        retval = self.re_match_iter_typed(
            r'^\s*switchport\s+access\s+vlan\s+(\d+)$',
            result_type=int,
            default=default_val)
        return retval

    @property
    def trunk_vlans_allowed(self):
        """Return a CiscoRange() with the list of allowed vlan numbers (as int).  Return 0 if the port isn't a switchport in trunk mode"""

        # The default values...
        if self.is_switchport and not self.has_manual_switch_access:
            retval = CiscoRange('1-{0}'.format(MAX_VLAN), result_type=int)
        else:
            return 0

        ## Iterate over switchport trunk statements
        for obj in self.children:

            ## For every child object, check whether the vlan list is modified
            abs_str = obj.re_match_typed(
                '^\s+switchport\s+trunk\s+allowed\s+vlan\s(all|none|\d.*?)$',
                default='_nomatch_', result_type=str).lower()
            add_str = obj.re_match_typed(
                '^\s+switchport\s+trunk\s+allowed\s+vlan\s+add\s+(\d.*?)$',
                default='_nomatch_', result_type=str).lower()
            exc_str = obj.re_match_typed(
                '^\s+switchport\s+trunk\s+allowed\s+vlan\s+except\s+(\d.*?)$',
                default='_nomatch_', result_type=str).lower()
            rem_str = obj.re_match_typed(
                '^\s+switchport\s+trunk\s+allowed\s+vlan\s+remove\s+(\d.*?)$',
                default='_nomatch_', result_type=str).lower()

            ## Build a vdict for each vlan modification statement
            vdict = {
                'absolute_str': abs_str,
                'add_str': add_str,
                'except_str': exc_str,
                'remove_str': rem_str,
            }

            ## Analyze each vdict in sequence and apply to retval sequentially
            for key, val in vdict.items():
                if val!='_nomatch_':
                    ## absolute in the key overrides previous values
                    if 'absolute' in key:
                        if val.lower()=='all':
                            retval = CiscoRange('1-{0}'.format(MAX_VLAN), 
                                result_type=int)
                        elif val.lower()=='none':
                            retval = CiscoRange(result_type=int)
                        else:
                            retval = CiscoRange(val, result_type=int)
                    elif 'add' in key:
                        retval.append(val)
                    elif 'except' in key:
                        retval = CiscoRange('1-{0}'.format(MAX_VLAN), 
                            result_type=int)
                        retval.remove(val)
                    elif 'remove' in key:
                        retval.remove(val)

        return retval


    @property
    def native_vlan(self):
        """Return an integer with the native vlan number.  Return 1, if the switchport has no explicit native vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0
        retval = self.re_match_iter_typed(
            r'^\s*switchport\s+trunk\s+native\s+vlan\s+(\d+)$',
            result_type=int,
            default=default_val)
        return retval

    ##-------------  CDP

    @property
    def has_manual_disable_cdp(self):
        retval = self.re_match_iter_typed(
            r'^\s*(no\s+cdp\s+enable\s*)', result_type=bool, default=False)
        return retval

    ##-------------  EoMPLS

    @property
    def has_xconnect(self):
        return bool(self.xconnect_vc)

    @property
    def xconnect_vc(self):
        retval = self.re_match_iter_typed(
            r'^\s*xconnect\s+\S+\s+(\d+)\s+\S+', result_type=int, default=0)
        return retval

    ##-------------  HSRP

    @property
    def has_ip_hsrp(self):
        return bool(self.hsrp_ip_addr)

    @property
    def hsrp_ip_addr(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        if (self.ipv4_addr == ''):
            return ''

        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*ip\s+(\S+)',
            group=2,
            result_type=str,
            default='')
        return retval

    @property
    def hsrp_ip_mask(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        if (self.ipv4_addr == ''):
            return ''
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*ip\s+\S+\s+(\S+)\s*$',
            group=2,
            result_type=str,
            default='')
        return retval

    @property
    def hsrp_group(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+)\s+ip\s+\S+', result_type=int, default=-1)
        return retval

    @property
    def hsrp_priority(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        if not self.has_ip_hsrp:
            return 0  # Return this if there is no hsrp on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*priority\s+(\d+)',
            group=2,
            result_type=int,
            default=100)
        return retval

    @property
    def hsrp_hello_timer(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface

        # FIXME: handle msec timers...
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*timers\s+(\d+)\s+\d+',
            group=2,
            result_type=float,
            default=0.0)
        return retval

    @property
    def hsrp_hold_timer(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface

        # FIXME: this should be a float (in case of msec timers)
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*timers\s+\d+\s+(\d+)',
            group=2,
            result_type=float,
            default=0.0)
        return retval

    @property
    def has_hsrp_track(self):
        return bool(self.hsrp_track)

    @property
    def hsrp_track(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*track\s(\S+.+?)\s+\d+\s*',
            group=2,
            result_type=str,
            default='')
        return retval

    @property
    def has_hsrp_usebia(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*(use-bia)',
            group=2,
            result_type=bool,
            default=False)
        return retval

    @property
    def has_hsrp_preempt(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*(use-bia)',
            group=2,
            result_type=bool,
            default=False)
        return retval

    @property
    def hsrp_authentication_md5_keychain(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r'^\s*standby\s+(\d+\s+)*authentication\s+md5\s+key-chain\s+(\S+)',
            group=2,
            result_type=str,
            default='')
        return retval

    @property
    def has_hsrp_authentication_md5(self):
        keychain = self.hsrp_authentication_md5_keychain
        return bool(keychain)

    @property
    def hsrp_authentication_cleartext(self):
        pass

    ##-------------  MAC ACLs

    @property
    def has_mac_accessgroup_in(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_in)

    @property
    def has_mac_accessgroup_out(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_out)

    @property
    def mac_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r'^\s*mac\saccess-group\s+(\S+)\s+in\s*$',
            result_type=str,
            default='')
        return retval

    @property
    def mac_accessgroup_out(self):
        retval = self.re_match_iter_typed(
            r'^\s*mac\saccess-group\s+(\S+)\s+out\s*$',
            result_type=str,
            default='')
        return retval

    ##-------------  IPv4 ACLs

    @property
    def has_ip_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    @property
    def has_ip_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    @property
    def has_ipv4_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    @property
    def has_ipv4_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    @property
    def ip_accessgroup_in(self):
        return self.ipv4_accessgroup_in

    @property
    def ip_accessgroup_out(self):
        return self.ipv4_accessgroup_out

    @property
    def ipv4_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r'^\s*ip\saccess-group\s+(\S+)\s+in\s*$',
            result_type=str,
            default='')
        return retval

    @property
    def ipv4_accessgroup_out(self):
        retval = self.re_match_iter_typed(
            r'^\s*ip\saccess-group\s+(\S+)\s+out\s*$',
            result_type=str,
            default='')
        return retval


##
##-------------  IOS Interface Object
##


class IOSIntfLine(BaseIOSIntfLine):
    def __init__(self, *args, **kwargs):
        """Accept an IOS line number and initialize family relationship
        attributes

        .. warning::

          All :class:`~models_cisco.IOSIntfLine` methods are still considered beta-quality, until this notice is removed.  The behavior of APIs on this object could change at any time.
        """
        super(IOSIntfLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        intf_regex = r'^interface\s+(\S+.+)'
        if re.search(intf_regex, line):
            return True
        return False


##
##-------------  IOS Interface Globals
##


class IOSIntfGlobal(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSIntfGlobal, self).__init__(*args, **kwargs)
        self.feature = 'interface global'

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(
                '^(no\s+cdp\s+run)|(logging\s+event\s+link-status\s+global)|(spanning-tree\sportfast\sdefault)|(spanning-tree\sportfast\sbpduguard\sdefault)',
                line):
            return True
        return False

    @property
    def has_cdp_disabled(self):
        if self.re_search('^no\s+cdp\s+run\s*'):
            return True
        return False

    @property
    def has_intf_logging_def(self):
        if self.re_search('^logging\s+event\s+link-status\s+global'):
            return True
        return False

    @property
    def has_stp_portfast_def(self):
        if self.re_search('^spanning-tree\sportfast\sdefault'):
            return True
        return False

    @property
    def has_stp_portfast_bpduguard_def(self):
        if self.re_search('^spanning-tree\sportfast\sbpduguard\sdefault'):
            return True
        return False

    @property
    def has_stp_mode_rapidpvst(self):
        if self.re_search('^spanning-tree\smode\srapid-pvst'):
            return True
        return False


##
##-------------  IOS Hostname Line
##


class IOSHostnameLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSHostnameLine, self).__init__(*args, **kwargs)
        self.feature = 'hostname'

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.hostname)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^hostname', line):
            return True
        return False

    @property
    def hostname(self):
        retval = self.re_match_typed(
            r'^hostname\s+(\S+)', result_type=str, default='')
        return retval


##
##-------------  IOS Access Line
##


class IOSAccessLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAccessLine, self).__init__(*args, **kwargs)
        self.feature = 'access line'

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (self.classname, self.linenum,
                                              self.name, self.range_str)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^line', line):
            return True
        return False

    @property
    def is_accessline(self):
        retval = self.re_match_typed(
            r'^(line\s+\S+)', result_type=str, default='')
        return bool(retval)

    @property
    def name(self):
        retval = self.re_match_typed(
            r'^line\s+(\S+)', result_type=str, default='')
        # special case for IOS async lines: i.e. "line 33 48"
        if re.search('\d+', retval):
            return ''
        return retval

    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        return "default " + self.text

    @property
    def range_str(self):
        return ' '.join(map(str, self.line_range))

    @property
    def line_range(self):
        ## Return the access-line's numerical range as a list
        ## line con 0 => [0]
        ## line 33 48 => [33, 48]
        retval = self.re_match_typed(
            r'([a-zA-Z]+\s+)*(\d+\s*\d*)$',
            group=2,
            result_type=str,
            default='')
        tmp = map(int, retval.strip().split())
        return tmp

    def manual_exectimeout_min(self):
        tmp = self.parse_exectimeout
        return tmp[0]

    def manual_exectimeout_sec(self):
        tmp = self.parse_exectimeout
        if len(tmp > 0):
            return 0
        return tmp[1]

    @property
    def parse_exectimeout(self):
        retval = self.re_match_iter_typed(
            r'^\s*exec-timeout\s+(\d+\s*\d*)\s*$',
            group=1,
            result_type=str,
            default='')
        tmp = map(int, retval.strip().split())
        return tmp


##
##-------------  Base IOS Route line object
##


class BaseIOSRouteLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseIOSRouteLine, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
            self.classname, self.linenum, self.network_object, self.routeinfo)

    @property
    def routeinfo(self):
        ### Route information for the repr string
        if self.tracking_object_name:
            return self.nexthop_str + " AD: " + str(
                self.admin_distance) + " Track: " + self.tracking_object_name
        else:
            return self.nexthop_str + " AD: " + str(self.admin_distance)

    @classmethod
    def is_object_for(cls, line="", re=re):
        return False

    @property
    def vrf(self):
        raise NotImplementedError

    @property
    def address_family(self):
        ## ipv4, ipv6, etc
        raise NotImplementedError

    @property
    def network(self):
        raise NotImplementedError

    @property
    def netmask(self):
        raise NotImplementedError

    @property
    def admin_distance(self):
        raise NotImplementedError

    @property
    def nexthop_str(self):
        raise NotImplementedError

    @property
    def tracking_object_name(self):
        raise NotImplementedError


##
##-------------  IOS Route line object
##

_RE_IP_ROUTE = re.compile(r"""^ip\s+route
(?:\s+(?:vrf\s+(?P<vrf>\S+)))?          # VRF detection
\s+
(?P<prefix>\d+\.\d+\.\d+\.\d+)          # Prefix detection
\s+
(?P<netmask>\d+\.\d+\.\d+\.\d+)         # Netmask detection
(?:\s+(?P<nh_intf>[^\d]\S+))?           # NH intf
(?:\s+(?P<nh_addr>\d+\.\d+\.\d+\.\d+))? # NH addr
(?:\s+(?P<dhcp>dhcp))?           # DHCP keyword       (FIXME: add unit test)
(?:\s+(?P<global>global))?       # Global keyword
(?:\s+(?P<ad>\d+))?              # Administrative distance
(?:\s+(?P<mcast>multicast))?     # Multicast Keyword  (FIXME: add unit test)
(?:\s+name\s+(?P<name>\S+))?     # Route name
(?:\s+(?P<permanent>permanent))? # Permanent Keyword  (exclusive of track)
(?:\s+track\s+(?P<track>\d+))?   # Track object (exclusive of permanent)
(?:\s+tag\s+(?P<tag>\d+))?       # Route tag
""", re.VERBOSE)

_RE_IPV6_ROUTE = re.compile(r"""^ipv6\s+route
(?:\s+vrf\s+(?P<vrf>\S+))?
(?:\s+(?P<prefix>{0})\/(?P<masklength>\d+))    # Prefix detection
(?:
  (?:\s+(?P<nh_addr1>{1}))
  |(?:\s+(?P<nh_intf>\S+(?:\s+\d\S*?\/\S+)?)(?:\s+(?P<nh_addr2>{2}))?)
)
(?:\s+nexthop-vrf\s+(?P<nexthop_vrf>\S+))?
(?:\s+(?P<ad>\d+))?              # Administrative distance
(?:\s+(?:(?P<ucast>unicast)|(?P<mcast>multicast)))?
(?:\s+tag\s+(?P<tag>\d+))?       # Route tag
""".format(_IPV6_REGEX_STR_COMPRESSED1, _IPV6_REGEX_STR_COMPRESSED2,
           _IPV6_REGEX_STR_COMPRESSED3), re.VERBOSE)


class IOSRouteLine(BaseIOSRouteLine):
    def __init__(self, *args, **kwargs):
        super(IOSRouteLine, self).__init__(*args, **kwargs)
        if 'ipv6' in self.text[0:4]:
            self.feature = 'ipv6 route'
            self._address_family = "ipv6"
            mm = _RE_IPV6_ROUTE.search(self.text)
            if not (mm is None):
                self.route_info = mm.groupdict()
            else:
                raise ValueError("Could not parse '{0}'".format(self.text))
        else:
            self.feature = 'ip route'
            self._address_family = "ip"
            mm = _RE_IP_ROUTE.search(self.text)
            if not (mm is None):
                self.route_info = mm.groupdict()
            else:
                raise ValueError("Could not parse '{0}'".format(self.text))

    @classmethod
    def is_object_for(cls, line="", re=re):
        if (line[0:8] == 'ip route') or (line[0:11] == 'ipv6 route '):
            return True
        return False

    @property
    def vrf(self):
        if not (self.route_info['vrf'] is None):
            return self.route_info['vrf']
        else:
            return ''

    @property
    def address_family(self):
        ## ipv4, ipv6, etc
        return self._address_family

    @property
    def network(self):
        if self._address_family == 'ip':
            return self.route_info['prefix']
        elif self._address_family == 'ipv6':
            retval = self.re_match_typed(
                r'^ipv6\s+route\s+(vrf\s+)*(\S+?)\/\d+',
                group=2,
                result_type=str,
                default='')
        return retval

    @property
    def netmask(self):
        if self._address_family == 'ip':
            return self.route_info['netmask']
        elif self._address_family == 'ipv6':
            return str(self.network_object.netmask)
        return retval

    @property
    def masklen(self):
        if self._address_family == 'ip':
            return self.network_object.prefixlen
        elif self._address_family == 'ipv6':
            masklen_str = self.route_info['masklength'] or '128'
            return int(masklen_str)

    @property
    def network_object(self):
        try:
            if self._address_family == 'ip':
                return IPv4Obj(
                    '%s/%s' % (self.network, self.netmask), strict=False)
            elif self._address_family == 'ipv6':
                return IPv6Obj('%s/%s' % (self.network, self.masklen))
        except:
            return None

    @property
    def nexthop_str(self):
        if self._address_family == 'ip':
            if self.next_hop_interface:
                return self.next_hop_interface + " " + self.next_hop_addr
            else:
                return self.next_hop_addr
        elif self._address_family == 'ipv6':
            retval = self.re_match_typed(
                r'^ipv6\s+route\s+(vrf\s+)*\S+\s+(\S+)',
                group=2,
                result_type=str,
                default='')
        return retval

    @property
    def next_hop_interface(self):
        if self._address_family == 'ip':
            if self.route_info['nh_intf']:
                return self.route_info['nh_intf']
            else:
                return ''
        elif self._address_family == 'ipv6':
            if self.route_info['nh_intf']:
                return self.route_info['nh_intf']
            else:
                return ''

    @property
    def next_hop_addr(self):
        if self._address_family == 'ip':
            return self.route_info['nh_addr'] or ''
        elif self._address_family == 'ipv6':
            return self.route_info['nh_addr1'] or self.route_info['nh_addr2'] \
                or ''

    @property
    def global_next_hop(self):
        if self._address_family == 'ip' and bool(self.vrf):
            return bool(self.route_info['global'])
        elif self._address_family == 'ip' and not bool(self.vrf):
            return True
        elif self._address_family == 'ipv6':
            ## ipv6 uses nexthop_vrf
            raise ValueError(
                "[FATAL] ipv6 doesn't support a global_next_hop for '{0}'".
                format(self.text))
        else:
            raise ValueError(
                "[FATAL] Could not identify global next-hop for '{0}'".format(
                    self.text))

    @property
    def nexthop_vrf(self):
        if self._address_family == 'ipv6':
            return self.route_info['nexthop_vrf'] or ''
        else:
            raise ValueError(
                "[FATAL] ip doesn't support a global_next_hop for '{0}'".
                format(self.text))

    @property
    def admin_distance(self):
        if self.route_info['ad']:
            return int(self.route_info['ad'])
        else:
            return 1

    @property
    def multicast(self):
        """Return whether the multicast keyword was specified"""
        return bool(self.route_info['mcast'])

    @property
    def unicast(self):
        ## FIXME It's unclear how to implement this...
        raise NotImplementedError

    @property
    def route_name(self):
        if self._address_family == 'ip':
            if self.route_info['name']:
                return self.route_info['name']
            else:
                return ''
        elif self._address_family == 'ipv6':
            raise NotImplementedError

    @property
    def permanent(self):
        if self._address_family == 'ip':
            if self.route_info['permanent']:
                return bool(self.route_info['permanent'])
            else:
                return False
        elif self._address_family == 'ipv6':
            raise NotImplementedError

    @property
    def tracking_object_name(self):
        if self._address_family == 'ip':
            if bool(self.route_info['track']):
                return self.route_info['track']
            else:
                return ''
        elif self._address_family == 'ipv6':
            raise NotImplementedError

    @property
    def tag(self):
        return self.route_info['tag'] or ''


################################
################################ Groups ###############################
################################


##
##-------------  IOS TACACS+ Group
##
class IOSAaaGroupServerLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaGroupServerLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa group server'

        REGEX = r'^aaa\sgroup\sserver\s(?P<protocol>\S+)\s(?P<group>\S+)\s*$'
        mm = re.search(REGEX, self.text)
        if not (mm is None):
            groups = mm.groupdict()
            self.protocol = groups.get('protocol', '')
            self.group = groups.get('group', '')
        else:
            raise ValueError

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\sgroup\sserver', line):
            return True
        return False

    @property
    def vrf(self):
        return self.re_match_iter_typed(
            r'^\s+(ip\s+)*vrf\s+forwarding\s+(\S+)',
            group=2,
            result_type=str,
            default='')

    @property
    def source_interface(self):
        return self.re_match_iter_typed(
            r'^\s+ip\s+tacacs\s+source-interface\s+(\S.+?\S)\s*$',
            group=1,
            result_type=str,
            default='')

    @property
    def server_private(self, re=re):
        retval = set([])
        rgx_priv = re.compile('^\s+server-private\s+(\S+)\s')
        for cobj in self.children:
            mm = rgx_priv.search(cobj.text)
            if not (mm is None):
                retval.add(mm.group(1))  # This is the server's ip
        return retval


##
##-------------  IOS AAA Lines
##


class IOSAaaLoginAuthenticationLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaLoginAuthenticationLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa authentication login'

        regex = r'^aaa\sauthentication\slogin\s(\S+)\sgroup\s(\S+)(.+?)$'
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default='')
        self.group = self.re_match_typed(
            regex, group=2, result_type=str, default='')
        methods_str = self.re_match_typed(
            regex, group=3, result_type=str, default='')
        self.methods = methods_str.strip().split('\s')

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\sauthentication\slogin', line):
            return True
        return False


class IOSAaaEnableAuthenticationLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaEnableAuthenticationLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa authentication enable'

        regex = r'^aaa\sauthentication\senable\s(\S+)\sgroup\s(\S+)(.+?)$'
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default='')
        self.group = self.re_match_typed(
            regex, group=2, result_type=str, default='')
        methods_str = self.re_match_typed(
            regex, group=3, result_type=str, default='')
        self.methods = methods_str.strip().split('\s')

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\sauthentication\senable', line):
            return True
        return False


class IOSAaaCommandsAuthorizationLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaCommandsAuthorizationLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa authorization commands'

        regex = r'^aaa\sauthorization\scommands\s(\d+)\s(\S+)\sgroup\s(\S+)(.+?)$'
        self.level = self.re_match_typed(
            regex, group=1, result_type=int, default=0)
        self.list_name = self.re_match_typed(
            regex, group=2, result_type=str, default='')
        self.group = self.re_match_typed(
            regex, group=3, result_type=str, default='')
        methods_str = self.re_match_typed(
            regex, group=4, result_type=str, default='')
        self.methods = methods_str.strip().split('\s')

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\sauthorization\scommands', line):
            return True
        return False


class IOSAaaCommandsAccountingLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaCommandsAccountingLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa accounting commands'

        regex = r'^aaa\saccounting\scommands\s(\d+)\s(\S+)\s(none|stop\-only|start\-stop)\sgroup\s(\S+)$'
        self.level = self.re_match_typed(
            regex, group=1, result_type=int, default=0)
        self.list_name = self.re_match_typed(
            regex, group=2, result_type=str, default='')
        self.record_type = self.re_match_typed(
            regex, group=3, result_type=str, default='')
        self.group = self.re_match_typed(
            regex, group=4, result_type=str, default='')

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\saccounting\scommands', line):
            return True
        return False


class IOSAaaExecAccountingLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAaaExecAccountingLine, self).__init__(*args, **kwargs)
        self.feature = 'aaa accounting exec'

        regex = r'^aaa\saccounting\sexec\s(\S+)\s(none|stop\-only|start\-stop)\sgroup\s(\S+)$'
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default='')
        self.record_type = self.re_match_typed(
            regex, group=2, result_type=str, default='')
        self.group = self.re_match_typed(
            regex, group=3, result_type=str, default='')

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search(r'^aaa\saccounting\sexec', line):
            return True
        return False
