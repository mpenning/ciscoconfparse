#!/usr/bin/env python

from ciscoconfparse import *
import unittest

class knownValues(unittest.TestCase):

    c01 = [
    'policy-map QOS_1',
    ' class GOLD',
    '  priority percent 10',
    ' !',
    ' class SILVER',
    '  bandwidth 30',
    '  random-detect',
    ' !',
    ' class BRONZE',
    '  random-detect',
    '!',
    'interface Serial 1/0',
    ' encapsulation ppp',
    ' ip address 1.1.1.1 255.255.255.252',
    '!',
    'interface GigabitEthernet4/1',
    ' switchport',
    ' switchport access vlan 100',
    ' switchport voice vlan 150',
    ' power inline static max 7000',
    '!',
    'interface GigabitEthernet4/2',
    ' switchport',
    ' switchport access vlan 100',
    ' switchport voice vlan 150',
    ' power inline static max 7000',
    '!',
    'interface GigabitEthernet4/3',
    ' switchport',
    ' switchport access vlan 100',
    ' switchport voice vlan 150',
    '!',
    'interface GigabitEthernet4/4',
    ' shutdown',
    '!',
    'interface GigabitEthernet4/5',
    ' switchport',
    ' switchport access vlan 110',
    '!',
    'interface GigabitEthernet4/6',
    ' switchport',
    ' switchport access vlan 110',
    '!',
    'interface GigabitEthernet4/7',
    ' switchport',
    ' switchport access vlan 110',
    '!',
    'interface GigabitEthernet4/8',
    ' switchport',
    ' switchport access vlan 110',
    '!',
    'access-list 101 deny tcp any any eq 25 log',
    'access-list 101 permit ip any any',
    '!',
    '!',
    'logging 1.1.3.5',
    'logging 1.1.3.17',
    '!',
    'banner login ^C'
    'This is a router, and you cannot have it.',
    'Log off now while you still can type. I break the fingers',
    'of all tresspassers.',
    '^C',
    'alias exec showthang show ip route vrf THANG',
    ]

    c01_intf = [
    'interface Serial 1/0',
    ]

    c01_pmap_children = [
    'policy-map QOS_1',
    ' class GOLD',
    ' class SILVER',
    ' class BRONZE',
    ]

    c01_pmap_all_children = [
    'policy-map QOS_1',
    ' class GOLD',
    '  priority percent 10',
    ' class SILVER',
    '  bandwidth 30',
    '  random-detect',
    ' class BRONZE',
    '  random-detect',
    ]


    c01_parents_w_child_power = [
    'interface GigabitEthernet4/1',
    'interface GigabitEthernet4/2',
    ]


    c01_parents_w_child_voice = [
    'interface GigabitEthernet4/1',
    'interface GigabitEthernet4/2',
    'interface GigabitEthernet4/3',
    ]

    c01_parents_wo_child_power = [
    'interface GigabitEthernet4/3',
    'interface GigabitEthernet4/4',
    'interface GigabitEthernet4/5',
    'interface GigabitEthernet4/6',
    'interface GigabitEthernet4/7',
    'interface GigabitEthernet4/8',
    ]


    c01_req_excl_logging = [
    'no logging 1.1.3.17',
    'logging 1.1.3.4',
    'logging 1.1.3.6',
    ]

    c01_req_all_logging = [
    'logging 1.1.3.4',
    'logging 1.1.3.6',
    ]

    c02 = [
    'interface Serial1/0',
    ' encapsulation ppp',
    ' ip address 1.1.1.1 255.255.255.252',
    ]

    c02_encap = [
    ' encapsulation ppp',
    ]

    c03 = [
    'set snmp community read-only     myreadonlystring'
    ]

    #--------------------------------

    find_lines_Values = (
    ( c02, [ "encapsulation", False ], c02_encap ),
    ( c01, [ "interface Serial 1/0", False], c01_intf ),
    ( c01, [ "interface Serial1/0", True], [] ),
    )

    find_children_Values = (
    ( c01, [ "policy-map", False ], c01_pmap_children ),
    ( c01, [ "policy-map", True ], [] ),
    )

    find_all_children_Values = (
    ( c01, [ "policy-map", False ], c01_pmap_all_children ),
    ( c01, [ "policy-map", True ], [] ),
    )

    find_parents_w_child_Values = (
    ( c01, [ "interf", "power inline" ], c01_parents_w_child_power ),
    ( c01, [ "interf", " switchport voice" ], c01_parents_w_child_voice ),
    ( c01, [ "^interface$", "switchport voice" ], [] ),
    )

    find_parents_wo_child_Values = (
    ( c01, [ "interface Gig", "power inline" ], c01_parents_wo_child_power ),
    )

    #--------------------------------

    def testValues_find_lines(self):
        for config, args, resultGood in self.find_lines_Values:
            cfg = CiscoConfParse( config )
            result = cfg.find_lines( args[0], args[1] )
            self.assertEqual( resultGood, result )


    def testValues_find_children(self):
        ## test find_chidren
        for config, args, resultGood in self.find_children_Values:
            cfg = CiscoConfParse( config )
            result = cfg.find_children( args[0], args[1] )
            self.assertEqual( resultGood, result )


    def testValues_find_all_children(self):
        ## test find_all_chidren
        for config, args, resultGood in self.find_all_children_Values:
            cfg = CiscoConfParse( config )
            result = cfg.find_all_children( args[0], args[1] )
            self.assertEqual( resultGood, result )


    def testValues_find_parents_w_child(self):
        ## test find_parents_w_child
        for config, args, resultGood in self.find_parents_w_child_Values:
            cfg = CiscoConfParse( config )
            result = cfg.find_parents_w_child( args[0], args[1] )
            self.assertEqual( resultGood, result )


    def testValues_find_parents_wo_child(self):
        ## test find_parents_wo_child
        for config, args, resultGood in self.find_parents_wo_child_Values:
            cfg = CiscoConfParse( config )
            result = cfg.find_parents_wo_child( args[0], args[1] )
            self.assertEqual( resultGood, result )

    def testValues_req_cfgspec_excl_diff(self):
        ## test req_cfgspec_excl_diff
        resultGood = self.c01_req_excl_logging
        cfg = CiscoConfParse( self.c01 )
        result = cfg.req_cfgspec_excl_diff(
             "^logging\s+",
             "logging\s+\d+\.\d+\.\d+\.\d+",
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual( resultGood, result )


    def testValues_req_cfgspec_all_diff(self):
        ## test req_cfgspec_all_diff
        resultGood = self.c01_req_all_logging
        cfg = CiscoConfParse( self.c01 )
        result = cfg.req_cfgspec_all_diff(
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual( resultGood, result )


    def testValues_ignore_ws(self):
        ## test find_lines with ignore_ws flag
        resultGood = self.c03
        cfg = CiscoConfParse( self.c03 )
        result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            ignore_ws = True
            )
        self.assertEqual( resultGood, result )

    def testValues_negative_ignore_ws(self):
        ## test find_lines WITHOUT ignore_ws
        resultGood = []
        cfg = CiscoConfParse( self.c03 )
        result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            )
        self.assertEqual( resultGood, result )

if __name__ == "__main__":
     unittest.main()
