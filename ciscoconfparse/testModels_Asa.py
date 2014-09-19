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
            'hostname TEST-FW',
            '!',
            'name 1.1.2.20 loghost01',
            'name 1.1.3.10 dmzsrv00',
            'name 1.1.3.11 dmzsrv01',
            'name 1.1.3.12 dmzsrv02',
            'name 1.1.3.13 dmzsrv03',
            '!',
            'interface Ethernet0/0',
            ' description Uplink to SBC F923X2K425',
            ' nameif OUTSIDE',
            ' security-level 0',
            ' delay 70',
            ' ip address 1.1.1.1 255.255.255.252',
            '!',
            'interface Ethernet0/1',
            ' nameif INSIDE',
            ' security-level 100',
            ' ip address 1.1.2.1 255.255.255.0',
            '!',
            'interface Ethernet0/2',
            ' switchport access vlan 100',
            '!',
            'interface VLAN100',
            ' nameif DMZ',
            ' security-level 50',
            ' ip address 1.1.3.1 255.255.255.0',
            '!',
            'object-group network ANY_addrs',
            ' network-object 0.0.0.0 0.0.0.0',
            '!',
            'object-group network INSIDE_addrs',
            ' network-object 1.1.2.0 255.255.255.0',
            '!',
            'object-group service DNS_svc',
            ' service-object udp destination eq dns',
            '!',
            'object-group service NTP_svc',
            ' service-object udp destination eq ntp',
            '!',
            'object-group service FTP_svc',
            ' service-object tcp destination eq ftp',
            '!',
            'object-group service HTTP_svc',
            ' service-object tcp destination eq http',
            '!',
            'object-group service HTTPS_svc',
            ' service-object tcp destination eq https',
            '!',
            'access-list INSIDE_in extended permit object-group FTP_svc object-group INSIDE_addrs object-group ANY_addrs log',
            'access-list INSIDE_in extended deny ip any any log',
            '!',
            '!',
            'clock timezone CST -6',
            'clock summer-time CDT recurring',
            '!',
            'logging enable',
            'logging timestamp',
            'logging buffer-size 1048576',
            'logging buffered informational',
            'logging trap informational',
            'logging asdm informational',
            'logging facility 22',
            'logging host INSIDE loghost01',
            'no logging message 302021',
            '!',
            'banner login ^C'
            'This is a router, and you cannot have it.',
            'Log off now while you still can type. I break the fingers',
            'of all tresspassers.',
            '^C',
            '!',
            'access-group OUTSIDE_in in interface OUTSIDE',
            'access-group INSIDE_in in interface INSIDE',
            '!',
            ]

    #--------------------------------

    def testVal_Names(self):
        cfg = CiscoConfParse(self.c01, factory=False, syntax='asa')
        cfg_factory = CiscoConfParse(self.c01, factory=True, syntax='asa')
        result_correct = {'dmzsrv00': '1.1.3.10', 
            'dmzsrv01': '1.1.3.11', 
            'dmzsrv02': '1.1.3.12', 
            'dmzsrv03': '1.1.3.13', 
            'loghost01': '1.1.2.20',
        }
        self.assertEqual(cfg.ConfigObjs.names, result_correct)
        self.assertEqual(cfg_factory.ConfigObjs.names, result_correct)


if __name__ == "__main__":
     unittest.main()
