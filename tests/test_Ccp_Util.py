#!/usr/bin/env python

import sys
import re
import os

sys.path.insert(0, "..")

from ciscoconfparse.ccp_util import _RGX_IPV4ADDR, _RGX_IPV6ADDR
from ciscoconfparse.ccp_util import IPv4Obj, L4Object
from ciscoconfparse.ccp_util import CiscoRange
from ciscoconfparse.ccp_util import IPv6Obj
from ciscoconfparse.ccp_util import dns_lookup, reverse_dns_lookup
import pytest

if sys.version_info[0] < 3:
    from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
else:
    from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address


@pytest.mark.parametrize(
    "addr", ["192.0.2.1", "4.2.2.2", "10.255.255.255", "127.0.0.1",]
)
def test_IPv4_REGEX(addr):
    test_result = _RGX_IPV4ADDR.search(addr)
    assert test_result.group("addr") == addr


@pytest.mark.parametrize(
    "addr",
    [
        "fe80::",  # Trailing double colons
        "fe80:beef::",  # Trailing double colons
        "fe80:dead:beef::",  # Trailing double colons
        "fe80:a:dead:beef::",  # Trailing double colons
        "fe80:a:a:dead:beef::",  # Trailing double colons
        "fe80:a:a:a:dead:beef::",  # Trailing double colons
        "fe80:a:a:a:a:dead:beef::",  # Trailing double colons
        "fe80:dead:beef::a",  #
        "fe80:dead:beef::a:b",  #
        "fe80:dead:beef::a:b:c",  #
        "fe80:dead:beef::a:b:c:d",  #
        "FE80:AAAA::DEAD:BEEF",  # Capital letters
        "FE80:AAAA:0000:0000:0000:0000:DEAD:BEEF",  # Capital Letters
        "0:0:0:0:0:0:0:1",  # Loopback
        "::1",  # Loopback, leading double-colons
        "::",  # Shorthand for 0:0:0:0:0:0:0:0
    ],
)
def test_IPv6_REGEX(addr):
    test_result = _RGX_IPV6ADDR.search(addr)
    assert test_result.group("addr") == addr


