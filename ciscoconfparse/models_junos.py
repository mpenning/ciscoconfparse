from __future__  import absolute_import
import sys
import re
import os

from ciscoconfparse.ccp_abc import BaseCfgLine
from ciscoconfparse.ccp_util import IPv4Obj

### HUGE UGLY WARNING:
###   Anything in models_junos.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and 
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality. 
###
###   Use models_junos.py at your own risk.  You have been warned :-)

""" models_junos.py - Parse, Query, Build, and Modify Junos-style configurations
     Copyright (C) 2015 David Michael Pennington

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

##
##-------------  Junos Configuration line object
##


class JunosCfgLine(BaseCfgLine):
    """An object for a parsed Junos-style configuration line.  
    :class:`~models_junos.JunosCfgLine` objects contain references to other 
    parent and child :class:`~models_junos.JunosCfgLine` objects.

    .. note::

       Originally, :class:`~models_junos.JunosCfgLine` objects were only 
       intended for advanced ciscoconfparse users.  As of ciscoconfparse 
       version 0.9.10, *all users* are strongly encouraged to prefer the 
       methods directly on :class:`~models_junos.JunosCfgLine` objects.  
       Ultimately, if you write scripts which call methods on 
       :class:`~models_junos.JunosCfgLine` objects, your scripts will be much 
       more efficient than if you stick strictly to the classic 
       :class:`~ciscoconfparse.CiscoConfParse` methods.

    Args:
        - text (str): A string containing a text copy of the Junos configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration. 
        - comment_delimiter (str): A string which is considered a comment for the configuration format.  Since this is for Cisco Junos-style configurations, it defaults to ``!``.

    Attributes:
        - text     (str): A string containing the parsed Junos configuration statement
        - linenum  (int): The line number of this configuration statement in the original config; default is -1 when first initialized.
        - parent (:class:`~models_junos.JunosCfgLine()`): The parent of this object; defaults to ``self``.
        - children (list): A list of ``JunosCfgLine()`` objects which are children of this object.
        - child_indent (int): An integer with the indentation of this object's children
        - indent (int): An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
        - is_comment (bool): A boolean indicating whether this is a comment

    Returns:
        - An instance of :class:`~models_junos.JunosCfgLine`.

    """
    def __init__(self, *args, **kwargs):
        """Accept an Junos line number and initialize family relationship
        attributes"""
        super(JunosCfgLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        ## Default object, for now
        return True

    @property
    def is_intf(self):
        # Includes subinterfaces
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_junos.JunosCfgLine` is an interface; subinterfaces
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
        intf_regex = r'^interface\s+(\S+.+)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_subintf(self):
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_junos.JunosCfgLine` is a subinterface.

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
           >>> obj.is_subintf
           False
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_subintf
           True
           >>>
        """
        intf_regex = r'^interface\s+(\S+?\.\d+)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_virtual_intf(self):
        intf_regex = r'^interface\s+(Loopback|Tunnel|Dialer|Virtual-Template|Port-Channel)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_loopback_intf(self):
        """Returns a boolean (True or False) to answer whether this 
        :class:`~models_junos.JunosCfgLine` is a loopback interface.

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
           >>> obj = parse.find_objects('^interface\sFast')[0]
           >>> obj.is_loopback_intf
           False
           >>> obj = parse.find_objects('^interface\sLoop')[0]
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
        :class:`~models_junos.JunosCfgLine` is an ethernet interface.
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

##
##-------------  Junos Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def

class BaseJunosIntfLine(JunosCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseJunosIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None    # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj('127.0.0.1/32', 
            strict=False)

    def __repr__(self):
        if not self.is_switchport:
            if self.ipv4_addr_object==self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                ip = str(self.ipv4_addr_object.ip)
                prefixlen = str(self.ipv4_addr_object.prefixlen)
                addr = "{0}/{1}".format(ip, prefixlen)
            return "<%s # %s '%s' info: '%s'>" % (self.classname, 
                self.linenum, self.name, addr)
        else:
            return "<%s # %s '%s' info: 'switchport'>" % (self.classname, self.linenum, self.name)

    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    def build_reset_string(self):
        # Junos interfaces are defaulted like this...
        return "default " + self.text

    @property
    def verbose(self):
        if not self.is_switchport:
            return "<%s # %s '%s' info: '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>" % (self.classname, self.linenum, self.text, self.ipv4_addr_object or "No IPv4", self.child_indent, len(self.children), self.family_endpoint) 
        else:
            return "<%s # %s '%s' info: 'switchport' (child_indent: %s / len(children): %s / family_endpoint: %s)>" % (self.classname, self.linenum, self.text, self.child_indent, len(self.children), self.family_endpoint) 

    @classmethod
    def is_object_for(cls, line="", re=re):
        return False


    ##-------------  Basic interface properties



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
        intf_regex = r'^interface\s+(\S+[0-9\/\.\s]+)\s*'
        name = self.re_match(intf_regex).strip()
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
            intf_regex = r'^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$'
            intf_number = self.re_match(intf_regex, group=1, default='')
            if intf_number:
                return tuple([int(ii) for ii in intf_number.split('/')])
            else:
                return ()

    @property
    def description(self):
        """Return the current interface description string.

        """
        retval = self.re_match_iter_typed(r'^\s*description\s+(\S.+)$',
            result_type=str, default='')
        return retval


    @property
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(r'^\s*bandwidth\s+(\d+)$',
            result_type=int, default=0)
        return retval


    @property
    def manual_delay(self):
        retval = self.re_match_iter_typed(r'^\s*delay\s+(\d+)$',
            result_type=int, default=0)
        return retval


##
##-------------  Junos Interface Globals
##

class JunosIntfGlobal(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(JunosIntfGlobal, self).__init__(*args, **kwargs)
        self.feature = 'interface global'

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, 
            self.text)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^(no\s+cdp\s+run)|(logging\s+event\s+link-status\s+global)|(spanning-tree\sportfast\sdefault)|(spanning-tree\sportfast\sbpduguard\sdefault)', line):
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
##-------------  Junos Hostname Line
##

class JunosHostnameLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(JunosHostnameLine, self).__init__(*args, **kwargs)
        self.feature = 'hostname'

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, 
            self.hostname)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^hostname', line):
            return True
        return False

    @property
    def hostname(self):
        retval = self.re_match_typed(r'^hostname\s+(\S+)',
            result_type=str, default='')
        return retval


##
##-------------  Base Junos Route line object
##

class BaseJunosRouteLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseJunosRouteLine, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (self.classname, self.linenum, self.network_object, self.routeinfo)

    @property
    def routeinfo(self):
        ### Route information for the repr string
        if self.tracking_object_name:
            return self.nexthop_str+" AD: "+str(self.admin_distance)+" Track: "+self.tracking_object_name
        else:
            return self.nexthop_str+" AD: "+str(self.admin_distance)

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
##-------------  Junos Configuration line object
##

class JunosRouteLine(BaseJunosRouteLine):
    def __init__(self, *args, **kwargs):
        super(JunosRouteLine, self).__init__(*args, **kwargs)
        if 'ipv6' in self.text:
            self.feature = 'ipv6 route'
        else:
            self.feature = 'ip route'

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^(ip|ipv6)\s+route\s+\S', line):
            return True
        return False

    @property
    def vrf(self):
        retval = self.re_match_typed(r'^(ip|ipv6)\s+route\s+(vrf\s+)*(\S+)',
            group=3, result_type=str, default='')
        return retval

    @property
    def address_family(self):
        ## ipv4, ipv6, etc
        retval = self.re_match_typed(r'^(ip|ipv6)\s+route\s+(vrf\s+)*(\S+)',
            group=1, result_type=str, default='')
        return retval

    @property
    def network(self):
        if self.address_family=='ip':
            retval = self.re_match_typed(r'^ip\s+route\s+(vrf\s+)*(\S+)',
                group=2, result_type=str, default='')
        elif self.address_family=='ipv6':
            retval = self.re_match_typed(r'^ipv6\s+route\s+(vrf\s+)*(\S+?)\/\d+',
                group=2, result_type=str, default='')
        return retval

    @property
    def netmask(self):
        if self.address_family=='ip':
            retval = self.re_match_typed(r'^ip\s+route\s+(vrf\s+)*\S+\s+(\S+)',
                group=2, result_type=str, default='')
        elif self.address_family=='ipv6':
            retval = self.re_match_typed(r'^ipv6\s+route\s+(vrf\s+)*\S+?\/(\d+)',
                group=2, result_type=str, default='')
        return retval

    @property
    def network_object(self):
        try:
            if self.address_family=='ip':
                return IPv4Obj('%s/%s' % (self.network, self.netmask), 
                    strict=False)
            elif self.address_family=='ipv6':
                return IPv6Network('%s/%s' % (self.network, self.netmask))
        except:
            return None

    @property
    def nexthop_str(self):
        if self.address_family=='ip':
            retval = self.re_match_typed(r'^ip\s+route\s+(vrf\s+)*\S+\s+\S+\s+(\S+)',
                group=2, result_type=str, default='')
        elif self.address_family=='ipv6':
            retval = self.re_match_typed(r'^ipv6\s+route\s+(vrf\s+)*\S+\s+(\S+)',
                group=2, result_type=str, default='')
        return retval

    @property
    def admin_distance(self):
        retval = self.re_match_typed(r'(\d+)$',
            group=1, result_type=int, default=1)
        return retval


    @property
    def tracking_object_name(self):
        retval = self.re_match_typed(r'^ip(v6)*\s+route\s+.+?track\s+(\S+)',
            group=2, result_type=str, default='')
        return retval
