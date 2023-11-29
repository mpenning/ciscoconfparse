r""" test_Ccp_Util.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2014-2019 David Michael Pennington at Samsung Data Services

     This program is free software: you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation, either version 3 of the License, or
     (at your option) any later version.

     This program is distributed in the hope that it will be useful,
     but WITHOUT ANY WARRANTY; without even the implied warranty of
     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
     GNU General Public License for more details.

     You should have received a copy of the GNU General Public License
     along with this program.  If not, see <http://www.gnu.org/licenses/>.

     If you need to contact the author, you can do so by emailing:
     mike [~at~] pennington [/dot\] net
"""
##############################################################################
# Disable SonarCloud warnings in this file
#   - S1192: Define a constant instead of duplicating this literal
#   - S1313: Disable alerts on magic IPv4 / IPv6 addresses
#   - S5843: Avoid regex complexity
#   - S5852: Slow regex are security-sensitive
#   - S6395: Unwrap this unnecessarily grouped regex subpattern.
##############################################################################
#pragma warning disable S1192
#pragma warning disable S1313
#pragma warning disable S5843
#pragma warning disable S5852
#pragma warning disable S6395


import ipaddress
from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address
from loguru import logger
import pytest
from ciscoconfparse.ccp_util import CiscoRange
from ciscoconfparse.ccp_util import CiscoIOSInterface, CiscoIOSXRInterface
from ciscoconfparse.ccp_util import _RGX_IPV4ADDR, _RGX_IPV6ADDR
from ciscoconfparse.ccp_util import IPv6Obj, IPv4Obj, L4Object, ip_factory
from ciscoconfparse.ccp_util import collapse_addresses
import sys

sys.path.insert(0, "..")




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


