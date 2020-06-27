from __future__ import absolute_import
import re

from ciscoconfparse.protocol_values import (
    ASA_TCP_PORTS,
    ASA_UDP_PORTS,
    ASA_IP_PROTOCOLS,
)
from ciscoconfparse.ccp_abc import BaseCfgLine
from ciscoconfparse.ccp_util import L4Object
from ciscoconfparse.ccp_util import IPv4Obj

### HUGE UGLY WARNING:
###   Anything in models_asa.py could change at any time, until I remove this
###   warning.  I have good reason to believe that these methods
###   function correctly, but I've been wrong before.  There are no unit tests
###   for this functionality yet, so I consider all this code alpha quality.
###
###   Use models_asa.py at your own risk.  You have been warned :-)

""" models_asa.py - Parse, Query, Build, and Modify IOS-style configurations
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

##
##-------------  ASA Configuration line object
##


class ASACfgLine(BaseCfgLine):
    """An object for a parsed ASA-style configuration line.  
    :class:`~models_asa.ASACfgLine` objects contain references to other 
    parent and child :class:`~models_asa.ASACfgLine` objects.

    .. note::

       Originally, :class:`~models_asa.ASACfgLine` objects were only 
       intended for advanced ciscoconfparse users.  As of ciscoconfparse 
       version 0.9.10, *all users* are strongly encouraged to prefer the 
       methods directly on :class:`~models_asa.ASACfgLine` objects.  
       Ultimately, if you write scripts which call methods on 
       :class:`~models_asa.ASACfgLine` objects, your scripts will be much 
       more efficient than if you stick strictly to the classic 
       :class:`~ciscoconfparse.CiscoConfParse` methods.

    Args:
        - text (str): A string containing a text copy of the ASA configuration line.  :class:`~ciscoconfparse.CiscoConfParse` will automatically identify the parent and children (if any) when it parses the configuration. 
        - comment_delimiter (str): A string which is considered a comment for the configuration format.  Since this is for Cisco ASA-style configurations, it defaults to ``!``.

    Attributes:
        - text     (str): A string containing the parsed ASA configuration statement
        - linenum  (int): The line number of this configuration statement in the original config; default is -1 when first initialized.
        - parent (:class:`~models_asa.ASACfgLine()`): The parent of this object; defaults to ``self``.
        - children (list): A list of ``ASACfgLine()`` objects which are children of this object.
        - child_indent (int): An integer with the indentation of this object's children
        - indent (int): An integer with the indentation of this object's ``text``
        - oldest_ancestor (bool): A boolean indicating whether this is the oldest ancestor in a family
        - is_comment (bool): A boolean indicating whether this is a comment

    Returns:
        - an instance of :class:`~models_asa.ASACfgLine`.

    """

    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASACfgLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        ## Default object, for now
        return True

    @property
    def is_intf(self):
        # Includes subinterfaces
        intf_regex = r"^interface\s+(\S+.+)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_subintf(self):
        intf_regex = r"^interface\s+(\S+?\.\d+)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_virtual_intf(self):
        intf_regex = r"^interface\s+(Loopback|Tunnel|Virtual-Template|Port-Channel)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_loopback_intf(self):
        intf_regex = r"^interface\s+(\Soopback)"
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_ethernet_intf(self):
        intf_regex = r"^interface\s+(.*?\Sthernet)"
        if self.re_match(intf_regex):
            return True
        return False


##
##-------------  ASA Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def


class BaseASAIntfLine(ASACfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseASAIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None  # Optional, for user use
        self.default_ipv4_addr_object = IPv4Obj("127.0.0.1/32", strict=False)

    def __repr__(self):
        if not self.is_switchport:
            if self.ipv4_addr_object == self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                addr = self.ipv4_addr_object
            return "<%s # %s '%s' info: '%s'>" % (
                self.classname,
                self.linenum,
                self.name,
                addr,
            )
        else:
            return "<%s # %s '%s' info: 'switchport'>" % (
                self.classname,
                self.linenum,
                self.name,
            )

    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    def build_reset_string(self):
        # ASA interfaces are defaulted like this...
        raise NotImplementedError

    @property
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

    @classmethod
    def is_object_for(cls, line="", re=re):
        return False

    ##-------------  Basic interface properties

    @property
    def name(self):
        """Return a string, such as 'GigabitEthernet0/1'"""
        if not self.is_intf:
            return ""
        intf_regex = r"^interface\s+(\S+[0-9\/\.\s]+)\s*"
        name = self.re_match(intf_regex).strip()
        return name

    @property
    def port(self):
        """Return the interface's port number"""
        return self.ordinal_list[-1]

    @property
    def port_type(self):
        """Return Loopback, GigabitEthernet, etc..."""
        port_type_regex = r"^interface\s+([A-Za-z\-]+)"
        return self.re_match(port_type_regex, group=1, default="")

    @property
    def ordinal_list(self):
        """Return a list of numbers representing card, slot, port for this interface.  If you call ordinal_list on GigabitEthernet2/25.100, you'll get this python list of integers: [2, 25].  If you call ordinal_list on GigabitEthernet2/0/25.100 you'll get this python list of integers: [2, 0, 25].  This method strips all subinterface information in the returned value.

        ..warning:: ordinal_list should silently fail (returning an empty python list) if the interface doesn't parse correctly"""
        if not self.is_intf:
            return []
        else:
            intf_regex = r"^interface\s+[A-Za-z\-]+\s*(\d+.*?)(\.\d+)*(\s\S+)*\s*$"
            intf_number = self.re_match(intf_regex, group=1, default="")
            if intf_number:
                return [int(ii) for ii in intf_number.split("/")]
            else:
                return []

    @property
    def description(self):
        retval = self.re_match_iter_typed(
            r"^\s*description\s+(\S.+)$", result_type=str, default=""
        )
        return retval

    @property
    def manual_delay(self):
        retval = self.re_match_iter_typed(
            r"^\s*delay\s+(\d+)$", result_type=int, default=0
        )
        return retval

    @property
    def ipv4_addr_object(self):
        """Return a ccp_util.IPv4Obj object representing the address on this interface; if there is no address, return IPv4Obj('127.0.0.1/32')"""
        try:
            return IPv4Obj("%s/%s" % (self.ipv4_addr, self.ipv4_netmask))
        except:
            return self.default_ipv4_addr_object

    @property
    def ipv4_standby_addr_object(self):
        """Return a ccp_util.IPv4Obj object representing the standby address on this interface; if there is no address, return IPv4Obj('127.0.0.1/32')"""
        try:
            return IPv4Obj("%s/%s" % (self.ipv4_standby_addr, self.ipv4_netmask))
        except:
            return self.default_ipv4_addr_object

    @property
    def ipv4_network_object(self):
        """Return an ccp_util.IPv4Obj object representing the subnet on this interface; if there is no address, return ccp_util.IPv4Obj('127.0.0.1/32')"""
        return self.ip_network_object

    @property
    def ip_network_object(self):
        try:
            return IPv4Obj(
                "%s/%s" % (self.ipv4_addr, self.ipv4_netmask), strict=False
            ).network
        except AttributeError:
            return IPv4Obj(
                "%s/%s" % (self.ipv4_addr, self.ipv4_netmask), strict=False
            ).network_address
        except:
            return self.default_ipv4_addr_object

    @property
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

    @property
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(
            r"^\s*speed\s+(\d+)$", result_type=bool, default=False
        )
        return retval

    @property
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(
            r"^\s*duplex\s+(\S.+)$", result_type=bool, default=False
        )
        return retval

    @property
    def is_shutdown(self):
        retval = self.re_match_iter_typed(
            r"^\s*(shut\S*)\s*$", result_type=bool, default=False
        )
        return retval

    @property
    def ip_addr(self):
        return self.ipv4_addr

    @property
    def ipv4_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+(\sstandby\s+\S+\s*)*$",
            result_type=str,
            default="",
        )
        return retval

    @property
    def ipv4_standby_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+\d+\.\d+\.\d+\.\d+\sstandby\s+(\S+)\s*$",
            result_type=str,
            default="",
        )
        return retval

    @property
    def ipv4_netmask(self):
        """Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(
            r"^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)(\sstandby\s+\S+\s*)*$",
            result_type=str,
            default="",
        )
        return retval

    @property
    def ipv4_masklength(self):
        """Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object != self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    def in_ipv4_subnet(self, ipv4network=IPv4Obj("0.0.0.0/32", strict=False)):
        """Accept two string arguments for network and netmask, and return a boolean for whether this interface is within the requested subnet.  Return None if there is no address on the interface"""
        if not (str(self.ipv4_addr_object.ip) == "127.0.0.1"):
            try:
                # Return a boolean for whether the interface is in that network and mask
                return self.ipv4_addr_object in ipv4network
            except:
                raise ValueError(
                    "FATAL: %s.in_ipv4_subnet(ipv4network={0}) is an invalid arg".format(
                        ipv4network
                    )
                )
        else:
            return None

    def in_ipv4_subnets(self, subnets=None):
        """Accept a set or list of ccp_util.IPv4Obj objects, and return a boolean for whether this interface is within the requested subnets."""
        if subnets is None:
            raise ValueError(
                "A python list or set of ccp_util.IPv4Obj objects must be supplied"
            )
        for subnet in subnets:
            tmp = self.in_ipv4_subnet(ipv4network=subnet)
            if self.ipv4_addr_object in subnet:
                return tmp
        return tmp

    @property
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if self.ipv4_addr == "":
            return False

        retval = self.re_match_iter_typed(
            r"^\s*ip\spim\ssparse-mode\s*$)\s*$", result_type=bool, default=False
        )
        return retval

    @property
    def is_switchport(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport)\s*", result_type=bool, default=False
        )
        return retval

    @property
    def has_manual_switch_access(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\smode\s+access)\s*$", result_type=bool, default=False
        )
        return retval

    @property
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    @property
    def has_manual_switch_trunk(self):
        retval = self.re_match_iter_typed(
            r"^\s*(switchport\s+mode\s+trunk)\s*$", result_type=bool, default=False
        )
        return retval

    @property
    def access_vlan(self):
        """Return an integer with the access vlan number.  Return 0, if the port has no explicit vlan configured."""
        retval = self.re_match_iter_typed(
            r"^\s*switchport\s+access\s+vlan\s+(\d+)$", result_type=int, default=0
        )
        return retval


