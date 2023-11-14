#!/usr/bin/env python

import sys
import os

sys.path.insert(0, "..")

from ciscoconfparse.ccp_util import IPv4Obj, CiscoRange, CiscoIOSInterface
from ciscoconfparse.errors import DynamicAddressException
from ciscoconfparse.ciscoconfparse import CiscoConfParse
import pytest

from loguru import logger

r""" test_Ccp_Abc.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2023      David Michael Pennington

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

def testVal_re_match_iter_typed_parent_default_type_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the parent and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"^interface\s+(\S.+)$",
        group=1,
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "GigabitEthernet 1/1"

def testVal_re_match_iter_typed_first_child_default_type_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the first child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+mode\s+(\S+)$",
        group=1,
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "trunk"

def testVal_re_match_iter_typed_first_child_default_type_recurse():
    """Test that re_match_iter_typed(recurse=True) finds the first child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+mode\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "trunk"

def testVal_re_match_iter_typed_child_deep_fail_norecurse():
    """Test that re_match_iter_typed(recurse=False) fails on a deep recurse through multiple children"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^policy.map\s+EXTERNAL_CBWFQ")[0]

    uut_result = obj.re_match_iter_typed(
        r"exceed\-action\s+(\S+)$",
        group=1,
        recurse=False,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "policy-map EXTERNAL_CBWFQ"
    assert uut_result == "_no_match"

def testVal_re_match_iter_typed_child_deep_pass_recurse():
    """Test that re_match_iter_typed(recurse=False) finds during a deep recurse through multiple levels of children"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^policy.map\s+EXTERNAL_CBWFQ")[0]

    uut_result = obj.re_match_iter_typed(
        r"exceed\-action\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "policy-map EXTERNAL_CBWFQ"
    assert uut_result == "drop"

def testVal_re_match_iter_typed_second_child_default_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(\S+)$",
        group=1,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == "911"

def testVal_re_match_iter_typed_second_child_int_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns the default `result_type`, which is `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(\S+)$",
        group=1,
        result_type=int,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == 911

def testVal_re_match_iter_typed_named_regex_group_second_child_int_type_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child with a named regex"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(?P<native_vlan>\S+)$",
        group=1,
        result_type=int,
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result == 911

def testVal_re_match_iter_typed_intf_norecurse():
    """Test that re_match_iter_typed(recurse=False) finds the parent and returns a `str`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"^interface\s+(?P<intf>\S.+)$",
        groupdict={"intf": str},
        default="_no_match",
        recurse=False,
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result["intf"] == "GigabitEthernet 1/1"

def testVal_re_match_iter_typed_vlan_recurse():
    """Test that re_match_iter_typed(recurse=False) finds the second child and returns an `int`"""
    config = """!
interface GigabitEthernet 1/1
 switchport mode trunk
 switchport trunk native vlan 911
 channel-group 25 mode active
!
!
class-map match-all IP_PREC_MEDIUM
 match ip precedence 2  3  4  5
class-map match-all IP_PREC_HIGH
 match ip precedence 6  7
class-map match-all TEST
class-map match-all TO_ATM
 match access-group name NOT_INTERNAL
class-map match-any ALL
 match any
!
!
policy-map EXTERNAL_CBWFQ
 class IP_PREC_HIGH
  priority percent 10
  police cir percent 10
    conform-action transmit
    exceed-action drop
 class IP_PREC_MEDIUM
  bandwidth percent 50
  queue-limit 100
 class class-default
  bandwidth percent 40
  queue-limit 100
policy-map SHAPE_HEIR
 class ALL
  shape average 630000
  service-policy EXTERNAL_CBWFQ
!
!"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    obj = cfg.find_objects("^interface")[0]

    uut_result = obj.re_match_iter_typed(
        r"switchport\s+trunk\s+native\s+vlan\s+(?P<vlan>\S+)$",
        groupdict={"vlan": int},
        recurse=True,
        default="_no_match",
        debug=False,
    )
    # Check that base assumption is True... we are checking the right parent
    assert obj.text == "interface GigabitEthernet 1/1"
    assert uut_result["vlan"] == 911
