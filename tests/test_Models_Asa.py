""" test_Models_Asa.py - Parse, Query, Build, and Modify IOS-style configs

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
     mike [~at~] pennington [.dot.] net
"""

from collections.abc import MutableSequence
import uuid
import sys
import re
import os

sys.path.insert(0, "..")

import pytest
from conftest import parse_a01, parse_a01_factory

from ciscoconfparse.ciscoconfparse import CiscoConfParse
from ciscoconfparse.models_asa import ASAObjGroupService
from ciscoconfparse.ccp_util import L4Object
from ciscoconfparse.ccp_util import IPv4Obj

if sys.version_info[0] < 3:
    from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
else:
    from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address

from loguru import logger




def testVal_Access_List(parse_a01_factory):
    result_correct = {}
    assert len(parse_a01_factory.objs.access_list["INSIDE_in"]) == 4


def testParse_asa_factory(config_a02):
    parse = CiscoConfParse(config_a02, syntax="asa", factory=True)
    assert (parse is not None)


def testVal_Names(parse_a01, parse_a01_factory):
    result_correct = {
        "dmzsrv00": "1.1.3.10",
        "dmzsrv01": "1.1.3.11",
        "dmzsrv02": "1.1.3.12",
        "dmzsrv03": "1.1.3.13",
        "loghost01": "1.1.2.20",
    }
    assert parse_a01.ConfigObjs.names == result_correct
    assert parse_a01_factory.ConfigObjs.names == result_correct


def testVal_object_group_network_01():
    """Test object group network results"""
    conf = [
        "!",
        "name 1.1.2.20 loghost01",
        "!",
        "object-group network INSIDE_addrs",
        " network-object host loghost01",
        " network-object host 1.1.2.1",
        " network-object 1.1.2.2 255.255.255.255",
        " network-object 1.1.2.0 255.255.255.0",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, syntax="asa", factory=True)
    obj = cfg_factory.find_objects(r"object-group\snetwork")[0]

    result_correct_01 = [
        IPv4Obj("1.1.2.20/32"),
        IPv4Obj("1.1.2.1/32"),
        IPv4Obj("1.1.2.2/32"),
        IPv4Obj("1.1.2.0/24"),
    ]
    result_correct_02 = ["1.1.2.20", "1.1.2.1", "1.1.2.2", "1.1.2.0/255.255.255.0"]
    # Ensure obj.name is set correctly
    assert obj.name == "INSIDE_addrs"
    assert obj.networks == result_correct_01
    assert obj.network_strings == result_correct_02
    ## Test obj.networks again to test the result_cache
    assert obj.networks == result_correct_01


