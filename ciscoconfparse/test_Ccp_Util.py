#!/usr/bin/env python

from mock import Mock, patch
from copy import deepcopy
import unittest
import sys
import re
import os


from ccp_util import IPv4Obj, L4Object
try:
    if sys.version_info[0]<3:
        from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
    else:
        from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
except:
    sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), "local_py"))
    # re: modules usage... thank you Delnan
    # http://stackoverflow.com/a/5027393
    if (sys.version_info[0]<3) and \
        (bool(sys.modules.get('ipaddr', False)) is False):
        # Relative import path referenced to this directory
        from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
    elif (sys.version_info[0]==3) and \
        (bool(sys.modules.get('ipaddress', False)) is False):
        # Relative import path referenced to this directory
        from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address


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
        self.assertEqual(pp.port_list, range(25, 33))

    def testL4Object_asa_lt01(self):
        pp = L4Object(protocol='tcp', port_spec='lt echo', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, range(1, 7))

    def testL4Object_asa_lt02(self):
        pp = L4Object(protocol='tcp', port_spec='lt 7', syntax='asa')
        self.assertEqual(pp.protocol, 'tcp')
        self.assertEqual(pp.port_list, range(1, 7))

    def testIPv4Obj_contain(self):
        ## Test ccp_util.IPv4Obj.__contains__()
        ##
        ## Test whether a prefix is or is not contained in another prefix
        results_correct = [
            ('1.0.0.0/8', '0.0.0.0/0', True),    # Is 1.0.0.0/8 in 0.0.0.0/0?
            ('0.0.0.0/0', '1.0.0.0/8', False),   # Is 0.0.0.0/0 in 1.0.0.0/8?
            ('1.1.1.0/27', '1.0.0.0/8', True),   # Is 1.1.1.0/27 in 1.0.0.0/8?
            ('1.1.1.0/27', '9.9.9.9/32', False), # Is 1.1.1.0/27 in 9.9.9.9/32?
            ('9.9.9.0/27', '9.9.9.9/32', False), # Is 9.9.9.0/27 in 9.9.9.9/32?
        ]
        for prefix1, prefix2, result_correct in results_correct:
            ## 'foo in bar' tests bar.__contains__(foo)
            test_result = IPv4Obj(prefix1) in IPv4Obj(prefix2)
            self.assertEqual(test_result, result_correct)

    def testIPv4Obj_parse(self):
        ## Ensure that IPv4Obj can correctly parse various inputs
        test_strings = [
            '1.0.0.1/24',
            '1.0.0.1/32',
            '1.0.0.1   255.255.255.0',
            '1.0.0.1   255.255.255.255',
            '1.0.0.1 255.255.255.0',
            '1.0.0.1 255.255.255.255',
            '1.0.0.1/255.255.255.0',
            '1.0.0.1/255.255.255.255',
        ]
        for test_string in test_strings:
            test_result = IPv4Obj(test_string)
            self.assertTrue(isinstance(test_result, IPv4Obj))

    def testIPv4Obj_attributes(self):
        ## Ensure that attributes are accessible and pass the smell test
        test_object = IPv4Obj('1.0.0.1 255.255.255.0')
        results_correct = [
            ('ip',            IPv4Address('1.0.0.1')),
            ('netmask',       IPv4Address('255.255.255.0')),
            ('prefixlen',     24),
            ('broadcast',     IPv4Address('1.0.0.255')),
            ('network',       IPv4Network('1.0.0.0/24')),
            ('hostmask',      IPv4Address('0.0.0.255')),
            ('numhosts',      256),
            ('version',       4),
            ('is_reserved',   False),
            ('is_multicast',  False),
            ('is_private',    False),
            ('as_decimal',    16777217),
            ('as_hex_tuple', ('01', '00', '00', '01')),
            ('as_binary_tuple', ('00000001', '00000000', '00000000', '00000001')),
        ]
        for attribute, result_correct in results_correct:
            self.assertEqual(getattr(test_object, attribute), result_correct)

if __name__ == "__main__":
     unittest.main()