def testL4Object_asa_eq01():
    pp = L4Object(protocol="tcp", port_spec="eq smtp", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == [25]


def testL4Object_asa_eq02():
    pp = L4Object(protocol="tcp", port_spec="smtp", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == [25]


def testL4Object_asa_range01():
    pp = L4Object(protocol="tcp", port_spec="range smtp 32", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == sorted(range(25, 33))


def testL4Object_asa_lt01():
    pp = L4Object(protocol="tcp", port_spec="lt echo", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == sorted(range(1, 7))


def testL4Object_asa_gt01():
    pp = L4Object(protocol="tcp", port_spec="gt 65534", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == [65535]


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2 due to range()",
)
def testL4Object_asa_lt02():
    pp = L4Object(protocol="tcp", port_spec="lt 7", syntax="asa")
    assert pp.protocol == "tcp"
    assert pp.port_list == sorted(range(1, 7))


def testIPv4Obj_contains_01():
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


def testIPv4Obj_contains_02():

    test_result = IPv4Obj("200.1.1.1/24") in IPv4Network("200.1.1.0/24")
    assert test_result is True

    test_result = IPv4Obj("1.1.1.1/24") in IPv4Network("200.1.1.0/24")
    assert test_result is False


@pytest.mark.parametrize(
    "addr_mask", [
        "1.0.0.1/24",
        "1.0.0.1/32",
        "1.0.0.1 255.255.255.0",
        "1.0.0.1\r255.255.255.0",
        "1.0.0.1\n255.255.255.0",
        "1.0.0.1\t255.255.255.0",
        "1.0.0.1\t 255.255.255.0",
        "1.0.0.1 \t255.255.255.0",
        "1.0.0.1 \t 255.255.255.0",
        "1.0.0.1\t \t255.255.255.0",
        "1.0.0.1     255.255.255.0",
        "1.0.0.1     255.255.255.255",
        "1.0.0.1 255.255.255.0",
        "1.0.0.1 255.255.255.255",
        "1.0.0.1/255.255.255.0",
        "1.0.0.1/255.255.255.255",
    ]
)
def testIPv4Obj_parse(addr_mask):
    ## Ensure that IPv4Obj can correctly parse various inputs
    test_result = IPv4Obj(addr_mask)
    assert isinstance(test_result, IPv4Obj)


def testIPv4Obj_set_masklen01():

    MASK_RESET = 32
    test_object = IPv4Obj("1.1.1.1/%s" % MASK_RESET)

    for result_correct_masklen in [32, 24, 16, 8]:

        test_object = IPv4Obj("1.1.1.1/%s" % MASK_RESET)

        # Test the masklen setter method...
        test_object.masklen = result_correct_masklen

        assert test_object.masklen == result_correct_masklen
        assert test_object.masklength == result_correct_masklen
        assert test_object.prefixlen == result_correct_masklen
        assert test_object.prefixlength == result_correct_masklen

        test_object = IPv4Obj("1.1.1.1/%s" % MASK_RESET)

        # Test the prefixlen setter method...
        test_object.prefixlen = result_correct_masklen

        assert test_object.masklen == result_correct_masklen
        assert test_object.masklength == result_correct_masklen
        assert test_object.prefixlen == result_correct_masklen
        assert test_object.prefixlength == result_correct_masklen


def testIPv4Obj_network_offset():
    test_object = IPv4Obj("192.0.2.28/24")
    assert test_object.masklength == 24
    assert test_object.network_offset == 28


def testIPv4Obj_set_network_offset():
    test_object = IPv4Obj("192.0.2.28/24")
    # Change the last octet to be 200...
    test_object.network_offset = 200
    assert test_object == IPv4Obj("192.0.2.200/24")


def testIPv4Obj_attributes_01():
    ## Ensure that attributes are accessible and pass the smell test
    test_object = IPv4Obj("1.0.0.1 255.255.255.0")
    results_correct = [
        ("as_binary_tuple", ("00000001", "00000000", "00000000", "00000001")),
        ("as_cidr_addr", "1.0.0.1/24"),
        ("as_cidr_net", "1.0.0.0/24"),
        ("as_decimal", 16777217),
        ("as_decimal_network", 16777216),
        ("as_hex_tuple", ("01", "00", "00", "01")),
        ("as_zeropadded", "001.000.000.001"),
        ("as_zeropadded_network", "001.000.000.000/24"),
        ("broadcast", IPv4Address("1.0.0.255")),
        ("hostmask", IPv4Address("0.0.0.255")),
        ("ip", IPv4Address("1.0.0.1")),
        ("ip_object", IPv4Address("1.0.0.1")),
        ("is_multicast", False),
        ("is_private", False),
        ("is_reserved", False),
        ("masklen", 24),
        ("masklength", 24),
        ("netmask", IPv4Address("255.255.255.0")),
        ("network", IPv4Network("1.0.0.0/24")),
        ("network_object", IPv4Network("1.0.0.0/24")),
        ("network_offset", 1),
        ("prefixlen", 24),
        ("prefixlength", 24),
        ("numhosts", 254),
        ("version", 4),
    ]
    for attribute, result_correct in results_correct:

        assert getattr(test_object, attribute) == result_correct


def test_ip_factory_inputs_01():
    """Test input / output of ccp_util.ip_factory()"""
    # Test whether IPv4Obj is retured
    test_params = (
        # Test format...
        #    (<dict with test inputs>, result_correct)
        ({'val': '1.1.1.1/16', 'stdlib': False}, IPv4Obj("1.1.1.1/16")),
        ({'val': '1.1.1.1/16', 'stdlib': True}, IPv4Network("1.1.1.1/16", strict=False)),
        ({'val': '1.1.1.1/32', 'stdlib': False}, IPv4Obj("1.1.1.1/32")),
        ({'val': '1.1.1.1/32', 'stdlib': True}, IPv4Address("1.1.1.1")),
        ({'val': '2b00:cd80:14:10::1/64', 'stdlib': False}, IPv6Obj("2b00:cd80:14:10::1/64")),
        ({'val': '2b00:cd80:14:10::1/64', 'stdlib': True}, IPv6Network("2b00:cd80:14:10::/64", strict=True)),
        ({'val': '::1/64', 'stdlib': False}, IPv6Obj("::1/64")),
        ({'val': '::1/64', 'stdlib': True}, IPv6Network("::0/64")),
        ({'val': '::1/128', 'stdlib': False}, IPv6Obj("::1/128")),
        ({'val': '::1/128', 'stdlib': True}, IPv6Address("::1")),
    )
    for test_args, result_correct in test_params:
        assert ip_factory(**test_args) == result_correct


def test_ip_factory_inputs_02():
    """Test input / output of ccp_util.ip_factory().  This tests checks error conditions"""

    # invalid ip address...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("brickTrick", stdlib=False, mode="auto_detect")

    # invalid ipv4 address
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("brickTrick", stdlib=False, mode="ipv4")

    # invalid ipv6 address
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("brickTrick", stdlib=False, mode="ipv6")

    # invalid ipv4 address
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("::1/128", stdlib=False, mode="ipv4")

    # invalid ipv4 address
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("1.2.3.4.5", stdlib=False, mode="ipv4")

    # invalid first octet and parse auto_detect...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("256.1.1.1", stdlib=False, mode="auto_detect")

    # invalid first octet and parse as ipv4
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("256.1.1.1", stdlib=False, mode="ipv4")

    # invalid first octet and parse as ipv6
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("256.1.1.1", stdlib=False, mode="ipv6")

    # netmask too long...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("239.1.1.1/33", stdlib=False, mode="ipv4")

    # parse ipv6 as ipv6...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("239.1.1.1/24", stdlib=False, mode="ipv6")

    # parse invalid ipv6 address...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("FE80:AAAA::DEAD:BEEEEEEEEEEF", stdlib=False, mode="ipv6")

    # parse invalid auto_detect ipv6 address...
    with pytest.raises(ipaddress.AddressValueError):
        ip_factory("FE80:AAAA::DEAD:BEEEEEEEEEEF", stdlib=False, mode="auto_detect")


def testIPv6Obj_attributes_01():
    ## Ensure that attributes are accessible and pass the smell test
    test_object = IPv6Obj("2001::dead:beef/64")
    results_correct = [
        (
            "as_binary_tuple",
            (
                "0010000000000001",
                "0000000000000000",
                "0000000000000000",
                "0000000000000000",
                "0000000000000000",
                "0000000000000000",
                "1101111010101101",
                "1011111011101111",
            ),
        ),
        ("as_cidr_addr", "2001::dead:beef/64"),
        ("as_cidr_net", "2001::/64"),
        ("as_decimal", 42540488161975842760550356429036175087),
        ("as_decimal_network", 42540488161975842760550356425300246528),
        ("ip", IPv6Address("2001::dead:beef")),
        ("ip_object", IPv6Address("2001::dead:beef")),
        ("netmask", IPv6Address("ffff:ffff:ffff:ffff::")),
        ("prefixlen", 64),
        ("network", IPv6Network("2001::/64")),
        ("network_object", IPv6Network("2001::/64")),
        ("network_offset", 3735928559),
        ("hostmask", IPv6Address("::ffff:ffff:ffff:ffff")),
        ("numhosts", 18446744073709551614),
        ("version", 6),
        ("is_multicast", False),
        ("is_link_local", False),
        ("is_private", True),
        ("is_reserved", False),
        ("is_site_local", False),
        (
            "as_hex_tuple",
            ("2001", "0000", "0000", "0000", "0000", "0000", "dead", "beef"),
        ),
    ]
    for attribute, result_correct in results_correct:

        assert getattr(test_object, attribute) == result_correct


def testIPv6Obj_network_offset_01():
    test_object = IPv6Obj("2001::dead:beef/64")
    assert test_object.network_offset == 3735928559


def testIPv6Obj_set_network_offset_01():
    test_object = IPv6Obj("2001::dead:beef/64")
    test_object.network_offset = 200
    assert test_object == IPv6Obj("2001::c8/64")


def testIPv4Obj_sort_01():
    """Simple IPv4Obj sorting test"""
    cidr_addrs_list = [
        "192.168.1.3/32",
        "192.168.1.2/32",
        "192.168.1.1/32",
        "192.168.1.4/15",
    ]

    result_correct = [
        "192.168.1.4/15",  # Shorter prefixes are "lower" than longer prefixes
        "192.168.1.1/32",
        "192.168.1.2/32",
        "192.168.1.3/32",
    ]

    obj_list = [IPv4Obj(ii) for ii in cidr_addrs_list]
    # Ensure we get the correct sorted order for this list
    assert [ii.as_cidr_addr for ii in sorted(obj_list)] == result_correct


def testIPv4Obj_sort_02():
    """Complex IPv4Obj sorting test"""
    cidr_addrs_list = [
        "192.168.1.1/32",
        "192.168.0.1/32",
        "192.168.0.2/16",
        "192.168.0.3/15",
        "0.0.0.0/32",
        "0.0.0.1/31",
        "16.0.0.1/8",
        "0.0.0.2/30",
        "127.0.0.0/0",
        "16.0.0.0/1",
        "128.0.0.0/1",
        "16.0.0.0/4",
        "16.0.0.3/4",
        "0.0.0.0/0",
        "0.0.0.0/8",
    ]

    result_correct = [
        "0.0.0.0/0",
        "127.0.0.0/0",
        "16.0.0.0/1",
        "0.0.0.0/8",  # for the same network, longer prefixlens sort "higher" than shorter prefixlens
        "0.0.0.2/30",  # for the same network, longer prefixlens sort "higher" than shorter prefixlens
        "0.0.0.1/31",  # for the same network, longer prefixlens sort "higher" than shorter prefixlens
        "0.0.0.0/32",
        "16.0.0.0/4",
        "16.0.0.3/4",
        "16.0.0.1/8",  # for the same network, longer prefixlens sort "higher" than shorter prefixlens
        "128.0.0.0/1",
        "192.168.0.3/15",
        "192.168.0.2/16",
        "192.168.0.1/32",
        "192.168.1.1/32",
    ]

    obj_list = [IPv4Obj(ii) for ii in cidr_addrs_list]
    # Ensure we get the correct sorted order for this list
    assert [ii.as_cidr_addr for ii in sorted(obj_list)] == result_correct


def testIPv4Obj_recursive():
    """IPv4Obj() should be able to parse itself"""
    obj = IPv4Obj(IPv4Obj("1.1.1.1/24"))
    assert str(obj.ip_object) == "1.1.1.1"
    assert obj.prefixlen == 24


def testIPv4Obj_from_int():
    assert IPv4Obj(2886729984).ip == IPv4Address('172.16.1.0')


def testIPv4Obj_neq_01():
    """Simple in-equality test fail (ref - Github issue #180)"""
    assert IPv4Obj("1.1.1.1/24") != ""


def testIPv4Obj_neq_02():
    """Simple in-equality test"""
    obj1 = IPv4Obj("1.1.1.1/24")
    obj2 = IPv4Obj("1.1.1.2/24")
    assert obj1 != obj2


def testIPv4Obj_eq_01():
    """Simple equality test"""
    obj1 = IPv4Obj("1.1.1.1/24")
    obj2 = IPv4Obj("1.1.1.1/24")
    assert obj1 == obj2


def testIPv4Obj_eq_02():
    """Simple equality test"""
    obj1 = IPv4Obj("1.1.1.1/24")
    obj2 = IPv4Obj("1.1.1.0/24")
    assert obj1 != obj2


def testIPv4Obj_gt_01():
    """Simple greater-than test - same network number"""
    assert IPv4Obj("1.1.1.1/24") > IPv4Obj("1.1.1.0/24")


def testIPv4Obj_gt_02():
    """Simple greater-than test - different network number"""
    assert IPv4Obj("1.1.1.0/24") > IPv4Obj("1.1.0.0/24")


def testIPv4Obj_gt_03():
    """Simple greater-than test - different prefixlen"""
    assert IPv4Obj("1.1.1.0/24") > IPv4Obj("1.1.0.0/23")


def testIPv4Obj_lt_01():
    """Simple less-than test - same network number"""
    obj1 = IPv4Obj("1.1.1.1/24")
    obj2 = IPv4Obj("1.1.1.0/24")
    assert obj2 < obj1


def testIPv4Obj_lt_02():
    """Simple less-than test - different network number"""
    obj1 = IPv4Obj("1.1.1.0/24")
    obj2 = IPv4Obj("1.1.0.0/24")
    assert obj2 < obj1


def testIPv4Obj_lt_03():
    """Simple less-than test - different prefixlen"""
    obj1 = IPv4Obj("1.1.1.0/24")
    obj2 = IPv4Obj("1.1.0.0/23")
    assert obj2 < obj1


def testIPv4Obj_contains_03():
    """Test __contains__ method"""
    obj1 = IPv4Obj("1.1.1.0/24")
    obj2 = IPv4Obj("1.1.0.0/23")
    assert obj1 in obj2


def testIPv4Obj_contains_04():
    """Test __contains__ method"""
    obj1 = IPv4Obj("1.1.1.1/32")
    obj2 = IPv4Obj("1.1.1.0/24")
    assert obj1 in obj2


def testIPv4Obj_contains_05():
    """Test __contains__ method"""
    obj1 = IPv4Obj("1.1.1.255/32")
    obj2 = IPv4Obj("1.1.1.0/24")
    assert obj1 in obj2


def testIPv6Obj_recursive():
    """IPv6Obj() should be able to parse itself"""
    obj = IPv6Obj(IPv6Obj("fe80:a:b:c:d:e::1/64"))
    assert str(obj.ip_object) == "fe80:a:b:c:d:e:0:1"
    assert obj.prefixlen == 64


def testIPv6Obj_neq_01():
    """Simple in-equality test fail (ref - Github issue #180)"""
    assert IPv6Obj("::1") != ""


def testIPv6Obj_neq_02():
    """Simple in-equality test"""
    assert IPv6Obj("::1") != IPv6Obj("::2")


def testIPv6Obj_eq_01():
    """Simple equality test"""
    assert IPv6Obj("::1") == IPv6Obj("::1")


def testIPv6Obj_gt_01():
    """Simple greater_than test"""
    assert IPv6Obj("::2") > IPv6Obj("::1")


def testIPv6Obj_lt_01():
    """Simple less_than test"""
    assert IPv6Obj("::1") < IPv6Obj("::2")


def testIPv6Obj_IPv4_embedded_in_IPv6_01():
    """Test IPv6Obj with an IPv4 address (192.168.1.254) embedded in an IPv6 address"""
    assert IPv6Obj("::192.168.1.254") == IPv6Obj("::c0a8:1fe")


def testIPv6Obj_IPv4_embedded_in_IPv6_02():
    """Test IPv6Obj with an IPv4 address (192.0.2.33) embedded in an IPv6 address"""
    assert IPv6Obj("2001:db8:122:344::192.0.2.33") == IPv6Obj("2001:db8:122:344::c000:221")


def testIPv6Obj_IPv4_embedded_in_IPv6_03():
    """Test IPv6Obj with an RFC 6052 NAT64 prefix (64:ff9b::) using IPv4 address (10.20.0.1) embedded in an IPv6 address"""
    assert IPv6Obj("64:ff9b::192.0.2.33") == IPv6Obj("64:ff9b::c000:221")


def testIPv6Obj_IPv4_embedded_in_IPv6_04():
    """Test IPv6Obj with an IPv4 address (192.0.2.4) embedded in an IPv6 address"""
    assert IPv6Obj("::ffff:192.0.2.4") == IPv6Obj("::ffff:c000:204")


def test_collapse_addresses_01():

    net_collapsed = ipaddress.collapse_addresses([IPv4Network('192.0.0.0/22'), IPv4Network('192.0.2.128/25')])
    for idx, entry in enumerate(net_collapsed):
        if idx == 0:
            assert entry == IPv4Network("192.0.0.0/22")


def test_collapse_addresses_02():
    net_list = [IPv4Obj('192.0.2.128/25'), IPv4Obj('192.0.0.0/26')]
    collapsed_list = sorted(collapse_addresses(net_list))
    assert collapsed_list[0].network_address == IPv4Obj('192.0.0.0/26').ip
    assert collapsed_list[1].network_address == IPv4Obj('192.0.2.128/25').ip


def test_CiscoIOSInterface_01():
    """Check that a single number is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1")
    assert uut.prefix == "Ethernet"
    assert uut.card is None
    assert uut.slot is None
    assert uut.port == 1
    assert uut.subinterface is None
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_02():
    """Check that a card and port is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/42")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card is None
    assert uut.port == 42
    assert uut.subinterface is None
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_03():
    """Check that a card and large port-number is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/4242")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card is None
    assert uut.port == 4242
    assert uut.subinterface is None
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_04():
    """Check that a card, port and subinterface is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/42.5")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card is None
    assert uut.port == 42
    assert uut.subinterface == 5
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_05():
    """Check that a card, slot, port  is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/3/42")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card == 3
    assert uut.port == 42
    assert uut.subinterface is None
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_06():
    """Check that a card, slot, port and subinterface  is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/3/42.5")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card == 3
    assert uut.port == 42
    assert uut.subinterface == 5
    assert uut.channel is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_07():
    """Check that a card, slot, port, subinterface, and channel is parsed correctly"""
    uut = CiscoIOSInterface("Ethernet1/3/42.5:9")
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card == 3
    assert uut.port == 42
    assert uut.subinterface == 5
    assert uut.channel == 9
    assert uut.interface_class is None


def test_CiscoIOSInterface_08():
    """Check that a card, slot, port, subinterface, and channel is parsed correctly from a dict"""
    uut = CiscoIOSInterface(
        interface_dict={
            'prefix': 'Ethernet',
            'card': 2,
            'slot': 1,
            'port': 3,
            'digit_separator': '/',
            'subinterface': 4,
            'channel': 5,
            'interface_class': None,
        })
    assert uut.prefix == "Ethernet"
    assert uut.slot == 1
    assert uut.card == 2
    assert uut.port == 3
    assert uut.subinterface == 4
    assert uut.channel == 5
    assert uut.digit_separator == "/"
    assert uut.interface_class is None


def test_CiscoIOSInterface_09():
    """Check that a port is parsed correctly from a dict"""
    uut = CiscoIOSInterface(
        interface_dict={
            'prefix': 'Ethernet',
            'card': None,
            'slot': None,
            'port': 1,
            'digit_separator': None,
            'subinterface': None,
            'channel': None,
            'interface_class': None,
        })
    assert uut.prefix == "Ethernet"
    assert uut.slot == None
    assert uut.card is None
    assert uut.port is 1
    assert uut.subinterface is None
    assert uut.channel is None
    assert uut.digit_separator is None
    assert uut.interface_class is None


def test_CiscoIOSInterface_10():
    """Check that a card, slot, port, subinterface, and channel is parsed correctly"""
    uut = CiscoIOSInterface("Serial1/3/42.5:9 multipoint")
    assert uut.prefix == "Serial"
    assert uut.slot == 1
    assert uut.card == 3
    assert uut.port == 42
    assert uut.subinterface == 5
    assert uut.channel == 9
    assert uut.interface_class == "multipoint"


def test_CiscoRange_01():
    """Basic vlan range test"""
    result_correct = {1, 2, 3}
    uut_str = "1-3"
    assert CiscoRange(uut_str, result_type=int).as_set(result_type=int) == result_correct


def test_CiscoRange_02():
    """Basic vlan range test"""
    result_correct = {1, 3}
    uut_str = "1,3"
    assert CiscoRange(uut_str, result_type=int).as_set(result_type=int) == result_correct


def test_CiscoRange_03():
    """Basic vlan range test"""
    result_correct = {1, 2, 3, 4, 5}
    uut_str = "1,2-4,5"
    assert CiscoRange(uut_str, result_type=int).as_set(result_type=int) == result_correct


def test_CiscoRange_04():
    """Basic vlan range test"""
    result_correct = {1, 2, 3, 4, 5}
    uut_str = "1-3,4,5"
    assert CiscoRange(uut_str, result_type=int).as_set(result_type=int) == result_correct


def test_CiscoRange_05():
    """Basic vlan range test"""
    result_correct = {1, 2, 3, 4, 5}
    uut_str = "1,2,3-5"
    assert CiscoRange(uut_str, result_type=int).as_set(result_type=int) == result_correct


def test_CiscoRange_06():
    """Basic slot range test"""
    result_correct = {"1/1", "1/2", "1/3", "1/4", "1/5"}
    uut_str = "1/1-3,4,5"
    # the CiscoRange() result_type None is a CiscoIOSInterface() type with a
    #     port attribute...
    assert CiscoRange(uut_str, result_type=CiscoIOSInterface).as_set(result_type=str) == result_correct
    assert CiscoRange(uut_str).iterate_attribute == "port"


def test_CiscoRange_07():
    """Basic slot range test"""
    result_correct = {"1/1", "1/2", "1/3", "1/4", "1/5"}
    uut_str = "1/1,2-4,5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_08():
    """Basic slot range test"""
    result_correct = {"1/1", "1/2", "1/3", "1/4", "1/5"}
    uut_str = "1/1,2,3-5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_09():
    """Basic slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1-3,4,5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_10():
    """Basic slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1,2-4,5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_11():
    """Basic slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1,2,3-5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_12():
    """Basic interface slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1-3,4,5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_13():
    """Basic interface slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1,2-4,5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_14():
    """Basic interface slot range test"""
    result_correct = {"2/1/1", "2/1/2", "2/1/3", "2/1/4", "2/1/5"}
    uut_str = "2/1/1,2,3-5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_15():
    """Basic interface slot range test"""
    result_correct = {"Eth2/1/1", "Eth2/1/2", "Eth2/1/3", "Eth2/1/4", "Eth2/1/5"}
    uut_str = "Eth 2/1/1,2,3-5"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_16():
    """Basic interface port range test"""
    result_correct = {"Eth7", "Eth8", "Eth9"}
    uut_str = "Eth 7-9"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_17():
    """Basic interface slot and port range test"""
    result_correct = {"Eth1/7", "Eth1/8", "Eth1/9"}
    uut_str = "Eth 1/7-9"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_18():
    """Basic interface slot, card, and port range test"""
    result_correct = {"Eth1/2/7", "Eth1/2/8", "Eth1/2/9"}
    uut_str = "Eth 1/2/7-9"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_19():
    """Basic interface slot, card, port, and subinterface range test"""
    result_correct = {"Eth1/2/3.7", "Eth1/2/3.8", "Eth1/2/3.9"}
    uut_str = "Eth 1/2/3.7-9"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_20():
    """Basic interface slot, card, port, subinterface and channel range test"""
    result_correct = {"Eth1/2/3.4:7", "Eth1/2/3.4:8", "Eth1/2/3.4:9"}
    uut_str = "Eth 1/2/3.4:7-9"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_21():
    """Basic interface slot, card, port, subinterface, channel and interface_class range test"""
    result_correct = {"Eth1/2/3.4:7 multipoint", "Eth1/2/3.4:8 multipoint", "Eth1/2/3.4:9 multipoint"}
    uut_str = "Eth 1/2/3.4:7-9 multipoint"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_22():
    """Parse a string with a common prefix on all of the CiscoRange() inputs"""
    result_correct = {
        "Eth1/1", "Eth1/10", "Eth1/12", "Eth1/13", "Eth1/14",
        "Eth1/15", "Eth1/16", "Eth1/17", "Eth1/18", "Eth1/19",
        "Eth1/20"
    }
    uut_str = "Eth1/1,Eth1/12-20,Eth1/16,Eth1/10"
    assert CiscoRange(uut_str).as_set(result_type=str) == result_correct


def test_CiscoRange_23():
    """Check that the exact results are correct for CiscoRange().as_set() with a redundant input ('Eth1/1')"""
    result_correct = {
        CiscoIOSInterface("Eth1/1"),
        CiscoIOSInterface("Eth1/2"),
        CiscoIOSInterface("Eth1/3"),
        CiscoIOSInterface("Eth1/4"),
        CiscoIOSInterface("Eth1/5"),
        CiscoIOSInterface("Eth1/16"),
    }
    uut_str = "Eth1/1,Eth1/1-5,Eth1/16"
    # CiscoRange(text="foo", result_type=None) returns CiscoIOSInterface() instances...
    assert CiscoRange(uut_str, result_type=None).as_set(result_type=None) == result_correct


def test_CiscoRange_24():
    """Check that the exact results are correct for CiscoRange().as_list() with a redundant input ('Eth1/1')"""
    result_correct = [
        CiscoIOSInterface("Eth1/1"),
        CiscoIOSInterface("Eth1/2"),
        CiscoIOSInterface("Eth1/3"),
        CiscoIOSInterface("Eth1/4"),
        CiscoIOSInterface("Eth1/5"),
        CiscoIOSInterface("Eth1/16"),
    ]
    uut_str = "Eth1/1,Eth1/1-5,Eth1/16"
    # CiscoRange(text="foo", result_type=None) returns CiscoIOSInterface() instances...
    assert CiscoRange(uut_str, result_type=None).as_list(result_type=None) == result_correct


def test_CiscoRange_compressed_str_01():
    """compressed_str test with a very basic set of vlan numbers"""
    uut_str = "1,2,911"
    assert CiscoRange(uut_str, result_type=int).as_compressed_str() == "1,2,911"


def test_CiscoRange_compressed_str_02():
    """compressed_str test with vlan number ranges"""
    uut_str = "1,2, 3, 6, 7,  8 , 9, 911"
    assert CiscoRange(uut_str, result_type=int).as_compressed_str() == "1-3,6-9,911"


def test_CiscoRange_contains_01():
    """Check that the exact results are correct that a CiscoRange() contains an input"""
    uut_str = "Ethernet1/1-20"
    # Ethernet1/5 is in CiscoRange("Ethernet1/1-20")...
    assert CiscoIOSInterface("Ethernet1/5") in CiscoRange(uut_str)


def test_CiscoRange_contains_02():
    """Check that the exact results are correct that a CiscoRange() does not contain an input"""
    uut_str = "Ethernet1/1-20"
    # Ethernet1/5 is in CiscoRange("Ethernet1/1-20")...
    assert (CiscoIOSInterface("Ethernet1/48") in CiscoRange(uut_str)) is False

#pragma warning restore S1192
#pragma warning restore S1313
#pragma warning restore S5843
#pragma warning restore S5852
#pragma warning restore S6395
