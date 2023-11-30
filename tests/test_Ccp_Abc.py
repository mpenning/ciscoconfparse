#!/usr/bin/env python

from loguru import logger
import pytest
from ciscoconfparse.ciscoconfparse import CiscoConfParse
from ciscoconfparse.errors import DynamicAddressException
from ciscoconfparse.ccp_util import IPv4Obj, CiscoRange, CiscoIOSInterface
from ciscoconfparse.ccp_abc import BaseCfgLine
from ciscoconfparse.models_cisco import IOSCfgLine
import sys

sys.path.insert(0, "..")



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


def testVal_BaseCfgLine_obj_01():
    """Test the text and other attributes of ccp_abc.BaseCfgLine()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    assert obj01.text == "hostname Foo"
    assert obj01.linenum == -1
    assert obj01.child_indent == 0
    assert obj01.is_comment is False
    assert str(obj01) == "<BaseCfgLine # -1 'hostname Foo'>"


def testVal_BaseCfgLine_eq_01():
    """Test the equality of BaseCfgLine() objects"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    assert obj01 == obj02


def testVal_BaseCfgLine_neq_01():
    """Test the inequality of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj01 != obj02


def testVal_BaseCfgLine_gt_01():
    """Test the __gt__ of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj02 > obj01


def testVal_BaseCfgLine_lt_01():
    """Test the __lt__ of BaseCfgLine() objects if their linenumbers are different"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj02.linenum = 2
    assert obj01 < obj02


def testVal_BaseCfgLine_index_01():
    """Test BaseCfgLine().index"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.linenum == 1
    assert obj01.index == obj01.linenum


def testVal_BaseCfgLine_calculate_line_id_01():
    """Test BaseCfgLine().calculate_line_id() is an integer.  calculate_line_id() returns a different number for each unique object and it cannot be easily predicted"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert isinstance(obj01.calculate_line_id(), int)


def testVal_BaseCfgLine_diff_id_list_01():
    """Test BaseCfgLine().diff_id_list() is a list.  diff_id_list() returns a different contents for each unique object and it cannot be easily predicted"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert len(obj01.diff_id_list) == 1
    assert isinstance(obj01.diff_id_list, list)
    assert isinstance(obj01.diff_id_list[0], int)


def testVal_BaseCfgLine_safe_escape_curly_braces_01():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("hello{") == "hello{{"


def testVal_BaseCfgLine_safe_escape_curly_braces_02():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("hello}") == "hello}}"


def testVal_BaseCfgLine_safe_escape_curly_braces_03():
    """Test BaseCfgLine().safe_escape_curly_braces()"""
    obj01 = BaseCfgLine(all_lines=None, line="hostname Foo")
    obj01.linenum = 1
    assert obj01.safe_escape_curly_braces("{hello} {") == "{{hello}} {{"


def testVal_BaseCfgLine_parent_01():
    """Test BaseCfgLine().parent"""
    parse = CiscoConfParse(
        ["interface GigabitEthernet1/1", " ip address 192.0.2.1 255.255.255.0"],
        syntax="ios",
    )
    obj01 = parse.find_objects("interface")[0]
    obj01.linenum = 1
    assert len(obj01.children) == 1
    assert obj01.children[0].parent is obj01


def testVal_BaseCfgLine_hash_children_01():
    """Test BaseCfgLine().hash_children"""
    parse = CiscoConfParse(
        ["interface GigabitEthernet1/1", " ip address 192.0.2.1 255.255.255.0"],
        syntax="ios",
    )
    obj01 = parse.find_objects("interface")[0]
    obj01.linenum = 1
    assert len(obj01.children) == 1
    assert isinstance(obj01.children, list)
    assert isinstance(obj01.hash_children, int)


def testVal_BaseCfgLine_family_endpoint_01():
    """Test BaseCfgLine().family_endpoint"""
    obj01 = BaseCfgLine(all_lines=None, line="interface Ethernet0/0")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line=" ip address 192.0.2.1 255.255.255.0")
    obj02.linenum = 2
    obj03 = BaseCfgLine(all_lines=None, line=" no ip proxy-arp")
    obj03.linenum = 3
    obj01.children = [obj02, obj03]
    assert len(obj01.children) == 2
    assert obj01.family_endpoint == 3


def testVal_BaseCfgLine_has_child_with_01():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            " no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    uut = obj.has_child_with('proxy-arp', all_children=False)
    assert uut is True


def testVal_BaseCfgLine_has_child_with_02():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    uut = obj.has_child_with('proxy-arp', all_children=False)
    assert uut is False