@pytest.mark.parametrize(
    "addr",
    [
        "fe80:",  # Single trailing colon
        "fe80:beef",  # Insufficient number of bytes
        "fe80:dead:beef",  # Insufficient number of bytes
        "fe80:a:dead:beef",  # Insufficient number of bytes
        "fe80:a:a:dead:beef",  # Insufficient number of bytes
        "fe80:a:a:a:dead:beef",  # Insufficient number of bytes
        "fe80:a:a:a:a:dead:beef",  # Insufficient number of bytes
        "fe80:a:a:a :a:dead:beef",  # Superflous space
        "zzzz:a:a:a:a:a:dead:beef",  # bad characters
        "0:0:0:0:0:0:1",  # Loopback, insufficient bytes
        "0:0:0:0:0:1",  # Loopback, insufficient bytes
        "0:0:0:0:1",  # Loopback, insufficient bytes
        "0:0:0:1",  # Loopback, insufficient bytes
        "0:0:1",  # Loopback, insufficient bytes
        "0:1",  # Loopback, insufficient bytes
        ":1",  # Loopback, insufficient bytes
        # FIXME: The following *should* fail, but I'm not failing on them
        #':::beef',                     # FAIL Too many leading colons
        #'fe80::dead::beef',            # FAIL multiple double colons
        #'::1::',                       # FAIL too many double colons
        #'fe80:0:0:0:0:0:dead:beef::',  # FAIL Too many bytes with double colons
    ],
)
def test_negative_IPv6_REGEX(addr):
    test_result = _RGX_IPV6ADDR.search(addr)
    assert test_result is None  # The regex *should* fail on these addrs


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2",
)
def testL4Object_asa_eq01():
    pp = L4Object(protocol="tcp", port_spec="eq smtp", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == [25]


def testL4Object_asa_eq02():
    pp = L4Object(protocol="tcp", port_spec="smtp", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == [25]


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2 due to range()",
)
def testL4Object_asa_range01():
    pp = L4Object(protocol="tcp", port_spec="range smtp 32", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == range(25, 33)


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2 due to range()",
)
def testL4Object_asa_lt01():
    pp = L4Object(protocol="tcp", port_spec="lt echo", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == range(1, 7)


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2 due to range()",
)
def testL4Object_asa_lt02():
    pp = L4Object(protocol="tcp", port_spec="lt 7", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == range(1, 7)


def testIPv4Obj_contain():
    ## Test ccp_util.IPv4Obj.__contains__()
    ##
    ## Test whether a prefix is or is not contained in another prefix
    results_correct = [
        ("1.0.0.0/8", "0.0.0.0/0", True),  # Is 1.0.0.0/8 in 0.0.0.0/0?
        ("0.0.0.0/0", "1.0.0.0/8", False),  # Is 0.0.0.0/0 in 1.0.0.0/8?
        ("1.1.1.0/27", "1.0.0.0/8", True),  # Is 1.1.1.0/27 in 1.0.0.0/8?
        ("1.1.1.0/27", "9.9.9.9/32", False),  # Is 1.1.1.0/27 in 9.9.9.9/32?
        ("9.9.9.0/27", "9.9.9.9/32", False),  # Is 9.9.9.0/27 in 9.9.9.9/32?
    ]
    for prefix1, prefix2, result_correct in results_correct:
        ## 'foo in bar' tests bar.__contains__(foo)
        test_result = IPv4Obj(prefix1) in IPv4Obj(prefix2)
        assert test_result == result_correct


def testIPv4Obj_parse():
    ## Ensure that IPv4Obj can correctly parse various inputs
    test_strings = [
        "1.0.0.1/24",
        "1.0.0.1/32",
        "1.0.0.1   255.255.255.0",
        "1.0.0.1   255.255.255.255",
        "1.0.0.1 255.255.255.0",
        "1.0.0.1 255.255.255.255",
        "1.0.0.1/255.255.255.0",
        "1.0.0.1/255.255.255.255",
    ]
    for test_string in test_strings:
        test_result = IPv4Obj(test_string)
        assert isinstance(test_result, IPv4Obj)


def testIPv4Obj_attributes():
    ## Ensure that attributes are accessible and pass the smell test
    test_object = IPv4Obj("1.0.0.1 255.255.255.0")
    results_correct = [
        ("ip", IPv4Address("1.0.0.1")),
        ("ip_object", IPv4Address("1.0.0.1")),
        ("netmask", IPv4Address("255.255.255.0")),
        ("prefixlen", 24),
        ("broadcast", IPv4Address("1.0.0.255")),
        ("network", IPv4Network("1.0.0.0/24")),
        ("network_object", IPv4Network("1.0.0.0/24")),
        ("hostmask", IPv4Address("0.0.0.255")),
        ("numhosts", 256),
        ("version", 4),
        ("is_reserved", False),
        ("is_multicast", False),
        ("is_private", False),
        ("as_decimal", 16777217),
        ("as_hex_tuple", ("01", "00", "00", "01")),
        ("as_binary_tuple", ("00000001", "00000000", "00000000", "00000001")),
    ]
    for attribute, result_correct in results_correct:
        assert getattr(test_object, attribute) == result_correct


def testIPv4Obj_recursive():
    """IPv4Obj() should be able to parse itself"""
    obj = IPv4Obj(IPv4Obj("1.1.1.1/24"))
    assert str(obj.ip_object) == "1.1.1.1"
    assert obj.prefixlen == 24


def testIPv6Obj_recursive():
    """IPv6Obj() should be able to parse itself"""
    obj = IPv6Obj(IPv6Obj("fe80:a:b:c:d:e::1/64"))
    assert str(obj.ip_object) == "fe80:a:b:c:d:e:0:1"
    assert obj.prefixlen == 64


def test_dns_lookup():
    # Use VMWare's opencloud A-record to test...
    #   ref http://stackoverflow.com/a/7714208/667301
    result_correct = {"addrs": ["127.0.0.1"], "name": "*.vcap.me", "error": ""}
    test_result = dns_lookup("*.vcap.me")
    if not test_result["error"]:
        assert dns_lookup("*.vcap.me") == result_correct
    else:
        pytest.skip(test_result["error"])


def test_reverse_dns_lookup():
    result_correct = {"addr": "127.0.0.1", "name": "localhost.", "error": ""}
    test_result = reverse_dns_lookup("127.0.0.1")
    if not test_result["error"]:
        assert "localhost" in test_result["name"].lower()
    else:
        pytest.skip(test_result["error"])


def test_CiscoRange_01():
    """Basic vlan range test"""
    result_correct = ["1"]
    assert CiscoRange("1").as_list == result_correct


def test_CiscoRange_02():
    """Basic vlan range test"""
    result_correct = ["1", "3"]
    assert CiscoRange("1,3").as_list == result_correct


def test_CiscoRange_03():
    """Basic vlan range test"""
    result_correct = ["1", "2", "3", "4", "5"]
    assert CiscoRange("1,2-4,5").as_list == result_correct


def test_CiscoRange_03():
    """Basic vlan range test"""
    result_correct = ["1", "2", "3", "4", "5"]
    assert CiscoRange("1-3,4,5").as_list == result_correct


def test_CiscoRange_04():
    """Basic vlan range test"""
    result_correct = ["1", "2", "3", "4", "5"]
    assert CiscoRange("1,2,3-5").as_list == result_correct


def test_CiscoRange_05():
    """Basic slot range test"""
    result_correct = ["1/1", "1/2", "1/3", "1/4", "1/5"]
    assert CiscoRange("1/1-3,4,5").as_list == result_correct


def test_CiscoRange_06():
    """Basic slot range test"""
    result_correct = ["1/1", "1/2", "1/3", "1/4", "1/5"]
    assert CiscoRange("1/1,2-4,5").as_list == result_correct


def test_CiscoRange_07():
    """Basic slot range test"""
    result_correct = ["1/1", "1/2", "1/3", "1/4", "1/5"]
    assert CiscoRange("1/1,2,3-5").as_list == result_correct


def test_CiscoRange_08():
    """Basic slot range test"""
    result_correct = ["2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"]
    assert CiscoRange("2/1/1-3,4,5").as_list == result_correct


def test_CiscoRange_09():
    """Basic slot range test"""
    result_correct = ["2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"]
    assert CiscoRange("2/1/1,2-4,5").as_list == result_correct


def test_CiscoRange_10():
    """Basic slot range test"""
    result_correct = ["2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"]
    assert CiscoRange("2/1/1,2,3-5").as_list == result_correct


def test_CiscoRange_11():
    """Basic interface slot range test"""
    result_correct = [
        "interface Eth2/1/1",
        "interface Eth2/1/2",
        "interface Eth2/1/3",
        "interface Eth2/1/4",
        "interface Eth2/1/5",
    ]
    assert CiscoRange("interface Eth2/1/1-3,4,5").as_list == result_correct


def test_CiscoRange_12():
    """Basic interface slot range test"""
    result_correct = [
        "interface Eth2/1/1",
        "interface Eth2/1/2",
        "interface Eth2/1/3",
        "interface Eth2/1/4",
        "interface Eth2/1/5",
    ]
    assert CiscoRange("interface Eth2/1/1,2-4,5").as_list == result_correct


def test_CiscoRange_13():
    """Basic interface slot range test"""
    result_correct = [
        "interface Eth2/1/1",
        "interface Eth2/1/2",
        "interface Eth2/1/3",
        "interface Eth2/1/4",
        "interface Eth2/1/5",
    ]
    assert CiscoRange("interface Eth2/1/1,2,3-5").as_list == result_correct


def test_CiscoRange_14():
    """Basic interface slot range test"""
    result_correct = [
        "interface Eth 2/1/1",
        "interface Eth 2/1/2",
        "interface Eth 2/1/3",
        "interface Eth 2/1/4",
        "interface Eth 2/1/5",
    ]
    assert CiscoRange("interface Eth 2/1/1,2,3-5").as_list == result_correct


def test_CiscoRange_15():
    """Empty range test"""
    result_correct = []
    assert CiscoRange("").as_list == result_correct


def test_CiscoRange_16():
    """Append range test"""
    result_correct = [1, 2, 3]
    assert CiscoRange("", result_type=int).append("1-3").as_list == result_correct


def test_CiscoRange_compressed_str_01():
    """compressed_str test"""
    assert CiscoRange("1,2, 3, 6, 7, 8, 9, 911").compressed_str == "1-3,6-9,911"


def test_CiscoRange_contanis():
    assert "Ethernet1/2" in CiscoRange("Ethernet1/1-20")
