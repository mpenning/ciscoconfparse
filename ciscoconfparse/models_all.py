from __future__ import absolute_import
from abc import abstractmethod
import copy
import re
import os

from ciscoconfparse.errors import DynamicAddressException

from ciscoconfparse.ccp_util import CiscoRange, CiscoInterface
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
r""" models_all.py - Parse, Query, Build, and Modify IOS-style configurations

     Copyright (C) 2023      David Michael Pennington

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

class BaseCfgModel(BaseCfgLine):
    """An object for a parsed IOS-style configuration line.
    :class:`~models_cisco.IOSCfgLine` objects contain references to other
    parent and child :class:`~models_cisco.IOSCfgLine` objects.

    Parameters
    ----------
    text : str
        A string containing a text copy of the text configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration.
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
    An instance of :class:`~models_all.BaseCfgModel`.

    """

    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        r"""Accept an IOS line number and initialize family relationship
        attributes"""
        super().__init__(*args, **kwargs)

    def __init_subclass__(cls, *args, **kwargs):
        """Block methods in subclass that do not exist on this parent class:
            ref: https://stackoverflow.com/q/61328355"""
        super().__init_subclass__(*args, **kwargs)
        # By inspecting `cls.__dict__` we pick all methods declared directly on the class
        for name, attr in cls.__dict__.items():
            attr = getattr(cls, name)
            if not callable(attr):
                continue
            for superclass in cls.__mro__[1:]:
                if name in dir(superclass):
                    break
            else:
                # method not found in superclasses:
                raise TypeError(f"Method {name} defined in {cls.__name__}  does not exist in superclasses BaseCfgModel()")


    def __str__(self):
        raise NotImplementedError()

    def __repr__(self):
        raise NotImplementedError()

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        ## Default object, for now
        raise NotImplementedError()

    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def _list(self):
        raise NotImplementedError()

    @property
    @abstractmethod
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
        raise NotImplementedError()

    @property
    @abstractmethod
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
        raise NotImplementedError()

    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def is_virtual_intf(self):
        raise NotImplementedError()

    @property
    @abstractmethod
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
        raise NotImplementedError()

    @property
    @abstractmethod
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
        raise NotImplementedError()

    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def intf_in_portchannel(self):
        r"""Return a boolean indicating whether this port is configured in a port-channel

        Returns
        -------
        bool
        """
        raise NotImplementedError()

    @property
    @abstractmethod
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
        raise NotImplementedError()

    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def is_portchannel_intf(self):
        r"""Return a boolean indicating whether this port is a port-channel intf

        Returns
        -------
        bool
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @abstractmethod
    @logger.catch(reraise=True)
    def _build_abbvs(self):
        r"""Build a set of valid abbreviations (lowercased) for the interface"""
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def abbvs(self):
        r"""A python set of valid abbreviations (lowercased) for the interface"""
        return self._build_abbvs()

    @abstractmethod
    @logger.catch(reraise=True)
    def get_vrrp_tracking_interfaces(self):
        raise NotImplementedError()

    @abstractmethod
    @logger.catch(reraise=True)
    def get_glbp_tracking_interfaces(self):
        raise NotImplementedError()

    @abstractmethod
    @logger.catch(reraise=True)
    def get_hsrp_tracking_interfaces(self):
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def hsrp_interfaces(self):
        """Return the list of configured HSRPInterfaceGroup() instances"""
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @abstractmethod
    @logger.catch(reraise=True)
    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @abstractmethod
    @logger.catch(reraise=True)
    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def verbose(self):
        """Return a verbose string representation of this object"""
        raise NotImplementedError()

    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def interface_object(self):
        """Return a CiscoInterface() instance for this interface

        Returns
        -------
        CiscoInterface
            The interface name as a CiscoInterface() instance, or '' if the object is not an interface.  The CiscoInterface instance can be transparently cast as a string into a typical Cisco IOS name.
        """
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_bandwidth(self):
        retval = self.re_match_iter_typed(
            r"^\s*bandwidth\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_holdqueue_out(self):
        r"""Return the current hold-queue out depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+out$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_holdqueue_in(self):
        r"""Return the current hold-queue in depth, if default return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*hold-queue\s+(\d+)\s+in$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_encapsulation(self):
        retval = self.re_match_iter_typed(
            r"^\s*encapsulation\s+(\S+)", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_mpls(self):
        retval = self.re_match_iter_typed(
            r"^\s*(mpls\s+ip)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4_addr_object(self):
        r"""Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj()"""

        if self.ipv4_addr=="":
            return self.default_ipv4_addr_object
        elif self.ipv4_addr=="dhcp":
            return self.default_ipv4_addr_object
        else:
            return IPv4Obj(f"{self.ipv4_addr}/{self.ipv4_netmask}")

        try:
            logger.info(f"intf='{self.name}' ipv4_addr='{self.ipv4_addr}' ipv4_netmask='{self.ipv4_netmask}'")
            return IPv4Obj(f"{self.ipv4_addr}/{self.ipv4_netmask}")
        except DynamicAddressException as eee:
            logger.critical(f"intf='{self.name}' ipv4_addr='{self.ipv4_addr}' ipv4_netmask='{self.ipv4_netmask}': {eee}")
            raise DynamicAddressException(eee)
        except BaseException:
            logger.warning(f"intf='{self.name}' ipv4_addr='{self.ipv4_addr}' ipv4_netmask='{self.ipv4_netmask}'")
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_no_ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object == IPv4Obj()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ip(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4(self):
        r"""Return an ccp_util.IPv4Obj object representing the IPv4 address on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4_network_object(self):
        r"""Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj()"""
        return self.ip_network_object

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ip_network_object(self):
        # Simplified on 2014-12-02
        try:
            return IPv4Obj(f"{self.ipv4_addr}/{self.ipv4_mask}", strict=False)
        except DynamicAddressException as e:
            raise DynamicAddressException(e)
        except BaseException as e:
            return self.default_ipv4_addr_object

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_carrierdelay(self):
        r"""Return a python boolean for whether carrier delay is manually configured on the interface"""
        return bool(self.manual_carrierdelay)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_clock_rate(self):
        return bool(self.manual_clock_rate)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_clock_rate(self):
        r"""Return the clock rate of the interface as a python integer. If there is no explicit clock rate, return 0"""
        retval = self.re_match_iter_typed(
            r"^\s*clock\s+rate\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=int, default=0
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_mtu(self):
        return bool(self.manual_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_mpls_mtu(self):
        return bool(self.manual_mpls_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_ip_mtu(self):
        return bool(self.manual_ip_mtu)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_vrf(self):
        return bool(self.vrf)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def vrf(self):
        retval = self.re_match_iter_typed(
            r"^\s*(ip\s+)*vrf\sforwarding\s(\S+)$", result_type=str, group=2, default=""
        )
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ip_addr(self):
        return self.ipv4_addr

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
        if condition1.lower() == "dhcp":
            return ""
        else:
            return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4_masklength(self):
        r"""Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    # This method is on BaseIOSIntfLine()
    @abstractmethod
    @logger.catch(reraise=True)
    def is_abbreviated_as(self, val):
        r"""Test whether `val` is a good abbreviation for the interface"""
        if val.lower() in self.abbvs:
            return True
        return False

    # This method is on BaseIOSIntfLine()
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ip_helper_addresses(self):
        r"""Return a True if the intf has helper-addresses; False if not"""
        if len(self.ip_helper_addresses) > 0:
            return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def is_switchport(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0] == "switchport":
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_switch_access(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "access"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def manual_switch_trunk_encap(self):
        for _obj in self.children:
            _parts = _obj.text.strip().split()
            if len(_parts) == 4 and _parts[0:3] == ["switchport", "trunk", "encap"]:
                return _parts[3]
        return ""

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_manual_switch_trunk(self):
        for _obj in self.children:
            if _obj.text.strip().split()[0:3] == ["switchport", "mode", "trunk"]:
                return True
        return False

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def trunk_vlans_allowed(self):
        r"""Return a CiscoRange() with the list of allowed vlan numbers (as int).  Return 0 if the port isn't a switchport in trunk mode"""

        # The default value for retval...
        if self.is_switchport and not self.has_manual_switch_access:
            retval = CiscoRange(result_type=int)
        else:
            return 0


        # Default to allow allow all vlans...
        vdict = {"allowed": "1-4094"}

        ## Iterate over switchport trunk statements
        for obj in self.children:
            split_line = [ii for ii in obj.text.split() if ii.strip() != ""]
            length_split_line = len(split_line)

            ## For every child object, check whether the vlan list is modified
            allowed_str = obj.re_match_typed(
                # switchport trunk allowed vlan
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+(all|none|\d[\d\-\,\s]*)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            if allowed_str != "_nomatch_":
                if vdict.get("allowed", "_no_allowed_") != "_no_allowed_":
                    # Replace the default allow of 1-4094...
                    vdict["allowed"] = allowed_str
                elif vdict.get("allowed", None) is None:
                    # Specify an initial list of vlans...
                    vdict["allowed"] = allowed_str
                elif allowed_str != "none" and allowed_str != "all":
                    # handle **double allowed** statements here...
                    vdict["allowed"] += f",{allowed_str}"
                else:
                    raise NotImplementedError("Unexpected command: `{obj.text}`")

            add_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+add\s+(\d[\d\-\,\s]*)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            if add_str != "_nomatch_":
                if vdict.get("add", None) is None:
                    vdict["add"] = add_str
                else:
                    vdict["add"] += f",{add_str}"

            exc_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+except\s+(\d[\d\-\,\s]*)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            if exc_str != "_nomatch_":
                if vdict.get("except", None) is None:
                    vdict["except"] = exc_str
                else:
                    vdict["except"] += f",{exc_str}"

            rem_str = obj.re_match_typed(
                r"^\s+switchport\s+trunk\s+allowed\s+vlan\s+remove\s+(\d[\d\-\,\s]*)$",
                default="_nomatch_",
                result_type=str,
            ).lower()
            if rem_str != "_nomatch_":
                if vdict.get("remove", None) is None:
                    vdict["remove"] = rem_str
                else:
                    vdict["remove"] += f",{rem_str}"

        ## Analyze each vdict in sequence and apply to retval sequentially
        if isinstance(vdict.get("allowed", None), str):
            if vdict.get("allowed") == "all":
                if len(retval) != 4094:
                    retval = CiscoRange(f"1-{MAX_VLAN}", result_type=int)
            elif vdict.get("allowed") == "none":
                retval = CiscoRange(result_type=int)
            elif vdict.get("allowed") != "_nomatch_":
                retval = CiscoRange(vdict["allowed"], result_type=int)

        for key, _value in vdict.items():
            _value = _value.strip()
            if _value == "":
                continue
            elif _value != "_nomatch_":
                ## allowed in the key overrides previous values
                if key=="allowed":
                    retval = CiscoRange(result_type=int)
                    if _value.lower() == "none":
                        continue
                    elif _value.lower() == "all":
                        retval = CiscoRange(text=f"1-{MAX_VLAN}", result_type=int)
                    elif _value == "_nomatch_":
                        for ii in _value.split(","):
                            if "-" in _value:
                                for jj in CiscoRange(_value, result_type=int):
                                    retval.append(int(jj), ignore_errors=True)
                            else:
                                retval.append(int(ii), ignore_errors=True)
                    elif isinstance(re.search(r"^\d[\d\-\,]*", _value), re.Match):
                        for ii in _value.split(","):
                            if "-" in _value:
                                for jj in CiscoRange(_value, result_type=int):
                                    retval.append(int(jj), ignore_errors=True)
                            else:
                                retval.append(int(ii), ignore_errors=True)
                    else:
                        error = f"Could not derive a vlan range for {_value}"
                        logger.error(error)
                        raise InvalidCiscoEthernetVlan(error)

                elif key=="add":
                    for ii in _value.split(","):
                        if "-" in _value:
                            for jj in CiscoRange(_value, result_type=int):
                                retval.append(int(jj), ignore_errors=True)
                        else:
                            retval.append(int(ii), ignore_errors=True)
                elif key=="except":
                    retval = CiscoRange(text=f"1-{MAX_VLAN}", result_type=int)
                    for ii in _value.split(","):
                        if "-" in _value:
                            for jj in CiscoRange(_value, result_type=int):
                                retval.remove(int(jj), ignore_errors=True)
                        else:
                            retval.remove(int(ii), ignore_errors=True)
                elif key=="remove":
                    for ii in _value.split(","):
                        if "-" in _value:
                            for jj in CiscoRange(text=_value, result_type=int):
                                # Use ignore_errors to ignore missing elements...
                                retval.remove(int(jj), ignore_errors=True)
                        else:
                            # Use ignore_errors to ignore missing elements...
                            retval.remove(int(ii), ignore_errors=True)
                else:
                    error = f"{key} is an invalid Cisco switched dot1q ethernet trunk action."
                    logger.error(error)
                    raise InvalidCiscoEthernetTrunkAction(error)
        return retval

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_xconnect(self):
        return bool(self.xconnect_vc)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def xconnect_vc(self):
        retval = self.re_match_iter_typed(
            r"^\s*xconnect\s+\S+\s+(\d+)\s+\S+", result_type=int, default=0
        )
        return retval

    ##-------------  HSRP

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ip_hsrp(self):
        return bool(self.hsrp_ip_addr)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
            groupdict = {"mask": str},
            default="",
        )
        return retval["mask"]

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_hsrp_track(self):
        return bool(self.hsrp_track)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_hsrp_authentication_md5(self):
        keychain = self.hsrp_authentication_md5_keychain
        return bool(keychain)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def hsrp_authentication_cleartext(self):
        pass

    ##-------------  MAC ACLs

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_mac_accessgroup_in(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_mac_accessgroup_out(self):
        if not self.is_switchport:
            return False
        return bool(self.mac_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
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
    @abstractmethod
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
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ip_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ip_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_in(self):
        return bool(self.ipv4_accessgroup_in)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def has_ipv4_accessgroup_out(self):
        return bool(self.ipv4_accessgroup_out)

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ip_accessgroup_in(self):
        return self.ipv4_accessgroup_in

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ip_accessgroup_out(self):
        return self.ipv4_accessgroup_out

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4_accessgroup_in(self):
        """Return the name of the inbound IPv4 ACL on the interface"""
        raise NotImplementedError()

    # This method is on BaseIOSIntfLine()
    @property
    @abstractmethod
    @logger.catch(reraise=True)
    def ipv4_accessgroup_out(self):
        """Return the name of the outbound IPv4 ACL on the interface"""
        raise NotImplementedError()

    @abstractmethod
    @logger.catch(reraise=True)
    def manual_exectimeout_minutes(self):
        """Return the VTY timeout minutes on the VTY line"""
        raise NotImplementedError()

    @abstractmethod
    @logger.catch(reraise=True)
    def manual_exectimeout_seconds(self):
        """Return the VTY timeout seconds on the VTY line"""
        raise NotImplementedError()


if False:
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
            super(IOSIntfLine, self).__init__(*args, **kwargs)
            self.feature = "interface"

        # This method is on IOSIntfLine()
        @classmethod
        @logger.catch(reraise=True)
        def is_object_for(cls, all_lines, line, re=re):
            intf_regex = re.search(r"^interface\s+(?P<interface>\S+.+)", line.strip())
            if isinstance(intf_regex, re.Match):
                interface = intf_regex.groupdict()["interface"]
                return True
            else:
                return False

    ##
    ##-------------  IOS Interface Globals
    ##


        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def has_cdp_disabled(self):
            raise NotImplementedError()

        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def has_intf_logging_def(self):
            raise NotImplementedError()

        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def has_stp_portfast_def(self):
            raise NotImplementedError()

        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def has_stp_portfast_bpduguard_def(self):
            raise NotImplementedError()

        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def has_stp_mode_rapidpvst(self):
            raise NotImplementedError()

        @property
        @abstractmethod
        @logger.catch(reraise=True)
        def hostname(self):
            raise NotImplementedError()


##
##-------------  Base IOS Route line object
##


class BaseIOSRouteLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(BaseIOSRouteLine, self).__init__(*args, **kwargs)

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
class IOSAaaGroupServerLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaGroupServerLine, self).__init__(*args, **kwargs)
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

class IOSAaaLoginAuthenticationLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaLoginAuthenticationLine, self).__init__(*args, **kwargs)
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
        if re.search(r"^aaa\sauthentication\slogin", line):
            return True
        return False

##
##-------------  IOS AAA Enable Authentication Lines
##

class IOSAaaEnableAuthenticationLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaEnableAuthenticationLine, self).__init__(*args, **kwargs)
        self.feature = "aaa authentication enable"

        regex = r"^aaa\sauthentication\senable\s(\S+)\sgroup\s(\S+)(.+?)$"
        self.list_name = self.re_match_typed(
            regex, group=1, result_type=str, default=""
        )
        self.group = self.re_match_typed(regex, group=2, result_type=str, default="")
        methods_str = self.re_match_typed(regex, group=3, result_type=str, default="")
        self.methods = methods_str.strip().split(r"\s")

    @classmethod
    @logger.catch(reraise=True)
    def is_object_for(cls, all_lines, line, re=re):
        if re.search(r"^aaa\sauthentication\senable", line):
            return True
        return False

##
##-------------  IOS AAA Commands Authorization Lines
##

class IOSAaaCommandsAuthorizationLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaCommandsAuthorizationLine, self).__init__(*args, **kwargs)
        self.feature = "aaa authorization commands"

        regex = r"^aaa\sauthorization\scommands\s(\d+)\s(\S+)\sgroup\s(\S+)(.+?)$"
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
        if re.search(r"^aaa\sauthorization\scommands", line):
            return True
        return False

##
##-------------  IOS AAA Commands Accounting Lines
##

class IOSAaaCommandsAccountingLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaCommandsAccountingLine, self).__init__(*args, **kwargs)
        self.feature = "aaa accounting commands"

        regex = r"^aaa\saccounting\scommands\s(\d+)\s(\S+)\s(none|stop\-only|start\-stop)\sgroup\s(\S+)$"
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
        if re.search(r"^aaa\saccounting\scommands", line):
            return True
        return False

##
##-------------  IOS AAA Exec Accounting Lines
##

class IOSAaaExecAccountingLine(BaseCfgLine):
    @logger.catch(reraise=True)
    def __init__(self, *args, **kwargs):
        super(IOSAaaExecAccountingLine, self).__init__(*args, **kwargs)
        self.feature = "aaa accounting exec"

        regex = r"^aaa\saccounting\sexec\s(\S+)\s(none|stop\-only|start\-stop)\sgroup\s(\S+)$"
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
        if re.search(r"^aaa\saccounting\sexec", line):
            return True
        return False
