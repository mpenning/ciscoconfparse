#!/usr/bin/env python

import sys
import re
import os

sys.path.insert(0, "..")

from ciscoconfparse.errors import DynamicAddressException
from ciscoconfparse.ciscoconfparse import CiscoConfParse
from ciscoconfparse.ccp_util import IPv4Obj, CiscoRange
import pytest


@pytest.mark.parametrize(
    "line",
    [
        "interface GigabitEthernet4/1",
        "interface  GigabitEthernet4/1",  # Two spaces
        "interface  GigabitEthernet4/1 ",  # Two spaces and trailing space
    ],
)
def testVal_IOSIntfLine_dna(line):
    cfg = CiscoConfParse([line], factory=True, syntax="ios")
    obj = cfg.ConfigObjs[0]
    assert obj.dna == "IOSIntfLine"


@pytest.mark.parametrize(
    "line",
    [
        "hostname Router",
        "hostname  Router",  # Two spaces
        "hostname  Router ",  # Two spaces and trailing space
    ],
)
def testVal_IOSHostnameLine_dna(line):
    cfg = CiscoConfParse([line], factory=True, syntax="ios")
    obj = cfg.ConfigObjs[0]
    assert obj.dna == "IOSHostnameLine"


def testValues_IOSIntfLine(parse_c01_factory):
    """Test to check IOSIntfLine values"""
    obj = parse_c01_factory.find_objects_dna("IOSIntf")[0]
    assert obj.name == "Serial 1/0"
    assert obj.ipv4_addr == "1.1.1.1"
    assert obj.ipv4_netmask == "255.255.255.252"


