import sys
import re
import os

from ccp_abc import BaseCfgLine

### ipaddr is optional, and Apache License 2.0 is compatible with GPLv3 per
###   the ASL web page: http://www.apache.org/licenses/GPL-compatibility.html
try:
    sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)),
        "local_py"))
    from ipaddr import IPv4Network, IPv6Network
except ImportError:
    # I raise an ImportError elsewhere if ipaddr is required
    pass

""" ciscoconfparse.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2007-2014 David Michael Pennington

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
##-------------  IOS Interface ABC
##

# Valid method name substitutions:
#    switchport -> switch
#    spanningtree -> stp
#    interfce -> intf
#    address -> addr
#    default -> def

class BaseIOSIntfLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseIOSIntfLine, self).__init__(*args, **kwargs)
        self.ifindex = None    # Optional, for user use
        self.default_ipv4_addr_object = IPv4Network('127.0.0.1/32')

    def __repr__(self):
        if not self.is_switchport:
            if self.ipv4_addr_object==self.default_ipv4_addr_object:
                addr = "No IPv4"
            else:
                addr = self.ipv4_addr_object
            return "<%s # %s '%s' info: '%s'>" % (self.classname, 
                self.linenum, self.name, addr)
        else:
            return "<%s # %s '%s' info: 'switchport'>" % (self.classname, self.linenum, self.name)

    def reset(self, atomic=True):
        # Insert build_reset_string() before this line...
        self.insert_before(self.build_reset_string(), atomic=atomic)

    def build_reset_string(self):
        # IOS interfaces are defaulted like this...
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
    def is_intf(self):
        # Includes subinterfaces
        intf_regex = r'^interface\s+(\S+.+)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_subinterface(self):
        intf_regex = r'^interface\s+(\S+?\.\d+)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_virtual(self):
        intf_regex = r'^interface\s+(Loopback|Tunnel|Dialer|Virtual-Template|Port-Channel)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_loopback(self):
        intf_regex = r'^interface\s+(\Soopback)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def is_ethernet(self):
        intf_regex = r'^interface\s+(.*?\Sthernet)'
        if self.re_match(intf_regex):
            return True
        return False

    @property
    def name(self):
        if not self.is_intf:
            return ''
        intf_regex = r'^interface\s+(\S+.+)'
        name = self.re_match(intf_regex)
        return name


    @property
    def description(self):
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


    @property
    def manual_holdqueue_out(self):
        """Return the current hold-queue out depth, if default return 0"""
        retval = self.re_match_iter_typed(r'^\s*hold-queue\s+(\d+)\s+out$',
            result_type=int, default=0)
        return retval


    @property
    def manual_holdqueue_in(self):
        """Return the current hold-queue in depth, if default return 0"""
        retval = self.re_match_iter_typed(r'^\s*hold-queue\s+(\d+)\s+in$',
            result_type=int, default=0)
        return retval


    @property
    def manual_encapsulation(self):
        retval = self.re_match_iter_typed(r'^\s*encapsulation\s+(\S.+)$',
            result_type=str, default='')
        return retval


    @property
    def has_mpls(self):
        retval = self.re_match_iter_typed(r'^\s*(mpls\s+ip)$',
            result_type=bool, default=False)
        return retval


    @property
    def ipv4_addr_object(self):
        """Return an IPv4Network object representing the address on this interface; if there is no address, return IPv4Network('127.0.0.1/32')"""
        try:
            return IPv4Network('%s/%s' % (self.ipv4_addr, self.ipv4_netmask))
        except:
            return self.default_ipv4_addr_object

    @property
    def ipv4_network_object(self):
        """Return an IPv4Network object representing the subnet on this interface; if there is no address, return IPv4Network('127.0.0.1/32')"""
        return self.ip_network_object

    @property
    def ip_network_object(self):
        try:
            return IPv4Network('%s/%s' % (self.ipv4_addr, self.ipv4_netmask)).network
        except:
            return self.default_ipv4_addr_object


    @property
    def has_autonegotiation(self):
        if self.has_manual_speed or self.has_manual_duplex:
            return False
        return True

    @property
    def has_manual_speed(self):
        retval = self.re_match_iter_typed(r'^\s*speed\s+(\d+)$',
            result_type=bool, default=False)
        return retval


    @property
    def has_manual_duplex(self):
        retval = self.re_match_iter_typed(r'^\s*duplex\s+(\S.+)$',
            result_type=bool, default=False)
        return retval


    @property
    def has_manual_carrierdelay(self):
        return bool(self.manual_carrierdelay)


    @property
    def manual_carrierdelay(self):
        cd_seconds = self.re_match_iter_typed(r'^\s*carrier-delay\s+(\d+)$',
            result_type=float, default=0.0)
        cd_msec = self.re_match_iter_typed(r'^\s*carrier-delay\s+msec\s+(\d+)$',
            result_type=float, default=0.0)
        if (cd_seconds>0.0):
            return cd_seconds
        else:
            return cd_msec/1000.0

    @property
    def has_manual_clock_rate(self):
        return bool(self.manual_clock_rate)

    @property
    def manual_clock_rate(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(r'^\s*clock\s+rate\s+(\d+)$',
            result_type=int, default=0)
        return retval

    @property
    def manual_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(r'^\s*mtu\s+(\d+)$',
            result_type=int, default=0)
        return retval

    @property
    def manual_mpls_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(r'^\s*mpls\s+mtu\s+(\d+)$',
            result_type=int, default=0)
        return retval

    @property
    def manual_ip_mtu(self):
        ## Due to the diverse platform defaults, this should be the
        ##    only mtu information I plan to support
        retval = self.re_match_iter_typed(r'^\s*ip\s+mtu\s+(\d+)$',
            result_type=int, default=0)
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
        retval = self.re_match_iter_typed(r'^\s*(shut\S*)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_vrf(self):
        return bool(self.vrf)

    @property
    def vrf(self):
        retval = self.re_match_iter_typed(r'^\s*ip\svrf\sforwarding\s(\S+)$',
            result_type=str, default='')
        return retval

    @property
    def ip_addr(self):
        return self.ipv4_addr

    @property
    def ipv4_addr(self):
        """Return a string with the interface's IPv4 address, or '' if there is none"""
        retval = self.re_match_iter_typed(r'^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+\d+\.\d+\.\d+\.\d+\s*$', 
            result_type=str, default='')
        return retval

    @property
    def ipv4_netmask(self):
        """Return a string with the interface's IPv4 netmask, or '' if there is none"""
        retval = self.re_match_iter_typed(r'^\s+ip\s+address\s+\d+\.\d+\.\d+\.\d+\s+(\d+\.\d+\.\d+\.\d+)\s*$',
            result_type=str, default='')
        return retval

    @property
    def ipv4_masklength(self):
        """Return an integer with the interface's IPv4 mask length, or 0 if there is no IP address on the interace"""
        ipv4_addr_object = self.ipv4_addr_object
        if ipv4_addr_object!=self.default_ipv4_addr_object:
            return ipv4_addr_object.prefixlen
        return 0

    def in_ipv4_subnet(self, network='', mask=''):
        """Accept two string arguments for network and netmask, and return a boolean for whether this interface is within the requested subnet.  Return None if there is no address on the interface"""
        if isinstance(network, str) and isinstance(mask, str):
            if not (str(self.ipv4_addr_object.ip)=="127.0.0.1"):
                try:
                    # Return a boolean for whether the interface is in that network and mask
                    return self.ipv4_addr_object in IPv4Network('%s/%s' % (network, mask))
                except:
                    raise ValueError("FATAL: %s.in_ipv4_subnet() could not convert network='%s', mask='%s' to an address" % (self.__class__.__name__, network, mask))
            else:
                return None
        raise ValueError("FATAL: %s.in_ipv4_subnet() requires string arguments" % self.__class__.__name__)

    def in_ipv4_subnets(self, subnets=None):
        """Accept a set or list of ipaddr.IPv4Network objects, and return a boolean for whether this interface is within the requested subnets."""
        if (subnets is None):
            raise ValueError("A python list or set of ipaddr.IPv4Network objects must be supplied")
        for subnet in subnets:
            if (self.ipv4_addr_object in subnet):
                return True
        return False

    @property
    def has_manual_disable_icmp_unreachables(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr==''):
            return False

        retval = self.re_match_iter_typed(r'^\s*no\sip\s(unreachables)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_manual_disable_icmp_redirects(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr==''):
            return False

        retval = self.re_match_iter_typed(r'^\s*no\sip\s(redirects)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_manual_disable_proxy_arp(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr==''):
            return False

        ## By default, Cisco IOS answers proxy-arp
        ## By default, Nexus disables proxy-arp
        retval = self.re_match_iter_typed(r'^\s*no\sip\s(proxy-arp)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr==''):
            return False

        retval = self.re_match_iter_typed(r'^\s*ip\spim\sdense-mode\s*$)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_ip_pim_sparse_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr==''):
            return False

        retval = self.re_match_iter_typed(r'^\s*ip\spim\ssparse-mode\s*$)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_ip_pim_sparsedense_mode(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to run PIM
        if (self.ipv4_addr==''):
            return False

        retval = self.re_match_iter_typed(r'^\s*ip\spim\ssparse-dense-mode\s*$)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def manual_arp_timeout(self):
        """Return an integer with the current interface ARP timeout, if there isn't one set, return 0.  If there is no IP address, return -1"""
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## Interface must have an IP addr to respond
        if (self.ipv4_addr==''):
            return -1

        ## By default, Cisco IOS defaults to 4 hour arp timers
        ## By default, Nexus defaults to 15 minute arp timers
        retval = self.re_match_iter_typed(r'^\s*arp\s+timeout\s+(\d+)\s*$',
            result_type=int, default=0)
        return retval

    @property
    def is_switchport(self):
        retval = self.re_match_iter_typed(r'^\s*(switchport)\s*',
            result_type=bool, default=False)
        return retval

    @property
    def has_manual_switch_access(self):
        retval = self.re_match_iter_typed(r'^\s*(switchport\smode\s+access)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_manual_switch_trunk_encap(self):
        return bool(self.manual_switch_trunk_encap)

    @property
    def manual_switch_trunk_encap(self):
        retval = self.re_match_iter_typed(r'^\s*(switchport\s+trunk\s+encap\s+(\S+))\s*$',
            result_type=str, default='')
        return retval

    @property
    def has_manual_switch_trunk(self):
        retval = self.re_match_iter_typed(r'^\s*(switchport\s+mode\s+trunk)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_switch_portsecurity(self):
        if not self.is_switchport:
            return False
        ## IMPORTANT: Cisco IOS will not enable port-security on the port
        ##    unless 'switch port-security' (with no other options)
        ##    is in the configuration
        retval = self.re_match_iter_typed(r'^\s*(switchport\sport-security)\s*$',
            result_type=bool, default=False)
        return retval

    @property
    def has_switch_stormcontrol(self):
        if not self.is_switchport:
            return False
        retval = self.re_match_iter_typed(r'^\s*(switchport\sport-security)\s*$',
            result_type=bool, default=False)
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
        """Return an integer with the access vlan number.  Return 0, if the port has no explicit vlan configured."""
        retval = self.re_match_iter_typed(r'^\s*switchport\s+access\s+vlan\s+(\d+)$',
            result_type=int, default=0)
        return retval

    ##-------------  CDP

    @property
    def has_manual_disable_cdp(self):
        retval = self.re_match_iter_typed(r'^\s*(no\s+cdp\s+enable\s*)',
            result_type=bool, default=False)
        return retval

    ##-------------  EoMPLS

    def has_xconnect(self):
        return bool(self.xconnect_vc)

    def xconnect_vc(self):
        retval = self.re_match_iter_typed(r'^\s*xconnect\s+\S+\s+(\d+)\s+\S+',
            result_type=int, default=0)
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
        if (self.ipv4_addr==''):
            return ''

        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*ip\s+(\S+)',
            group=2, result_type=str, default='')
        return retval

    @property
    def hsrp_ip_mask(self):
        ## NOTE: I have no intention of checking self.is_shutdown here
        ##     People should be able to check the sanity of interfaces
        ##     before they put them into production

        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        if (self.ipv4_addr==''):
            return ''
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*ip\s+\S+\s+(\S+)\s*$',
            group=2, result_type=str, default='')
        return retval

    @property
    def hsrp_group(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+)\s+ip\s+\S+',
            result_type=int, default=-1)
        return retval

    @property
    def hsrp_priority(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        if not self.has_ip_hsrp:
            return 0         # Return this if there is no hsrp on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*priority\s+(\d+)',
            group=2, result_type=int, default=100)
        return retval

    @property
    def hsrp_hello_timer(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*timers\s+(\d+)\s+\d+',
            group=2, result_type=int, default=0)
        return retval

    @property
    def hsrp_hold_timer(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*timers\s+\d+\s+(\d+)',
            group=2, result_type=int, default=0)
        return retval

    @property
    def has_hsrp_track(self):
        return bool(self.hsrp_track)

    @property
    def hsrp_track(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*track\s(\S+.+?)\s+\d+\s*',
            group=2, result_type=str, default='')
        return retval

    @property
    def has_hsrp_usebia(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*(use-bia)',
            group=2, result_type=bool, default=False)
        return retval

    @property
    def has_hsrp_preempt(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*(use-bia)',
            group=2, result_type=bool, default=False)
        return retval

    @property
    def hsrp_authentication_md5_keychain(self):
        ## For API simplicity, I always assume there is only one hsrp 
        ##     group on the interface
        retval = self.re_match_iter_typed(r'^\s*standby\s+(\d+\s+)*authentication\s+md5\s+key-chain\s+(\S+)',
            group=2, result_type=str, default='')
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
        retval = self.re_match_iter_typed(r'^\s*mac\saccess-group\s+(\S+)\s+in\s*$',
            result_type=str, default='')
        return retval

    @property
    def mac_accessgroup_out(self):
        retval = self.re_match_iter_typed(r'^\s*mac\saccess-group\s+(\S+)\s+out\s*$',
            result_type=str, default='')
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
        retval = self.re_match_iter_typed(r'^\s*ip\saccess-group\s+(\S+)\s+in\s*$',
            result_type=str, default='')
        return retval

    @property
    def ipv4_accessgroup_out(self):
        retval = self.re_match_iter_typed(r'^\s*ip\saccess-group\s+(\S+)\s+out\s*$',
            result_type=str, default='')
        return retval

##
##-------------  IOS Interface Object
##

class IOSIntfLine(BaseIOSIntfLine):

    def __init__(self, *args, **kwargs):
        """Accept an IOS line number and initialize family relationship
        attributes"""
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
##-------------  IOS Hostname Line
##

class IOSHostnameLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSHostnameLine, self).__init__(*args, **kwargs)
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
##-------------  IOS Access Line
##

class IOSAccessLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(IOSAccessLine, self).__init__(*args, **kwargs)
    def __repr__(self):
        return "<%s # %s '%s' info: '%s'>" % (self.classname, self.linenum, self.name, self.range_str)

    @classmethod
    def is_object_for(cls, line="", re=re):
        if re.search('^line', line):
            return True
        return False

    @property
    def is_accessline(self):
        retval = self.re_match_typed(r'^(line\s+\S+)',
            result_type=str, default='')
        return bool(retval)

    @property
    def name(self):
        retval = self.re_match_typed(r'^line\s+(\S+)',
            result_type=str, default='')
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
        retval = self.re_match_typed(r'([a-zA-Z]+\s+)*(\d+\s*\d*)$',
           group=2, result_type=str, default='')
        tmp = map(int, retval.strip().split())
        return tmp

    def manual_exectimeout_min(self):
        tmp = self.parse_exectimeout
        return tmp[0]

    def manual_exectimeout_sec(self):
        tmp = self.parse_exectimeout
        if len(tmp>0):
            return 0
        return tmp[1]

    @property
    def parse_exectimeout(self):
        retval = self.re_match_iter_typed(r'^\s*exec-timeout\s+(\d+\s*\d*)\s*$',
            group=1, result_type=str, default='')
        tmp = map(int, retval.strip().split())
        return tmp


##
##-------------  Base IOS Route line object
##

class BaseIOSRouteLine(BaseCfgLine):
    def __init__(self, *args, **kwargs):
        super(BaseIOSRouteLine, self).__init__(*args, **kwargs)

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
##-------------  IOS Configuration line object
##

class IOSRouteLine(BaseIOSRouteLine):
    def __init__(self, *args, **kwargs):
        super(IOSRouteLine, self).__init__(*args, **kwargs)

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
                return IPv4Network('%s/%s' % (self.network, self.netmask))
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

    Parameters
    ----------

    text : str, required
         A string containing a text copy of the IOS configuration line.
         :class:`~ciscoconfparse.CiscoConfParse` will automatically identify 
         the parent and children (if any) when it parses the configuration. 
    comment_delimiter : str, required
         A string which is considered a comment for the configuration 
         format.  Since this is for Cisco IOS-style configurations, it 
         defaults to ``!``.


    Returns
    -------

    retval : an instance of :class:`~models_cisco.IOSCfgLine`.

    Attributes
    ----------

    text     : str
         A string containing the parsed IOS configuration statement
    linenum  : int
         The line number of this configuration statement in the original config;
         default is -1 when first initialized.
    parent : :class:`~models_cisco.IOSCfgLine()`
         The parent of this object; defaults to ``self``.
    children : list
         A list of ``IOSCfgLine()`` objects which are children of this object.
    child_indent : int
         An integer with the indentation of this object's children
    indent : int
         An integer with the indentation of this object's ``text``
    oldest_ancestor : boolean
         A boolean indicating whether this is the oldest ancestor in a family
    is_comment : boolean
         A boolean indicating whether this is a comment
    """
    ### Example of family relationships
    ###
    #Line01:policy-map QOS_1
    #Line02: class GOLD
    #Line03:  priority percent 10
    #Line04: class SILVER
    #Line05:  bandwidth 30
    #Line06:  random-detect
    #Line07: class default
    #Line08:!
    #Line09:interface Serial 1/0
    #Line10: encapsulation ppp
    #Line11: ip address 1.1.1.1 255.255.255.252
    #Line12:!
    #Line13:access-list 101 deny tcp any any eq 25 log
    #Line14:access-list 101 permit ip any any
    #
    # parents: 01, 02, 04, 09
    # children: of 01 = 02, 04, 07
    #           of 02 = 03
    #           of 04 = 05, 06
    #           of 09 = 10, 11
    # siblings: 05 and 06
    #           10 and 11
    # oldest_ancestors: 01, 09
    # families: 01, 02, 03, 04, 05, 06, 07
    #           09, 10, 11
    # family_endpoints: 07, 11
    #
    def __init__(self, *args, **kwargs):
        """Accept an IOS line number and initialize family relationship
        attributes"""
        super(IOSCfgLine, self).__init__(*args, **kwargs)

    @classmethod
    def is_object_for(cls, line="", re=re):
        ## Default object, for now
        return True
