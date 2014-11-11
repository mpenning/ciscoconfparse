#!/usr/bin/env python

from mock import Mock, patch
from copy import deepcopy
import unittest
import sys
import re
import os


from ccp_util import IPv4Obj, L4Object

class knownValues(unittest.TestCase):

    def setUp(self):
        """This method is called before all tests, initializing all variables"""
        pass
    #--------------------------------

    def testL4Object_asa_eq01(self):
        pp = L4Object(protocol='tcp', port_spec='eq smtp', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, [25])

    def testL4Object_asa_eq02(self):
        pp = L4Object(protocol='tcp', port_spec='smtp', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, [25])

    def testL4Object_asa_range01(self):
        pp = L4Object(protocol='tcp', port_spec='range smtp 32', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, [25, 26, 27, 28, 29, 30, 31, 32])

    def testL4Object_asa_lt01(self):
        pp = L4Object(protocol='tcp', port_spec='lt echo', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, [1, 2, 3, 4, 5, 6])

    def testL4Object_asa_lt02(self):
        pp = L4Object(protocol='tcp', port_spec='lt 7', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, [1, 2, 3, 4, 5, 6])


if __name__ == "__main__":
     unittest.main()