def testVal_IOSCfgLine_is_intf():
    # Map a config line to result_correct
    result_map = {
        "interface Serial 1/0": True,
        "interface GigabitEthernet4/1": True,
        "interface GigabitEthernet4/8.120": True,
        "interface ATM5/0/0": True,
        "interface ATM5/0/0.32 point-to-point": True,
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.is_intf is result_correct


def testVal_IOSCfgLine_is_subintf():
    # Map a config line to result_correct
    result_map = {
        "interface Serial 1/0": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/8.120": True,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": True,
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.is_subintf is result_correct


def testVal_IOSCfgLine_is_loopback_intf():
    # Map a config line to result_correct
    result_map = {
        "interface Loopback 0": True,
        "interface Loopback1": True,
        "interface Serial 1/0": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.is_loopback_intf is result_correct


def testVal_IOSCfgLine_is_virtual_intf():
    # Map a config line to result_correct
    result_map = {
        "interface Loopback 0": True,
        "interface Loopback1": True,
        "interface Tunnel 0": True,
        "interface Tunnel0": True,
        "interface Dialer 0": True,
        "interface Dialer0": True,
        "interface Port-Channel 1": True,
        "interface Port-channel 1": True,
        "interface Port-Channel1": True,
        "interface Port-channel1": True,
        "interface Serial 1/0": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True, syntax="ios")
        obj = cfg.ConfigObjs[0]
        assert obj.is_virtual_intf is result_correct


def testVal_IOSCfgLine_is_ethernet_intf():
    # Map a config line to result_correct
    result_map = {
        "interface Loopback 0": False,
        "interface Loopback1": False,
        "interface Serial 1/0": False,
        "interface Ethernet4/1": True,
        "interface Ethernet 4/1": True,
        "interface FastEthernet4/1": True,
        "interface FastEthernet 4/1": True,
        "interface GigabitEthernet4/1": True,
        "interface GigabitEthernet 4/1": True,
        "interface GigabitEthernet4/8.120": True,
        "interface GigabitEthernet 4/8.120": True,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.is_ethernet_intf is result_correct


def testVal_IOSIntfLine_name():
    # Map a config line to result_correct
    result_map = {
        "interface Loopback 0": "Loopback 0",
        "interface Loopback1": "Loopback1",
        "interface Serial 1/0": "Serial 1/0",
        "interface Ethernet4/1": "Ethernet4/1",
        "interface Ethernet 4/1": "Ethernet 4/1",
        "interface FastEthernet4/1": "FastEthernet4/1",
        "interface FastEthernet 4/1": "FastEthernet 4/1",
        "interface GigabitEthernet4/1": "GigabitEthernet4/1",
        "interface GigabitEthernet 4/1": "GigabitEthernet 4/1",
        "interface GigabitEthernet4/8.120": "GigabitEthernet4/8.120",
        "interface GigabitEthernet 4/8.120": "GigabitEthernet 4/8.120",
        "interface ATM5/0/0": "ATM5/0/0",
        "interface ATM5/0/0.32 point-to-point": "ATM5/0/0.32",
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.name == result_correct


def testVal_IOSIntfLine_intf_in_portchannel01(parse_c01_factory):
    cfg = parse_c01_factory
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/1$"):
        assert intf_obj.intf_in_portchannel is False
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/4$"):
        assert intf_obj.intf_in_portchannel is False


def testVal_IOSIntfLine_in_portchannel02():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk native vlan 911",
        " channel-group 25 mode active",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.intf_in_portchannel is True


def testVal_IOSIntfLine_portchannel_number_01():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk native vlan 911",
        " channel-group 25 mode active",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.portchannel_number == 25


def testVal_IOSIntfLine_portchannel_number_02():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.portchannel_number == -1


def testVal_IOSIntfLine_is_switchport(parse_c01_factory):
    cfg = parse_c01_factory
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/1$"):
        assert intf_obj.is_switchport is True
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/4$"):
        assert intf_obj.is_switchport is False


def testVal_IOSIntfLine_access_vlan(parse_c01_factory):
    cfg = parse_c01_factory
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/1$"):
        assert intf_obj.access_vlan == 100
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/8$"):
        assert intf_obj.access_vlan == 110
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet4\/4$"):
        assert intf_obj.access_vlan == 0


def testVal_IOSIntfLine_native_vlan(parse_c01_factory):
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.native_vlan == 911


def testVal_IOSIntfLine_trunk_vlan_allowed_01():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed.as_list == list(range(1, 4095))


def testVal_IOSIntfLine_trunk_vlan_allowed_02():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk allowed vlan 2,4,6,911",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed.as_list == [2, 4, 6, 911]


def testVal_IOSIntfLine_trunk_vlan_allowed_03():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk allowed vlan 2,4,6,911",
        " switchport trunk allowed vlan remove 2,5",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed.as_list == [4, 6, 911]


def testVal_IOSIntfLine_trunk_vlan_allowed_04():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk allowed vlan all",
        " switchport trunk allowed vlan remove 2-4094",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed.as_list == [1]


def testVal_IOSIntfLine_trunk_vlan_allowed_05():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk allowed vlan all",
        " switchport trunk allowed vlan except 2-4094",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed.as_list == [1]


def testVal_IOSIntfLine_trunk_vlan_allowed_06():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " switchport mode trunk",
        " switchport trunk allowed vlan none",
        " switchport trunk allowed vlan add 2-1000",
        " switchport trunk allowed vlan add 1010-4094",
        " switchport trunk native vlan 911",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed == CiscoRange(
        "2-1000,1010-4094", result_type=int
    )


def testVal_IOSIntfLine_trunk_vlan_allowed_07():
    config = """!
interface GigabitEthernet 1/1
 switchport
 switchport mode trunk
 switchport trunk allowed vlan none
 switchport trunk allowed vlan add 1-20
 ! except 1 implicitly allows vlans 2-4094 on the trunk
 switchport trunk allowed vlan except 1
 switchport trunk allowed vlan remove 20
!
"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed == CiscoRange("2-19,21-4094", result_type=int)


def testVal_IOSIntfLine_trunk_vlan_allowed_08():
    config = """!
interface GigabitEthernet 1/1
 switchport
 switchport mode trunk
 switchport trunk allowed vlan none
!
"""
    cfg = CiscoConfParse(config.splitlines(), factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.trunk_vlans_allowed == CiscoRange()


def testVal_IOSIntfLine_abbvs(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": set(
            [
                "s1/0",
                "se1/0",
                "s 1/0",
                "ser1/0",
                "se 1/0",
                "ser 1/0",
                "seri1/0",
                "seri 1/0",
                "seria1/0",
                "serial1/0",
                "seria 1/0",
                "serial 1/0",
            ]
        ),
        "interface Serial 1/1": set(
            [
                "s1/1",
                "se1/1",
                "s 1/1",
                "ser1/1",
                "se 1/1",
                "ser 1/1",
                "seri1/1",
                "seri 1/1",
                "seria1/1",
                "serial1/1",
                "seria 1/1",
                "serial 1/1",
            ]
        ),
        "interface GigabitEthernet4/1": set(
            [
                "g4/1",
                "gi4/1",
                "g 4/1",
                "gi 4/1",
                "gig4/1",
                "giga4/1",
                "gig 4/1",
                "gigab4/1",
                "giga 4/1",
                "gigab 4/1",
                "gigabi4/1",
                "gigabit4/1",
                "gigabi 4/1",
                "gigabite4/1",
                "gigabit 4/1",
                "gigabite 4/1",
                "gigabitet4/1",
                "gigabiteth4/1",
                "gigabitet 4/1",
                "gigabiteth 4/1",
                "gigabitethe4/1",
                "gigabitethe 4/1",
                "gigabitether4/1",
                "gigabitether 4/1",
                "gigabitethern4/1",
                "gigabitethern 4/1",
                "gigabitetherne4/1",
                "gigabitetherne 4/1",
                "gigabitethernet4/1",
                "gigabitethernet 4/1",
            ]
        ),
        "interface GigabitEthernet4/2": set(
            [
                "g4/2",
                "gi4/2",
                "g 4/2",
                "gi 4/2",
                "gig4/2",
                "giga4/2",
                "gig 4/2",
                "gigab4/2",
                "giga 4/2",
                "gigab 4/2",
                "gigabi4/2",
                "gigabit4/2",
                "gigabi 4/2",
                "gigabite4/2",
                "gigabit 4/2",
                "gigabite 4/2",
                "gigabitet4/2",
                "gigabiteth4/2",
                "gigabitet 4/2",
                "gigabiteth 4/2",
                "gigabitethe4/2",
                "gigabitethe 4/2",
                "gigabitether4/2",
                "gigabitether 4/2",
                "gigabitethern4/2",
                "gigabitethern 4/2",
                "gigabitetherne4/2",
                "gigabitetherne 4/2",
                "gigabitethernet4/2",
                "gigabitethernet 4/2",
            ]
        ),
        "interface GigabitEthernet4/3": set(
            [
                "g4/3",
                "gi4/3",
                "g 4/3",
                "gi 4/3",
                "gig4/3",
                "giga4/3",
                "gig 4/3",
                "gigab4/3",
                "giga 4/3",
                "gigab 4/3",
                "gigabi4/3",
                "gigabit4/3",
                "gigabi 4/3",
                "gigabite4/3",
                "gigabit 4/3",
                "gigabite 4/3",
                "gigabitet4/3",
                "gigabiteth4/3",
                "gigabitet 4/3",
                "gigabiteth 4/3",
                "gigabitethe4/3",
                "gigabitethe 4/3",
                "gigabitether4/3",
                "gigabitether 4/3",
                "gigabitethern4/3",
                "gigabitethern 4/3",
                "gigabitetherne4/3",
                "gigabitetherne 4/3",
                "gigabitethernet4/3",
                "gigabitethernet 4/3",
            ]
        ),
        "interface GigabitEthernet4/4": set(
            [
                "g4/4",
                "g 4/4",
                "gi4/4",
                "gi 4/4",
                "gig4/4",
                "giga4/4",
                "gig 4/4",
                "gigab4/4",
                "giga 4/4",
                "gigab 4/4",
                "gigabi4/4",
                "gigabit4/4",
                "gigabi 4/4",
                "gigabite4/4",
                "gigabit 4/4",
                "gigabitet4/4",
                "gigabite 4/4",
                "gigabiteth4/4",
                "gigabitet 4/4",
                "gigabiteth 4/4",
                "gigabitethe4/4",
                "gigabitethe 4/4",
                "gigabitether4/4",
                "gigabitether 4/4",
                "gigabitethern4/4",
                "gigabitethern 4/4",
                "gigabitetherne4/4",
                "gigabitethernet4/4",
                "gigabitetherne 4/4",
                "gigabitethernet 4/4",
            ]
        ),
        "interface GigabitEthernet4/5": set(
            [
                "g4/5",
                "gi4/5",
                "g 4/5",
                "gi 4/5",
                "gig4/5",
                "giga4/5",
                "gig 4/5",
                "gigab4/5",
                "giga 4/5",
                "gigab 4/5",
                "gigabi4/5",
                "gigabit4/5",
                "gigabi 4/5",
                "gigabite4/5",
                "gigabit 4/5",
                "gigabite 4/5",
                "gigabitet4/5",
                "gigabiteth4/5",
                "gigabitet 4/5",
                "gigabiteth 4/5",
                "gigabitethe4/5",
                "gigabitethe 4/5",
                "gigabitether4/5",
                "gigabitether 4/5",
                "gigabitethern4/5",
                "gigabitethern 4/5",
                "gigabitetherne4/5",
                "gigabitetherne 4/5",
                "gigabitethernet4/5",
                "gigabitethernet 4/5",
            ]
        ),
        "interface GigabitEthernet4/6": set(
            [
                "g4/6",
                "gi4/6",
                "g 4/6",
                "gi 4/6",
                "gig4/6",
                "giga4/6",
                "gig 4/6",
                "gigab4/6",
                "giga 4/6",
                "gigab 4/6",
                "gigabi4/6",
                "gigabit4/6",
                "gigabi 4/6",
                "gigabite4/6",
                "gigabit 4/6",
                "gigabite 4/6",
                "gigabitet4/6",
                "gigabiteth4/6",
                "gigabitet 4/6",
                "gigabiteth 4/6",
                "gigabitethe4/6",
                "gigabitethe 4/6",
                "gigabitether4/6",
                "gigabitether 4/6",
                "gigabitethern4/6",
                "gigabitethern 4/6",
                "gigabitetherne4/6",
                "gigabitetherne 4/6",
                "gigabitethernet4/6",
                "gigabitethernet 4/6",
            ]
        ),
        "interface GigabitEthernet4/7": set(
            [
                "g4/7",
                "gi4/7",
                "g 4/7",
                "gi 4/7",
                "gig4/7",
                "giga4/7",
                "gig 4/7",
                "gigab4/7",
                "giga 4/7",
                "gigab 4/7",
                "gigabi4/7",
                "gigabit4/7",
                "gigabi 4/7",
                "gigabite4/7",
                "gigabit 4/7",
                "gigabite 4/7",
                "gigabitet4/7",
                "gigabiteth4/7",
                "gigabitet 4/7",
                "gigabiteth 4/7",
                "gigabitethe4/7",
                "gigabitethe 4/7",
                "gigabitether4/7",
                "gigabitether 4/7",
                "gigabitethern4/7",
                "gigabitethern 4/7",
                "gigabitetherne4/7",
                "gigabitetherne 4/7",
                "gigabitethernet4/7",
                "gigabitethernet 4/7",
            ]
        ),
        "interface GigabitEthernet4/8.120": set(
            [
                "g4/8.120",
                "gi4/8.120",
                "g 4/8.120",
                "gi 4/8.120",
                "gig4/8.120",
                "giga4/8.120",
                "gig 4/8.120",
                "gigab4/8.120",
                "giga 4/8.120",
                "gigab 4/8.120",
                "gigabi4/8.120",
                "gigabi 4/8.120",
                "gigabit4/8.120",
                "gigabit 4/8.120",
                "gigabite4/8.120",
                "gigabite 4/8.120",
                "gigabitet4/8.120",
                "gigabitet 4/8.120",
                "gigabiteth4/8.120",
                "gigabitethe4/8.120",
                "gigabiteth 4/8.120",
                "gigabitethe 4/8.120",
                "gigabitether4/8.120",
                "gigabitethern4/8.120",
                "gigabitether 4/8.120",
                "gigabitethern 4/8.120",
                "gigabitetherne4/8.120",
                "gigabitethernet4/8.120",
                "gigabitetherne 4/8.120",
                "gigabitethernet 4/8.120",
            ]
        ),
        "interface ATM5/0/0": set(
            ["a5/0/0", "at5/0/0", "a 5/0/0", "at 5/0/0", "atm5/0/0", "atm 5/0/0"]
        ),
        "interface ATM5/0/0.32 point-to-point": set(
            [
                "a5/0/0.32",
                "at5/0/0.32",
                "a 5/0/0.32",
                "at 5/0/0.32",
                "atm5/0/0.32",
                "atm 5/0/0.32",
            ]
        ),
        "interface ATM5/0/1": set(
            ["a5/0/1", "at5/0/1", "a 5/0/1", "at 5/0/1", "atm5/0/1", "atm 5/0/1"]
        ),
    }
    test_result = dict()
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.abbvs
    assert result_correct == test_result


def testVal_IOSIntfLine_is_abbv_as(parse_c03_factory):
    cfg = parse_c03_factory
    params = {
        "interface Serial 1/0": ("Ser1/0", True),
        "interface Serial 1/1": ("ser11/1", False),
        "interface GigabitEthernet4/1": ("GI4", False),
        "interface GigabitEthernet4/2": ("gig 4", False),
        "interface GigabitEthernet4/3": ("g4/3", True),
        "interface GigabitEthernet4/4": ("g 4/4", True),
        "interface GigabitEthernet4/5": ("g 4/4", False),
        "interface GigabitEthernet4/6": ("gigabitethernet4/6", True),
        "interface GigabitEthernet4/7": ("GigabitEthernet 4/7", True),
        "interface GigabitEthernet4/8.120": ("G 4/8.120", True),
        "interface ATM5/0/0": ("atm5/0", False),
        "interface ATM5/0/0.32 point-to-point": ("At 5/0/0", False),
        "interface ATM5/0/1": ("atm5/0/1", True),
    }
    for intf_text, vals in params.items():
        abbv, result_correct = vals[0], vals[1]
        intfobj = cfg.find_objects(intf_text, exactmatch=True)[0]
        assert intfobj.is_abbreviated_as(abbv) is result_correct


def testVal_IOSIntfLine_ordinal_list(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": (1, 0),
        "interface Serial 1/1": (1, 1),
        "interface GigabitEthernet4/1": (4, 1),
        "interface GigabitEthernet4/2": (4, 2),
        "interface GigabitEthernet4/3": (4, 3),
        "interface GigabitEthernet4/4": (4, 4),
        "interface GigabitEthernet4/5": (4, 5),
        "interface GigabitEthernet4/6": (4, 6),
        "interface GigabitEthernet4/7": (4, 7),
        "interface GigabitEthernet4/8.120": (4, 8),
        "interface ATM5/0/0": (5, 0, 0),
        "interface ATM5/0/0.32 point-to-point": (5, 0, 0),
        "interface ATM5/0/1": (5, 0, 1),
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check ordinal_list
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.ordinal_list
    assert result_correct == test_result


def testVal_IOSIntfLine_interface_number(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "1/0",
        "interface Serial 1/1": "1/1",
        "interface GigabitEthernet4/1": "4/1",
        "interface GigabitEthernet4/2": "4/2",
        "interface GigabitEthernet4/3": "4/3",
        "interface GigabitEthernet4/4": "4/4",
        "interface GigabitEthernet4/5": "4/5",
        "interface GigabitEthernet4/6": "4/6",
        "interface GigabitEthernet4/7": "4/7",
        "interface GigabitEthernet4/8.120": "4/8",
        "interface ATM5/0/0": "5/0/0",
        "interface ATM5/0/0.32 point-to-point": "5/0/0",
        "interface ATM5/0/1": "5/0/1",
    }
    test_result = dict()
    ## Parse all interface objects in self.c01 and check interface_number
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.interface_number
    assert result_correct == test_result


def testVal_IOSIntfLine_subinterface_number(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "1/0",
        "interface Serial 1/1": "1/1",
        "interface GigabitEthernet4/1": "4/1",
        "interface GigabitEthernet4/2": "4/2",
        "interface GigabitEthernet4/3": "4/3",
        "interface GigabitEthernet4/4": "4/4",
        "interface GigabitEthernet4/5": "4/5",
        "interface GigabitEthernet4/6": "4/6",
        "interface GigabitEthernet4/7": "4/7",
        "interface GigabitEthernet4/8.120": "4/8.120",
        "interface ATM5/0/0": "5/0/0",
        "interface ATM5/0/0.32 point-to-point": "5/0/0.32",
        "interface ATM5/0/1": "5/0/1",
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check subinterface_number
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.subinterface_number
    assert result_correct == test_result


def testVal_IOSIntfLine_port(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 1,
        "interface GigabitEthernet4/1": 1,
        "interface GigabitEthernet4/2": 2,
        "interface GigabitEthernet4/3": 3,
        "interface GigabitEthernet4/4": 4,
        "interface GigabitEthernet4/5": 5,
        "interface GigabitEthernet4/6": 6,
        "interface GigabitEthernet4/7": 7,
        "interface GigabitEthernet4/8.120": 8,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 1,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check port number
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.port
    assert result_correct == test_result


def testVal_IOSIntfLine_port_type():
    # Map a config line to result_correct
    result_map = {
        "interface Loopback 0": "Loopback",
        "interface Loopback1": "Loopback",
        "interface Serial 1/0": "Serial",
        "interface Ethernet4/1": "Ethernet",
        "interface Ethernet 4/1": "Ethernet",
        "interface FastEthernet4/1": "FastEthernet",
        "interface FastEthernet 4/1": "FastEthernet",
        "interface GigabitEthernet4/1": "GigabitEthernet",
        "interface GigabitEthernet 4/1": "GigabitEthernet",
        "interface GigabitEthernet4/8.120": "GigabitEthernet",
        "interface GigabitEthernet 4/8.120": "GigabitEthernet",
        "interface ATM5/0/0": "ATM",
        "interface ATM5/0/0.32 point-to-point": "ATM",
    }
    for cfgline, result_correct in result_map.items():
        cfg = CiscoConfParse([cfgline], factory=True)
        obj = cfg.ConfigObjs[0]
        assert obj.port_type == result_correct


def testVal_IOSIntfLine_description(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "Uplink to SBC F923X2K425",
        "interface Serial 1/1": "Uplink to AT&T",
        "interface GigabitEthernet4/1": "",
        "interface GigabitEthernet4/2": "",
        "interface GigabitEthernet4/3": "",
        "interface GigabitEthernet4/4": "",
        "interface GigabitEthernet4/5": "",
        "interface GigabitEthernet4/6": "Simulate a Catalyst6500 access port",
        "interface GigabitEthernet4/7": "Dot1Q trunk allowing vlans 2-4,7,10,11-19,21-4094",
        "interface GigabitEthernet4/8.120": "",
        "interface ATM5/0/0": "",
        "interface ATM5/0/0.32 point-to-point": "",
        "interface ATM5/0/1": "",
    }
    test_result = dict()
    ## Parse all interface objects in self.c01 and check description
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.description
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_bandwidth(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 1500,
        "interface Serial 1/1": 0,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in self.c01 and check bandwidth
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_bandwidth
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_delay(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 70,
        "interface Serial 1/1": 0,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check delay
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_delay
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_holdqueue_in(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 1000,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 500,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check holdqueue in
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_holdqueue_in
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_holdqueue_out(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 1000,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check holdqueue out
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_holdqueue_out
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_encapsulation(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "ppp",
        "interface Serial 1/1": "hdlc",
        "interface GigabitEthernet4/1": "",
        "interface GigabitEthernet4/2": "",
        "interface GigabitEthernet4/3": "",
        "interface GigabitEthernet4/4": "",
        "interface GigabitEthernet4/5": "",
        "interface GigabitEthernet4/6": "",
        "interface GigabitEthernet4/7": "",
        "interface GigabitEthernet4/8.120": "dot1q",
        "interface ATM5/0/0": "",
        "interface ATM5/0/0.32 point-to-point": "",
        "interface ATM5/0/1": "",
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check encapsulation
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_encapsulation
    assert result_correct == test_result


def testVal_IOSIntfLine_has_mpls(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": True,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_mpls
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_mpls
    assert result_correct == test_result


def testVal_IOSIntfLine_ipv4_addr_object01(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": IPv4Obj("1.1.1.1/30", strict=False),
        "interface Serial 1/1": IPv4Obj("1.1.1.9/31", strict=False),
        "interface GigabitEthernet4/1": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/2": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/3": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/4": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/5": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/6": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/7": IPv4Obj("127.0.0.1/32", strict=False),
        "interface GigabitEthernet4/8.120": IPv4Obj("1.1.2.254/24", strict=False),
        "interface ATM5/0/0": IPv4Obj("127.0.0.1/32", strict=False),
        "interface ATM5/0/0.32 point-to-point": IPv4Obj("1.1.1.5/30", strict=False),
        "interface ATM5/0/1": IPv4Obj("127.0.0.1/32", strict=False),
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check ipv4_addr_object
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.ipv4_addr_object
    assert result_correct == test_result


def testVal_IOSIntfLine_ipv4_addr_object02():
    """Ensure we raise an error for intf.ipv4_addr_object if the intf uses dhcp"""
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " ip address dhcp",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    with pytest.raises(DynamicAddressException):
        cfg.find_objects("^interface")[0].ipv4_addr_object


def testVal_IOSIntfLine_ip_network_object01():
    """Ensure we raise an error for intf.ip_network_object if the intf uses dhcp"""
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " ip address dhcp",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    with pytest.raises(DynamicAddressException):
        cfg.find_objects("^interface")[0].ip_network_object


def testVal_IOSIntfLine_has_autonegotiation(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": True,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": True,
        "interface GigabitEthernet4/4": True,
        "interface GigabitEthernet4/5": True,
        "interface GigabitEthernet4/6": True,
        "interface GigabitEthernet4/7": True,
        "interface GigabitEthernet4/8.120": True,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_autonegotiation
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_autonegotiation
    assert result_correct == test_result


def testVal_IOSIntfLine_has_manual_speed(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": True,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_manual_speed
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_manual_speed
    assert result_correct == test_result


def testVal_IOSIntfLine_has_manual_duplex(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": True,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_manual_duplex
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_manual_duplex
    assert result_correct == test_result


def testVal_IOSIntfLine_has_manual_carrierdelay(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": True,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in self.c01 and check has_manual_carrierdelay
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_manual_carrierdelay
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_carrierdelay(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0.0,
        "interface Serial 1/1": 0.0,
        "interface GigabitEthernet4/1": 0.0,
        "interface GigabitEthernet4/2": 0.0,
        "interface GigabitEthernet4/3": 0.0,
        "interface GigabitEthernet4/4": 0.0,
        "interface GigabitEthernet4/5": 0.0,
        "interface GigabitEthernet4/6": 0.0,
        "interface GigabitEthernet4/7": 0.0,
        "interface GigabitEthernet4/8.120": 0.0,
        "interface ATM5/0/0": 0.1,
        "interface ATM5/0/0.32 point-to-point": 0.0,
        "interface ATM5/0/1": 0.0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check manual_carrierdelay
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_carrierdelay
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_clock_rate(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 1500,
        "interface Serial 1/1": 0,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in self.c01 and check manual_clock_rate
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_clock_rate
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_mtu(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 0,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 9216,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check manual_mtu
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_mtu
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_mpls_mtu(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 1540,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check manual_mpls_mtu
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_mpls_mtu
    assert result_correct == test_result


def testVal_IOSIntfLine_manual_ip_mtu(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 0,
        "interface Serial 1/1": 1500,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 0,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 0,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check manual_ip_mtu
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.manual_ip_mtu
    assert result_correct == test_result


def testVal_IOSIntfLine_is_shutdown(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": True,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": False,
        "interface ATM5/0/1": True,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check is_shutdown
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.is_shutdown
    assert result_correct == test_result


def testVal_IOSIntfLine_vrf01(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "",
        "interface Serial 1/1": "",
        "interface GigabitEthernet4/1": "",
        "interface GigabitEthernet4/2": "",
        "interface GigabitEthernet4/3": "",
        "interface GigabitEthernet4/4": "",
        "interface GigabitEthernet4/5": "",
        "interface GigabitEthernet4/6": "",
        "interface GigabitEthernet4/7": "",
        "interface GigabitEthernet4/8.120": "TEST_100_001",
        "interface ATM5/0/0": "",
        "interface ATM5/0/0.32 point-to-point": "",
        "interface ATM5/0/1": "",
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check vrf
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.vrf
    assert result_correct == test_result


def testVal_IOSIntfLine_vrf02():
    lines = [
        "!",
        "interface GigabitEthernet 1/1",
        " vrf forwarding blue",
        " ip address 192.0.2.1 255.255.255.0",
        " no ip proxy-arp",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    intf_obj = cfg.find_objects("^interface")[0]
    assert intf_obj.vrf == "blue"


def testVal_IOSIntfLine_ipv4_addr(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "1.1.1.1",
        "interface Serial 1/1": "1.1.1.9",
        "interface GigabitEthernet4/1": "",
        "interface GigabitEthernet4/2": "",
        "interface GigabitEthernet4/3": "",
        "interface GigabitEthernet4/4": "",
        "interface GigabitEthernet4/5": "",
        "interface GigabitEthernet4/6": "",
        "interface GigabitEthernet4/7": "",
        "interface GigabitEthernet4/8.120": "1.1.2.254",
        "interface ATM5/0/0": "",
        "interface ATM5/0/0.32 point-to-point": "1.1.1.5",
        "interface ATM5/0/1": "",
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check ipv4_addr
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.ipv4_addr
    assert result_correct == test_result


def testVal_IOSIntfLine_ipv4_netmask(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": "255.255.255.252",
        "interface Serial 1/1": "255.255.255.254",
        "interface GigabitEthernet4/1": "",
        "interface GigabitEthernet4/2": "",
        "interface GigabitEthernet4/3": "",
        "interface GigabitEthernet4/4": "",
        "interface GigabitEthernet4/5": "",
        "interface GigabitEthernet4/6": "",
        "interface GigabitEthernet4/7": "",
        "interface GigabitEthernet4/8.120": "255.255.255.0",
        "interface ATM5/0/0": "",
        "interface ATM5/0/0.32 point-to-point": "255.255.255.252",
        "interface ATM5/0/1": "",
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check ipv4_netmask
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.ipv4_netmask
    assert result_correct == test_result


def testVal_IOSIntfLine_ipv4_masklength(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": 30,
        "interface Serial 1/1": 31,
        "interface GigabitEthernet4/1": 0,
        "interface GigabitEthernet4/2": 0,
        "interface GigabitEthernet4/3": 0,
        "interface GigabitEthernet4/4": 0,
        "interface GigabitEthernet4/5": 0,
        "interface GigabitEthernet4/6": 0,
        "interface GigabitEthernet4/7": 0,
        "interface GigabitEthernet4/8.120": 24,
        "interface ATM5/0/0": 0,
        "interface ATM5/0/0.32 point-to-point": 30,
        "interface ATM5/0/1": 0,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check ipv4_masklength
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.ipv4_masklength
    assert result_correct == test_result


def testVal_IOSIntfLine_in_ipv4_subnet(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": True,
        "interface Serial 1/1": True,
        "interface GigabitEthernet4/1": None,
        "interface GigabitEthernet4/2": None,
        "interface GigabitEthernet4/3": None,
        "interface GigabitEthernet4/4": None,
        "interface GigabitEthernet4/5": None,
        "interface GigabitEthernet4/6": None,
        "interface GigabitEthernet4/7": None,
        "interface GigabitEthernet4/8.120": True,
        "interface ATM5/0/0": None,
        "interface ATM5/0/0.32 point-to-point": True,
        "interface ATM5/0/1": None,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check in_ipv4_subnet
    ##   where the subnet is 1.1.0.0/22
    test_network = IPv4Obj("1.1.0.0/22", strict=False)
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.in_ipv4_subnet(test_network)
    assert result_correct == test_result


def testVal_IOSIntfLine_in_ipv4_subnets(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": True,
        "interface Serial 1/1": True,
        "interface GigabitEthernet4/1": None,
        "interface GigabitEthernet4/2": None,
        "interface GigabitEthernet4/3": None,
        "interface GigabitEthernet4/4": None,
        "interface GigabitEthernet4/5": None,
        "interface GigabitEthernet4/6": None,
        "interface GigabitEthernet4/7": None,
        "interface GigabitEthernet4/8.120": True,
        "interface ATM5/0/0": None,
        "interface ATM5/0/0.32 point-to-point": True,
        "interface ATM5/0/1": None,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check in_ipv4_subnets
    test_network1 = IPv4Obj("1.1.0.0/23", strict=False)
    test_network2 = IPv4Obj("1.1.2.0/23", strict=False)
    networks = set([test_network1, test_network2])
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.in_ipv4_subnets(networks)
    assert result_correct == test_result


def testVal_IOSIntfLine_has_no_icmp_unreachables(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": True,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_no_icmp_unreachables
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_no_icmp_unreachables
    assert result_correct == test_result


def testVal_IOSIntfLine_has_no_icmp_redirects(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": True,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_no_icmp_redirects
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_no_icmp_redirects
    assert result_correct == test_result


def testVal_IOSIntfLine_has_no_ip_proxyarp(parse_c03_factory):
    cfg = parse_c03_factory
    result_correct = {
        "interface Serial 1/0": False,
        "interface Serial 1/1": False,
        "interface GigabitEthernet4/1": False,
        "interface GigabitEthernet4/2": False,
        "interface GigabitEthernet4/3": False,
        "interface GigabitEthernet4/4": False,
        "interface GigabitEthernet4/5": False,
        "interface GigabitEthernet4/6": False,
        "interface GigabitEthernet4/7": False,
        "interface GigabitEthernet4/8.120": False,
        "interface ATM5/0/0": False,
        "interface ATM5/0/0.32 point-to-point": True,
        "interface ATM5/0/1": False,
    }
    test_result = dict()
    ## Parse all interface objects in c01 and check has_no_ip_proxyarp
    for intf_obj in cfg.find_objects("^interface"):
        test_result[intf_obj.text] = intf_obj.has_no_ip_proxyarp
    assert result_correct == test_result


###
### ------ Static Route tests
###


def testVal_IOSRouteLine_01():
    line = "ip route 0.0.0.0 0.0.0.0 172.16.1.254"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is True  # All non-vrf routes have global NHs
    assert 1 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_02():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 172.16.1.254"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is False
    assert 1 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_03():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 172.16.1.254 254"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is False
    assert 254 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_04():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 172.16.1.254 global 254"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is True
    assert 254 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_05():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 172.16.1.254 global 254 track 35"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "35" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is True
    assert 254 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_06():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 FastEthernet0/0 172.16.1.254 global 254 track 35"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "FastEthernet0/0" == obj.next_hop_interface
    assert "172.16.1.254" == obj.next_hop_addr
    assert obj.multicast is False
    assert "35" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is True
    assert 254 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_07():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 FastEthernet0/0 254 track 35"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "FastEthernet0/0" == obj.next_hop_interface
    assert "" == obj.next_hop_addr
    assert obj.multicast is False
    assert "35" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is False  # TODO: Figure out if False is right
    assert 254 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_08():
    line = "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 FastEthernet0/0 254 track 35 tag 20"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "FastEthernet0/0" == obj.next_hop_interface
    assert "" == obj.next_hop_addr
    assert obj.multicast is False
    assert "35" == obj.tracking_object_name
    assert "" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is False  # TODO: Figure out if False is right
    assert 254 == obj.admin_distance
    assert "20" == obj.tag


def testVal_IOSRouteLine_09():
    line = (
        "ip route vrf mgmtVrf 0.0.0.0 0.0.0.0 FastEthernet0/0 254 name foobarme tag 20"
    )
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ip" == obj.address_family
    assert "mgmtVrf" == obj.vrf
    assert "0.0.0.0" == obj.network
    assert "0.0.0.0" == obj.netmask
    assert 0 == obj.masklen
    assert "FastEthernet0/0" == obj.next_hop_interface
    assert "" == obj.next_hop_addr
    assert obj.multicast is False
    assert "" == obj.tracking_object_name
    assert "foobarme" == obj.route_name
    assert obj.permanent is False
    assert obj.global_next_hop is False  # TODO: Figure out if False is right
    assert 254 == obj.admin_distance
    assert "20" == obj.tag


def testVal_IOSRouteLine_10():
    line = "ipv6 route ::/0 2001:DEAD:BEEF::1"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ipv6" == obj.address_family
    assert "" == obj.vrf
    assert "::" == obj.network
    assert "::" == obj.netmask
    assert 0 == obj.masklen
    assert "" == obj.next_hop_interface
    assert "2001:DEAD:BEEF::1" == obj.next_hop_addr
    assert obj.multicast is False
    # assert ''==obj.tracking_object_name
    # assert ''==obj.route_name
    # assert obj.permanent is False
    # assert obj.global_next_hop is True    # All non-vrf routes have global NHs
    assert 1 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_11():
    line = "ipv6 route 2001:DEAD:BEEF::1/32 Serial 1/0 201"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ipv6" == obj.address_family
    assert "" == obj.vrf
    assert "2001:DEAD:BEEF::1" == obj.network
    assert "ffff:ffff::" == obj.netmask
    assert 32 == obj.masklen
    assert "Serial 1/0" == obj.next_hop_interface
    assert "" == obj.next_hop_addr
    assert obj.multicast is False
    # assert ''==obj.tracking_object_name
    # assert ''==obj.route_name
    # assert obj.permanent is False
    # assert obj.global_next_hop is True    # All non-vrf routes have global NHs
    assert 201 == obj.admin_distance
    assert "" == obj.tag


def testVal_IOSRouteLine_12():
    line = "ipv6 route 2001::/16 Tunnel0 2002::1 multicast"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "ipv6" == obj.address_family
    assert "" == obj.vrf
    assert "2001::" == obj.network
    assert "ffff::" == obj.netmask
    assert 16 == obj.masklen
    assert "Tunnel0" == obj.next_hop_interface
    assert "2002::1" == obj.next_hop_addr
    assert obj.multicast is True
    # assert ''==obj.tracking_object_name
    # assert ''==obj.route_name
    # assert obj.permanent is False
    # assert obj.global_next_hop is True    # All non-vrf routes have global NHs
    assert 1 == obj.admin_distance
    assert "" == obj.tag


###
### ------ IPv4 Helper-Addresses --------
###


def testVal_IOSIPv4HelperAddress_01():
    CONFIG = [
        "interface GigabitEthernet0/1",
        " ip address 172.16.30.1 255.255.255.0",
        " ip helper-address global 10.1.1.1",
        " ip helper-address 10.1.1.2",
        " ip helper-address vrf FOO 10.1.1.3",
    ]
    result_correct = [
        {"global": True, "addr": "10.1.1.1", "vrf": ""},
        {"global": False, "addr": "10.1.1.2", "vrf": ""},
        {"global": False, "addr": "10.1.1.3", "vrf": "FOO"},
    ]
    parse = CiscoConfParse(CONFIG, syntax="ios", factory=True)
    obj = parse.find_objects("^interface")[0]
    assert obj.ip_helper_addresses == result_correct


###
### ------ AAA Tests --------
###


def testVal_IOSAaaLoginAuthenticationLine():
    line = "aaa authentication login default group tacacs+ local-case"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "tacacs+" == obj.group
    assert "default" == obj.list_name
    assert ["local-case"] == obj.methods


def testVal_IOSAaaEnableAuthenticationLine():
    line = "aaa authentication enable default group tacacs+ enable"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "tacacs+" == obj.group
    assert "default" == obj.list_name
    assert ["enable"] == obj.methods


def testVal_IOSAaaCommandsAuthorizationLine():
    line = "aaa authorization commands 15 default group tacacs+ local"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]

    assert 15 == obj.level
    assert "tacacs+" == obj.group
    assert "default" == obj.list_name
    assert ["local"] == obj.methods


def testVal_IOSAaaCommandsAccountingLine():
    line = "aaa accounting commands 15 default start-stop group tacacs+"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert 15 == obj.level
    assert "tacacs+" == obj.group
    assert "default" == obj.list_name
    assert "start-stop" == obj.record_type


def testVal_IOSAaaExecAccountingLine():
    line = "aaa accounting exec default start-stop group tacacs+"
    cfg = CiscoConfParse([line], factory=True)
    obj = cfg.ConfigObjs[0]
    assert "tacacs+" == obj.group
    assert "default" == obj.list_name
    assert "start-stop" == obj.record_type


def testVal_IOSAaaGroupServerLine_01():
    lines = [
        "!",
        "aaa group server tacacs+ TACACS_01",
        " server-private 192.0.2.10 key cisco",
        " server-private 192.0.2.11 key cisco",
        " ip vrf forwarding VRF_001",
        " ip tacacs source-interface FastEthernet0/48",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    obj = cfg.ConfigObjs[1]
    assert "TACACS_01" == obj.group
    assert "tacacs+" == obj.protocol
    assert set(["192.0.2.10", "192.0.2.11"]) == obj.server_private
    assert "VRF_001" == obj.vrf
    assert "FastEthernet0/48" == obj.source_interface


def testVal_IOSAaaGroupServerLine_02():
    """Test for Github issue #64"""
    lines = [
        "!",
        "aaa group server tacacs+ TACACS_01 ",
        " server-private 192.0.2.10 key cisco",
        " server-private 192.0.2.11 key cisco",
        " ip vrf forwarding VRF_001",
        " ip tacacs source-interface FastEthernet0/48",
        "!",
    ]
    cfg = CiscoConfParse(lines, factory=True)
    obj = cfg.ConfigObjs[1]
    assert "TACACS_01" == obj.group
    assert "tacacs+" == obj.protocol
    assert set(["192.0.2.10", "192.0.2.11"]) == obj.server_private
    assert "VRF_001" == obj.vrf
    assert "FastEthernet0/48" == obj.source_interface