def testVal_object_group_network_02():
    """Test recursion through a group object"""
    conf = [
        "!",
        "name 1.1.2.20 loghost01",
        "name 1.2.2.20 loghost02",
        "!",
        "object-group network INSIDE_recurse",
        " network-object host loghost02",
        "object-group network INSIDE_addrs",
        " network-object host loghost01",
        " network-object host 1.1.2.1",
        " network-object 1.1.2.2 255.255.255.255",
        " network-object 1.1.2.0 255.255.255.0",
        " group-object INSIDE_recurse",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")
    obj = cfg_factory.find_objects(r"object-group\snetwork")[1]

    result_correct_01 = [
        IPv4Obj("1.1.2.20/32"),
        IPv4Obj("1.1.2.1/32"),
        IPv4Obj("1.1.2.2/32"),
        IPv4Obj("1.1.2.0/24"),
        IPv4Obj("1.2.2.20/32"),
    ]
    result_correct_02 = [
        "1.1.2.20",
        "1.1.2.1",
        "1.1.2.2",
        "1.1.2.0/255.255.255.0",
        "1.2.2.20",
    ]
    # Ensure obj.name is set correctly
    assert obj.name == "INSIDE_addrs"
    assert obj.networks == result_correct_01
    assert obj.network_strings == result_correct_02
    ## Test obj.networks again to test the result_cache
    assert obj.networks == result_correct_01


def testVal_ipv4_addr_01():
    conf = [
        "hostname MYASA",
        "!",
        "interface Ethernet0/0",
        " nameif OUTSIDE",
        " ip address 198.101.172.106 255.255.255.128 standby 198.101.172.107",
        " ipv6 address 2001:dead:beef::1/64 standby 2001:dead:beef::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/1",
        " nameif INSIDE",
        " ip address 192.0.2.254 255.255.255.0",
        " ipv6 address fd80::1/64 standby fd80::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/2",
        " shutdown",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/0$")[0]
    # Ensure obj.ipv4_addr is set correctly
    assert obj.ipv4_addr == "198.101.172.106"
    assert obj.ipv4_standby_addr == "198.101.172.107"

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/1$")[0]
    assert obj.ipv4_addr == "192.0.2.254"

def testVal_ipv6_addr_01():
    conf = [
        "hostname MYASA",
        "!",
        "interface Ethernet0/0",
        " nameif OUTSIDE",
        " ip address 198.101.172.106 255.255.255.128 standby 198.101.172.107",
        " ipv6 address 2001:dead:beef::1/64 standby 2001:dead:beef::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/1",
        " nameif INSIDE",
        " ip address 192.0.2.254 255.255.255.0",
        " ipv6 address fd80::1/64 standby fd80::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/2",
        " shutdown",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/0$")[0]
    assert obj.ipv6_addr == "2001:dead:beef::1"
    assert obj.ipv6_standby_addr == "2001:dead:beef::2"
    assert obj.ipv6_masklength == 64

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/1$")[0]
    assert obj.ipv6_addr == "fd80::1"
    assert obj.ipv6_standby_addr == "fd80::2"
    assert obj.ipv6_masklength == 64

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/2$")[0]
    assert obj.ipv6_addr == ""
    assert obj.ipv6_standby_addr == ""
    assert obj.ipv6_masklength == 0

def testVal_interface_name_01():
    conf = [
        "hostname MYASA",
        "!",
        "interface Ethernet0/0",
        " nameif OUTSIDE",
        " ip address 198.101.172.106 255.255.255.128 standby 198.101.172.107",
        " ipv6 address 2001:dead:beef::1/64 standby 2001:dead:beef::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/1",
        " nameif INSIDE",
        " ip address 192.0.2.254 255.255.255.0",
        " ipv6 address fd80::1/64 standby fd80::2",
        " ipv6 enable",
        "!",
        "interface Ethernet0/2",
        " shutdown",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")

    obj = cfg_factory.find_objects(r"^interface\sEthernet0\/0$")[0]
    assert obj.name == "Ethernet0/0"

def testVal_object_group_service_01():
    ## This can only be configured as protocol object-group
    conf = [
        "!",
        "object-group service APP01_svc",
        " service-object tcp destination smtp",
        " service-object tcp destination https",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")
    obj = cfg_factory.find_objects(r"object-group\sservice")[0]
    result_correct = [
        L4Object(protocol="tcp", port_spec="eq 25", syntax="asa"),
        L4Object(protocol="tcp", port_spec="eq 443", syntax="asa"),
    ]
    assert obj.name == "APP01_svc"
    assert obj.ports == result_correct
    assert obj.L4Objects_are_directional is True
    assert obj.protocol_type == ""


@pytest.mark.xfail(
    sys.version_info[0] == 3 and sys.version_info[1] == 2,
    reason="Known failure in Python3.2",
)
def testVal_object_group_service_02():
    ## This can only be configured as an object group after a host / network
    conf = [
        "!",
        "object-group service APP02_svc tcp",
        " port-object eq smtp",
        " port-object eq https",
        " port-object range 8080 8081",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")
    obj = cfg_factory.find_objects(r"object-group\sservice")[0]
    result_correct = [
        L4Object(protocol="tcp", port_spec="eq 25", syntax="asa"),
        L4Object(protocol="tcp", port_spec="eq 443", syntax="asa"),
        L4Object(protocol="tcp", port_spec="range 8080 8081", syntax="asa"),
    ]
    assert obj.name == "APP02_svc"
    assert obj.ports == result_correct
    assert obj.L4Objects_are_directional is False
    assert obj.protocol_type == "tcp"


def testVal_object_group_service_03():
    ## This can only be configured as an object group after a host / network
    conf = [
        "!",
        "object-group service APP03_svc tcp-udp",
        " port-object eq domain",
        "!",
    ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax="asa")
    obj = cfg_factory.find_objects(r"object-group\sservice")[0]
    ## Test whether the proper port objects are returned
    results_correct = [
        L4Object(port_spec="eq 53", protocol="tcp", syntax="asa"),
        L4Object(port_spec="eq 53", protocol="udp", syntax="asa"),
    ]
    assert obj.name == "APP03_svc"
    assert obj.ports == results_correct
    assert obj.L4Objects_are_directional is False
    assert obj.protocol_type == "tcp-udp"


@pytest.mark.parametrize(
    "line",
    [
        "access-list TESTME_01 remark TESTING THE REMARK FIELD",
        "access-list TESTME_01 extended permit ip any any",
        "access-list TESTME_01 extended permit ip any any log",
        "access-list TESTME_01 extended permit ip any any log disable time-range MYTIME",
        "access-list TESTME_01 extended permit ip any any log informational disable time-range MYTIME",
        "access-list TESTME_01 extended deny ip any any",
        "access-list TESTME_01 extended deny ip any any log",
        "access-list TESTME_01 extended deny ip any any log informational disable time-range MYTIME",
        "access-list TESTME_01 extended deny ip any4 any",
        "access-list TESTME_01 extended deny ip any any4 log",
        "access-list TESTME_01 extended deny ip any4 any4 log disable",
        "access-list TESTME_01 extended deny ip any4 any4 log disable time-range MYTIME",
        "access-list TESTME_01 extended deny ip any4 any4 log informational disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp any4 eq www any",
        "access-list TESTME_01 extended deny tcp any any4 eq https log",
        "access-list TESTME_01 extended deny tcp any4 eq 1024 any4 eq www log disable",
        "access-list TESTME_01 extended deny tcp any4 eq 1024 any4 eq www log disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp any4 eq 1024 any4 eq www log informational disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp any4 eq www any gt 1024",
        "access-list TESTME_01 extended deny tcp any gt 1024 any4 eq https log",
        "access-list TESTME_01 extended deny tcp any4 gt 1024 any4 eq www log disable",
        "access-list TESTME_01 extended deny tcp any4 gt 1024 any4 eq www log disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp any4 gt 1024 any4 eq www log informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp any4 neq www any gt 1024",
        "access-list TESTME_01 extended permit tcp any gt 1024 any4 neq https log",
        "access-list TESTME_01 extended permit tcp any4 gt 1024 any4 neq www log disable",
        "access-list TESTME_01 extended permit tcp any4 gt 1024 any4 neq www log disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp any4 gt 1024 any4 neq www log  informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit object-group MYPROTO object SRC object DST",
        "access-list TESTME_01 extended permit object-group MYPROTO object SRC object DST log",
        "access-list TESTME_01 extended permit object-group MYPROTO object SRC object DST log disable",
        "access-list TESTME_01 extended permit object-group MYPROTO object SRC object DST log disable time-range MYTIME",
        "access-list TESTME_01 extended permit object-group MYPROTO object SRC object DST log informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object SRC gt 1023 object DST eq ssh",
        "access-list TESTME_01 extended permit tcp object SRC gt 1023 object DST eq ssh log",
        "access-list TESTME_01 extended permit tcp object SRC gt 1023 object DST eq ssh log disable",
        "access-list TESTME_01 extended permit tcp object SRC gt 1023 object DST eq ssh log disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object SRC gt 1023 object DST eq ssh log informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit object-group MYPROTO object-group SRC object-group DST",
        "access-list TESTME_01 extended permit object-group MYPROTO object-group SRC object-group DST log",
        "access-list TESTME_01 extended permit object-group MYPROTO object-group SRC object-group DST log disable",
        "access-list TESTME_01 extended permit object-group MYPROTO object-group SRC object-group DST log disable time-range MYTIME",
        "access-list TESTME_01 extended permit object-group MYPROTO object-group SRC object-group DST log  informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object-group SRC object-group DST",
        "access-list TESTME_01 extended permit tcp object-group SRC object-group DST log",
        "access-list TESTME_01 extended permit tcp object-group SRC object-group DST log disable",
        "access-list TESTME_01 extended permit tcp object-group SRC object-group DST log disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object-group SRC object-group DST log  informational disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp object-group SRC lt 1024 object-group DST eq ssh",
        "access-list TESTME_01 extended deny tcp object-group SRC lt 1024 object-group DST eq ssh log",
        "access-list TESTME_01 extended deny tcp object-group SRC lt 1024 object-group DST eq ssh log disable",
        "access-list TESTME_01 extended deny tcp object-group SRC lt 1024 object-group DST eq ssh log disable time-range MYTIME",
        "access-list TESTME_01 extended deny tcp object-group SRC lt 1024 object-group DST eq ssh log  informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object-group SRC range 1 1024 object-group DST eq ssh",
        "access-list TESTME_01 extended permit tcp object-group SRC range 1 1024 object-group DST eq ssh log",
        "access-list TESTME_01 extended permit tcp object-group SRC range 1 1024 object-group DST eq ssh log disable",
        "access-list TESTME_01 extended permit tcp object-group SRC range 1 1024 object-group DST eq ssh log disable time-range MYTIME",
        "access-list TESTME_01 extended permit tcp object-group SRC range 1 1024 object-group DST eq ssh log  informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit 47 object-group SRC object-group DST",
        "access-list TESTME_01 extended permit 47 object-group SRC object-group DST log",
        "access-list TESTME_01 extended permit 47 object-group SRC object-group DST log disable",
        "access-list TESTME_01 extended permit 47 object-group SRC object-group DST log disable time-range MYTIME",
        "access-list TESTME_01 extended permit 47 object-group SRC object-group DST log informational disable time-range MYTIME",
        "access-list TESTME_01 extended permit icmp object-group SRC object-group DST",
        "access-list TESTME_01 extended permit icmp object-group SRC object-group DST echo",
        "access-list TESTME_01 extended permit icmp object-group SRC object-group DST echo log",
        "access-list TESTME_01 extended permit icmp object-group SRC object-group DST echo log disable",
        "access-list TESTME_01 extended permit icmp object-group SRC object-group DST echo log disable time-range MYTIME",
        "access-list TESTME_01 extended permit icmp 10.0.0.0 255.0.0.0 object-group DST",
        "access-list TESTME_01 extended permit icmp 10.0.0.0 255.0.0.0 object-group DST echo",
        "access-list TESTME_01 extended permit icmp 10.0.0.0 255.0.0.0 object-group DST echo log",
        "access-list TESTME_01 extended permit icmp 10.0.0.0 255.0.0.0 object-group DST echo log disable",
        "access-list TESTME_01 extended permit icmp 10.0.0.0 255.0.0.0 object-group DST echo log disable time-range MYTIME",
        "access-list TESTME_01 standard permit 10.0.0.0 255.0.0.0",
    ],
)
def testVal_ASAAclLine_DNA(line):
    """Ensure that valid ACL lines are classified as an ASAAclLine"""
    cfg = CiscoConfParse([line], factory=True, syntax="asa")
    assert cfg.objs[0].dna == "ASAAclLine"
    assert cfg.objs[0].result_dict != {}


@pytest.mark.skip(reason="no way of currently testing this")
def testVal_ASAAclLine_DNA_negative():

    # Ensure that parsing the bogus ACL line in a config list raises a ValueError
    #     but ValueError triggers a SystemExit
    broken_config_list = ["access-list TESTME_01 extended VpAAmit987 ip any any log deactivate"]
    broken_config_list = ["access-list TESTME_01 extended VpAAmit987 ip any any log"]
    broken_filepath = "/%s" % str(uuid.uuid4())

    try:
        if isinstance(broken_config_list, (MutableSequence, tuple, list,)):
            parse = CiscoConfParse(broken_config_list, factory=True, syntax="asa")

        # Ensure that parsing the bogus filepath string raises OSError
        elif isinstance(broken_filepath, str):
            parse = CiscoConfParse(broken_filepath, factory=True, syntax="asa")

        return parse

    except ValueError as eee:
        # with pytest.raises(ValueError):
        # with pytest.raises(OSError):
        with pytest.raises(ValueError):
            logger.critical(str(eee))
            raise ValueError(str(eee))
