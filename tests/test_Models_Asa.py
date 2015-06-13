#!/usr/bin/env python

import sys
import re
import os
THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))

import pytest
from conftest import parse_a01, parse_a01_factory

from ciscoconfparse import CiscoConfParse
from models_asa import ASAObjGroupService
from ccp_util import L4Object
from ccp_util import IPv4Obj

if sys.version_info[0]<3:
    from ipaddr import IPv4Network, IPv6Network, IPv4Address, IPv6Address
else:
    from ipaddress import IPv4Network, IPv6Network, IPv4Address, IPv6Address


@pytest.mark.parametrize("cfg", [
    None,
    ])
def testVal_Names(cfg, parse_a01, parse_a01_factory):
    result_correct = {'dmzsrv00': '1.1.3.10', 
        'dmzsrv01': '1.1.3.11', 
        'dmzsrv02': '1.1.3.12', 
        'dmzsrv03': '1.1.3.13', 
        'loghost01': '1.1.2.20',
    }
    assert parse_a01.ConfigObjs.names==result_correct
    assert parse_a01_factory.ConfigObjs.names==result_correct

def testVal_object_group_network():
    conf = ['!',
        'name 1.1.2.20 loghost01',
        '!',
        'object-group network INSIDE_addrs',
        ' network-object host loghost01',
        ' network-object host 1.1.2.1',
        ' network-object 1.1.2.2 255.255.255.255',
        ' network-object 1.1.2.0 255.255.255.0',
        '!',]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax='asa')
    obj = cfg_factory.find_objects(r'object-group\snetwork')[0]

    result_correct = [IPv4Obj('1.1.2.20/32'), IPv4Obj('1.1.2.1/32'),
        IPv4Obj('1.1.2.2/32'), IPv4Obj('1.1.2.0/24')]
    # Ensure obj.name is set correctly
    assert obj.name=="INSIDE_addrs"
    assert obj.networks==result_correct

def testVal_ipv4_addr():
    conf = ['!',
        'interface Ethernet0/0',
        ' nameif OUTSIDE',
        ' ip address 198.101.172.106 255.255.255.128 standby 198.101.172.107',
        '!',
        'interface Ethernet0/1',
        ' nameif INSIDE',
        ' ip address 192.0.2.254 255.255.255.0',
        '!',
        ]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax='asa')

    obj = cfg_factory.find_objects(r'^interface\sEthernet0\/0$')[0]
    # Ensure obj.ipv4_addr is set correctly
    assert obj.ipv4_addr=='198.101.172.106'
    assert obj.ipv4_standby_addr=='198.101.172.107'

    obj = cfg_factory.find_objects(r'^interface\sEthernet0\/1$')[0]
    assert obj.ipv4_addr=='192.0.2.254'

def testVal_object_group_service_01():
    ## This can only be configured as protocol object-group
    conf = ['!',
        'object-group service APP01_svc',
        ' service-object tcp destination smtp',
        ' service-object tcp destination https',
        '!',]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax='asa')
    obj = cfg_factory.find_objects(r'object-group\sservice')[0]
    result_correct = [L4Object(protocol='tcp', port_spec='eq 25', 
        syntax='asa'), L4Object(protocol='tcp', port_spec='eq 443', 
        syntax='asa')]
    assert (obj.name=='APP01_svc')
    assert (obj.ports==result_correct)
    assert (obj.L4Objects_are_directional is True)
    assert (obj.protocol_type=='')

@pytest.mark.xfail(sys.version_info[0]==3 and sys.version_info[1]==2,
                   reason="Known failure in Python3.2")
def testVal_object_group_service_02():
    ## This can only be configured as an object group after a host / network
    conf = ['!',
        'object-group service APP02_svc tcp',
        ' port-object eq smtp',
        ' port-object eq https',
        ' port-object range 8080 8081',
        '!',]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax='asa')
    obj = cfg_factory.find_objects(r'object-group\sservice')[0]
    result_correct = [L4Object(protocol='tcp', port_spec='eq 25', 
        syntax='asa'), L4Object(protocol='tcp', port_spec='eq 443', 
        syntax='asa'), L4Object(protocol='tcp', port_spec='range 8080 8081',
        syntax='asa')]
    assert (obj.name=='APP02_svc')
    assert (obj.ports==result_correct)
    assert (obj.L4Objects_are_directional is False)
    assert (obj.protocol_type=='tcp')


def testVal_object_group_service_03():
    ## This can only be configured as an object group after a host / network
    conf = ['!',
        'object-group service APP03_svc tcp-udp',
        ' port-object eq domain',
        '!',]
    cfg_factory = CiscoConfParse(conf, factory=True, syntax='asa')
    obj = cfg_factory.find_objects(r'object-group\sservice')[0]
    ## Test whether the proper port objects are returned
    results_correct = [L4Object(port_spec='eq 53', protocol='tcp', 
        syntax='asa'), 
        L4Object(port_spec='eq 53', protocol='udp', syntax='asa')]
    assert (obj.name=='APP03_svc')
    assert (obj.ports==results_correct)
    assert (obj.L4Objects_are_directional is False)
    assert (obj.protocol_type=='tcp-udp')
