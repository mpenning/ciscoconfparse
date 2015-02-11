#!/usr/bin/env python

from operator import attrgetter
from itertools import repeat
from mock import Mock, patch
from copy import deepcopy
import unittest
import sys
import re
import os


from models_cisco import IOSCfgLine, IOSIntfLine
from ciscoconfparse import CiscoConfParse
from ccp_util import IPv4Obj

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

        self.c01_default_gigabitethernets = [
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
            'default interface GigabitEthernet4/1',
            'interface GigabitEthernet4/1',
            ' switchport',
            ' switchport access vlan 100',
            ' switchport voice vlan 150',
            ' power inline static max 7000',
            '!',
            'default interface GigabitEthernet4/2',
            'interface GigabitEthernet4/2',
            ' switchport',
            ' switchport access vlan 100',
            ' switchport voice vlan 150',
            ' power inline static max 7000',
            '!',
            'default interface GigabitEthernet4/3',
            'interface GigabitEthernet4/3',
            ' switchport',
            ' switchport access vlan 100',
            ' switchport voice vlan 150',
            '!',
            'default interface GigabitEthernet4/4',
            'interface GigabitEthernet4/4',
            ' shutdown',
            '!',
            'default interface GigabitEthernet4/5',
            'interface GigabitEthernet4/5',
            ' switchport',
            ' switchport access vlan 110',
            '!',
            'default interface GigabitEthernet4/6',
            'interface GigabitEthernet4/6',
            ' switchport',
            ' switchport access vlan 110',
            '!',
            'default interface GigabitEthernet4/7',
            'interface GigabitEthernet4/7',
            ' switchport',
            ' switchport access vlan 110',
            '!',
            'default interface GigabitEthernet4/8',
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

        self.c01_insert_serial_replace = [
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
            'default interface Serial 2/0',
            'interface Serial 2/0',
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

        self.c01_banner = [
            '!',
            'interface GigabitEthernet4/8',
            ' switchport',
            ' switchport access vlan 110',
            '!',
            'banner login ^C'
            'This is a router, and you cannot have it.',
            'Log off now while you still can type. I break the fingers',
            'of all tresspassers.',
            '^C',
            '!',
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

        tmp = [
              ('interface Serial 1/0', 11),
              ('interface GigabitEthernet4/1', 15),
              ('interface GigabitEthernet4/2', 21),
              ('interface GigabitEthernet4/3', 27),
              ('interface GigabitEthernet4/4', 32),
              ('interface GigabitEthernet4/5', 35),
              ('interface GigabitEthernet4/6', 39),
              ('interface GigabitEthernet4/7', 43),
              ('interface GigabitEthernet4/8', 47),
              ]
        self.c01_find_objects = list()
        for line, linenum in tmp:
            # Mock up the correct object
            obj = IOSCfgLine()
            obj.text = line
            obj.linenum = linenum
            self.c01_find_objects.append(obj)

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

        self.c04 = [
            '!',
            'interface Serial1/0',
            ' encapsulation ppp',
            ' ip address 1.1.1.1 255.255.255.252',
            ' no ip proxy-arp',
            '!',
            'interface Serial1/1',
            ' encapsulation ppp',
            ' ip address 1.1.1.5 255.255.255.252',
            '!',
            ]

        ##--------------------------------
        # Keep tuples of test parameters below the line
        #
        #    Format: (config, args, result_correct)
        #       config    : the configuration to test
        #       args      : the arguments to pass to the function
        #       result_correct: passing value
        

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

    def testValues_banner_child_parsing_01(self):
        """Associate banner lines as parent / child"""
        cfg = CiscoConfParse(self.c01_banner)
        parent_intf = {
            # Line 6's parent should be 5, etc...
            6: 5,
            7: 5,
            8: 5,
        }
        for obj in cfg.find_objects(''):
            result_correct = parent_intf.get(obj.linenum, False)
            if result_correct:
                test_result = obj.parent.linenum
                ## Does this object parent's line number match?
                self.assertEqual(result_correct, test_result)

    def testValues_parent_child_parsing_01(self):
        cfg = CiscoConfParse(self.c01)
        parent_intf = {
            # Line 13's parent should be 11, etc...
            13: 11,
            16: 15,
            17: 15,
            18: 15,
            19: 15,
            22: 21,
            23: 21,
            24: 21,
            25: 21,
        }
        for obj in cfg.find_objects(''):
            result_correct = parent_intf.get(obj.linenum, False)
            if result_correct:
                test_result = obj.parent.linenum
                ## Does this object parent's line number match?
                self.assertEqual(result_correct, test_result)

    def testValues_parent_child_parsing_02(self):
        cfg = CiscoConfParse(self.c01)
        # Expected child / parent line numbers before the insert
        parent_intf_before = {
            # Line 11 is Serial1/0, child is line 13
            13: 11,
            # Line 15 is GigabitEthernet4/1
            16: 15,
            17: 15,
            18: 15,
            19: 15,
            # Line 21 is GigabitEthernet4/2
            22: 21,
            23: 21,
            24: 21,
            25: 21,
        }
        # Expected child / parent line numbers after the insert

        # Validate line numbers *before* inserting
        for obj in cfg.find_objects(''):
            result_correct = parent_intf_before.get(obj.linenum, False)
            if result_correct:
                test_result = obj.parent.linenum
                ## Does this object parent's line number match?
                self.assertEqual(result_correct, test_result)

        # Insert lines here...
        for intf_obj in cfg.find_objects('^interface\sGigabitEthernet'):
            # Configured with an access vlan...
            if ' switchport access vlan 100' in set(map(attrgetter('text'), intf_obj.children)):
                intf_obj.insert_after(' spanning-tree portfast')
        cfg.atomic()

        parent_intf_after = {
            # Line 11 is Serial1/0, child is line 13
            13: 11,
            # Line 15 is GigabitEthernet4/1
            16: 15,
            17: 15,
            18: 15,
            19: 15,
            # Line 22 is GigabitEthernet4/2
            23: 22,
            24: 22,
            25: 22,
            26: 22,
        }
        # Validate line numbers *after* inserting
        for obj in cfg.find_objects(''):
            result_correct = parent_intf_after.get(obj.linenum, False)
            if result_correct:
                test_result = obj.parent.linenum
                ## Does this object parent's line number match?
                self.assertEqual(result_correct, test_result)

    def testValues_find_lines(self):
        for config, args, result_correct in self.find_lines_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.find_lines(**args)
            self.assertEqual(result_correct, test_result)


    def testValues_find_children(self):
        ## test find_chidren
        for config, args, result_correct in self.find_children_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.find_children(**args)
            self.assertEqual(result_correct, test_result)


    def testValues_find_all_children01(self):
        ## test find_all_chidren
        for config, args, result_correct in self.find_all_children_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.find_all_children(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_find_all_chidren02(self):
        CONFIG = ['thing1',
            ' foo',
            '  bar',
            '   100',
            '   200',
            '   300',
            '   400',
            'thing2',]
        RESULT_CORRECT = ['thing1',
            ' foo',
            '  bar',
            '   100',
            '   200',
            '   300',
            '   400',]
        cfg = CiscoConfParse(CONFIG)
        test_result = cfg.find_all_children('^thing1')
        self.assertEqual(RESULT_CORRECT, test_result)


    def testValues_find_parents_w_child(self):
        ## test find_parents_w_child
        for config, args, result_correct in self.find_parents_w_child_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.find_parents_w_child(**args)
            self.assertEqual(result_correct, test_result)


    def testValues_find_parents_wo_child(self):
        ## test find_parents_wo_child
        for config, args, result_correct in self.find_parents_wo_child_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.find_parents_wo_child(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_find_children_w_parents(self):
        ## test find_children_w_parents
        for config, args, result_correct in self.find_children_w_parents_Values:
            cfg = CiscoConfParse(config )
            test_result = cfg.find_children_w_parents(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_replace_lines_01(self):
        # We have to parse multiple times because of replacements
        for config, args, result_correct in self.replace_lines_Values01:
            cfg = CiscoConfParse(config)
            test_result = cfg.replace_lines(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_replace_lines_02(self):
        for config, args, result_correct in self.replace_lines_Values02:
            cfg = CiscoConfParse(config)
            test_result = cfg.replace_lines(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_replace_lines_03(self):
        for config, args, result_correct in self.replace_lines_Values03:
            cfg = CiscoConfParse(config)
            test_result = cfg.replace_lines(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_replace_children_01(self):
        # We have to parse multiple times because of replacements
        for config, args, result_correct in self.replace_children_Values:
            cfg = CiscoConfParse(config)
            test_result = cfg.replace_children(**args)
            self.assertEqual(result_correct, test_result)

    def testValues_req_cfgspec_excl_diff(self):
        ## test req_cfgspec_excl_diff
        result_correct = self.c01_req_excl_logging
        cfg = CiscoConfParse(self.c01)
        test_result = cfg.req_cfgspec_excl_diff(
            "^logging\s+",
            "logging\s+\d+\.\d+\.\d+\.\d+",
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual(result_correct, test_result)

    def testValues_req_cfgspec_all_diff(self):
        ## test req_cfgspec_all_diff
        result_correct = self.c01_req_all_logging
        cfg = CiscoConfParse(self.c01)
        test_result = cfg.req_cfgspec_all_diff(
            [
            'logging 1.1.3.4',
            'logging 1.1.3.5',
            'logging 1.1.3.6',
            ]
            )
        self.assertEqual(result_correct, test_result)


    def testValues_ignore_ws(self):
        ## test find_lines with ignore_ws flag
        result_correct = self.c03
        cfg = CiscoConfParse(self.c03)
        test_result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            ignore_ws = True
            )
        self.assertEqual(result_correct, test_result)

    def testValues_negative_ignore_ws(self):
        ## test find_lines WITHOUT ignore_ws
        result_correct = []
        cfg = CiscoConfParse(self.c03)
        test_result = cfg.find_lines(
            'set snmp community read-only myreadonlystring',
            )
        self.assertEqual(result_correct, test_result)

    def testValues_IOSCfgLine_all_parents(self):
        """Ensure IOSCfgLine.all_parents finds all parents, recursively"""
        result_correct = list()
        with patch('__main__.IOSCfgLine') as mock:
            vals = [('policy-map QOS_1', 0), (' class SILVER', 4)]
            # the mock pretends to be an IOSCfgLine so we can test against it
            for idx, fakeobj in enumerate(map(deepcopy, repeat(mock, len(vals)))):
                fakeobj.text = vals[idx][0]
                fakeobj.linenum = vals[idx][1]
                fakeobj.classname = "IOSCfgLine"
                result_correct.append(fakeobj)

        cfg = CiscoConfParse(self.c01)
        obj = cfg.find_objects('bandwidth 30')[0]
        ## Removed _find_parent_OBJ on 20140202
        #test_result = cfg._find_parent_OBJ(obj)
        test_result = obj.all_parents
        for idx, testobj in enumerate(test_result):
            self.assertEqual(result_correct[idx].text, test_result[idx].text)
            self.assertEqual(result_correct[idx].linenum, 
                test_result[idx].linenum)
            self.assertEqual(result_correct[idx].classname, 
                test_result[idx].classname)

    def testValues_find_objects(self):
        ## test whether find_objects returns correct IOSCfgLine objects
        result_correct = self.c01_find_objects
        cfg = CiscoConfParse(self.c01)
        test_result = cfg.find_objects('^interface')
        self.assertEqual(result_correct, test_result)

    def testValues_find_objects_replace_01(self):
        """test whether find_objects we can correctly replace object values using native IOSCfgLine object methods"""
        config01 = ['!',
            'boot system flash slot0:c2600-adventerprisek9-mz.124-21a.bin',
            'boot system flash bootflash:c2600-adventerprisek9-mz.124-21a.bin',
            '!',
            'interface Ethernet0/0',
            ' ip address 172.16.1.253 255.255.255.0',
            '!',
            'ip route 0.0.0.0 0.0.0.0 172.16.1.254',
            '!',
            'end',
            ]
        result_correct = ['!',
            '! old boot image flash slot0:c2600-adventerprisek9-mz.124-21a.bin',
            '! old boot image flash bootflash:c2600-adventerprisek9-mz.124-21a.bin',
            '!',
            'interface Ethernet0/0',
            ' ip address 172.16.1.253 255.255.255.0',
            '!',
            'ip route 0.0.0.0 0.0.0.0 172.16.1.254',
            '!',
            'end',
            ]
        cfg = CiscoConfParse(config01)
        for obj in cfg.find_objects('boot system'):
            obj.replace('boot system', '! old boot image')
        test_result = cfg.ioscfg
        self.assertEqual(result_correct, test_result)

    def testValues_find_objects_delete_01(self):
        """Test whether IOSCfgLine.delete() recurses through children correctly"""
        result_correct = ['!', '!', '!']
        cfg = CiscoConfParse(self.c04)
        for intf in cfg.find_objects(r'^interface'):
            intf.delete(recurse=True)  # recurse=True is the default
        test_result = cfg.ioscfg
        self.assertEqual(result_correct, test_result)


    def testValues_insert_after_atomic_01(self):
        """We expect insert_after(atomic=True) to correctly parse children"""
        ## See also -> testValues_insert_after_nonatomic_02()
        result_correct = [
            'interface GigabitEthernet4/1', 
            ' shutdown',
            ' switchport', 
            ' switchport access vlan 100', 
            ' switchport voice vlan 150', 
            ' power inline static max 7000',
            ]
        linespec = 'interface GigabitEthernet4/1'
        cfg = CiscoConfParse(self.c01, factory=False)
        cfg.insert_after(linespec, ' shutdown', exactmatch=True, atomic=True)
        test_result = cfg.find_children(linespec)

        self.assertEqual(result_correct, test_result)

    def testValues_insert_after_atomic_factory_01(self):
        """Ensure that comments which are added, assert is_comment"""
        with patch('__main__.IOSCfgLine') as mock:
            # the mock pretends to be an IOSCfgLine so we can test against it
            result_correct01 = mock
            result_correct01.linenum = 16
            result_correct01.text = ' ! TODO: some note to self'
            result_correct01.classname = 'IOSCfgLine'
            result_correct01.is_comment = True

        result_correct02 = [
            'interface GigabitEthernet4/1', 
            ' ! TODO: some note to self',
            ' switchport', 
            ' switchport access vlan 100', 
            ' switchport voice vlan 150', 
            ' power inline static max 7000',
            ]
        linespec = 'interface GigabitEthernet4/1'
        cfg = CiscoConfParse(self.c01, factory=True)
        cfg.insert_after(linespec, ' ! TODO: some note to self', 
            exactmatch=True, atomic=True)

        test_result01 = cfg.find_objects('TODO')[0]
        self.assertEqual(result_correct01.linenum, test_result01.linenum)
        self.assertEqual(result_correct01.text, test_result01.text)
        self.assertEqual(result_correct01.classname, test_result01.classname)
        self.assertEqual(result_correct01.is_comment, test_result01.is_comment)

        # FIXME: this fails... maybe because I don't parse comments as children correctly???
        test_result02 = cfg.find_children(linespec)
        self.assertEqual(result_correct02, test_result02)

    def testValues_insert_after_nonatomic_01(self):
        inputs = ['interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]
        cfg = CiscoConfParse(self.c01, factory=False)
        for idx, linespec in enumerate(inputs):
            test_result = cfg.insert_after(linespec, ' shutdown',
                exactmatch=True, atomic=False)
            result_correct = [inputs[idx]]
            self.assertEqual(result_correct, test_result)

    def testValues_insert_after_nonatomic_02(self):
        """Negative test.  We expect insert_after(atomic=False) to miss any children added like this at some point in the future I might fix insert_after so it knows how to correctly parse children"""
        result_correct = ['interface GigabitEthernet4/1', 
            #' shutdown',   <--- Intentionally commented out
            ' switchport', 
            ' switchport access vlan 100', 
            ' switchport voice vlan 150', 
            ' power inline static max 7000',
            ]
        linespec = 'interface GigabitEthernet4/1'
        cfg = CiscoConfParse(self.c01, factory=False)
        cfg.insert_after(linespec, ' shutdown', exactmatch=True, atomic=False)
        test_result = cfg.find_children(linespec)

        self.assertEqual(result_correct, test_result)


    def testValues_insert_before_nonatomic_01(self):
        inputs = ['interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]
        cfg = CiscoConfParse(self.c01, factory=False)
        for idx, linespec in enumerate(inputs):
            test_result = cfg.insert_before(linespec, 'default '+linespec, 
                exactmatch=True, atomic=False)
            result_correct = [inputs[idx]]
            self.assertEqual(result_correct, test_result)

    def testValues_insert_before_atomic_01(self):
        inputs = ['interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]
        cfg = CiscoConfParse(self.c01, factory=False)
        for idx, linespec in enumerate(inputs):
            test_result = cfg.insert_before(linespec, 'default '+linespec, 
                exactmatch=True, atomic=True)
            result_correct = [inputs[idx]]
            self.assertEqual(result_correct, test_result)

    def testValues_renumbering_insert_before_nonatomic_01(self):
        """Ensure we renumber lines after insert_before(atomic=False)"""
        inputs = ['interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]
        cfg = CiscoConfParse(self.c01, factory=False)
        for idx, linespec in enumerate(inputs):
            cfg.insert_before(linespec, 'default '+linespec, 
                exactmatch=True, atomic=False)
        test_result = cfg.ioscfg
        result_correct = self.c01_default_gigabitethernets
        self.assertEqual(result_correct, test_result)

    def testValues_renumbering_insert_before_atomic_01(self):
        """Ensure we renumber lines after insert_before(atomic=True)"""
        inputs = ['interface GigabitEthernet4/1',
            'interface GigabitEthernet4/2',
            'interface GigabitEthernet4/3',
            'interface GigabitEthernet4/4',
            'interface GigabitEthernet4/5',
            'interface GigabitEthernet4/6',
            'interface GigabitEthernet4/7',
            'interface GigabitEthernet4/8',
            ]
        cfg = CiscoConfParse(self.c01, factory=False)
        for idx, linespec in enumerate(inputs):
            cfg.insert_before(linespec, 'default '+linespec, 
                exactmatch=True, atomic=True)
        test_result = cfg.ioscfg
        result_correct = self.c01_default_gigabitethernets
        self.assertEqual(result_correct, test_result)

    def testValues_find_objects_factory_01(self):
        """Test whether find_objects returns the correct objects"""
        with patch('__main__.IOSIntfLine') as mock:
            vals = [('interface GigabitEthernet4/1', 15),
                ('interface GigabitEthernet4/2', 21),
                ('interface GigabitEthernet4/3', 27),
                ('interface GigabitEthernet4/4', 32),
                ('interface GigabitEthernet4/5', 35),
                ('interface GigabitEthernet4/6', 39),
                ('interface GigabitEthernet4/7', 43),
                ('interface GigabitEthernet4/8', 47),
                ]
            ## Build fake IOSIntfLine objects to validate unit tests...
            result_correct = list()
            # deepcopy a unique mock for every val with itertools.repeat()
            mockobjs = map(deepcopy, repeat(mock, len(vals)))
            # mock pretends to be an IOSCfgLine so we can test against it
            for idx, obj in enumerate(mockobjs):
                obj.text     = vals[idx][0]  # Check the text
                obj.linenum  = vals[idx][1]  # Check the line numbers
                # append the fake IOSIntfLine object to result_correct
                result_correct.append(obj)

            cfg = CiscoConfParse(self.c01, factory=True)
            test_result = cfg.find_objects('^interface GigabitEther')
            for idx, test_result_object in enumerate(test_result):
                # Check line numbers
                self.assertEqual(result_correct[idx].linenum, 
                    test_result_object.linenum)
                # Check text
                self.assertEqual(result_correct[idx].text, 
                    test_result_object.text)

    def testValues_IOSIntfLine_find_objects_factory_01(self):
        """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
        with patch('__main__.IOSIntfLine') as mock:
            # the mock pretends to be an IOSCfgLine so we can test against it
            result_correct = mock
            result_correct.linenum = 11
            result_correct.text = 'interface Serial 1/0'
            result_correct.classname = 'IOSIntfLine'
            result_correct.ipv4_addr_object = IPv4Obj('1.1.1.1/30', 
                strict=False)

            cfg = CiscoConfParse(self.c01, factory=True)
            # this test finds the IOSIntfLine instance for 'Serial 1/0'
            test_result = cfg.find_objects('^interface Serial 1/0')[0]

            self.assertEqual(result_correct.linenum,   test_result.linenum)
            self.assertEqual(result_correct.text,      test_result.text)
            self.assertEqual(result_correct.classname, test_result.classname)
            self.assertEqual(result_correct.ipv4_addr_object, 
                test_result.ipv4_addr_object)

    def testValues_IOSIntfLine_find_objects_factory_02(self):
        """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
        with patch('__main__.IOSIntfLine') as mock:
            # the mock pretends to be an IOSCfgLine so we can test against it
            result_correct01 = mock
            result_correct01.linenum = 12
            result_correct01.text = 'interface Serial 2/0'
            result_correct01.classname = 'IOSIntfLine'
            result_correct01.ipv4_addr_object = IPv4Obj('1.1.1.1/30', 
                strict=False)

            result_correct02 = self.c01_insert_serial_replace

            cfg = CiscoConfParse(self.c01, factory=True)
            # Insert a line above the IOSIntfLine object
            cfg.insert_before('interface Serial 1/0', 'default interface Serial 1/0')
            # Replace text in the IOSIntfLine object
            cfg.replace_lines('interface Serial 1/0', 'interface Serial 2/0', exactmatch=False)

            test_result01 = cfg.find_objects('^interface Serial 2/0')[0]
            test_result02 = cfg.ioscfg

            # Check attributes of the IOSIntfLine object
            self.assertEqual(result_correct01.linenum,   test_result01.linenum)
            self.assertEqual(result_correct01.text,      test_result01.text)
            self.assertEqual(result_correct01.classname, test_result01.classname)
            self.assertEqual(result_correct01.ipv4_addr_object, 
                test_result01.ipv4_addr_object)

            # Ensure the text configs are exactly what we wanted
            self.assertEqual(result_correct02, test_result02)


if __name__ == "__main__":
     unittest.main()
