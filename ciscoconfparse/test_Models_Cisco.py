#!/usr/bin/env python

from mock import Mock, patch
from copy import deepcopy
import unittest
import sys
import re
import os


from ciscoconfparse import CiscoConfParse
from ccp_util import IPv4Obj

class knownValues(unittest.TestCase):

    def setUp(self):
        """This method is called before all tests, initializing all variables"""

        self.c01 = [
            '!',
            'service timestamps debug datetime msec localtime show-timezone',
            'service timestamps log datetime msec localtime show-timezone',
            '!',
            'errdisable recovery cause bpduguard',
            'errdisable recovery interval 400',
            '!',
            'aaa new-model',
            '!',
            'ip vrf TEST_100_001',
            ' route-target 100:1',
            ' rd 100:1',
            '!',
            'interface Serial 1/0',
            ' description Uplink to SBC F923X2K425',
            ' bandwidth 1500',
            ' clock rate 1500',
            ' delay 70',
            ' encapsulation ppp',
            ' ip address 1.1.1.1 255.255.255.252',
            '!',
            'interface Serial 1/1',
            ' description Uplink to AT&T',
            ' encapsulation hdlc',
            ' ip address 1.1.1.9 255.255.255.254',
            ' hold-queue 1000 in',
            ' hold-queue 1000 out',
            ' mpls mtu 1540',
            ' ip mtu 1500',
            ' mpls ip',
            '!',
            'interface GigabitEthernet4/1',
            ' description',
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
            ' speed 100',
            ' duplex full',
            '!',
            'interface GigabitEthernet4/3',
            ' mtu 9216',
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
            ' switchport port-security',
            ' switchport port-security maximum 3',
            ' switchport port-security mac-address sticky',
            ' switchport port-security mac-address 1000.2000.3000',
            ' switchport port-security mac-address 1000.2000.3001',
            ' switchport port-security mac-address 1000.2000.3002',
            ' switchport port-security violation shutdown',
            '!',
            'interface GigabitEthernet4/6',
            ' description Simulate a Catalyst6500 access port',
            ' switchport',
            ' switchport access vlan 110',
            ' switchport mode access',
            ' switchport nonegotiate',
            ' switchport port-security',
            ' switchport port-security maximum 2',
            ' switchport port-security violation restrict',
            ' switchport port-security aging type inactivity',
            ' switchport port-security aging time 5',
            ' spanning-tree portfast',
            ' spanning-tree portfast bpduguard',
            ' storm-control action shutdown',
            ' storm-control broadcast level 0.40',
            ' storm-control multicast level 0.35',
            '!',
            'interface GigabitEthernet4/7',
            ' description Dot1Q trunk allowing vlans 2-4,7,10,11-19,21-4094',
            ' switchport',
            ' switchport trunk encapsulation dot1q',
            ' switchport mode trunk',
            ' switchport trunk native vlan 4094',
            ' switchport trunk allowed vlan remove 1,5-10,20',
            ' switchport trunk allowed vlan add 7,10',
            ' switchport nonegotiate',
            '!',
            'interface GigabitEthernet4/8.120',
            ' no switchport',
            ' encapsulation dot1q 120',
            ' ip vrf forwarding TEST_100_001',
            ' ip address 1.1.2.254 255.255.255.0',
            '!',
            'interface ATM5/0/0',
            ' no ip address',
            ' no ip redirects',
            ' no ip unreachables',
            ' no ip proxy-arp',
            ' load-interval 30',
            ' carrier-delay msec 100',
            ' no atm ilmi-keepalive',
            ' bundle-enable',
            ' max-reserved-bandwidth 100',
            ' hold-queue 500 in',
            '!',
            'interface ATM5/0/0.32 point-to-point',
            ' ip address 1.1.1.5 255.255.255.252',
            ' no ip redirects',
            ' no ip unreachables',
            ' no ip proxy-arp',
            ' ip accounting access-violations',
            ' pvc 0/32',
            '  vbr-nrt 704 704',
            '!',
            'interface ATM5/0/1',
            ' shutdown',
            '!',
            'router ospf 100 vrf TEST_100_001',
            ' router-id 1.1.2.254',
            ' network 1.1.2.0 0.0.0.255 area 0',
            '!',
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
            '!',
            'alias exec showthang show ip route vrf THANG',
            ]

    #--------------------------------

    def testVal_IOSCfgLine_is_intf(self):
        # Map a config line to result_correct
        result_map = {
            'interface Serial 1/0': True,
            'interface GigabitEthernet4/1': True,
            'interface GigabitEthernet4/8.120': True,
            'interface ATM5/0/0': True,
            'interface ATM5/0/0.32 point-to-point': True,
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.is_intf, result_correct)

    def testVal_IOSCfgLine_is_subintf(self):
        # Map a config line to result_correct
        result_map = {
            'interface Serial 1/0': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/8.120': True,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': True,
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.is_subintf, result_correct)

    def testVal_IOSCfgLine_is_loopback_intf(self):
        # Map a config line to result_correct
        result_map = {
            'interface Loopback 0': True,
            'interface Loopback1': True,
            'interface Serial 1/0': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.is_loopback_intf, result_correct)

    def testVal_IOSCfgLine_is_ethernet_intf(self):
        # Map a config line to result_correct
        result_map = {
            'interface Loopback 0': False,
            'interface Loopback1': False,
            'interface Serial 1/0': False,
            'interface Ethernet4/1': True,
            'interface Ethernet 4/1': True,
            'interface FastEthernet4/1': True,
            'interface FastEthernet 4/1': True,
            'interface GigabitEthernet4/1': True,
            'interface GigabitEthernet 4/1': True,
            'interface GigabitEthernet4/8.120': True,
            'interface GigabitEthernet 4/8.120': True,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.is_ethernet_intf, result_correct)

    def testVal_IOSIntfLine_name(self):
        # Map a config line to result_correct
        result_map = {
            'interface Loopback 0': "Loopback 0",
            'interface Loopback1': "Loopback1",
            'interface Serial 1/0': "Serial 1/0",
            'interface Ethernet4/1': "Ethernet4/1",
            'interface Ethernet 4/1': "Ethernet 4/1",
            'interface FastEthernet4/1': "FastEthernet4/1",
            'interface FastEthernet 4/1': "FastEthernet 4/1",
            'interface GigabitEthernet4/1': "GigabitEthernet4/1",
            'interface GigabitEthernet 4/1': "GigabitEthernet 4/1",
            'interface GigabitEthernet4/8.120': "GigabitEthernet4/8.120",
            'interface GigabitEthernet 4/8.120': "GigabitEthernet 4/8.120",
            'interface ATM5/0/0': "ATM5/0/0",
            'interface ATM5/0/0.32 point-to-point': "ATM5/0/0.32",
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.name, result_correct)

    def testVal_IOSIntfLine_ordinal_list(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': (1, 0),
            'interface Serial 1/1': (1, 1),
            'interface GigabitEthernet4/1': (4, 1),
            'interface GigabitEthernet4/2': (4, 2),
            'interface GigabitEthernet4/3': (4, 3),
            'interface GigabitEthernet4/4': (4, 4),
            'interface GigabitEthernet4/5': (4, 5),
            'interface GigabitEthernet4/6': (4, 6),
            'interface GigabitEthernet4/7': (4, 7),
            'interface GigabitEthernet4/8.120': (4, 8),
            'interface ATM5/0/0': (5, 0, 0),
            'interface ATM5/0/0.32 point-to-point': (5, 0, 0),
            'interface ATM5/0/1': (5, 0, 1),
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ordinal_list
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ordinal_list
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_port(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 1,
            'interface GigabitEthernet4/1': 1,
            'interface GigabitEthernet4/2': 2,
            'interface GigabitEthernet4/3': 3,
            'interface GigabitEthernet4/4': 4,
            'interface GigabitEthernet4/5': 5,
            'interface GigabitEthernet4/6': 6,
            'interface GigabitEthernet4/7': 7,
            'interface GigabitEthernet4/8.120': 8,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 1,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check port number
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.port
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_port_type(self):
        # Map a config line to result_correct
        result_map = {
            'interface Loopback 0': "Loopback",
            'interface Loopback1': "Loopback",
            'interface Serial 1/0': "Serial",
            'interface Ethernet4/1': "Ethernet",
            'interface Ethernet 4/1': "Ethernet",
            'interface FastEthernet4/1': "FastEthernet",
            'interface FastEthernet 4/1': "FastEthernet",
            'interface GigabitEthernet4/1': "GigabitEthernet",
            'interface GigabitEthernet 4/1': "GigabitEthernet",
            'interface GigabitEthernet4/8.120': "GigabitEthernet",
            'interface GigabitEthernet 4/8.120': "GigabitEthernet",
            'interface ATM5/0/0': "ATM",
            'interface ATM5/0/0.32 point-to-point': "ATM",
        }
        for cfgline, result_correct in result_map.items():
            cfg = CiscoConfParse([cfgline], factory=True)
            obj = cfg.ConfigObjs[0]
            self.assertEqual(obj.port_type, result_correct)

    def testVal_IOSIntfLine_description(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': "Uplink to SBC F923X2K425",
            'interface Serial 1/1': "Uplink to AT&T",
            'interface GigabitEthernet4/1': '',
            'interface GigabitEthernet4/2': '',
            'interface GigabitEthernet4/3': '',
            'interface GigabitEthernet4/4': '',
            'interface GigabitEthernet4/5': '',
            'interface GigabitEthernet4/6': 'Simulate a Catalyst6500 access port',
            'interface GigabitEthernet4/7': 'Dot1Q trunk allowing vlans 2-4,7,10,11-19,21-4094',
            'interface GigabitEthernet4/8.120': '',
            'interface ATM5/0/0': '',
            'interface ATM5/0/0.32 point-to-point': '',
            'interface ATM5/0/1': '',
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check description
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.description
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_bandwidth(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 1500,
            'interface Serial 1/1': 0,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check bandwidth
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_bandwidth
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_delay(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 70,
            'interface Serial 1/1': 0,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check delay
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_delay
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_holdqueue_in(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 1000,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 500,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check holdqueue in
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_holdqueue_in
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_holdqueue_out(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 1000,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check holdqueue out
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_holdqueue_out
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_encapsulation(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 'ppp',
            'interface Serial 1/1': 'hdlc',
            'interface GigabitEthernet4/1': '',
            'interface GigabitEthernet4/2': '',
            'interface GigabitEthernet4/3': '',
            'interface GigabitEthernet4/4': '',
            'interface GigabitEthernet4/5': '',
            'interface GigabitEthernet4/6': '',
            'interface GigabitEthernet4/7': '',
            'interface GigabitEthernet4/8.120': 'dot1q',
            'interface ATM5/0/0': '',
            'interface ATM5/0/0.32 point-to-point': '',
            'interface ATM5/0/1': '',
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check encapsulation
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_encapsulation
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_mpls(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': True,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_mpls
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_mpls
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_ipv4_addr_object(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': IPv4Obj('1.1.1.1/30', strict=False),
            'interface Serial 1/1': IPv4Obj('1.1.1.9/31', strict=False),
            'interface GigabitEthernet4/1': IPv4Obj('127.0.0.1/32', 
                strict=False),
            'interface GigabitEthernet4/2': IPv4Obj('127.0.0.1/32', 
                strict=False),
            'interface GigabitEthernet4/3': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/4': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/5': IPv4Obj('127.0.0.1/32', 
                strict=False),
            'interface GigabitEthernet4/6': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/7': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/8.120': IPv4Obj('1.1.2.254/24', 
                strict=False),
            'interface ATM5/0/0': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface ATM5/0/0.32 point-to-point': IPv4Obj('1.1.1.5/30',
                strict=False),
            'interface ATM5/0/1': IPv4Obj('127.0.0.1/32', strict=False),
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ipv4_addr_object
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ipv4_addr_object
        self.maxDiff=None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_ipv4_network_object(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': IPv4Obj('1.1.1.0/30', strict=False),
            'interface Serial 1/1': IPv4Obj('1.1.1.8/31', strict=False),
            'interface GigabitEthernet4/1': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/2': IPv4Obj('127.0.0.1/32', 
                strict=False),
            'interface GigabitEthernet4/3': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/4': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/5': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/6': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/7': IPv4Obj('127.0.0.1/32',
                strict=False),
            'interface GigabitEthernet4/8.120': IPv4Obj('1.1.2.0/24',
                strict=False),
            'interface ATM5/0/0': IPv4Obj('127.0.0.1/32', strict=False),
            'interface ATM5/0/0.32 point-to-point': IPv4Obj('1.1.1.4/30',
                strict=False),
            'interface ATM5/0/1': IPv4Obj('127.0.0.1/32', strict=False),
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ipv4_network_object
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ipv4_network_object
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_autonegotiation(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': True,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': True,
            'interface GigabitEthernet4/4': True,
            'interface GigabitEthernet4/5': True,
            'interface GigabitEthernet4/6': True,
            'interface GigabitEthernet4/7': True,
            'interface GigabitEthernet4/8.120': True,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_autonegotiation
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_autonegotiation
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_manual_speed(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': True,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_manual_speed
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_manual_speed
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_manual_duplex(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': True,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_manual_duplex
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_manual_duplex
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_manual_carrierdelay(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': True,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_manual_carrierdelay
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_manual_carrierdelay
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_carrierdelay(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0.0,
            'interface Serial 1/1': 0.0,
            'interface GigabitEthernet4/1': 0.0,
            'interface GigabitEthernet4/2': 0.0,
            'interface GigabitEthernet4/3': 0.0,
            'interface GigabitEthernet4/4': 0.0,
            'interface GigabitEthernet4/5': 0.0,
            'interface GigabitEthernet4/6': 0.0,
            'interface GigabitEthernet4/7': 0.0,
            'interface GigabitEthernet4/8.120': 0.0,
            'interface ATM5/0/0': 0.1,
            'interface ATM5/0/0.32 point-to-point': 0.0,
            'interface ATM5/0/1': 0.0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check manual_carrierdelay
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_carrierdelay
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_clock_rate(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 1500,
            'interface Serial 1/1': 0,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check manual_clock_rate
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_clock_rate
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_mtu(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 0,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 9216,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check manual_mtu
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_mtu
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_mpls_mtu(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 1540,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check manual_mpls_mtu
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_mpls_mtu
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_manual_ip_mtu(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 0,
            'interface Serial 1/1': 1500,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 0,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 0,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check manual_ip_mtu
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.manual_ip_mtu
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_is_shutdown(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': True,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': False,
            'interface ATM5/0/1': True,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check is_shutdown
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.is_shutdown
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_vrf(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': '',
            'interface Serial 1/1': '',
            'interface GigabitEthernet4/1': '',
            'interface GigabitEthernet4/2': '', 
            'interface GigabitEthernet4/3': '',
            'interface GigabitEthernet4/4': '',
            'interface GigabitEthernet4/5': '',
            'interface GigabitEthernet4/6': '',
            'interface GigabitEthernet4/7': '',
            'interface GigabitEthernet4/8.120': 'TEST_100_001',
            'interface ATM5/0/0': '',
            'interface ATM5/0/0.32 point-to-point': '',
            'interface ATM5/0/1': '',
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check vrf
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.vrf
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_ipv4_addr(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': '1.1.1.1',
            'interface Serial 1/1': '1.1.1.9',
            'interface GigabitEthernet4/1': '',
            'interface GigabitEthernet4/2': '',
            'interface GigabitEthernet4/3': '',
            'interface GigabitEthernet4/4': '',
            'interface GigabitEthernet4/5': '',
            'interface GigabitEthernet4/6': '',
            'interface GigabitEthernet4/7': '',
            'interface GigabitEthernet4/8.120': '1.1.2.254',
            'interface ATM5/0/0': '',
            'interface ATM5/0/0.32 point-to-point': '1.1.1.5',
            'interface ATM5/0/1': '',
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ipv4_addr
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ipv4_addr
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_ipv4_netmask(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': '255.255.255.252',
            'interface Serial 1/1': '255.255.255.254',
            'interface GigabitEthernet4/1': '',
            'interface GigabitEthernet4/2': '',
            'interface GigabitEthernet4/3': '',
            'interface GigabitEthernet4/4': '',
            'interface GigabitEthernet4/5': '',
            'interface GigabitEthernet4/6': '',
            'interface GigabitEthernet4/7': '',
            'interface GigabitEthernet4/8.120': '255.255.255.0',
            'interface ATM5/0/0': '',
            'interface ATM5/0/0.32 point-to-point': '255.255.255.252',
            'interface ATM5/0/1': '',
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ipv4_netmask
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ipv4_netmask
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_ipv4_masklength(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': 30,
            'interface Serial 1/1': 31,
            'interface GigabitEthernet4/1': 0,
            'interface GigabitEthernet4/2': 0,
            'interface GigabitEthernet4/3': 0,
            'interface GigabitEthernet4/4': 0,
            'interface GigabitEthernet4/5': 0,
            'interface GigabitEthernet4/6': 0,
            'interface GigabitEthernet4/7': 0,
            'interface GigabitEthernet4/8.120': 24,
            'interface ATM5/0/0': 0,
            'interface ATM5/0/0.32 point-to-point': 30,
            'interface ATM5/0/1': 0,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check ipv4_masklength
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.ipv4_masklength
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_in_ipv4_subnet(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': True,
            'interface Serial 1/1': True,
            'interface GigabitEthernet4/1': None,
            'interface GigabitEthernet4/2': None,
            'interface GigabitEthernet4/3': None,
            'interface GigabitEthernet4/4': None,
            'interface GigabitEthernet4/5': None,
            'interface GigabitEthernet4/6': None,
            'interface GigabitEthernet4/7': None,
            'interface GigabitEthernet4/8.120': True,
            'interface ATM5/0/0': None,
            'interface ATM5/0/0.32 point-to-point': True,
            'interface ATM5/0/1': None,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check in_ipv4_subnet
        ##   where the subnet is 1.1.0.0/22
        test_network = IPv4Obj('1.1.0.0/22', strict=False)
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.in_ipv4_subnet(test_network)
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_in_ipv4_subnets(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': True,
            'interface Serial 1/1': True,
            'interface GigabitEthernet4/1': None,
            'interface GigabitEthernet4/2': None,
            'interface GigabitEthernet4/3': None,
            'interface GigabitEthernet4/4': None,
            'interface GigabitEthernet4/5': None,
            'interface GigabitEthernet4/6': None,
            'interface GigabitEthernet4/7': None,
            'interface GigabitEthernet4/8.120': True,
            'interface ATM5/0/0': None,
            'interface ATM5/0/0.32 point-to-point': True,
            'interface ATM5/0/1': None,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check in_ipv4_subnets
        test_network1 = IPv4Obj('1.1.0.0/23', strict=False)
        test_network2 = IPv4Obj('1.1.2.0/23', strict=False)
        networks = set([test_network1, test_network2])
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.in_ipv4_subnets(networks)
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_no_icmp_unreachables(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': True,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_no_icmp_unreachables
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_no_icmp_unreachables
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_no_icmp_redirects(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': True,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_no_icmp_redirects
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_no_icmp_redirects
        self.maxDiff = None
        self.assertEqual(result_correct, test_result)

    def testVal_IOSIntfLine_has_no_ip_proxyarp(self):
        cfg = CiscoConfParse(self.c01, factory=True)
        result_correct = {
            'interface Serial 1/0': False,
            'interface Serial 1/1': False,
            'interface GigabitEthernet4/1': False,
            'interface GigabitEthernet4/2': False,
            'interface GigabitEthernet4/3': False,
            'interface GigabitEthernet4/4': False,
            'interface GigabitEthernet4/5': False,
            'interface GigabitEthernet4/6': False,
            'interface GigabitEthernet4/7': False,
            'interface GigabitEthernet4/8.120': False,
            'interface ATM5/0/0': False,
            'interface ATM5/0/0.32 point-to-point': True,
            'interface ATM5/0/1': False,
        }
        test_result = dict()
        ## Parse all interface objects in self.c01 and check has_no_ip_proxyarp
        for intf_obj in cfg.find_objects('^interface'):
            test_result[intf_obj.text] = intf_obj.has_no_ip_proxyarp
        self.assertEqual(result_correct, test_result)

###
### ------ AAA Tests --------
###

    def testVal_IOSAaaLoginAuthenticationLine(self):
        line = 'aaa authentication login default group tacacs+ local-case'
        cfg = CiscoConfParse([line], factory=True)
        obj = cfg.ConfigObjs[0]
        self.assertEqual('tacacs+', obj.group)
        self.assertEqual('default', obj.list_name)
        self.assertEqual(['local-case'], obj.methods)

    def testVal_IOSAaaEnableAuthenticationLine(self):
        line = 'aaa authentication enable default group tacacs+ enable'
        cfg = CiscoConfParse([line], factory=True)
        obj = cfg.ConfigObjs[0]
        self.assertEqual('tacacs+', obj.group)
        self.assertEqual('default', obj.list_name)
        self.assertEqual(['enable'], obj.methods)

    def testVal_IOSAaaCommandsAuthorizationLine(self):
        line = 'aaa authorization commands 15 default group tacacs+ local'
        cfg = CiscoConfParse([line], factory=True)
        obj = cfg.ConfigObjs[0]
        self.assertEqual(15, obj.level)
        self.assertEqual('tacacs+', obj.group)
        self.assertEqual('default', obj.list_name)
        self.assertEqual(['local'], obj.methods)

    def testVal_IOSAaaCommandsAccountingLine(self):
        line = 'aaa accounting commands 15 default start-stop group tacacs+'
        cfg = CiscoConfParse([line], factory=True)
        obj = cfg.ConfigObjs[0]
        self.assertEqual(15, obj.level)
        self.assertEqual('tacacs+', obj.group)
        self.assertEqual('default', obj.list_name)
        self.assertEqual('start-stop', obj.record_type)

    def testVal_IOSAaaExecAccountingLine(self):
        line = 'aaa accounting exec default start-stop group tacacs+'
        cfg = CiscoConfParse([line], factory=True)
        obj = cfg.ConfigObjs[0]
        self.assertEqual('tacacs+', obj.group)
        self.assertEqual('default', obj.list_name)
        self.assertEqual('start-stop', obj.record_type)

    def testVal_IOSAaaGroupServerLine(self):
        lines = ['!',
            'aaa group server tacacs+ TACACS_01',
            ' server-private 192.0.2.10 key cisco',
            ' server-private 192.0.2.11 key cisco',
            ' ip vrf forwarding VRF_001',
            ' ip tacacs source-interface FastEthernet0/48',
            '!',
        ]
        cfg = CiscoConfParse(lines, factory=True)
        obj = cfg.ConfigObjs[1]
        self.assertEqual('TACACS_01', obj.group)
        self.assertEqual('tacacs+', obj.protocol)
        self.assertEqual(set(['192.0.2.10', '192.0.2.11']), obj.server_private)
        self.assertEqual('VRF_001', obj.vrf)
        self.assertEqual('FastEthernet0/48', obj.source_interface)


if __name__ == "__main__":
     unittest.main()
