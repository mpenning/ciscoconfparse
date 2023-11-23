r""" models_junos.py - Parse, Query, Build, and Modify Junos-style configurations

     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2015-2019 David Michael Pennington at Samsung Data Services

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
### HUGE UGLY WARNING:
###   Anything in models_junos.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_junos.py at your own risk.  You have been warned :-)

import ipaddress
import re

from ciscoconfparse.ccp_abc import BaseCfgLine
from ciscoconfparse.ccp_util import IPv4Obj, IPv6Obj

from loguru import logger

##
##-------------  Junos Configuration line object
##


class JunosCfgLine(BaseCfgLine):
    r"""An object for a parsed Junos-style configuration line.
    :class:`~models_junos.JunosCfgLine` objects contain references to other
    parent and child :class:`~models_junos.JunosCfgLine` objects.

    Notes
    -----
    Originally, :class:`~models_junos.JunosCfgLine` objects were only
    intended for advanced ciscoconfparse users.  As of ciscoconfparse
    version 0.9.10, *all users* are strongly encouraged to prefer the
    methods directly on :class:`~models_junos.JunosCfgLine` objects.
    Ultimately, if you write scripts which call methods on
    :class:`~models_junos.JunosCfgLine` objects, your scripts will be much
    more efficient than if you stick strictly to the classic
    :class:`~ciscoconfparse.CiscoConfParse` methods.

    Parameters
    ----------
    line : str
        A string containing a text copy of the Junos configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.
     comment_delimiter : str
         A string which is considered a comment for the configuration format.  Since this is for Cisco Junos-style configurations, it defaults to ``!``.

    Attributes
    ----------
    text : str
        A string containing the parsed Junos configuration statement
    linenum : int
        The line number of this configuration statement in the original config; default is -1 when first initialized.
    parent : :class:`~models_junos.JunosCfgLine()`
        The parent of this object; defaults to ``self``.
    children : list
        A list of ``JunosCfgLine()`` objects which are children of this object.
    child_indent : int
        An integer with the indentation of this object's children
    indent : int
        An integer with the indentation of this object's ``text`` oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
    is_comment : bool
        A boolean indicating whether this is a comment

    Returns
    -------
    :class:`~models_junos.JunosCfgLine`

    """

    # This method is on JunosCfgLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an Junos line number and initialize family relationship
        attributes"""
        super().__init__(*args, **kwargs)

    # This method is on JunosCfgLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        ## Default object, for now
        return True

    # This method is on JunosCfgLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_interface(cls, all_lines, line, re=re):
        return False

    @property
    def name(self):
        """If this is an interface, return a name such as 'ge-0/0/0 unit 0', otherwise return None"""
        return self.intf_name

    # This method is on JunosCfgLine()
    @property
    def intf_name(self):
        """If this is an interface, return a name such as 'ge-0/0/0 unit 0', otherwise return None"""
        if self.is_intf is True:
            intf_parts = list()
            for pobj in self.all_parents:
                if pobj.text.strip() == "interfaces":
                    continue
                intf_parts.append(pobj.text.strip())
            # Append this object text
            intf_parts.append(self.text.strip())
            return " ".join(intf_parts)
        else:
            return None

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_intf(self):
        # Includes subinterfaces / JunOS units
        r"""Returns a boolean (True or False) to answer whether this :class:`~models_junos.JunosCfgLine` is an interface; subinterfaces
        and unit numbers also return True.

        Returns
        -------
        bool

        Examples
        --------

        .. code-block:: python

           >>> config = [
           ...     "interfaces {",
           ...     "    ge-0/0/0 {",
           ...     "        unit 0 {",
           ...     "        }",
           ...     "    }",
           ...     "}",
           ...     ]
           >>> parse = CiscoConfParse(config)
           >>> obj = parse.find_objects('^\s+ge-0.0.0')[0]
           >>> obj.is_intf
           True
           >>> obj = parse.find_objects('^\s+unit\s0')[0]
           >>> obj.is_intf
           True
           >>>
        """
        # Check whether the oldest parent is "interfaces {"...
        if len(self.all_parents) >= 1:
            in_intf_block = bool(self.all_parents[0].text.strip()[0:10] == "interfaces")
            interfacesobj = self.all_parents[0]
        else:
            in_intf_block = False

        if in_intf_block is True:
            for intfobj in interfacesobj.children:
                ##############################################################
                # identify a junos physical interface
                ##############################################################
                if intfobj is self:
                    return True

                ##############################################################
                # identify a junos subinterfaces (i.e. unit numbers)
                ##############################################################
                for unitobj in intfobj.children:
                    if unitobj is self:
                        return True
            return False
        return False

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_subintf(self):
        r"""Returns a boolean (True or False) to answer whether this
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
           >>> obj = parse.find_objects(r'^interface\sSerial')[0]
           >>> obj.is_subintf
           False
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.is_subintf
           True
           >>>
        """
        if self.is_intf is True:
            if "unit" in self.intf_name:
                return True
        return False

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        """Return True if this is a switchport interface"""
        if self.is_intf is True:
            for cobj in self.all_children:
                if "family ethernet-switching" in cobj.text:
                    return True
        return False

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self):
        intf_regex = (
            r"^interface\s+(Loopback|Tunnel|Dialer|Virtual-Template|Port-Channel)"
        )
        if self.re_match(intf_regex):
            return True
        return False

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_loopback_intf(self):
        r"""Returns a boolean (True or False) to answer whether this
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

    # This method is on JunosCfgLine()
    @property
    @logger.catch(reraise=True)
    def is_ethernet_intf(self):
        r"""Returns a boolean (True or False) to answer whether this
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
        intf_regex = r"^interface\s+(.*?\Sthernet)"
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

    # This method is on BaseJunosIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj("0.0.0.1/32", strict=False)

    # This method is on BaseJunosIntfLine()
    @logger.catch(reraise=True)
    def __repr__(self):
        if not self.is_switchport:
            if self.ipv4_addr_object == self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                ip = str(self.ipv4_addr_object.ip)
                prefixlen = str(self.ipv4_addr_object.prefixlen)
                addr = f"{ip}/{prefixlen}"
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: '{addr}'>"
        else:
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' info: 'switchport'>"

    # This method is on BaseJunosIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_interface(cls, all_lines, line, re=re):
        is_interfaces = False
        intf_idx = -1
        parents = []

        # This is the indent of the first interface line
        for lidx, lline in enumerate(all_lines):
            _llindent = len(lline) - len(lline.strip())

            #################################################################
            # Identify beginning of the 'interfaces' block...
            #################################################################
            if lline.strip() == "interfaces":
                is_interfaces = True
                intf_idx = lidx
                parents.append(lline.strip())
            elif is_interfaces is True and _llindent == 0:
                intf_idx = -1
                is_interfaces = False

            if is_interfaces is True:
                _intf_level = lidx - intf_idx
            else:
                _intf_level = -1

            if _intf_level > 0:
                #############################################################
                # Reset is_interfaces in another base config block...
                #############################################################
                if _intf_level > 0 and line.strip == lline.strip():
                    return True

        if _intf_level >= 0:
            return True
        else:
            return False

    # This method is on BaseJunosIntfLine()
    @logger.catch(reraise=True)
    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    # This method is on BaseJunosIntfLine()
    @logger.catch(reraise=True)
    def build_reset_string(self):
        # Junos interfaces are defaulted like this...
        return "default " + self.text

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self):
        r"""Return a ccp_util.IPv4Obj object representing the address on this logical interface; if there is no address, return IPv4Obj()"""
        ######################################################################
        # Return an empty IPv4Obj() unless tihs is an interface unit line
        ######################################################################
        if self.text.split()[0] != "unit":
            return IPv4Obj()

        ######################################################################
        # Check if a child is 'family inet', and then return the IPv4 addr
        #     for it
        ######################################################################
        for obj in self.children:
            if obj.text.split()[0:2] == ["family", "inet"]:
                for cobj in obj.children:
                    if cobj.text.split()[0] == "address":
                        return IPv4Obj(cobj.text.split()[1].strip(";"))
        return IPv4Obj()

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr_object(self):
        r"""Return a ccp_util.IPv6Obj object representing the address on this logical interface; if there is no address, return IPv6Obj()"""
        ######################################################################
        # Return an empty IPv6Obj() unless tihs is an interface unit line
        ######################################################################
        if self.text.split()[0] != "unit":
            return IPv6Obj()

        ######################################################################
        # Check if a child is 'family inet6', and then return the IPv6 addr
        #     for it
        ######################################################################
        for obj in self.children:
            if obj.text.split()[0:2] == ["family", "inet6"]:
                for cobj in obj.children:
                    if cobj.text.split()[0] == "address":
                        return IPv6Obj(cobj.text.split()[1].strip(";"))
        return IPv6Obj()

    # This method is on JunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        for obj in self.parent.all_children:
            if obj.parent.text.split()[0] == "unit" and obj.text.split()[0:2] == ["family", "ethernet-switching"]:
                return True
        return False

    # This method is on BaseJunosIntfLine()
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

    ##-------------  Basic interface properties

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def name(self):
        raise NotImplementedError()

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def port(self):
        r"""Return the interface's port number

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
           >>> obj = parse.find_objects(r'^interface\sFast')[0]
           >>> obj.port
           0
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.port
           0
           >>>
        """
        return self.ordinal_list[-1]

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def port_type(self):
        r"""Return Loopback, ATM, GigabitEthernet, Virtual-Template, etc...

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
           >>> obj = parse.find_objects(r'^interface\sFast')[0]
           >>> obj.port_type
           'FastEthernet'
           >>> obj = parse.find_objects(r'^interface\sATM')[0]
           >>> obj.port_type
           'ATM'
           >>>
        """
        port_type_regex = r"^interface\s+([A-Za-z\-]+)"
        return self.re_match(port_type_regex, group=1, default="")

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def ordinal_list(self):
        r"""Return a tuple of numbers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python tuple of integers: (2, 25).  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: (2, 0, 25).  This method strips all subinterface information in the returned value.

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
            intf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$"
            intf_number = self.re_match(intf_regex, group=1, default="")
            if intf_number:
                return tuple(int(ii) for ii in intf_number.split("/"))
            else:
                return ()

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def description(self):
        """Return the current interface description string.

        """
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(
            r"^\s*bandwidth\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseJunosIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

##
##-------------  IOS Interface Object
##


class JunosIntfLine(BaseJunosIntfLine):

    # This method is on JunosIntfLine()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept a JunOS interface number and initialize family relationship
        attributes

        Warnings
        --------
        All :class:`~models_cisco.JunosIntfLine` methods are still considered beta-quality, until this notice is removed.  The behavior of APIs on this object could change at any time.
        """
        super().__init__(*args, **kwargs)
        self.feature = "interface"

    # This method is on JunosIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        return cls.is_object_for_interface(all_lines, line, re=re)

