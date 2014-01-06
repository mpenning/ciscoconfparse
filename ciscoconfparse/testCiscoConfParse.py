#!/usr/bin/env python

from ciscoconfparse import *
import unittest
import re

class knownValues(unittest.TestCase):

    def setUp(self):
        """This method is called before all tests, initializing all variables"""
        self.c01 = [
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

        self.c01_intf = [
            'interface Serial 1/0',
            ]

        self.c01_pmap_children = [
            'policy-map QOS_1',
            ' class GOLD',
            ' class SILVER',
            ' class BRONZE',
            ]

        self.c01_pmap_all_children = [
            'policy-map QOS_1',
            ' class GOLD',
            '  priority percent 10',
            ' class SILVER',
            '  bandwidth 30',
            '  random-detect',
            ' class BRONZE',
            '  random-detect',
            ]

        self.c01_find_gige_no_exactmatch = [
            'interface GigabitEthernet4/1', 
            'interface GigabitEthernet4/2', 
            'interface GigabitEthernet4/3', 
            'interface GigabitEthernet4/4', 
            'interface GigabitEthernet4/5', 
            'interface GigabitEthernet4/6', 
            'interface GigabitEthernet4/7', 
            'interface GigabitEthernet4/8']

        self.c01_intf_no_exactmatch = [
            'interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            ]


        self.c01_parents_w_child_power = [
            'interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            ]


        self.c01_parents_w_child_voice = [
            'interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            ]

        self.c01_parents_wo_child_power = [
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]

        self.c01_replace_gige_no_exactmatch = [
            'interface GigabitEthernet8/1', 
            'interface GigabitEthernet8/2', 
            'interface GigabitEthernet8/3', 
            'interface GigabitEthernet8/4', 
            'interface GigabitEthernet8/5', 
            'interface GigabitEthernet8/6', 
            'interface GigabitEthernet8/7', 
            'interface GigabitEthernet8/8']

        self.c01_replace_gige_exclude = [
            'interface GigabitEthernet8/1', 
            'interface GigabitEthernet8/2', 
            'interface GigabitEthernet8/3', 
            'interface GigabitEthernet8/7', 
            'interface GigabitEthernet8/8']


        self.c01_children_w_parents_switchport = [
            ' switchport',
            ' switchport access vlan 100',
            ' switchport voice vlan 150',
            ]

        self.c01_replace_children = [
            ' power inline static max 30000', 
            ' power inline static max 30000'
            ]

        self.c01_req_excl_logging = [
            'no logging 1.1.3.17',
            'logging 1.1.3.4',
            'logging 1.1.3.6',
            ]

        self.c01_req_all_logging = [
            'logging 1.1.3.4',
            'logging 1.1.3.6',
            ]

        self.c02 = [
            'interface Serial1/0',
            ' encapsulation ppp',
            ' ip address 1.1.1.1 255.255.255.252',
            ]

        # Expected result from one of the unit tests
        self.c02_encap = [
            ' encapsulation ppp',
            ]

        self.c03 = [
            'set snmp community read-only     myreadonlystring'
            ]

        ##--------------------------------
        # Keep tuples of test parameters below the line
        #
        #    Format: (config, args, resultGood)
        #       config    : the configuration to test
        #       args      : the arguments to pass to the function
        #       resultGood: passing value
        

        self.find_lines_Values = (
            # Ensure exact matches work regardless of the exactmatch boolean
            (self.c01, {'linespec': "interface Serial 1/0", 
                'exactmatch': False}, self.c01_intf),
            (self.c01, {'linespec': "interface Serial 1/0", 
                'exactmatch': True}, self.c01_intf),
            # Ensure we can find string matches inside an interface config block
            (self.c02, {'linespec': "encapsulation", 
                'exactmatch': False}, self.c02_encap),
            # Ensure exactmatch=False catches beginning phrases in the config
            (self.c01, {'linespec': "interface GigabitEthernet4/", 
                'exactmatch': False}, self.c01_find_gige_no_exactmatch),
            # Ensure exactmatch=False catches single words in the config
            (self.c01, {'linespec': "igabitEthernet", 
                'exactmatch': False}, self.c01_find_gige_no_exactmatch),
            # Negative test: matches are Case-Sensitive
            (self.c01, {'linespec': "GigaBitEtherNeT", 
                'exactmatch': False}, []),
            # Negative test for exactmatch=True
            (self.c01, {'linespec': "interface GigabitEthernet4/", 
                'exactmatch': True}, []),
            # Negative test for exactmatch=True and ignore_ws=False
            (self.c01, {'linespec': "interface Serial1/0", 
                'exactmatch': True, 'ignore_ws': False}, []),
        )

        self.find_children_Values = (
            (self.c01, {'linespec': "policy-map", 'exactmatch': False}, 
                self.c01_pmap_children),
            (self.c01, {'linespec': "policy-map", 'exactmatch': True}, []),
        )

        self.find_all_children_Values = (
            (self.c01, {'linespec': "policy-map", 'exactmatch': False}, 
                self.c01_pmap_all_children),
            (self.c01, {'linespec': "policy-map", 'exactmatch': True}, []),
        )

        self.find_parents_w_child_Values = (
            (self.c01, {'parentspec': "interf", 'childspec': "power inline"}, 
                self.c01_parents_w_child_power),
        (self.c01, {'parentspec': "interf", 'childspec': " switchport voice"}, 
                self.c01_parents_w_child_voice),
        (self.c01, {'parentspec': "^interface$", 
                'childspec': "switchport voice"}, 
                []),
        )

        self.find_parents_wo_child_Values = (
            (self.c01, {'parentspec': "interface Gig", 
                'childspec': "power inline"}, 
                self.c01_parents_wo_child_power),
        )

        self.find_children_w_parents_Values = (
            (self.c01, {'parentspec': "^interface GigabitEthernet4/1", 
                'childspec': "switchport"}, 
                self.c01_children_w_parents_switchport),
        )

        self.replace_lines_Values01 = (
            # Ensure basic replacements work
            (self.c01, {'linespec': r"interface Serial 1/0", 
                'replacestr': "interface Serial 2/0"}, 
                ['interface Serial 2/0']),
            # Ensure we make multiple replacements as required
            (self.c01, {'linespec': "GigabitEthernet4/", 
                'replacestr': "GigabitEthernet8/", 'exactmatch': False}, 
                self.c01_replace_gige_no_exactmatch),
        )

        self.replace_lines_Values02 = (
            # Ensure exactmatch rejects substrings
            (self.c01, {'linespec': "interface Serial 1/", 
                'replacestr': "interface Serial 2/", 'exactmatch': True}, 
                []),
            # Ensure we exclude lines to be replaced
            (self.c01, {'linespec': "GigabitEthernet4/", 
                'excludespec': r'/4|/5|/6', 
                'replacestr': "GigabitEthernet8/", 'exactmatch': False}, 
                self.c01_replace_gige_exclude),
        )

        self.replace_lines_Values03 = (
        # Ensure we can use a compiled regexp in excludespec...
            (self.c01, {'linespec': "GigabitEthernet4/", 
                'excludespec': re.compile(r'/4|/5|/6'), 
                'replacestr': "GigabitEthernet8/", 'exactmatch': False}, 
                self.c01_replace_gige_exclude),
        )

        self.replace_children_Values = (
        # Ensure we can use a compiled regexp in excludespec...
            (self.c01, {'parentspec': "GigabitEthernet4/", 
                'childspec': 'max 7000',
                'excludespec': re.compile(r'/4|/5|/6'), 
                'replacestr': "max 30000", 'exactmatch': False}, 
                self.c01_replace_children),
        )

    #--------------------------------

    def testValues_find_lines(self):
        for config, args, resultGood in self.find_lines_Values:
            cfg = CiscoConfParse(config)
            result = cfg.find_lines(**args)
            self.assertEqual(resultGood, result)


    def testValues_find_children(self):
        ## test find_chidren
        for config, args, resultGood in self.find_children_Values:
            cfg = CiscoConfParse(config)
            result = cfg.find_children(**args)
            self.assertEqual(resultGood, result)


    def testValues_find_all_children(self):
        ## test find_all_chidren
        for config, args, resultGood in self.find_all_children_Values:
            cfg = CiscoConfParse(config)
            result = cfg.find_all_children(**args)
            self.assertEqual(resultGood, result)


    def testValues_find_parents_w_child(self):
        ## test find_parents_w_child
        for config, args, resultGood in self.find_parents_w_child_Values:
            cfg = CiscoConfParse(config)
            result = cfg.find_parents_w_child(**args)
            self.assertEqual(resultGood, result)


    def testValues_find_parents_wo_child(self):
        ## test find_parents_wo_child
        for config, args, resultGood in self.find_parents_wo_child_Values:
            cfg = CiscoConfParse(config)
            result = cfg.find_parents_wo_child(**args)
            self.assertEqual(resultGood, result)

    def testValues_find_children_w_parents(self):
        ## test find_children_w_parents
        for config, args, resultGood in self.find_children_w_parents_Values:
            cfg = CiscoConfParse(config )
            result = cfg.find_children_w_parents(**args)
            self.assertEqual(resultGood, result)

    def testValues01_replace_lines(self):
        # We have to parse multiple times because of replacements
        for config, args, resultGood in self.replace_lines_Values01:
            cfg = CiscoConfParse(config)
            result = cfg.replace_lines(**args)
            self.assertEqual(resultGood, result)

    def testValues02_replace_lines(self):
        for config, args, resultGood in self.replace_lines_Values02:
            cfg = CiscoConfParse(config)
            result = cfg.replace_lines(**args)
            self.assertEqual(resultGood, result)

    def testValues03_replace_lines(self):
        for config, args, resultGood in self.replace_lines_Values03:
            cfg = CiscoConfParse(config)
            result = cfg.replace_lines(**args)
            self.assertEqual(resultGood, result)

    def testValues01_replace_children(self):
        # We have to parse multiple times because of replacements
        for config, args, resultGood in self.replace_children_Values:
            cfg = CiscoConfParse(config)
            result = cfg.replace_children(**args)
            self.assertEqual(resultGood, result)

    def testValues_req_cfgspec_excl_diff(self):
        ## test req_cfgspec_excl_diff
        resultGood = self.c01_req_excl_logging
        cfg = CiscoConfParse(self.c01)
        result = cfg.req_cfgspec_excl_diff(
            "^logging\s+",
            "logging\s+\d+\.\d+\.\d+\.\d+",
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual(resultGood, result)

    def testValues_req_cfgspec_all_diff(self):
        ## test req_cfgspec_all_diff
        resultGood = self.c01_req_all_logging
        cfg = CiscoConfParse(self.c01)
        result = cfg.req_cfgspec_all_diff(
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual(resultGood, result)


    def testValues_ignore_ws(self):
        ## test find_lines with ignore_ws flag
        resultGood = self.c03
        cfg = CiscoConfParse(self.c03)
        result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            ignore_ws = True
            )
        self.assertEqual(resultGood, result)

    def testValues_negative_ignore_ws(self):
        ## test find_lines WITHOUT ignore_ws
        resultGood = []
        cfg = CiscoConfParse(self.c03)
        result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            )
        self.assertEqual(resultGood, result)

if __name__ == "__main__":
     unittest.main()
