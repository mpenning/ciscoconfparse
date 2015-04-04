#!/usr/bin/env python

import sys
import re
import os
THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))

from ccp_util import _RGX_IPV4ADDR, _RGX_IPV6ADDR
from ccp_util import IPv4Obj, L4Object
import pytest

if sys.version_info[0]<3:
    from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
else:
    from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address


@pytest.mark.parametrize("addr", [
        '192.0.2.1',
        '4.2.2.2',
        '10.255.255.255',
        '127.0.0.1',
    ])
def test_IPv4_REGEX(addr):
    test_result = _RGX_IPV4ADDR.search(addr)
    assert test_result.group('addr')==addr

@pytest.mark.parametrize("addr", [
        'fe80::',                                  # Trailing double colons
        'fe80:beef::',                             # Trailing double colons
        'fe80:dead:beef::',                        # Trailing double colons
        'fe80:a:dead:beef::',                      # Trailing double colons
        'fe80:a:a:dead:beef::',                    # Trailing double colons
        'fe80:a:a:a:dead:beef::',                  # Trailing double colons
        'fe80:a:a:a:a:dead:beef::',                # Trailing double colons
        'fe80:dead:beef::a',                       #
        'fe80:dead:beef::a:b',                     #
        'fe80:dead:beef::a:b:c',                   #
        'fe80:dead:beef::a:b:c:d',                 #
        'FE80:AAAA::DEAD:BEEF',                    # Capital letters
        'FE80:AAAA:0000:0000:0000:0000:DEAD:BEEF', # Capital Letters
        '0:0:0:0:0:0:0:1',                         # Loopback
        '::1',                           # Loopback, leading double-colons
    ])
def test_IPv6_REGEX(addr):
    test_result = _RGX_IPV6ADDR.search(addr)
    assert test_result.group('addr')==addr

@pytest.mark.parametrize("addr", [
        'fe80:',                        # Single trailing colon
        'fe80:beef',                    # Insufficient number of bytes
        'fe80:dead:beef',               # Insufficient number of bytes
        'fe80:a:dead:beef',             # Insufficient number of bytes
        'fe80:a:a:dead:beef',           # Insufficient number of bytes
        'fe80:a:a:a:dead:beef',         # Insufficient number of bytes
        'fe80:a:a:a:a:dead:beef',       # Insufficient number of bytes
        'fe80:a:a:a :a:dead:beef',      # Superflous space
        'zzzz:a:a:a:a:a:dead:beef',     # bad characters
        '0:0:0:0:0:0:1',                # Loopback, insufficient bytes
        '0:0:0:0:0:1',                  # Loopback, insufficient bytes
        '0:0:0:0:1',                    # Loopback, insufficient bytes
        '0:0:0:1',                      # Loopback, insufficient bytes
        '0:0:1',                        # Loopback, insufficient bytes
        '0:1',                          # Loopback, insufficient bytes
        ':1',                           # Loopback, insufficient bytes
        # FIXME: The following *should* fail, but I'm not failing on them
        #':::beef',                     # FAIL Too many leading colons
        #'fe80::dead::beef',            # FAIL multiple double colons
        #'::1::',                       # FAIL too many double colons
        #'fe80:0:0:0:0:0:dead:beef::',  # FAIL Too many bytes with double colons
    ])
def test_negative_IPv6_REGEX(addr):
    test_result = _RGX_IPV6ADDR.search(addr)
    assert test_result is None    # The regex *should* fail on these addrs

@pytest.mark.xfail(sys.version_info[0]==3 and sys.version_info[1]==2,
                   reason="Known failure in Python3.2")
def testL4Object_asa_eq01():
    pp = L4Object(protocol='tcp', port_spec='eq smtp', syntax='asa')
    assert pp.protocol=='tcp'
    assert pp.port_list==[25]

def testL4Object_asa_eq02():
    pp = L4Object(protocol='tcp', port_spec='smtp', syntax='asa')
    assert pp.protocol=='tcp'
    assert pp.port_list==[25]

@pytest.mark.xfail(sys.version_info[0]==3 and sys.version_info[1]==2,
                   reason="Known failure in Python3.2 due to range()")
def testL4Object_asa_range01():
    pp = L4Object(protocol='tcp', port_spec='range smtp 32', syntax='asa')
    assert pp.protocol=='tcp'
    assert pp.port_list==range(25, 33)

@pytest.mark.xfail(sys.version_info[0]==3 and sys.version_info[1]==2,
                   reason="Known failure in Python3.2 due to range()")
def testL4Object_asa_lt01():
    pp = L4Object(protocol='tcp', port_spec='lt echo', syntax='asa')
    assert pp.protocol=='tcp'
    assert pp.port_list==range(1, 7)

@pytest.mark.xfail(sys.version_info[0]==3 and sys.version_info[1]==2,
                   reason="Known failure in Python3.2 due to range()")
def testL4Object_asa_lt02():
    pp = L4Object(protocol='tcp', port_spec='lt 7', syntax='asa')
    assert pp.protocol=='tcp'
    assert pp.port_list==range(1, 7)

def testIPv4Obj_contain():
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
        assert test_result==result_correct

def testIPv4Obj_parse():
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
        assert isinstance(test_result, IPv4Obj)

def testIPv4Obj_attributes():
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
        assert getattr(test_object, attribute)==result_correct