def testVal_BaseCfgLine_has_child_with_03():
    """Test BaseCfgLine().has_child_with()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    uut = obj.has_child_with('proxy-arp', all_children=True)
    assert uut is True


def testVal_BaseCfgLine_insert_before_01():
    """Test BaseCfgLine().insert_before()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.insert_before('hostname Foo')
    parse.commit()
    uut = parse.find_objects('hostname')[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_before_02():
    """Test BaseCfgLine().insert_before()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.insert_before(BaseCfgLine(line='hostname Foo'))
    parse.commit()
    uut = parse.find_objects('hostname')[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_before_03():
    """Test BaseCfgLine().insert_before() raises TypeError"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    with pytest.raises(NotImplementedError):
        obj.insert_before(None)


def testVal_BaseCfgLine_insert_after_01():
    """Test BaseCfgLine().insert_after()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.insert_after(' description This or that')
    parse.commit()
    uut = parse.find_objects('description')[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_after_02():
    """Test BaseCfgLine().insert_after()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.insert_after(BaseCfgLine(line=' description This or that'))
    parse.commit()
    uut = parse.find_objects('description')[0]
    assert isinstance(uut, IOSCfgLine) is True


def testVal_BaseCfgLine_insert_after_03():
    """Test BaseCfgLine().insert_after() raises TypeError"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    with pytest.raises(NotImplementedError):
        obj.insert_after(None)


def testVal_BaseCfgLine_append_to_family_01():
    """Test BaseCfgLine().append_to_family()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.append_to_family(' description This or that')
    assert parse.text == [
        'interface Ethernet0/0',
        ' description This or that',
        ' ip address 192.0.2.1 255.255.255.0',
        '  no ip proxy-arp',
    ]


def testVal_BaseCfgLine_append_to_family_02():
    """Test BaseCfgLine().append_to_family() with a BaseCfgLine()"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.append_to_family(BaseCfgLine(line=' description This or that'))
    # commit is required if appending a BaseCfgLine()
    parse.commit()
    uut = parse.objs[1]
    assert uut.text == " description This or that"
    assert parse.objs[0].children[0].text == " description This or that"


def testVal_BaseCfgLine_append_to_family_03():
    """Test BaseCfgLine().append_to_family(auto_indent=False)"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.append_to_family('description This or that', auto_indent=False)
    parse.commit()
    uut = parse.objs[1]
    assert uut.text == "description This or that"
    # Now the children should be empty; this is a new parent line
    assert len(uut.children) == 1
    assert uut.children[0].text == " ip address 192.0.2.1 255.255.255.0"
    assert len(uut.all_children) == 2
    assert uut.all_children[1].text == "  no ip proxy-arp"


def testVal_BaseCfgLine_append_to_family_04():
    """Test BaseCfgLine().append_to_family(auto_indent=True) and last line is a grandchild"""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.append_to_family('description This or that', auto_indent=True)
    parse.commit()
    uut = parse.objs[1]
    # Test that auto_indent worked
    assert uut.text == ' description This or that'
    assert uut.children == []
    # Ensure this is the first line in the family
    assert parse.objs[0].children[0].text == ' description This or that'


def testVal_BaseCfgLine_append_to_family_05():
    """Test BaseCfgLine().append_to_family(auto_indent=True) and last line is a grandchild."""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('interface')[0]
    obj.append_to_family('description This or that', auto_indent=True)
    parse.commit()
    uut = parse.objs[1]
    assert uut.children == []
    # Ensure the line is single indented after insert
    # below a grandchild
    assert uut.text == ' description This or that'
    # Ensure this is the last line in the family
    assert parse.objs[0].children[0].text == ' description This or that'
    assert parse.objs[0].all_children[-1].text == '  no ip proxy-arp'


def testVal_BaseCfgLine_append_to_family_06():
    """Test BaseCfgLine().append_to_family(auto_indent=True) appending a great-grandchild of Ethernet0/0 (below '  no ip proxy-arp')."""
    parse = CiscoConfParse(
        # A fake double-indent on 'no ip proxy-arp'
        ["interface Ethernet0/0",
            " ip address 192.0.2.1 255.255.255.0",
            "  no ip proxy-arp",]
    )
    obj = parse.find_objects('proxy-arp')[0]
    obj.append_to_family('a fake great-grandchild of interface Ethernet0/0', auto_indent=True)
    parse.commit()
    uut = parse.objs[-1]
    assert uut.children == []
    # Ensure the line is correctly indented after insert
    # below a grandchild
    assert uut.text == '   a fake great-grandchild of interface Ethernet0/0'
    # Ensure that the number of direct children is still correct
    assert len(parse.objs[0].children) == 1
    # Ensure this is the last line in the family
    assert parse.objs[0].all_children[-2].text == '  no ip proxy-arp'
    assert parse.objs[0].all_children[-1].text == '   a fake great-grandchild of interface Ethernet0/0'


def testVal_BaseCfgLine_verbose_01():
    """Test BaseCfgLine().verbose"""
    obj01 = BaseCfgLine(all_lines=None, line="interface Ethernet0/0")
    obj01.linenum = 1
    obj02 = BaseCfgLine(all_lines=None, line=" ip address 192.0.2.1 255.255.255.0")
    obj02.linenum = 2
    obj03 = BaseCfgLine(all_lines=None, line=" no ip proxy-arp")
    obj03.linenum = 3
    obj01.children = [obj02, obj03]
    assert obj01.verbose == "<BaseCfgLine # 1 'interface Ethernet0/0' (child_indent: 0 / len(children): 2 / family_endpoint: 3)>"
    assert obj02.verbose == "<BaseCfgLine # 2 ' ip address 192.0.2.1 255.255.255.0' (no_children / family_endpoint: 2)>"


def testVal_BaseCfgLine_is_comment_01():
    """Test BaseCfgLine().is_comment"""
    obj01 = BaseCfgLine(all_lines=None, line="! hostname Foo", comment_delimiter="!")
    assert obj01.is_comment is True
    obj02 = BaseCfgLine(all_lines=None, line="hostname !Foo", comment_delimiter="!")
    assert obj02.is_comment is False
    obj03 = BaseCfgLine(all_lines=None, line="hostname Foo!", comment_delimiter="!")
    assert obj03.is_comment is False


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
