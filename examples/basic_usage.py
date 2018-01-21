#!/usr/bin/env python
from ciscoconfparse import CiscoConfParse

CONFIG = """!
interface Serial 1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
interface GigabitEthernet4/1
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
interface GigabitEthernet4/2
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
interface GigabitEthernet4/3
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 shutdown
!"""


parse = CiscoConfParse(CONFIG.splitlines())

# Return a list of all interfaces
intfs = parse.find_objects("^interface")

# Return a list of all interfaces with ppp encap
ppp_intfs = parse.find_objects_w_child( "^interf", "encapsulation ppp")

# Return a list of all active interfaces (i.e. not shutdown)
active_intfs = parse.find_objects_wo_child( "^interf", "shutdown" )
for obj in active_intfs:
    print "OBJ", obj
    print "  CONFIG:", obj.text

