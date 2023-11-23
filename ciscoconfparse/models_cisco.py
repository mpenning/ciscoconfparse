from __future__ import absolute_import
import re

from ciscoconfparse.errors import DynamicAddressException

from ciscoconfparse.ccp_util import (
    _IPV6_REGEX_STR_COMPRESSED1,
    _IPV6_REGEX_STR_COMPRESSED2,
)
from ciscoconfparse.errors import InvalidCiscoEthernetTrunkAction
from ciscoconfparse.errors import InvalidCiscoEthernetVlan
from ciscoconfparse.errors import InvalidCiscoInterface

from ciscoconfparse.ccp_util import _IPV6_REGEX_STR_COMPRESSED3
from ciscoconfparse.ccp_util import CiscoRange, CiscoIOSInterface
from ciscoconfparse.ccp_util import IPv4Obj, IPv6Obj
from ciscoconfparse.ccp_abc import BaseCfgLine

from loguru import logger

### HUGE UGLY WARNING:
###   Anything in models_cisco.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods are stable and
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_cisco.py at your own risk.  You have been warned :-)
r""" models_cisco.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2021,2023 David Michael Pennington
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

MAX_VLAN = 4094

##
##-------------  Tracking Interface (HSRP, GLBP, VRRP)
##


class TrackingInterface(BaseCfgLine):
    feature = "tracking_interface"
    _parent = None
    _group = None
    _interface = None
    _decrement = None
    _weighting = None

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __init__(self, group, interface, decrement, weighting=None):
        """Implement a TrackingInterface() object for Cisco IOS HSRP, GLBP and VRRP"""
        super().__init__()

        self._parent = self.parent
        self._group = int(group)
        self._interface = interface
        self._decrement = decrement
        self._weighting = weighting

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __str__(self):
        return f"'{self.name}' group: {self.group}, weighting: {self.weighting}, decrement: {self.decrement}"

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __repr__(self):
        return f"<TrackingInterface {self.__str__()}>"""

    @logger.catch(reraise=True)
    def __hash__(self):
        """Return a hash value based on the Tracking interface group, interface name and decrement / weighting."""
        if self._name is None or self._group is None:
            error = f"Cannot hash TrackingInterface() {self}"
            logger.critical(error)
            raise ValueError(error)
        else:
            return hash(self.name) * hash(self._group) * hash(self.interface_name) * hash(self._decrement) * hash(self._weighting)

    # This method is on TrackingInterface()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        """Return True or False based on whether this Tracking interface is equal to the other instance; both instances must be a TrackingInterface() instance to compare True"""
        if isinstance(other, TrackingInterface):
            if self.name == other.name and self.group == other.group and self._interface == other._linterface and self._decrement == other._decrement and self._weighting == other._weighting:
                return True
            else:
                return False
        return False

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def interface_name(self):
        """Return the interface name as a string, or return None"""
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        if isinstance(self._interface, (int, str)):
            return str(self._interface)
        else:
            return None

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def name(self):
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        return self.interface_name

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def interface(self):
        # Derive the interface_name from 'interface GigabitEthernet 5/2'
        # return the name of the interface that owns this TrackingInterface()
        return self.interface_name

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def tracking_interface_group(self):
        """Return an integer with the TrackingInterface() Group"""
        return int(self._group)

    # This method is on TrackingInterfac3()
    @property
    @logger.catch(reraise=True)
    def decrement(self):
        """Return an integer with the TrackingInterface() decrement or None if there is no decrement."""
        if isinstance(self._decrement, (str, int)) and str(self._decrement) != "":
            return int(self._decrement)
        else:
            return None

    # This method is on TrackingInterface()
    @property
    @logger.catch(reraise=True)
    def weighting(self):
        """Return the weighting (ref GLBP) integer value."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        # Default HSRP weighting value...
        return None

##
##-------------  HSRP Interface Group
##


class HSRPInterfaceGroup(BaseCfgLine):
    feature = "hsrp"
    _group = None
    _parent = None

    ##-------------  HSRP

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __init__(self, group, parent):
        """A HSRP Interface Group object"""
        super().__init__()
        self.feature = "hsrp"
        self._group = int(group)
        if isinstance(parent, BaseCfgLine):
            self._parent = parent
        else:
            error = f"{parent} is not a valid configuration line"
            logger.error(error)
            raise ValueError(error)

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __str__(self):
        """Return a string representation of this HSRPInterfaceGroup() instance."""
        return f"'{self.interface_name}' version: {self.version}, group: {self.group}, ipv4: {self.ipv4}, has_ipv6: {self.has_ipv6}, priority: {self.priority}, preempt: {self.preempt}, preempt_delay: {self.preempt_delay}, hello_timer: {self.hello_timer}, hold_timer: {self.hold_timer}"

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __repr__(self):
        return f"<HSRPInterfaceGroup {self.__str__()}>"""

    @logger.catch(reraise=True)
    def __hash__(self):
        """Return a hash for this HSRPInterfaceGroup() instance."""
        return hash(self.interface_name) * hash(self.group)

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def __eq__(self, other):
        """Return True if this HSRPInterfaceGroup() is equal to the other instance or False if the other instance is not an HSRPInterfaceGroup()."""
        if isinstance(other, HSRPInterfaceGroup):
            if self.group == other.group and self.interface_name == other.interface_name:
                return True
            else:
                return False
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hsrp_group(self):
        """Return the integer HSRP group number for this HSRPInterfaceGroup() instance."""
        return int(self._group)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def group(self):
        """Return the integer HSRP group number for this HSRP group"""
        return self.hsrp_group

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ip(self):
        """Return the string IPv4 HSRP address for this HSRP group"""
        return self.ipv4

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ipv4(self):
        """Return the string IPv4 HSRP address for this HSRP group"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "ip"]:
                return obj_parts[-1]
        error = f"{self} does not have an HSRP ip configured"
        logger.error(error)
        raise ValueError(error)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_ipv6(self):
        """Return a boolean for whether this interface is configured with an IPv6 HSRP address"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        return bool(self.ipv6)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def ipv6(self):
        """Return the string IPv6 HSRP address for this HSRP group"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "ipv6"]:
                return obj_parts[-1]
        # Default to an empty string if there is no IPv6 HSRP addr config'd
        return ""

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def interface_name(self):
        """Return the string interface name of the interface owning this HSRP group instance."""
        # return the name of the interface that owns this HSRPInterfaceGroup()
        return " ".join(self._parent.text.strip().split()[1:])

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def interface_tracking(self):
        """Return a list of HSRP TrackingInterface() objects for this HSRPInterfaceGroup()"""
        return self.get_hsrp_tracking_interfaces()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_glbp_tracking_interfaces(self):
        """Get a list of unique GLBP tracked interfaces.  This may never be supported by HSRPInterfaceGroup()"""
        raise NotImplementedError()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_vrrp_tracking_interfaces(self):
        """Get a list of unique VRRP tracked interfaces.  This may never be supported by HSRPInterfaceGroup()"""
        raise NotImplementedError()

    # This method is on HSRPInterfaceGroup()
    @logger.catch(reraise=True)
    def get_hsrp_tracking_interfaces(self):
        """Return a list of HSRP TrackingInterface() interfaces for this HSRPInterfaceGroup()"""
        ######################################################################
        # Find decrement and interface
        ######################################################################
        retval = list()
        for obj in self._parent.children:
            obj_parts = obj.text.strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "track"]:
                interface = None
                decrement = 10
                _gg = obj.re_match_iter_typed(
                    r"standby\s(\d+)\s+track\s+(?P<intf>\S.+?)(?P<decr>\s+\d+)*$",
                    groupdict={"intf": str, "decr": str},
                )
                interface = _gg["intf"]
                if isinstance(_gg["decr"], str) and _gg["decr"] != "None":
                    decrement = int(_gg["decr"].strip())
                retval.append(
                    TrackingInterface(
                        group=int(self._group),
                        interface=interface,
                        decrement=decrement,
                        weighting=None
                    )
                )
        return retval

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def group(self):
        """Return the integer HSRP Group for this HSRPInterfaceGroup() instance."""
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        return self._group

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def preempt_delay(self):
        """Return the configured integer HSRP preempt delay, or 0 if there is none."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:4] == ["standby", str(self._group), "preempt", "delay", "minimum"]:
                return int(obj_parts[5])
        # The default hello timer is 3 seconds...
        return 0

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hello_timer(self):
        """Return the configured integer HSRP hello timer, or the HSRP default of 3 if there is no explicit hello timer."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:4] == ["standby", str(self._group), "timers", "msec"]:
                return float(obj_parts[4]) / 1000.0
            elif obj_parts[0:3] == ["standby", str(self._group), "timers"]:
                return int(obj_parts[-2])
        # The default hello timer is 3 seconds...
        return 3

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hold_timer(self):
        """Return the configured integer HSRP hold timer, or the HSRP default of 10 if there is no explicit hold timer."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:2] == ["standby", str(self._group)] and obj_parts[-2] == "msec":
                return float(obj_parts[-1]) / 1000.0
            elif obj_parts[0:3] == ["standby", str(self._group), "timers"]:
                return int(obj_parts[-1])
        # The default hold timer is 10 seconds...
        return 10

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def priority(self):
        """Return the configured integer HSRP priority, or the HSRP default of 100 if there is no explicit HSRP priority configured."""
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "priority"]:
                return int(obj_parts[3])
        # The default priority is 100...
        return 100

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def version(self):
        """Return the configured integer HSRP version, or the HSRP default of 1 if there is no explicit HSRP version configured."""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:2] == ["standby", "version"]:
                return int(obj_parts[-1])
        # default to version 1...
        return 1

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_track(self):
        return any(self.interface_tracking)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def use_bia(self):
        """Return True if the router is configured with `standby use-bia`; `standby use-bia` helps avoid instability when introducing new HSRP routers.  Return False if the router is not configured with `standby use-bia`."""
        for obj in self._parent.children:
            if "use-bia" in obj.text:
                return True
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def preempt(self):
        """Return True if the router is configured to preempt for this HSRP Group; otherwise return False."""
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        for obj in self._parent.children:
            obj_parts = obj.text.lower().strip().split()
            if obj_parts[0:3] == ["standby", str(self._group), "preempt"]:
                return True
        return False

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def authentication_md5_keychain(self):
        """Return the string text of the MD5 key-chain if this HSRP group is configured with an MD5 authentication key-chain; otherwise return an empty string."""
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+{self.group}\s+authentication\s+md5\s+key-chain\s+(\S+)",
            group=1,
            result_type=str,
            default="",
        )
        return retval

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def has_authentication_md5(self):
        """Return True if the router is configured with an MD5 key-chain; otherwise return False."""
        keychain = self.authentication_md5_keychain
        return bool(keychain)

    # This method is on HSRPInterfaceGroup()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_cleartext(self):
        pass

