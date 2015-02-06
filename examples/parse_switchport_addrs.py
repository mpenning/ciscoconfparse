from operator import methodcaller
import re

from ciscoconfparse import CiscoConfParse

def vlan_intf_dict(parse):
    """Return an integer vlan number to IP address string mapping"""
    retval = dict()
    VLAN_RE = re.compile(r'^interface\sVlan\s*(\d+)')
    for obj in parse.find_objects(VLAN_RE):
        vlan = obj.re_match_typed(VLAN_RE, result_type=int, default=-1)
        addr = obj.re_match_iter_typed(r'^\s+ip\s+address\s+(\S.+)$')
        retval[vlan] = addr
    return retval

def switchport_vlans(parse):
    """Return string interface name to list of vlans (as well as whether"""
    """ the port is in access or trunk mode)"""
    retval = dict()  # Interface name to list of vlans
    access = dict()  # Interface name to boolean for "access port"
    INTF_RE = re.compile(r'^interface\s(\S+?Ethernet\s*\S+)$')
    for obj in parse.find_objects(INTF_RE):
        vlans_access = obj.re_match_iter_typed(r'^\s+switchport\saccess\svlan\s(\S+)', default='')
        vlans_trunk = obj.re_match_iter_typed(r'^\s+switchport\strunk\sallowed\svlan\s(\S+)', default='')
        vlans_str = vlans_access or vlans_trunk
        try:
            vlans = map(int, map(methodcaller('strip'), vlans_str.split(','))) # NOTE: this intentionally fails on 1,3-11,15
            intf = obj.re_match_typed(INTF_RE)
            retval[intf] = vlans
            access[intf] = bool(vlans_access)
        except Exception, e:
            raise ValueError("FATAL error while parsing switchport vlans on {0}: {1}".format(obj, e))
    return retval, access

CONFIG = """!
!
interface GigabitEthernet 0/1
 switchport mode access
 switchport access vlan 20
!
interface GigabitEthernet 0/2
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk allowed vlan 12,16
!
interface Vlan12
 ip address 10.0.12.1 255.255.255.0
 no ip proxy-arp
!
interface Vlan16
 ip address 10.0.16.1 255.255.255.0
 no ip proxy-arp
!
interface Vlan20
 ip address 10.0.20.1 255.255.255.0
 no ip proxy-arp
!
"""

## Note, I don't pretend that this will be useful, it's a conceptual demo
##
## OUTPUT:
##
## GigabitEthernet 0/1     10.0.20.1 255.255.255.0
## GigabitEthernet 0/2.12     10.0.12.1 255.255.255.0
## GigabitEthernet 0/2.16     10.0.16.1 255.255.255.0

parse = CiscoConfParse(CONFIG.splitlines())
vlans = vlan_intf_dict(parse)
intfs, access = switchport_vlans(parse)

for intf in sorted(intfs):
    vlan_list = intfs.get(intf)
    for vlan in vlan_list:
        addr = vlans.get(vlan, 'ERROR')
        if access.get(intf, False):
            print("{0}     {1}".format(intf, addr))
        else:
            print("{0}.{1}     {2}".format(intf, vlan, addr))
