r""" models_iosxr.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2014-2019 David Michael Pennington at Samsung Data Services

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

import re

from loguru import logger

from ciscoconfparse.errors import DynamicAddressException

from ciscoconfparse.errors import InvalidCiscoInterface
from ciscoconfparse.ccp_util import CiscoRange, IPv4Obj
from ciscoconfparse.ccp_util import CiscoIOSXRInterface
from ciscoconfparse.ccp_abc import BaseCfgLine

### HUGE UGLY WARNING:
###   Anything in models_iosxr.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_cisco.py at your own risk.  You have been warned :-)

MAX_VLAN = 4094

##
##-------------  IOS Configuration line object
##


class IOSXRCfgLine(BaseCfgLine):
    """An object for a parsed IOS-style configuration line.
    :class:`~models_cisco.IOSCfgLine` objects contain references to other
    parent and child :class:`~models_cisco.IOSCfgLine` objects.

    Notes
    -----
    Originally, :class:`~models_cisco.IOSCfgLine` objects were only
    intended for advanced ciscoconfparse users.  As of ciscoconfparse
    version 0.9.10, *all users* are strongly encouraged to prefer the
    methods directly on :class:`~models_cisco.IOSCfgLine` objects.
    Ultimately, if you write scripts which call methods on
    :class:`~models_cisco.IOSCfgLine` objects, your scripts will be much
    more efficient than if you stick strictly to the classic
    :class:`~ciscoconfparse.CiscoConfParse` methods.

    Parameters
    ----------
    line : str
        A string containing a text copy of the IOS configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.
    comment_delimiter : str
        A string which is considered a comment for the configuration format.  Since this is for Cisco IOS-style configurations, it defaults to ``!``.

    Attributes
    ----------
    text : str
        A string containing the parsed IOS configuration statement
    linenum : int
        The line number of this configuration statement in the original config; default is -1 when first initialized.
    parent : (:class:`~models_cisco.IOSCfgLine()`)
        The parent of this object; defaults to ``self``.
    children : list
        A list of ``IOSCfgLine()`` objects which are children of this object.
    child_indent : int
        An integer with the indentation of this object's children
    indent : int
        An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
    is_comment : bool
        A boolean indicating whether this is a comment

    Returns
    -------
    An instance of :class:`~models_cisco.IOSCfgLine`.

    """

    # This method is on IOSXRCfgLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship
        attributes"""
        super().__init__(*args, **kwargs)

    # This method is on IOSXRCfgLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        ## Default object, for now
        return True

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_intf(self):
        # Includes subinterfaces
        r"""Returns a boolean (True or False) to answer whether this
        :class:`~models_cisco.IOSCfgLine` is an interface; subinterfaces
        also return True.

        Returns
        -------
        bool

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

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
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sSerial')[0]
           >>> obj.is_intf
           True
           >>> obj = parse.find_objects('^interface\sATM')[0]
           >>> obj.is_intf
           True
           >>>
        """
        if self.text[0:10] == "interface " and self.text[10] != " ":
            return True
        return False

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_subintf(self):
        r"""Returns a boolean (True or False) to answer whether this
        :class:`~models_cisco.IOSCfgLine` is a subinterface.

        Returns
        -------
        bool

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

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
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects(r'^interface\sSerial')[0]
           >>> obj.is_subintf
           False
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.is_subintf
           True
           >>>
        """
        intf_regex = r"^interface\s+(\S+?\.\d+)"
        if self.re_match(intf_regex):
            return True
        return False

    _VIRTUAL_INTF_REGEX_STR = (
        r"""^interface\s+(Loopback|Vlan|Tunnel|Dialer|Virtual-Template|Port-Channel)"""
    )
    _VIRTUAL_INTF_REGEX = re.compile(_VIRTUAL_INTF_REGEX_STR, re.I)

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self):
        if self.re_match(self._VIRTUAL_INTF_REGEX):
            return True
        return False

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_loopback_intf(self):
        r"""Returns a boolean (True or False) to answer whether this
        :class:`~models_cisco.IOSCfgLine` is a loopback interface.

        Returns
        -------
        bool

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 13,16

           >>> from ciscoconfparse import CiscoConfParse
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
        intf_regex = r"^interface\s+(\Soopback)"
        if self.re_match(intf_regex):
            return True
        return False

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_ethernet_intf(self):
        r"""Returns a boolean (True or False) to answer whether this
        :class:`~models_cisco.IOSCfgLine` is an ethernet interface.
        Any ethernet interface (10M through 10G) is considered an ethernet
        interface.

        Returns
        -------
        bool

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse import CiscoConfParse
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
        intf_regex = r"^interface\s+(.*?\Sthernet)"
        if self.re_match(intf_regex):
            return True
        return False

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def intf_in_portchannel(self):
        r"""Return a boolean indicating whether this port is configured in a port-channel

        Returns
        -------
        bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*channel-group\s+(\d+)", result_type=bool, default=False
        )
        return retval

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def portchannel_number(self):
        r"""Return an integer for the port-channel which it's configured in.  Return -1 if it's not configured in a port-channel

        Returns
        -------
        bool
        """
        retval = self.re_match_iter_typed(
            r"^\s*channel-group\s+(\d+)", result_type=int, default=-1
        )
        return retval

    # This method is on IOSXRCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_portchannel_intf(self):
        r"""Return a boolean indicating whether this port is a port-channel intf

        Returns
        -------
        bool
        """
        return "channel" in self.name.lower()


##
##-------------  IOS Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def


class BaseIOSXRIntfLine(IOSXRCfgLine):
    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj("0.0.0.1/32", strict=False)

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
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
                addr = f"{ip}/{prefixlen}"
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: '{addr}'>"
        else:
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: 'switchport'>"

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def _build_abbvs(self):
        r"""Build a set of valid abbreviations (lowercased) for the interface"""
        retval = set()
        port_type_chars = self.port_type.lower()
        subinterface_number = self.subinterface_number
        for sep in ["", " "]:
            for ii in range(1, len(port_type_chars) + 1):
                retval.add(
                    "{}{}{}".format(port_type_chars[0:ii], sep, subinterface_number)
                )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        return "default " + self.text

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def verbose(self):
        if not self.is_switchport:
            return (
                "<%s # %s '%s' info: '%s' (child_indent: %s / len(children): %s / family_endpoint: %s)>"
                % (
                    self.classname,
                    self.linenum,
                    self.text,
                    self.ipv4_addr_object or "No IPv4",
                    self.child_indent,
                    len(self.children),
                    self.family_endpoint,
                )
            )
        else:
            return (
                "<%s # %s '%s' info: 'switchport' (child_indent: %s / len(children): %s / family_endpoint: %s)>"
                % (
                    self.classname,
                    self.linenum,
                    self.text,
                    self.child_indent,
                    len(self.children),
                    self.family_endpoint,
                )
            )

    # This method is on BaseIOSXRIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        return False

    ##-------------  Basic interface properties

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def abbvs(self):
        r"""A python set of valid abbreviations (lowercased) for the interface"""
        return self._build_abbvs()

    _INTF_NAME_RE_STR = r"^interface\s+(\S+[0-9\/\.\s]+)\s*"
    _INTF_NAME_REGEX = re.compile(_INTF_NAME_RE_STR)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def interface_object(self):
        """Return a CiscoIOSXRInterface() instance for this interface

        Returns
        -------
        CiscoIOSXRInterface
            The interface name as a CiscoIOSXRInterface() instance, or '' if the object is not an interface.  The CiscoIOSXRInterface instance can be transparently cast as a string into a typical Cisco IOS name.
        """
        if not self.is_intf:
            error = "`{self.text}` is not a valid Cisco interface"
            logger.error(error)
            raise InvalidCiscoInterface(error)
        return CiscoIOSXRInterface("".join(self.text.split()[1:]))

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def name(self):
        r"""Return the interface name as a string, such as 'GigabitEthernet0/1'

        Returns
        -------
        str
            The interface name as a string instance, or '' if the object is not an interface.

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20,23

           >>> from ciscoconfparse import CiscoConfParse
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
        return str(self.interface_object)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def port(self):
        r"""Return the interface's port number

        Returns
        -------
        int
            The interface number.

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse import CiscoConfParse
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
        return self.interface_object.port

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def port_type(self):
        r"""Return Loopback, ATM, GigabitEthernet, Virtual-Template, etc...

        Returns
        -------
        str
            The port type.

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse import CiscoConfParse
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
        port_type_regex = r"^interface\s+([A-Za-z\-]+)"
        return self.re_match(port_type_regex, group=1, default="")

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ordinal_list(self):
        r"""Return a tuple of numbers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python tuple of integers: (2, 25).  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: (2, 0, 25).  This method strips all subinterface information in the returned value.

        Returns
        -------
        tuple
            A tuple of port numbers as integers.

        Warnings
        --------
        ordinal_list should silently fail (returning an empty python list) if the interface doesn't parse correctly

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse import CiscoConfParse
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
                return tuple(int(ii) for ii in intf_number.split("/"))
            else:
                return ()

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def interface_number(self):
        r"""Return a string representing the card, slot, port for this interface.  If you call interface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25'.  If you call interface_number on GigabitEthernet2/0/25.100 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.

        Returns
        -------
        str

        Warnings
        --------
        interface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse import CiscoConfParse
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
            intf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$"
            intf_number = self.re_match(intf_regex, group=1, default="")
            return intf_number

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def subinterface_number(self):
        r"""Return a string representing the card, slot, port for this interface or subinterface.  If you call subinterface_number on GigabitEthernet2/25.100, you'll get this python string: '2/25.100'.  If you call interface_number on GigabitEthernet2/0/25 you'll get this python string '2/0/25'.  This method strips all subinterface information in the returned value.

        Returns
        -------
        str

        Warnings
        --------
        subinterface_number should silently fail (returning an empty python string) if the interface doesn't parse correctly

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 17,20

           >>> from ciscoconfparse import CiscoConfParse
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
            subintf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?\.?\d?)(\s\S+)*\s*$"
            subintf_number = self.re_match(subintf_regex, group=1, default="")
            return subintf_number

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def description(self):
        r"""Return the current interface description string.

        """
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(
            r"^\s*bandwidth\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_out(self):
        r"""Return the current hold-queue out depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+out$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_in(self):
        r"""Return the current hold-queue in depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+in$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_encapsulation(self):
        retval = self.re_match_iter_typed(
            r"^\s*encapsulation\s+(\S+)", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mpls(self):
        retval = self.re_match_iter_typed(
            r"^\s*(mpls\s+ip)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self):
        r"""Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj('0.0.0.1/32')"""
        try:
            return IPv4Obj("{}/{}".format(self.ipv4_addr, self.ipv4_netmask))
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except Exception:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('0.0.0.1/32')"""
        return self.ip_network_object == IPv4Obj("0.0.0.1/32")

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('0.0.0.1/32')"""
        return self.ipv4_addr_object

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('0.0.0.1/32')"""
        return self.ipv4_addr_object

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_network_object(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('0.0.0.1/32')"""
        return self.ip_network_object

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_network_object(self):
        # Simplified on 2014-12-02
        try:
            return IPv4Obj(
                "{}/{}".format(self.ipv4_addr, self.ipv4_netmask), strict=False
            )
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except Exception:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_autonegotiation(self):
        if not self.is_ethernet_intf:
            return False
        elif self.is_ethernet_intf and (
            self.has_manual_speed or self.has_manual_duplex
        ):
            return False
        elif self.is_ethernet_intf:
            return True
        else:
            raise ValueError

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_carrierdelay(self):
        r"""Return a python boolean for whether carrier delay is manually configured on the interface"""
        return bool(self.manual_carrierdelay)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_carrierdelay(self):
        r"""Return the manual carrier delay (in seconds) of the interface as a python float. If there is no explicit carrier delay, return 0.0"""
        cd_seconds = self.re_match_iter_typed(
            r"^\s*carrier-delay\s+(\d+)$", result_type=float, default=0.0
        )
        cd_msec = self.re_match_iter_typed(
            r"^\s*carrier-delay\s+msec\s+(\d+)$", result_type=float, default=0.0
        )

        if cd_seconds > 0.0:
            return cd_seconds
        elif cd_msec > 0.0:
            return cd_msec / 1000.0
        else:
            return 0.0

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_clock_rate(self):
        return bool(self.manual_clock_rate)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_clock_rate(self):
        r"""Return the clock rate of the interface as a python integer. If there is no explicit clock rate, return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*clock\s+rate\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        r"""Returns a integer value for the manual MTU configured on an
        :class:`~models_cisco.IOSIntfLine` object.  Interfaces without a
        manual MTU configuration return 0.

        Returns
        -------
        int

        Examples
        --------
        This example illustrates use of the method.

        .. code-block:: python
           :emphasize-lines: 18,21

           >>> from ciscoconfparse import CiscoConfParse
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
            r"^\s*mtu\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_mpls_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r"^\s*mpls\s+mtu\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_ip_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r"^\s*ip\s+mtu\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_mtu(self):
        return bool(self.manual_mtu)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_mpls_mtu(self):
        return bool(self.manual_mpls_mtu)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_ip_mtu(self):
        return bool(self.manual_ip_mtu)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_vrf(self):
        return bool(self.vrf)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self):
        # See Github Issue #235...
        retval = self.re_match_iter_typed(
            r"^\s*vrf\s(\S+)$", result_type=str, group=2, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_addr(self):
        return self.ipv4_addr

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr(self):
        r"""Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ipv4\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+\s*$",
            result_type=str,
            default="",
        )
        condition1 = self.re_match_iter_typed(
            r"^\s+ipv4\s+address\s+(dhcp)\s*$", result_type=str, default=""
        )
        if condition1.lower() == "dhcp":
            error = "Cannot parse address from a dhcp interface: {}".format(self.name)
            raise DynamicAddressException(error)
        else:
            return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_netmask(self):
        r"""Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ipv4\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)\s*$",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_masklength(self):
        r"""Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def is_abbreviated_as(self, val):
        r"""Test whether `val` is a good abbreviation for the interface"""
        if val.lower() in self.abbvs:
            return True
        return False

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnet(self, ipv4network=IPv4Obj("0.0.0.0/32", strict=False)):
        r"""Accept an argument for the :class:`~ccp_util.IPv4Obj` to be
        considered, and return a boolean for whether this interface is within
        the requested :class:`~ccp_util.IPv4Obj`.

        Parameters
        ----------
        ipv4network : :class:`~ccp_util.IPv4Obj`
            An object to compare against IP addresses configured on this :class:`~models_cisco.IOSIntfLine` object.

        Returns
        -------
        bool
            If there is an ip address, or None if there is no ip address.

        Examples
        --------
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
        if not (str(self.ipv4_addr_object.ip) == "0.0.0.1"):
            try:
                # Return a boolean for whether the interface is in that
                #    network and mask
                return self.ipv4_network_object in ipv4network
            except (Exception) as e:
                raise ValueError(
                    "FATAL: %s.in_ipv4_subnet(ipv4network={}) is an invalid arg: {}".format(
                        ipv4network, e
                    )
                )
        else:
            return None

    # This method is on BaseIOSXRIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnets(self, subnets=None):
        r"""Accept a set or list of ccp_util.IPv4Obj objects, and return a boolean for whether this interface is within the requested subnets."""
        if subnets is None:
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if self.ipv4_addr_object in subnet:
                return tmp
        return tmp

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_unreachables(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(unreachables)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_icmp_redirects(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(redirects)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_ip_proxyarp(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        r"""Return a boolean for whether no ip proxy-arp is configured on the
        interface.

        Returns
        -------
        bool

        Examples
        --------
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
        if self.ipv4_addr == "":
            return False

        ## By default, Cisco IOS answers proxy-arp
        ## By default, Nexus disables proxy-arp
        ## By default, IOS-XR disables proxy-arp
        retval = self.re_match_iter_typed(
            r"^\s*no\sip\s(proxy-arp)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_dense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ip\spim\sdense-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ip\spim\ssparse-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparsedense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*(ip\spim\ssparse-dense-mode)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_arp_timeout(self):
        r"""Return an integer with the current interface ARP timeout, if there isn't one set, return 0.  If there is no IP address, return -1"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if self.ipv4_addr == "":
            return -1

        ## By default, Cisco IOS defaults to 4 hour arp timers
        ## By default, Nexus defaults to 15 minute arp timers
        retval = self.re_match_iter_typed(
            r"^\s*arp\s+timeout\s+(\d+)\s*$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_helper_addresses(self):
        r"""Return a True if the intf has helper-addresses; False if not"""
        if len(self.ip_helper_addresses) > 0:
            return True
        return False

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_helper_addresses(self):
        r"""Return a list of dicts with IP helper-addresses.  Each helper-address is in a dictionary.  The dictionary is in this format:

        Examples
        --------

        .. code-block:: python
           :emphasize-lines: 11

           >>> from ciscoconfparse import CiscoConfParse
           >>> config = [
           ...     '!',
           ...     'interface FastEthernet1/1',
           ...     ' ip address 1.1.1.1 255.255.255.0',
           ...     ' ip helper-address 172.16.20.12',
           ...     ' ip helper-address 172.19.185.91',
           ...     '!',
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^interface\sFastEthernet1/1$')[0]
           >>> obj.ip_helper_addresses
           [{'addr': '172.16.20.12', 'vrf': '', 'global': False}, {'addr': '172.19.185.91', 'vrf': '', 'global': False}]
           >>>"""
        retval = list()
        for child in self.children:
            if "helper-address" in child.text:
                addr = child.re_match_typed(
                    r"ip\s+helper-address\s.*?(\d+\.\d+\.\d+\.\d+)"
                )
                global_addr = child.re_match_typed(
                    r"ip\s+helper-address\s+(global)", result_type=bool, default=False
                )
                vrf = child.re_match_typed(
                    r"ip\s+helper-address\s+vrf\s+(\S+)", default=""
                )
                retval.append({"addr": addr, "vrf": vrf, "global": bool(global_addr)})
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport)\s*", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_access(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\smode\s+access)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_switch_trunk_encap(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\s+trunk\s+encap\s+(\S+))\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\s+mode\s+trunk)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_portsecurity(self):
        if not self.is_switchport:
            return False
        ## IMPORTANT: Cisco IOS will not enable port-security on the port
        ##    unless 'switch port-security' (with no other options)
        ##    is in the configuration
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\sport-security)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_stormcontrol(self):
        if not self.is_switchport:
            return False
        retval = self.re_match_iter_typed(
            r"^\s*(storm-control)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_dtp(self):
        if not self.is_switchport:
            return False

        ## Not using self.re_match_iter_typed, because I want to
        ##   be sure I build the correct API for regex_match is False, and
        ##   default value is True
        for obj in self.children:
            switch = obj.re_match(r"^\s*(switchport\snoneg\S*)\s*$")
            if (switch is not None):
                return False
        return True

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def access_vlan(self):
        r"""Return an integer with the access vlan number.  Return 1, if the switchport has no explicit vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0
        retval = self.re_match_iter_typed(
            r"^\s*switchport\s+access\s+vlan\s+(\d+)$",
            result_type=int,
            default=default_val,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def trunk_vlans_allowed(self):
        r"""Return a CiscoRange() with the list of allowed vlan numbers (as int).  Return 0 if the port isn't a switchport in trunk mode"""

        # The default values...
        if self.is_switchport and not self.has_manual_switch_access:
            retval = CiscoRange("1-{}".format(MAX_VLAN), result_type=int)
        else:
            return 0

        ## Iterate over switchport trunk statements
        for obj in self.children:

            ## For every child object, check whether the vlan list is modified
            abs_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s(all|none|\d.*?)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            add_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+add\s+(\d.*?)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            exc_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+except\s+(\d.*?)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            rem_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+remove\s+(\d.*?)$",
                default="_nomatch_",
                result_type=str,
            ).lower()

            ## Build a vdict for each vlan modification statement
            vdict = {
                "absolute_str": abs_str,
                "add_str": add_str,
                "except_str": exc_str,
                "remove_str": rem_str,
            }

            ## Analyze each vdict in sequence and apply to retval sequentially
            for key, val in vdict.items():
                if val != "_nomatch_":
                    ## absolute in the key overrides previous values
                    if "absolute" in key:
                        if val.lower() == "all":
                            retval = CiscoRange(
                                "1-{}".format(MAX_VLAN), result_type=int
                            )
                        elif val.lower() == "none":
                            retval = CiscoRange(result_type=int)
                        else:
                            retval = CiscoRange(val, result_type=int)
                    elif "add" in key:
                        retval.append(val)
                    elif "except" in key:
                        retval = CiscoRange("1-{}".format(MAX_VLAN), result_type=int)
                        retval.remove(val)
                    elif "remove" in key:
                        retval.remove(val)

        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def native_vlan(self):
        r"""Return an integer with the native vlan number.  Return 1, if the switchport has no explicit native vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0
        retval = self.re_match_iter_typed(
            r"^\s*switchport\s+trunk\s+native\s+vlan\s+(\d+)$",
            result_type=int,
            default=default_val,
        )
        return retval

    ##-------------  CDP

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_disable_cdp(self):
        retval = self.re_match_iter_typed(
            r"^\s*(no\s+cdp\s+enable\s*)", result_type=bool, default=False
        )
        return retval

    ##-------------  EoMPLS

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_xconnect(self):
        return bool(self.xconnect_vc)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def xconnect_vc(self):
        retval = self.re_match_iter_typed(
            r"^\s*xconnect\s+\S+\s+(\d+)\s+\S+", result_type=int, default=0
        )
        return retval

    ##-------------  HSRP

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_hsrp(self):
        return bool(self.hsrp_ip_addr)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_addr(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        if self.ipv4_addr == "":
            return ""

        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*ip\s+(\S+)", group=2, result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_ip_mask(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        if self.ipv4_addr == "":
            return ""
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*ip\s+\S+\s+(\S+)\s*$",
            group=2,
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_group(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+)\s+ip\s+\S+", result_type=int, default=-1
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_priority(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        if not self.has_ip_hsrp:
            return 0  # Return this if there is no hsrp on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*priority\s+(\d+)",
            group=2,
            result_type=int,
            default=100,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hello_timer(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface

        # FIXME: handle msec timers...
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*timers\s+(\d+)\s+\d+",
            group=2,
            result_type=float,
            default=0.0,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_hold_timer(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface

        # FIXME: this should be a float (in case of msec timers)
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*timers\s+\d+\s+(\d+)",
            group=2,
            result_type=float,
            default=0.0,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_track(self):
        return bool(self.hsrp_track)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_track(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*track\s(\S+.+?)\s+\d+\s*",
            group=2,
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_usebia(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*(use-bia)",
            group=2,
            result_type=bool,
            default=False,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_preempt(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*(use-bia)",
            group=2,
            result_type=bool,
            default=False,
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_md5_keychain(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(\d+\s+)*authentication\s+md5\s+key-chain\s+(\S+)",
            group=2,
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_authentication_md5(self):
        keychain = self.hsrp_authentication_md5_keychain
        return bool(keychain)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_cleartext(self):
        pass

    ##-------------  MAC ACLs

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mac_accessgroup_in(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_in)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mac_accessgroup_out(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_out)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_out(self):
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(\S+)\s+out\s*$", result_type=str, default=""
        )
        return retval

    ##-------------  IPv4 ACLs

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_in(self):
        return self.ipv4_accessgroup_in

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_out(self):
        return self.ipv4_accessgroup_out

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r"^\s*ip\saccess-group\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSXRIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_out(self):
        retval = self.re_match_iter_typed(
            r"^\s*ip\saccess-group\s+(\S+)\s+out\s*$", result_type=str, default=""
        )
        return retval


##
##-------------  IOS Interface Object
##


class IOSXRIntfLine(BaseIOSXRIntfLine):
    # This method is on IOSXRIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship
        attributes

        Warnings
        --------
        All :class:`~models_cisco.IOSIntfLine` methods are still considered beta-quality, until this notice is removed.  The behavior of APIs on this object could change at any time.
        """
        super().__init__(*args, **kwargs)
        self.feature = "interface"

    # This method is on IOSXRIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        intf_regex = r"^interface\s+(\S+.+)"
        if re.search(intf_regex, line):
            return True
        return False