##
##-------------  ASA name
##

_RE_NAMEOBJECT_STR = r"^name\s+(?P<addr>\d+\.\d+\.\d+\.\d+)\s(?P<name>\S+)"
_RE_NAMEOBJECT = re.compile(_RE_NAMEOBJECT_STR, re.VERBOSE)


class ASAName(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAName, self).__init__(*args, **kwargs)
        mm = _RE_NAMEOBJECT.search(self.text)
        if not (mm is None):
            self._mm_results = mm.groupdict()  # All regex match results
        else:
            raise ValueError

        self.name = self._mm_results["name"]
        self.addr = self._mm_results["addr"]

    @classmethod
    def is_object_for(cls, line="", re=re):
        if "name " in line[0:5].lower():
            return True
        return False

    @property
    def result_dict(self):
        mm_r = self._mm_results
        retval = dict()

        retval["name"] = self._mm_results["name"]
        retval["addr"] = self._mm_results["addr"]

        return retval


##
##-------------  ASA object network
##


class ASAObjNetwork(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjNetwork, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if "object network " in line[0:15].lower():
            return True
        return False


##
##-------------  ASA object service
##


class ASAObjService(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjService, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if "object service " in line[0:15].lower():
            return True
        return False


##
##-------------  ASA object-group network
##
_RE_NETOBJECT_STR = r"""(?:                         # Non-capturing parenthesis
 (^\s*network-object\s+host\s+(?P<host>\S+))
|(^\s*network-object\s+(?P<network>\S+)\s+(?P<netmask>\d+\.\d+\.\d+\.\d+))
|(^\s*group-object\s+(?P<groupobject>\S+))
)                                                   # Close non-capture parens
"""
_RE_NETOBJECT = re.compile(_RE_NETOBJECT_STR, re.VERBOSE)


class ASAObjGroupNetwork(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAObjGroupNetwork, self).__init__(*args, **kwargs)

        self.name = self.re_match_typed(
            r"^object-group\s+network\s+(\S+)", group=1, result_type=str
        )

    @classmethod
    def is_object_for(cls, line="", re=re):
        if "object-group network " in line[0:21].lower():
            return True
        return False

    @property
    def hash_children(self):
        ## Manually override the BaseCfgLine method since this recurses through
        ##    children
        ## FIXME: Implement hash_children for ASAObjGroupService
        return hash(tuple(self.network_strings))  # network_strings recurses...

    @property
    def network_count(self):
        ## Return the number of discrete network objects covered by this group
        ## FIXME: Implement port_count for ASAObjGroupService
        return len(self.network_strings)

    @property
    def network_strings(self):
        """Return a list of strings which represent the address space allowed by
        this object-group"""
        retval = list()
        names = self.confobj.names
        for obj in self.children:

            ## Parse out 'object-group ...' and 'group-object' lines...
            mm = _RE_NETOBJECT.search(obj.text)
            if not (mm is None):
                net_obj = mm.groupdict()
                if net_obj["netmask"] == "255.255.255.255":
                    net_obj["host"] = net_obj["network"]
            else:
                net_obj = dict()

            if net_obj.get("host", None):
                retval.append(names.get(net_obj["host"], net_obj["host"]))
            elif net_obj.get("network", None):
                ## This is a non-host network object
                retval.append(
                    "{0}/{1}".format(
                        names.get(net_obj["network"], net_obj["network"]),
                        net_obj["netmask"],
                    )
                )
            elif net_obj.get("groupobject", None):
                groupobject = net_obj["groupobject"]
                if groupobject == self.name:
                    ## Throw an error when importing self
                    raise ValueError(
                        "FATAL: Cannot recurse through group-object {0} in object-group network {1}".format(
                            groupobject, self.name
                        )
                    )

                group_nets = self.confobj.object_group_network.get(groupobject, None)
                if group_nets is None:
                    raise ValueError(
                        "FATAL: Cannot find group-object named {0}".format(name)
                    )
                else:
                    retval.extend(group_nets.network_strings)
            elif "description " in obj.text:
                pass
            else:
                raise NotImplementedError("Cannot parse '{0}'".format(obj.text))
        return retval

    @property
    def networks(self):
        """Return a list of IPv4Obj objects which represent the address space allowed by
        This object-group"""
        ## FIXME: Implement object caching for other ASAConfigList objects
        ## Return a cached result if the networks lookup has already been done

        retval = list()
        for net_str in self.network_strings:
            ## Check the ASACfgList cache of network objects
            if not self.confobj._network_cache.get(net_str, False):
                net = IPv4Obj(net_str)
                self.confobj._network_cache[net_str] = net
                retval.append(net)
            else:
                retval.append(self.confobj._network_cache[net_str])

        return retval


##
##-------------  ASA object-group service
##
_RE_PORTOBJ_STR = r"""(?:                            # Non-capturing parentesis
 # service-object udp destination eq dns
 (^\s*service-object\s+(?P<protocol>{0})\s+(?P<src_dst>\S+)\s+(?P<s_port>\S+))
|(^\s*port-object\s+(?P<operator>eq|range)\s+(?P<p_port>\S.+))
|(^\s*group-object\s+(?P<groupobject>\S+))
)                                                   # Close non-capture parens
""".format(
    "tcp|udp|tcp-udp"
)
_RE_PORTOBJECT = re.compile(_RE_PORTOBJ_STR, re.VERBOSE)


class ASAObjGroupService(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship 
            attributes"""
        super(ASAObjGroupService, self).__init__(*args, **kwargs)

        self.protocol_type = self.re_match_typed(
            r"^object-group\s+service\s+\S+(\s+.+)*$",
            group=1,
            default="",
            result_type=str,
        ).strip()
        self.name = self.re_match_typed(
            r"^object-group\s+service\s+(\S+)", group=1, default="", result_type=str
        )
        ## If *no protocol* is specified in the object-group statement, the
        ##   object-group can be used for both source or destination ports
        ##   at the same time.  Thus L4Objects_are_directional is True if we
        ##   do not specify a protocol in the 'object-group service' line
        if self.protocol_type == "":
            self.L4Objects_are_directional = True
        else:
            self.L4Objects_are_directional = False

    @classmethod
    def is_object_for(cls, line="", re=re):
        if "object-group service " in line[0:21].lower():
            return True
        return False

    def __repr__(self):
        return "<ASAObjGroupService {0} protocol: {1}>".format(
            self.name, self.protocol_type
        )

    @property
    def ports(self):
        """Return a list of objects which represent the protocol and ports allowed by this object-group"""
        retval = list()
        ## TODO: implement processing for group-objects (which obviously
        ##    involves iteration
        # GROUP_OBJ_REGEX = r'^\s*group-object\s+(\S+)'
        for obj in self.children:

            ## Parse out 'service-object ...' and 'port-object' lines...
            mm = _RE_PORTOBJECT.search(obj.text)
            if not (mm is None):
                svc_obj = mm.groupdict()
            else:
                svc_obj = dict()

            if svc_obj.get("protocol", None):
                protocol = svc_obj.get("protocol")
                src_dst = svc_obj.get("src_dst", "")
                port = svc_obj.get("s_port", "")

                if protocol == "tcp-udp":
                    retval.append(
                        L4Object(protocol="tcp", port_spec=port, syntax="asa")
                    )
                    retval.append(
                        L4Object(protocol="udp", port_spec=port, syntax="asa")
                    )
                else:
                    retval.append(
                        L4Object(protocol=protocol, port_spec=port, syntax="asa")
                    )

            elif svc_obj.get("operator", None):
                op = svc_obj.get("operator", "")
                port = svc_obj.get("p_port", "")
                port_spec = "{0} {1}".format(op, port)

                if self.protocol_type == "tcp-udp":
                    retval.append(
                        L4Object(protocol="tcp", port_spec=port_spec, syntax="asa")
                    )
                    retval.append(
                        L4Object(protocol="udp", port_spec=port_spec, syntax="asa")
                    )
                else:
                    retval.append(
                        L4Object(
                            protocol=self.protocol_type,
                            port_spec=port_spec,
                            syntax="asa",
                        )
                    )

            elif svc_obj.get("groupobject", None):
                name = svc_obj.get("groupobject")
                group_ports = self.confobj.object_group_service.get(name, None)
                if name == self.name:
                    ## Throw an error when importing self
                    raise ValueError(
                        "FATAL: Cannot recurse through group-object {0} in object-group service {1}".format(
                            name, self.name
                        )
                    )
                if group_ports is None:
                    raise ValueError(
                        "FATAL: Cannot find group-object named {0}".format(name)
                    )
                else:
                    retval.extend(group_ports.ports)
            elif "description " in obj.text:
                pass
            else:
                raise NotImplementedError("Cannot parse '{0}'".format(obj.text))
        return retval


##
##-------------  ASA Interface Object
##


class ASAIntfLine(BaseASAIntfLine):
    def __init__(self, *args, **kwargs):
        """Accept an ASA line number and initialize family relationship
        attributes"""
        super(ASAIntfLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        intf_regex = r"^interface\s+(\S+.+)"
        if re.search(intf_regex, line):
            return True
        return False


##
##-------------  ASA Interface Globals
##


class ASAIntfGlobal(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(ASAIntfGlobal, self).__init__(*args, **kwargs)
        self.feature = "interface global"

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.text)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search("^mtu", line):
            return True
        return False


##
##-------------  ASA Hostname Line
##


class ASAHostnameLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(ASAHostnameLine, self).__init__(*args, **kwargs)
        self.feature = "hostname"

    def __repr__(self):
        return "<%s # %s '%s'>" % (self.classname, self.linenum, self.hostname)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search("^hostname", line):
            return True
        return False

    @property
    def hostname(self):
        retval = self.re_match_typed(r"^hostname\s+(\S+)", result_type=str, default="")
        return retval


##
##-------------  Base ASA Route line object
##


class BaseASARouteLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseASARouteLine, self).__init__(*args, **kwargs)

    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (
            self.classname,
            self.linenum,
            self.network_object,
            self.routeinfo,
        )

    @property
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
    def is_object_for(cls, line="", re=re):
        return False

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
##-------------  ASA Configuration line object
##


class ASARouteLine(BaseASARouteLine):
    def __init__(self, *args, **kwargs):
        super(ASARouteLine, self).__init__(*args, **kwargs)
        if "ipv6" in self.text:
            self.feature = "ipv6 route"
        else:
            self.feature = "ip route"

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search("^(ip|ipv6)\s+route\s+\S", line):
            return True
        return False

    @property
    def address_family(self):
        ## ipv4, ipv6, etc
        retval = self.re_match_typed(
            r"^(ip|ipv6)\s+route\s+*(\S+)", group=1, result_type=str, default=""
        )
        return retval

    @property
    def network(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*(\S+)", group=2, result_type=str, default=""
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*(\S+?)\/\d+", group=2, result_type=str, default=""
            )
        return retval

    @property
    def netmask(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*\S+\s+(\S+)", group=2, result_type=str, default=""
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*\S+?\/(\d+)", group=2, result_type=str, default=""
            )
        return retval

    @property
    def network_object(self):
        try:
            if self.address_family == "ip":
                return IPv4Obj("%s/%s" % (self.network, self.netmask), strict=False)
            elif self.address_family == "ipv6":
                return IPv6Network("%s/%s" % (self.network, self.netmask))
        except:
            return None

    @property
    def nexthop_str(self):
        if self.address_family == "ip":
            retval = self.re_match_typed(
                r"^ip\s+route\s+*\S+\s+\S+\s+(\S+)",
                group=2,
                result_type=str,
                default="",
            )
        elif self.address_family == "ipv6":
            retval = self.re_match_typed(
                r"^ipv6\s+route\s+*\S+\s+(\S+)", group=2, result_type=str, default=""
            )
        return retval

    @property
    def admin_distance(self):
        retval = self.re_match_typed(r"(\d+)$", group=1, result_type=int, default=1)
        return retval

    @property
    def tracking_object_name(self):
        retval = self.re_match_typed(
            r"^ip(v6)*\s+route\s+.+?track\s+(\S+)", group=2, result_type=str, default=""
        )
        return retval


_ACL_PROTOCOLS = (
    "ip|tcp|udp|ah|eigrp|esp|gre|igmp|igrp|ipinip|ipsec|ospf|pcp|pim|pptp|snp|\d+"
)
_ACL_ICMP_PROTOCOLS = "alternate-address|conversion-error|echo-reply|echo|information-reply|information-request|mask-reply|mask-request|mobile-redirect|parameter-problem|redirect|router-advertisement|router-solicitation|source-quench|time-exceeded|timestamp-reply|timestamp-request|traceroute|unreachable"
_ACL_LOGLEVELS = r"alerts|critical|debugging|emergencies|errors|informational|notifications|warnings|[0-7]"
_RE_ACLOBJECT_STR = r"""(?:                         # Non-capturing parenthesis
# remark
 (^access-list\s+(?P<acl_name0>\S+)\s+(?P<action0>remark)\s+(?P<remark>\S.+?)$)

# extended service object with source network object, destination network object
|(?:^access-list\s+(?P<acl_name1>\S+)
  \s+extended\s+(?P<action1>permit|deny)
  \s+(?:
     (?:object-group\s+(?P<service_object1>\S+))
    |(?P<protocol1>{0})
  )
  \s+(?:                       # 10.0.0.0 255.255.255.0
     (?:object-group\s+(?P<src_networkobject1>\S+))
    |(?:object\s+(?P<src_object1>\S+))
    |(?:(?P<src_network1a>\S+)\s+(?P<src_netmask1a>\d+\.\d+\.\d+\.\d+))
  )
  \s+(?:                       # 10.0.0.0 255.255.255.0
     (?:object-group\s+(?P<dst_networkobject1>\S+))
    |(?:object\s+(?P<dst_object1>\S+))
    |(?:(?P<dst_network1a>\S+)\s+(?P<dst_netmask1a>\d+\.\d+\.\d+\.\d+))
  )
  (?:\s+
    (?P<log1>log)
    (?:\s+(?P<loglevel1>{1}))?
    (?:\s+interval\s+(?P<log_interval1>\d+))?
  )?
  (?:\s+(?P<disable1>disable))?
  (?:
    (?:\s+(?P<inactive1>inactive))
   |(?:\s+time-range\s+(?P<time_range1>\S+))
  )?
 \s*$)    # END access-list 1 parse

# extended service object with source network, destination network
# access-list TESTME1 extended permit ip any any log
|(?:^access-list\s+(?P<acl_name2>\S+)
  \s+extended
  \s+(?P<action2>permit|deny)
  \s+(?:                       # service-object or protocol
     (?:object-group\s+(?P<service_object2>\S+))
    |(?P<protocol2>{0})
  )
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<src_network2a>any|any4)
      |(?:host\s+(?P<src_network2b>\S+))
      |(?:object\s+(?P<src_object2>\S+))
      |(?:object-group\s+(?P<src_networkobject2>\S+))
      |(?:(?P<src_network2c>\S+)\s+(?P<src_netmask2c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+
    (?:
       (?:(?P<src_port_operator>eq|neq|lt|gt)\s+(?P<src_port>\S+))
      |(?:range\s+(?P<src_port_low>\S+)\s+(?P<src_port_high>\S+))
      |(?:object-group\s+(?P<src_service_object>\S+))
    )
  )?
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<dst_network2a>any|any4)
      |(?:host\s+(?P<dst_network2b>\S+))
      |(?:object\s+(?P<dst_object2>\S+))
      |(?:object-group\s+(?P<dst_networkobject2>\S+))
      |(?:(?P<dst_network2c>\S+)\s+(?P<dst_netmask2c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+
    (?:
       (?:(?P<dst_port_operator>eq|neq|lt|gt)\s+(?P<dst_port>\S+))
      |(?:range\s+(?P<dst_port_low>\S+)\s+(?P<dst_port_high>\S+))
      |(?:object-group\s+(?P<dst_service_object>\S+))
    )
  )?
  (?:\s+
    (?P<log2>log)
    (?:\s+(?P<loglevel2>{1}))?
    (?:\s+interval\s+(?P<log_interval2>\d+))?
  )?
  (?:\s+(?P<disable2>disable))?
  (?:
    (?:\s+(?P<inactive2>inactive))
   |(?:\s+time-range\s+(?P<time_range2>\S+))
  )?
 \s*$)    # END access-list 2 parse

# access-list SPLIT_TUNNEL_NETS standard permit 192.0.2.0 255.255.255.0
|(?:^access-list\s+(?P<acl_name3>\S+)
  \s+standard
  \s+(?P<action3>permit|deny)
  \s+(?:
    (?P<dst_network3a>any|any4)
   |(?:host\s+(?P<dst_network3b>\S+))
   |(?:(?P<dst_network3c>\S+)\s+(?P<dst_netmask3c>\d+\.\d+\.\d+\.\d+))
  )

  )
#access-list TESTME extended permit icmp any4 0.0.0.0 0.0.0.0 unreachable log interval 1
|(?:^access-list\s+(?P<acl_name4>\S+)
  \s+extended
  \s+(?P<action4>permit|deny)
  \s+(?P<protocol4>icmp)
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<src_network4a>any|any4)
      |(?:host\s+(?P<src_network4b>\S+))
      |(?:object\s+(?P<src_object4>\S+))
      |(?:object-group\s+(?P<src_networkobject4>\S+))
      |(?:(?P<src_network4c>\S+)\s+(?P<src_netmask4c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+       # any, any4, host foo, object-group FOO or 10.0.0.0 255.255.255.0
     (?:
       (?P<dst_network4a>any|any4)
      |(?:host\s+(?P<dst_network4b>\S+))
      |(?:object\s+(?P<dst_object4>\S+))
      |(?:object-group\s+(?P<dst_networkobject4>\S+))
      |(?:(?P<dst_network4c>\S+)\s+(?P<dst_netmask4c>\d+\.\d+\.\d+\.\d+))
    )
  )
  (?:\s+(?P<icmp_proto4>{2}|\d+))?
  (?:\s+
    (?P<log4>log)
    (?:\s+(?P<loglevel4>{1}))?
    (?:\s+interval\s+(?P<log_interval4>\d+))?
  )?
  (?:\s+(?P<disable4>disable))?
  (?:
    (?:\s+(?P<inactive4>inactive))
   |(?:\s+time-range\s+(?P<time_range4>\S+))
  )?
  )
)                                                   # Close non-capture parens
""".format(
    _ACL_PROTOCOLS, _ACL_LOGLEVELS, _ACL_ICMP_PROTOCOLS
)
_RE_ACLOBJECT = re.compile(_RE_ACLOBJECT_STR, re.VERBOSE)


class ASAAclLine(ASACfgLine):
    def __init__(self, *args, **kwargs):
        """Provide attributes on Cisco ASA Access-Lists"""
        super(ASAAclLine, self).__init__(*args, **kwargs)
        mm = _RE_ACLOBJECT.search(self.text)
        if not (mm is None):
            self._mm_results = mm.groupdict()  # All regex match results
        else:
            raise ValueError("[FATAL] models_asa cannot parse '{0}'".format(self.text))

    @classmethod
    def is_object_for(cls, line="", re=re):
        # if _RE_ACLOBJECT.search(line):
        if "access-list " in line[0:13].lower():
            return True
        return False

    @property
    def src_addr_method(self):
        mm_r = self._mm_results
        if mm_r["action0"] and (mm_r["action0"] == "remark"):
            # remarks return an empty string
            return ""
        elif (
            mm_r["src_networkobject1"]
            or mm_r["src_networkobject2"]
            or mm_r["src_networkobject4"]
        ):
            return "object-group"
        elif mm_r["src_object1"] or mm_r["src_object2"] or mm_r["src_object4"]:
            return "object"
        elif (
            mm_r["src_network1a"]
            or mm_r["src_network2a"]
            or mm_r["src_network2b"]
            or mm_r["src_network2c"]
            or mm_r["src_network4a"]
            or mm_r["src_network4b"]
            or mm_r["src_network4c"]
        ):
            return "network"
        ## NOTE: I intended to match dst addrs here...
        elif mm_r["acl_name3"]:
            ## Special case: standard ACLs match any src implicitly
            self._mm_results["src_network3"] = "any4"
            return "network"
        else:
            raise ValueError(
                "Cannot parse ACL source address method for '{0}'".format(self.text)
            )

    @property
    def dst_addr_method(self):
        mm_r = self._mm_results
        if mm_r["action0"] and (mm_r["action0"] == "remark"):
            # remarks return an empty string
            return ""
        elif (
            mm_r["dst_networkobject1"]
            or mm_r["dst_networkobject2"]
            or mm_r["dst_networkobject4"]
        ):
            return "object-group"
        elif mm_r["dst_object1"] or mm_r["dst_object2"] or mm_r["dst_object4"]:
            return "object"
        elif (
            mm_r["dst_network1a"]
            or mm_r["dst_network2a"]
            or mm_r["dst_network2b"]
            or mm_r["dst_network2c"]
            or mm_r["dst_network4a"]
            or mm_r["dst_network4b"]
            or mm_r["dst_network4c"]
        ):
            return "network"
        elif mm_r["dst_network3a"] or mm_r["dst_network3b"] or mm_r["dst_network3c"]:
            return "network"
        else:
            raise ValueError(
                "Cannot parse ACL destination address method for '{0}'".format(
                    self.text
                )
            )

    @property
    def acl_protocol_dict(self):
        mm_r = self._mm_results
        retval = dict()

        if mm_r["remark"]:
            # remarks get IP protocol -1
            retval["protocol"] = -1
            retval["protocol_object"] = ""
            return retval
        elif mm_r["protocol1"] or mm_r["protocol2"] or mm_r["protocol4"]:
            _proto = mm_r["protocol1"] or mm_r["protocol2"] or mm_r["protocol4"] or -1
            retval["protocol"] = int(ASA_IP_PROTOCOLS.get(_proto, _proto))
            retval["protocol_object"] = ""
            return retval
        elif mm_r["acl_name3"]:
            # Special case for standard ASA ACLs
            _proto = "ip"
            retval["protocol"] = int(ASA_IP_PROTOCOLS.get(_proto, _proto))
            retval["protocol_object"] = ""
            return retval
        elif mm_r["service_object1"] or mm_r["service_object2"]:
            # protocol service objects get a special protocol number
            retval["protocol"] = 65535
            retval["protocol_object"] = (
                mm_r["service_object1"] or mm_r["service_object2"]
            )
            return retval
        else:
            raise ValueError(
                "Cannot parse ACL protocol value for '{0}'".format(self.text)
            )

    @property
    def result_dict(self):
        mm_r = self._mm_results
        retval = dict()

        proto_dict = self.acl_protocol_dict
        retval["ip_protocol"] = proto_dict["protocol"]
        retval["ip_protocol_object"] = proto_dict["protocol_object"]
        retval["acl_name"] = (
            mm_r["acl_name0"]
            or mm_r["acl_name1"]
            or mm_r["acl_name2"]
            or mm_r["acl_name3"]
            or mm_r["acl_name4"]
        )
        retval["action"] = (
            mm_r["action0"]
            or mm_r["action1"]
            or mm_r["action2"]
            or mm_r["action3"]
            or mm_r["action4"]
        )
        retval["remark"] = mm_r["remark"]
        retval["src_addr_method"] = self.src_addr_method
        retval["dst_addr_method"] = self.dst_addr_method
        retval["disable"] = bool(
            mm_r["disable1"] or mm_r["disable2"] or mm_r["disable4"]
        )
        retval["time_range"] = (
            mm_r["time_range1"] or mm_r["time_range2"] or mm_r["time_range4"]
        )
        retval["log"] = bool(mm_r["log1"] or mm_r["log2"] or mm_r["log4"])
        if not retval["log"]:
            retval["log_interval"] = -1
            retval["log_level"] = ""
        else:
            retval["log_level"] = (
                mm_r["loglevel1"]
                or mm_r["loglevel2"]
                or mm_r["loglevel4"]
                or "informational"
            )
            retval["log_interval"] = int(
                mm_r["log_interval1"]
                or mm_r["log_interval2"]
                or mm_r["log_interval4"]
                or 300
            )

        return retval


################################
################################ Groups ###############################
################################