##
##-------------  Base Junos Route line object
##


class BaseJunosRouteLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<{} # {} '{}' info: '{}'>".format(
            self.classname,
            self.linenum,
            self.network_object,
            self.routeinfo,
        )

    @property
    @logger.catch(reraise=True)
    def routeinfo(self):
        ### Route information for the repr string
        if self.tracking_object_name:
            return (
                self.nexthop_str
                + " AD: "
                + str(self.admin_distance)
                + " Track: "
                + self.tracking_object_name
            )
        else:
            return self.nexthop_str + " AD: " + str(self.admin_distance)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        return False

    @property
    @logger.catch(reraise=True)
    def vrf(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def network(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def netmask(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        raise NotImplementedError


##
##-------------  Junos Configuration line object
##


class JunosRouteLine(BaseJunosRouteLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "ipv6" in self.text:
            self.feature = "ipv6 route"
        else:
            self.feature = "ip route"

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^(ip|ipv6)\s+route\s+\S", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def vrf(self):
        retval = self.re_match_typed(
            r"^(ip|ipv6)\s+route\s+(vrf\s+)*(\S+)", group=3, result_type=str, default=""
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        retval = self.re_match_typed(
            r"^(ip|ipv6)\s+route\s+(vrf\s+)*(\S+)", group=1, result_type=str, default=""
        )
        return retval

    @property
    @logger.catch(reraise=True)
    def network(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+(vrf\s+)*(\S+)", group=2, result_type=str, default=""
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*(\S+?)\/\d+",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def netmask(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+(vrf\s+)*\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*\S+?\/(\d+)",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def network_object(self):
        try:
            if self.address_family == "ip":
                return IPv4Obj("{}/{}".format(self.network, self.netmask), strict=False)
            elif self.address_family == "ipv6":
                return ipaddress.IPv6Network("{}/{}".format(self.network, self.netmask))
        except BaseException:
            return None

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+(vrf\s+)*\S+\s+\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        retval = self.re_match_typed(r"(\d+)$", group=1, result_type=int, default=1)
        return retval

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        retval = self.re_match_typed(
            r"^ip(v6)*\s+route\s+.+?track\s+(\S+)", group=2, result_type=str, default=""
        )
        return retval
