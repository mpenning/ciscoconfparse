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
            'logging host INSIDE host01',
            'no logging message 302021',
            '!',
            'banner login ^C'
            'This is a router, and you cannot have it.',
            'Log off now while you still can type. I break the fingers',
            'of all tresspassers.',
            '^C',
            '!',
            ]

    #--------------------------------

    def testVal_parse(self):
        cfg = CiscoConfParse(self.c01, factory=True, syntax='asa')
        self.assertEqual(True, True)


if __name__ == "__main__":
     unittest.main()