##
##-------------  IOS Configuration line object
##


class IOSCfgLine(BaseCfgLine):
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

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship attributes"""
        super().__init__(*args, **kwargs)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        """Return True if this object should be used for a given configuration line; otherwise return False"""
        ## Default object, for now
        if cls.is_object_for_hostname(line=line):
            return False
        elif cls.is_object_for_interface(line=line):
            return False
        elif cls.is_object_for_aaa_authentication(line=line):
            return False
        elif cls.is_object_for_aaa_authorization(line=line):
            return False
        elif cls.is_object_for_aaa_accounting(line=line):
            return False
        elif cls.is_object_for_ip_route(line=line):
            return False
        elif cls.is_object_for_ipv6_route(line=line):
            return False
        else:
            return True

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_hostname(cls, line):
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0] == "hostname":
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_interface(cls, line):
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0] == "interface":
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authentication(cls, line):
        """Return True if this is an object for aaa authentication.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "authentication"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_authorization(cls, line):
        """Return True if this is an object for aaa authorization.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "authorization"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_aaa_accounting(cls, line):
        """Return True if this is an object for aaa accounting.  Be sure to reject 'aaa new-model'"""
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["aaa", "accounting"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ip_route(cls, line):
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["ip", "route"]:
                return True
        return False

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for_ipv6_route(cls, line):
        if isinstance(line, str):
            line_parts = line.strip().split()
            if len(line_parts) > 0 and line_parts[0:2] == ["ipv6", "route"]:
                return True
        return False

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

    @property
    @logger.catch(reraise=True)
    def is_virtual_intf(self):
        if self.re_match(self._VIRTUAL_INTF_REGEX):
            return True
        return False

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


class BaseIOSIntfLine(IOSCfgLine):
    default_ipv4_addr_object = None
    default_ipv6_addr_object = None

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj()
        self.default_ipv6_addr_object = IPv6Obj()

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def __repr__(self):
        if not self.is_switchport:
            try:
                ipv4_addr_object = self.ipv4_addr_object
            except DynamicAddressException:
                ipv4_addr_object = None

            if ipv4_addr_object is None:
                addr_str = "IPv4 dhcp"
            elif ipv4_addr_object == self.default_ipv4_addr_object:
                addr_str = "No IPv4"
            else:
                addr_str = f"{self.ipv4_addr}/{self.ipv4_masklength}"
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' primary_ipv4: '{addr_str}'>"
        else:
            return f"<{self.classname} # {self.linenum} '{self.text.strip()}' switchport: 'switchport'>"

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def _build_abbvs(self):
        r"""Build a set of valid abbreviations (lowercased) for the interface"""
        retval = set([])
        port_type = self.port_type.lower()
        subinterface_number = self.subinterface_number
        for sep in ["", " "]:
            for ii in range(1, len(port_type) + 1):
                retval.add(f"{port_type[0:ii]}{sep}{subinterface_number}")
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_interfaces(self):
        """Return the list of configured HSRPInterfaceGroup() instances"""
        retval = set()
        for obj in self.children:
            # Get each HSRP group number...
            if re.search(r"standby\s+(?P<group>\d+)\s+ip", obj.text.strip()):
                group = int(obj.text.split()[1])
                retval.add(HSRPInterfaceGroup(group=group, parent=self))
        # Return a sorted list of HSRPInterfaceGroup() instances...
        intf_groups = sorted(retval, key=lambda x: x.group, reverse=False)
        return intf_groups

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        return f"default {self.text}"

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        return False

    ##-------------  Basic interface properties

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def abbvs(self):
        r"""A python set of valid abbreviations (lowercased) for the interface"""
        return self._build_abbvs()

    _INTF_NAME_RE_STR = r"^interface\s+(\S+[0-9\/\.\s]+)\s*"
    _INTF_NAME_REGEX = re.compile(_INTF_NAME_RE_STR)

    @property
    def interface_object(self):
        """Return a CiscoIOSInterface() instance for this interface

        Returns
        -------
        CiscoIOSInterface
            The interface name as a CiscoIOSInterface() instance, or '' if the object is not an interface.  The CiscoIOSInterface instance can be transparently cast as a string into a typical Cisco IOS name.
        """
        if not self.is_intf:
            error = f"`{self.text}` is not a valid Cisco interface"
            logger.error(error)
            raise InvalidCiscoInterface(error)
        return CiscoIOSInterface("".join(self.text.split()[1:]))

    # This method is on BaseIOSIntfLine()
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
        return " ".join(self.text.split()[1:])

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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
            ifobj = self.interface_object
            retval = []
            static_list = (
                ifobj.slot, ifobj.card, ifobj.port,
                ifobj.subinterface, ifobj.channel, ifobj.interface_class
            )
            if ifobj:
                for ii in static_list:
                    if isinstance(ii, int):
                        retval.append(ii)
                    else:
                        retval.append(-1)
                return tuple(retval)
            else:
                return ()

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def description(self):
        r"""Return the current interface description string.

        """
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.*)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(
            r"^\s*bandwidth\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_out(self):
        r"""Return the current hold-queue out depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+out$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_holdqueue_in(self):
        r"""Return the current hold-queue in depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+in$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_encapsulation(self):
        retval = self.re_match_iter_typed(
            r"^\s*encapsulation\s+(\S+)", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mpls(self):
        retval = self.re_match_iter_typed(
            r"^\s*(mpls\s+ip)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr_object(self):
        r"""Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj()"""

        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(?P<v4addr>\S+)\s+(?P<v4netmask>\d+\.\d+\.\d+\.\d+)",
            groupdict={"v4addr": str, "v4netmask": str},
            default="",
        )

        if retval["v4addr"] == "":
            return self.default_ipv4_addr_object
        elif retval["v4addr"] == "dhcp":
            return self.default_ipv4_addr_object
        elif retval["v4addr"] == "negotiated":
            return self.default_ipv4_addr_object
        else:
            return IPv4Obj(f"{retval['v4addr']}/{retval['v4netmask']}")

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr_object(self):
        r"""Return a ccp_util.IPv6Obj object representing the address on this interface; if there is no address, return IPv6Obj()"""

        retval = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(?P<v6addr>\S+?)\/(?P<v6masklength>\d+)",
            groupdict={"v6addr": str, "v6masklength": str},
            default="",
        )

        if retval["v6addr"] == "":
            return self.default_ipv6_addr_object
        elif retval["v6addr"] == "dhcp":
            return self.default_ipv6_addr_object
        elif retval["v6addr"] == "negotiated":
            return self.default_ipv6_addr_object
        else:
            return IPv6Obj(f"{retval['v6addr']}/{retval['v6masklength']}")

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_secondary(self):
        r"""Return an boolean for whether this interface has IPv4 secondary addresses"""
        retval = self.re_match_iter_typed(
            r"^\s*ip\s+address\s+\S+\s+\S+\s+(?P<secondary>secondary)\s*$",
            groupdict={"secondary": bool},
            default=False
        )
        return retval["secondary"]

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_addresses(self):
        r"""Return a set of IPv4 secondary addresses (as strings)"""
        retval = set()
        for obj in self.parent.all_children:
            _gg = obj.re_match_iter_typed(
                r"^\s*ip\s+address\s+(?P<secondary>\S+\s+\S+)\s+secondary\s*$",
                groupdict={"secondary": IPv4Obj},
                default=False
            )
            if _gg["secondary"]:
                retval.add(str(_gg["secondary"].ip))
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_secondary_networks(self):
        r"""Return a set  of IPv4 secondary addresses / prefixlen"""
        retval = set()
        for obj in self.parent.all_children:
            _gg = obj.re_match_iter_typed(
                r"^\s*ip\s+address\s+(?P<secondary>\S+\s+\S+)\s+secondary\s*$",
                groupdict={"secondary": IPv4Obj},
                default=False
            )
            if _gg["secondary"]:
                retval.add(f"{_gg['secondary'].ip}/{_gg['secondary'].prefixlen}")
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_no_ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object == IPv4Obj()

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_network_object(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ip_network_object

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_network_object(self):
        # Simplified on 2014-12-02
        try:
            return IPv4Obj(f"{self.ipv4_addr}/{self.ipv4_mask}", strict=False)
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except BaseException:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_carrierdelay(self):
        r"""Return a python boolean for whether carrier delay is manually configured on the interface"""
        return bool(self.manual_carrierdelay)

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_clock_rate(self):
        return bool(self.manual_clock_rate)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_clock_rate(self):
        r"""Return the clock rate of the interface as a python integer. If there is no explicit clock rate, return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*clock\s+rate\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_mpls_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r"^\s*mpls\s+mtu\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_ip_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(
            r"^\s*ip\s+mtu\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_mtu(self):
        return bool(self.manual_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_mpls_mtu(self):
        return bool(self.manual_mpls_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_ip_mtu(self):
        return bool(self.manual_ip_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_vrf(self):
        return bool(self.vrf)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def vrf(self):
        retval = self.re_match_iter_typed(
            r"^\s*(ip\s+)*vrf\sforwarding\s(\S+)$", result_type=str, group=2, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_addr(self):
        return self.ipv4_addr

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_addr(self):
        r"""Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+\s*$",
            result_type=str,
            default="",
        )
        condition1 = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(dhcp)\s*$", result_type=str, default=""
        )
        condition2 = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(negotiated)\s*$", result_type=str, default=""
        )
        if condition1.lower() == "dhcp":
            return ""
        elif condition2.lower() == "negotiated":
            return ""
        else:
            return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_netmask(self):
        r"""Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)\s*$",
            result_type=str,
            default="",
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_masklength(self):
        r"""Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_addr(self):
        r"""Return a string with the interface's IPv6 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(?P<v6addr>[^\/]+)",
            result_type=str,
            default="",
        )
        condition1 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(dhcp)\s*$", result_type=str, default=""
        )
        condition2 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(autoconfig)\s*$", result_type=str, default=""
        )
        condition3 = self.re_match_iter_typed(
            r"^\s+ipv6\s+address\s+(negotiated)\s*$", result_type=str, default=""
        )
        if condition1.lower() == "dhcp":
            return ""
        elif condition2.lower() == "autoconfig":
            return ""
        elif condition3.lower() == "negotiated":
            return ""
        else:
            return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv6_masklength(self):
        r"""Return an integer with the interface's IPv6 mask length, or 0 if there is no IP address on the interace"""
        ipv6_addr_object = self.ipv6_addr_object
        if ipv6_addr_object != self.default_ipv6_addr_object:
            return ipv6_addr_object.masklength
        return 0

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def is_abbreviated_as(self, val):
        r"""Test whether `val` is a good abbreviation for the interface"""
        if val.lower() in self.abbvs:
            return True
        return False

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnet(self, ipv4network=None, strict=False):
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
           <IOSIntfLine # 1 'Serial1/0' primary_ipv4: '1.1.1.1/30'>
           >>> obj.in_ipv4_subnet(IPv4Obj('1.1.1.0/24', strict=False))
           True
           >>> obj.in_ipv4_subnet(IPv4Obj('2.1.1.0/24', strict=False))
           False
           >>>
        """
        if self.ipv4_addr_object.empty is True:
            return False
        elif ipv4network is None:
            return False
        elif isinstance(ipv4network, IPv4Obj) and ipv4network.empty is True:
            return False
        elif isinstance(ipv4network, IPv4Obj):
            intf_ipv4obj = self.ipv4_addr_object
            if isinstance(intf_ipv4obj, IPv4Obj):
                try:
                    # Return a boolean for whether the interface is in that
                    #    network and mask
                    return intf_ipv4obj in ipv4network
                except Exception as eee:
                    error = f"FATAL: {self}.in_ipv4_subnet(ipv4network={ipv4network}) is invalid: {eee}"
                    logger.error(error)
                    raise ValueError(error)
            else:
                error = f"{self}.ipv4_addr_object must be an instance of IPv4Obj, but it is {type(intf_ipv4obj)}"
                logger.error(error)
                raise ValueError(error)
        else:
            return None

    # This method is on BaseIOSIntfLine()
    @logger.catch(reraise=True)
    def in_ipv4_subnets(self, subnets=None):
        r"""Accept a set or list of ccp_util.IPv4Obj objects, and return a boolean for whether this interface is within the requested subnets."""
        if subnets is None:
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            if subnet.empty is True:
                continue
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if self.ipv4_addr_object in subnet:
                return tmp
        return tmp

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_pim_sparsedense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["ip", "pim", "sparse-dense-mode"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_helper_addresses(self):
        r"""Return a True if the intf has helper-addresses; False if not"""
        if len(self.ip_helper_addresses) > 0:
            return True
        return False

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def is_switchport(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0] == "switchport":
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_access(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "access"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def manual_switch_trunk_encap(self):
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 4 and _parts[0:3] == ["switchport", "trunk", "encap"]:
                return _parts[3]
        return ""

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "trunk"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_portsecurity(self):
        if not self.is_switchport:
            return False
        ## IMPORTANT: Cisco IOS will not enable port-security on the port
        ##    unless 'switch port-security' (with no other options)
        ##    is in the configuration
        for _obj in self.children:
            if _obj.text.strip().split()[0:2] == ["switchport", "port-security"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_switch_stormcontrol(self):
        if not self.is_switchport:
            return False
        for _obj in self.children:
            if _obj.text.strip().split()[0:1] == ["storm-control"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def access_vlan(self):
        r"""Return an integer with the access vlan number.  Return 1, if the switchport has no explicit vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0

        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "access", "vlan"]:
                return int(_obj.text.strip().split()[3])
        return default_val

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def trunk_vlans_allowed(self):
        r"""Return a CiscoRange() with the list of allowed vlan numbers (as int).  Return 0 if the port isn't a switchport in trunk mode"""

        # The default value for retval...
        if self.is_switchport and not self.has_manual_switch_access:
            retval = CiscoRange(result_type=int)
        else:
            return 0

        _all_vlans = "1-4094"
        _max_number_vlans = 4094
        # Default to allow allow all vlans...
        vdict = {
            "allowed": _all_vlans,
            "add": None,
            "except": None,
            "remove": None,
        }

        ## Iterate over switchport trunk statements
        for obj in self.children:

            if obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "add"]:
                add_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+add\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if add_str != "_nomatch_":
                    if vdict["add"] is None:
                        vdict["add"] = add_str
                    else:
                        vdict["add"] += f",{add_str}"

            elif obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "except"]:
                exc_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+except\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if exc_str != "_nomatch_":
                    if vdict["except"] is None:
                        vdict["except"] = exc_str
                    else:
                        vdict["except"] += f",{exc_str}"

            elif obj.text.split()[0:5] == ["switchport", "trunk", "allowed", "vlan", "remove"]:
                rem_str = obj.re_match_typed(
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+remove\s+(\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if rem_str != "_nomatch_":
                    if vdict["remove"] is None:
                        vdict["remove"] = rem_str
                    else:
                        vdict["remove"] += f",{rem_str}"

            elif obj.text.split()[0:4] == ["switchport", "trunk", "allowed", "vlan"]:
                ## For every child object, check whether the vlan list is modified
                allowed_str = obj.re_match_typed(
                    # switchport trunk allowed vlan
                    r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+(all|none|\d[\d\-\,\s]*)$",
                    default="_nomatch_",
                    result_type=str,
                ).lower()
                if allowed_str != "_nomatch_":
                    if allowed_str == "none":
                        # Replace the default allow of 1-4094...
                        vdict["allowed"] = ""
                    elif allowed_str == "all":
                        # Specify an initial list of vlans...
                        vdict["allowed"] = _all_vlans
                    else:
                        # handle **double allowed** statements here...
                        if vdict["allowed"] == _all_vlans:
                            vdict["allowed"] = f"{allowed_str}"
                        elif vdict["allowed"] == "":
                            vdict["allowed"] = f"{allowed_str}"
                        else:
                            vdict["allowed"] += f",{allowed_str}"

        ## Analyze each vdict in sequence and apply to retval sequentially
        if isinstance(vdict["allowed"], str):
            if vdict["allowed"] == _all_vlans:
                if len(retval) != _max_number_vlans:
                    retval = CiscoRange(f"1-{MAX_VLAN}", result_type=int)
            elif vdict["allowed"] == "":
                retval = CiscoRange(result_type=int)
            elif vdict["allowed"] != "_nomatch_":
                retval = CiscoRange(vdict["allowed"], result_type=int)

        # Inspect vdict keys in a specific order to ensure best results...
        for key in ["allowed", "add", "except", "remove"]:
            _value = vdict[key]

            if isinstance(_value, str):
                _value = _value.strip()
            elif _value is None:
                # There is nothing to be done if _value is None...
                continue

            if _value == "":
                continue
            elif _value != "_nomatch_":
                ## allowed in the key overrides previous values
                if key == "allowed":
                    # When considering 'allowed', reset retval to be empty...
                    retval = CiscoRange(result_type=int)
                    if _value.lower() == "none":
                        continue
                    elif _value.lower() == "all":
                        retval = CiscoRange(text=f"1-{MAX_VLAN}", result_type=int)
                    elif isinstance(re.search(r"^\d[\d\-\,\s]*", _value), re.Match):
                        retval = retval + CiscoRange(_value, result_type=int)
                    else:
                        error = f"Could not derive a vlan range for {_value}"
                        logger.error(error)
                        raise InvalidCiscoEthernetVlan(error)

                elif key == "add":
                    retval = retval + CiscoRange(_value, result_type=int)
                elif key == "except" or key == "remove":
                    retval = retval - CiscoRange(_value, result_type=int)
                else:
                    error = f"{key} is an invalid Cisco switched dot1q ethernet trunk action."
                    logger.error(error)
                    raise InvalidCiscoEthernetTrunkAction(error)
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def native_vlan(self):
        r"""Return an integer with the native vlan number.  Return 1, if the switchport has no explicit native vlan configured; return 0 if the port isn't a switchport"""
        if self.is_switchport:
            default_val = 1
        else:
            default_val = 0
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 5 and _parts[0:4] == ["switchport", "trunk", "native", "vlan"]:
                # return the vlan integer from 'switchport trunk native vlan 911'
                return int(_parts[4])
        return default_val

    ##-------------  CDP

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_manual_disable_cdp(self):
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 3 and _parts[0:3] == ["no", "cdp", "enable",]:
                return True
        return False

    ##-------------  EoMPLS

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_xconnect(self):
        return bool(self.xconnect_vc)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def xconnect_vc(self):
        retval = self.re_match_iter_typed(
            r"^\s*xconnect\s+\S+\s+(\d+)\s+\S+", result_type=int, default=0
        )
        return retval

    ##-------------  HSRP

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_hsrp(self):
        return bool(self.hsrp_ip_addr)

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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
            r"^\s*standby\s+(?P<group>\d+\s+)*ip\s+\S+\s+(?P<mask>\S+)\s*$",
            groupdict={"mask": str},
            default="",
        )
        return retval["mask"]

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_group(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(?P<group>\d+)\s+ip\s+(?P<hsrp_addr>\S+)",
            groupdict={"group": int},
            default=-1
        )
        return retval["group"]

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_priority(self):
        ## For API simplicity, I always assume there is only one hsrp
        ##     group on the interface
        if not self.has_ip_hsrp:
            return 0  # Return this if there is no hsrp on the interface
        retval = self.re_match_iter_typed(
            r"^\s*standby\s+(?P<group>\d+\s+)*priority\s+(?P<priority>\d+)",
            groupdict={"group": int, "priority": int},
            default=100,
        )
        return retval["priority"]

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_track(self):
        return bool(self.hsrp_track)

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
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

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_hsrp_authentication_md5(self):
        keychain = self.hsrp_authentication_md5_keychain
        return bool(keychain)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def hsrp_authentication_cleartext(self):
        pass

    ##-------------  MAC ACLs

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mac_accessgroup_in(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_mac_accessgroup_out(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(?P<group_number>\S+)\s+in\s*$",
            groupdict={"group_number": str},
            default=""
        )
        return retval["group_number"]

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def mac_accessgroup_out(self):
        retval = self.re_match_iter_typed(
            r"^\s*mac\saccess-group\s+(?P<group_number>\S+)\s+out\s*$",
            groupdict={"group_number": str},
            default=""
        )
        return retval["group_number"]

    ##-------------  IPv4 ACLs

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ip_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_in(self):
        return self.ipv4_accessgroup_in

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ip_accessgroup_out(self):
        return self.ipv4_accessgroup_out

    # This method is on BaseIOSIntfLine()
    @property
    @logger.catch(reraise=True)
    def ipv4_accessgroup_in(self):
        retval = self.re_match_iter_typed(
            r"^\s*ip\saccess-group\s+(\S+)\s+in\s*$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
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


class IOSIntfLine(BaseIOSIntfLine):

    # This method is on IOSIntfLine()
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

    # This method is on IOSIntfLine()
    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        return cls.is_object_for_interface(line)

##
##-------------  IOS Interface Globals
##


class IOSIntfGlobal(IOSCfgLine):
    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "interface global"

    # This method is on IOSIntGlobal()
    @logger.catch(reraise=True)
    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(
            r"^(no\s+cdp\s+run)|(logging\s+event\s+link-status\s+global)|(spanning-tree\sportfast\sdefault)|(spanning-tree\sportfast\sbpduguard\sdefault)",
            line,
        ):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_cdp_disabled(self):
        if self.re_search(r"^no\s+cdp\s+run\s*"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_intf_logging_def(self):
        if self.re_search(r"^logging\s+event\s+link-status\s+global"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_def(self):
        if self.re_search(r"^spanning-tree\sportfast\sdefault"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_portfast_bpduguard_def(self):
        if self.re_search(r"^spanning-tree\sportfast\sbpduguard\sdefault"):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def has_stp_mode_rapidpvst(self):
        if self.re_search(r"^spanning-tree\smode\srapid-pvst"):
            return True
        return False


##
##-------------  IOS Hostname Line
##


class IOSHostnameLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "hostname"

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.hostname)

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^hostname", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def hostname(self):
        retval = self.re_match_typed(r"^hostname\s+(\S+)", result_type=str, default="")
        return retval


##
##-------------  IOS Access Line
##


class IOSAccessLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "access line"

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
            self.classname,
            self.linenum,
            self.name,
            self.range_str,
        )

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^line", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def is_accessline(self):
        retval = self.re_match_typed(r"^(line\s+\S+)", result_type=str, default="")
        return bool(retval)

    @property
    @logger.catch(reraise=True)
    def name(self):
        retval = self.re_match_typed(r"^line\s+(\S+)", result_type=str, default="")
        # special case for IOS async lines: i.e. "line 33 48"
        if re.search(r"\d+", retval):
            return ""
        return retval

    @logger.catch(reraise=True)
    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    @logger.catch(reraise=True)
    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        return "default " + self.text

    @property
    @logger.catch(reraise=True)
    def range_str(self):
        return " ".join(map(str, self.line_range))

    @property
    @logger.catch(reraise=True)
    def line_range(self):
        ## Return the access-line's numerical range as a list
        ## line con 0 => [0]
        ## line 33 48 => [33, 48]
        retval = self.re_match_typed(
            r"([a-zA-Z]+\s+)*(\d+\s*\d*)$", group=2, result_type=str, default=""
        )
        tmp = map(int, retval.strip().split())
        return tmp

    @logger.catch(reraise=True)
    def manual_exectimeout_minutes(self):
        tmp = self.parse_exectimeout
        return tmp[0]

    @logger.catch(reraise=True)
    def manual_exectimeout_seconds(self):
        tmp = self.parse_exectimeout
        if len(tmp > 0):
            return 0
        return tmp[1]

    @property
    @logger.catch(reraise=True)
    def parse_exectimeout(self):
        retval = self.re_match_iter_typed(
            r"^\s*exec-timeout\s+(\d+\s*\d*)\s*$", group=1, result_type=str, default=""
        )
        tmp = map(int, retval.strip().split())
        return tmp


##
##-------------  Base IOS Route line object
##


class BaseIOSRouteLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @logger.catch(reraise=True)
    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
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
##-------------  IOS Route line object
##

_RE_IP_ROUTE = re.compile(
    r"""^ip\s+route
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
""",
    re.VERBOSE,
)

_RE_IPV6_ROUTE = re.compile(
    r"""^ipv6\s+route
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
(?:\s+track\s+(?P<track>\d+))?   # Track object
(?:\s+name\s+(?P<name>\S+))?     # Route name
""".format(
        _IPV6_REGEX_STR_COMPRESSED1,
        _IPV6_REGEX_STR_COMPRESSED2,
        _IPV6_REGEX_STR_COMPRESSED3,
    ),
    re.VERBOSE,
)


class IOSRouteLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "ipv6" in self.text[0:4]:
            self.feature = "ipv6 route"
            self._address_family = "ipv6"
            mm = _RE_IPV6_ROUTE.search(self.text)
            if (mm is not None):
                self.route_info = mm.groupdict()
            else:
                raise ValueError("Could not parse '{0}'".format(self.text))
        else:
            self.feature = "ip route"
            self._address_family = "ip"
            mm = _RE_IP_ROUTE.search(self.text)
            if (mm is not None):
                self.route_info = mm.groupdict()
            else:
                raise ValueError("Could not parse '{0}'".format(self.text))

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if (line[0:9] == "ip route ") or (line[0:11] == "ipv6 route "):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def vrf(self):
        if (self.route_info["vrf"] is not None):
            return self.route_info["vrf"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def address_family(self):
        ## ipv4, ipv6, etc
        return self._address_family

    @property
    @logger.catch(reraise=True)
    def network(self):
        if self._address_family == "ip":
            return self.route_info["prefix"]
        elif self._address_family == "ipv6":
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
        if self._address_family == "ip":
            return self.route_info["netmask"]
        elif self._address_family == "ipv6":
            return str(self.network_object.netmask)

    @property
    @logger.catch(reraise=True)
    def masklen(self):
        if self._address_family == "ip":
            return self.network_object.prefixlen
        elif self._address_family == "ipv6":
            masklen_str = self.route_info["masklength"] or "128"
            return int(masklen_str)

    @property
    @logger.catch(reraise=True)
    def network_object(self):
        try:
            if self._address_family == "ip":
                return IPv4Obj("%s/%s" % (self.network, self.netmask), strict=False)
            elif self._address_family == "ipv6":
                return IPv6Obj("%s/%s" % (self.network, self.masklen))
        except BaseException:
            logger.critical("Found _address_family = '{}''".format(self._address_family))
            return None

    @property
    @logger.catch(reraise=True)
    def nexthop_str(self):
        if self._address_family == "ip":
            if self.next_hop_interface:
                return self.next_hop_interface + " " + self.next_hop_addr
            else:
                return self.next_hop_addr
        elif self._address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+(vrf\s+)*\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        return retval

    @property
    @logger.catch(reraise=True)
    def next_hop_interface(self):
        if self._address_family == "ip":
            if self.route_info["nh_intf"]:
                return self.route_info["nh_intf"]
            else:
                return ""
        elif self._address_family == "ipv6":
            if self.route_info["nh_intf"]:
                return self.route_info["nh_intf"]
            else:
                return ""

    @property
    @logger.catch(reraise=True)
    def next_hop_addr(self):
        if self._address_family == "ip":
            return self.route_info["nh_addr"] or ""
        elif self._address_family == "ipv6":
            return self.route_info["nh_addr1"] or self.route_info["nh_addr2"] or ""

    @property
    @logger.catch(reraise=True)
    def global_next_hop(self):
        if self._address_family == "ip" and bool(self.vrf):
            return bool(self.route_info["global"])
        elif self._address_family == "ip" and not bool(self.vrf):
            return True
        elif self._address_family == "ipv6":
            ## ipv6 uses nexthop_vrf
            raise ValueError(
                "[FATAL] ipv6 doesn't support a global_next_hop for '{0}'".format(
                    self.text
                )
            )
        else:
            raise ValueError(
                "[FATAL] Could not identify global next-hop for '{0}'".format(self.text)
            )

    @property
    @logger.catch(reraise=True)
    def nexthop_vrf(self):
        if self._address_family == "ipv6":
            return self.route_info["nexthop_vrf"] or ""
        else:
            raise ValueError(
                "[FATAL] ip doesn't support a global_next_hop for '{0}'".format(
                    self.text
                )
            )

    @property
    @logger.catch(reraise=True)
    def admin_distance(self):
        if self.route_info["ad"]:
            return int(self.route_info["ad"])
        else:
            return 1

    @property
    @logger.catch(reraise=True)
    def multicast(self):
        r"""Return whether the multicast keyword was specified"""
        return bool(self.route_info["mcast"])

    @property
    @logger.catch(reraise=True)
    def unicast(self):
        ## FIXME It's unclear how to implement this...
        raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def route_name(self):
        if self.route_info["name"]:
            return self.route_info["name"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def permanent(self):
        if self._address_family == "ip":
            if self.route_info["permanent"]:
                return bool(self.route_info["permanent"])
            else:
                return False
        elif self._address_family == "ipv6":
            raise NotImplementedError

    @property
    @logger.catch(reraise=True)
    def tracking_object_name(self):
        if bool(self.route_info["track"]):
            return self.route_info["track"]
        else:
            return ""

    @property
    @logger.catch(reraise=True)
    def tag(self):
        return self.route_info["tag"] or ""


################################
################################ Groups ###############################
################################

##
##-------------  IOS TACACS+ Group
##
class IOSAaaGroupServerLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa group server"

        REGEX = r"^aaa\sgroup\sserver\s(?P<protocol>\S+)\s(?P<group>\S+)\s*$"
        mm = re.search(REGEX, self.text)
        if (mm is not None):
            groups = mm.groupdict()
            self.protocol = groups.get("protocol", "")
            self.group = groups.get("group", "")
        else:
            raise ValueError

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\sgroup\sserver", line):
            return True
        return False

    @property
    @logger.catch(reraise=True)
    def vrf(self):
        return self.re_match_iter_typed(
            r"^\s+(ip\s+)*vrf\s+forwarding\s+(\S+)",
            group=2,
            result_type=str,
            default="",
        )

    @property
    @logger.catch(reraise=True)
    def source_interface(self):
        return self.re_match_iter_typed(
            r"^\s+ip\s+tacacs\s+source-interface\s+(\S.+?\S)\s*$",
            group=1,
            result_type=str,
            default="",
        )

    @property
    @logger.catch(reraise=True)
    def server_private(self, re=re):
        retval = set([])
        rgx_priv = re.compile(r"^\s+server-private\s+(\S+)\s")
        for cobj in self.children:
            mm = rgx_priv.search(cobj.text)
            if (mm is not None):
                retval.add(mm.group(1))  # This is the server's ip
        return retval


##
##-------------  IOS AAA Login Authentication Lines
##

class IOSAaaLoginAuthenticationLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa authentication login"

        regex = r"^aaa\sauthentication\slogin\s(\S+)\sgroup\s(\S+)(.+?)$"
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=2, result_type=str, default="")
        methods_str = self.re_match_typed(regex, group=3, result_type=str, default="")
        self.methods = methods_str.strip().split(r"\s")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+authentication\s+login", line.strip()):
            return True
        return False

##
##-------------  IOS AAA Enable Authentication Lines
##


class IOSAaaEnableAuthenticationLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa authentication enable"

        regex = r"^aaa\s+authentication\s+enable\s+(\S+)\s+group\s+(\S+)(.+?)$"
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=2, result_type=str, default="")
        methods_str = self.re_match_typed(regex, group=3, result_type=str, default="")
        self.methods = methods_str.strip().split(r"\s")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+authentication\s+enable", line.strip()):
            return True
        return False

##
##-------------  IOS AAA Commands Authorization Lines
##


class IOSAaaCommandsAuthorizationLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa authorization commands"

        regex = r"^aaa\s+authorization\s+commands\s+(\d+)\s+(\S+)\s+group\s+(\S+)(.+?)$"
        self.level = self.re_match_typed(regex, group=1, result_type=int, default=0)
        self.list_name = self.re_match_typed(
            regex, group=2, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=3, result_type=str, default="")
        methods_str = self.re_match_typed(regex, group=4, result_type=str, default="")
        self.methods = methods_str.strip().split(r"\s")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+authorization\s+commands", line.strip()):
            return True
        return False

##
##-------------  IOS AAA Console Authorization Lines
##


class IOSAaaConsoleAuthorizationLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa authorization console"

        regex = r"^aaa\s+authorization\s+console\s+(\d+)\s+(\S+)\s+group\s+(\S+)(.+?)$"
        self.level = self.re_match_typed(regex, group=1, result_type=int, default=0)
        self.list_name = self.re_match_typed(
            regex, group=2, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=3, result_type=str, default="")
        methods_str = self.re_match_typed(regex, group=4, result_type=str, default="")
        self.methods = methods_str.strip().split(r"\s")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+authorization\s+console", line.strip()):
            return True
        return False

##
##-------------  IOS AAA Commands Accounting Lines
##


class IOSAaaCommandsAccountingLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa accounting commands"

        regex = r"^aaa\s+accounting\s+commands\s+(\d+)\s+(\S+)\s+(none|stop\-only|start\-stop)\s+group\s+(\S+)$"
        self.level = self.re_match_typed(regex, group=1, result_type=int, default=0)
        self.list_name = self.re_match_typed(
            regex, group=2, result_type=str, default=""
        )
        self.record_type = self.re_match_typed(
            regex, group=3, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=4, result_type=str, default="")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+accounting\s+commands", line.strip()):
            return True
        return False

##
##-------------  IOS AAA Exec Accounting Lines
##


class IOSAaaExecAccountingLine(IOSCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.feature = "aaa accounting exec"

        regex = r"^aaa\s+accounting\s+exec\s+(\S+)\s+(none|stop\-only|start\-stop)\s+group\s(\S+)$"
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default=""
        )
        self.record_type = self.re_match_typed(
            regex, group=2, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=3, result_type=str, default="")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\s+accounting\s+exec", line.strip()):
            return True
        return False
