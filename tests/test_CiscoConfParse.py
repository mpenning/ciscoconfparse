from operator import attrgetter
from itertools import repeat
from copy import deepcopy
from mock import patch
import platform
import sys
import re
import os
THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))

from ciscoconfparse import CiscoConfParse, IOSCfgLine, IOSIntfLine
from ciscoconfparse import CiscoPassword
from ccp_util import IPv4Obj
from passlib.hash import cisco_type7
import pytest

def testValues_banner_delimiter_01():
    # Test banner delimiter on the same lines
    CONFIG = ['!', 'banner motd ^   trivial banner here ^', 'end']
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects('^banner')[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

def testValues_banner_delimiter_02():
    # Test multiple banner delimiters on the same lines
    CONFIG = ['!', 'banner motd ^   trivial banner here ^^', 'end']
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects('^banner')[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

def testValues_banner_delimiter_03():
    # Test banner delimiter on different lines
    CONFIG = ['!', 'banner motd ^', '    trivial banner here ^', 'end']
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects('^banner')[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

def testValues_banner_delimiter_04():
    # Test multiple banner delimiters on different lines
    CONFIG = ['!', 'banner motd ^', '    trivial banner here ^^', 'end']
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects('^banner')[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

def testValues_banner_delimiter_05():
    # Test multiple banners
    CONFIG = ['!', 'banner motd ^', '    trivial banner1 here ^', 
        'banner exec ^', '    trivial banner2 here ^',
        'end']
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects('^banner\smotd')[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

    bannerobj = parse.find_objects('^banner\sexec')[0]
    BANNER_LINE_NUMBER = 3
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

def testValues_banner_delete_01():
    # Ensure multiline banners are correctly deleted
    CONFIG = ['!', 
        'banner motd ^', '    trivial banner1 here ^', 
        'interface GigabitEthernet0/0',
        ' ip address 192.0.2.1 255.255.255.0',
        'banner exec ^', '    trivial banner2 here ^',
        'end']
    parse = CiscoConfParse(CONFIG)
    for obj in parse.find_objects('^banner'):
        obj.delete()
    parse.commit()
    assert parse.find_objects('^banner')==[]

def testValues_banner_delete_02():
    # Ensure multiline banners are correctly deleted
    #
    # Check for Github issue #37
    CONFIG = ['!', 
        'interface GigabitEthernet0/0',
        ' ip address 192.0.2.1 255.255.255.0',
        'banner motd ^', '    trivial banner1 here ^', 
        'interface GigabitEthernet0/1',
        ' ip address 192.0.2.1 255.255.255.0',
        'banner exec ^', '    trivial banner2 here ^',
        'end']
    parse = CiscoConfParse(CONFIG)
    for obj in parse.find_objects('^banner'):
        obj.delete()
    parse.commit()

    assert parse.find_objects('^banner')==[]

    # Github issue #37 assigned Gi0/1's child to Gi0/0 after deleting
    #  the banner motd line...
    for obj in parse.find_objects('^interface'):
        assert len(obj.children)==1

def testValues_banner_child_parsing_01(parse_c01):
    """Associate banner lines as parent / child"""
    result_correct = {
        59: 58,
        60: 58,
        61: 58,
        62: 58,
        63: 63,  # Ensure the line *after* the banner isn't a child
    }
    banner_obj = parse_c01.find_objects('^banner')[0]

    # Check banner's parent line (should be its line number)
    assert banner_obj.parent.linenum == 58
    for child in banner_obj.all_children:
        test_result = child.parent.linenum
        assert result_correct[child.linenum]==test_result

def testValues_parent_child_parsing_01(parse_c01):
    parent_intf = {
        # Line 13's parent should be 11, etc...
        13: 11,
        16: 15,
        17: 15,
        18: 15,
        19: 15,
        22: 21,
        23: 21,
        24: 21,
        25: 21,
    }
    for obj in parse_c01.find_objects(''):
        result_correct = parent_intf.get(obj.linenum, False)
        if result_correct:
            test_result = obj.parent.linenum
            ## Does this object parent's line number match?
            assert result_correct==test_result


def testValues_parent_child_parsing_02(parse_c01):
    cfg = parse_c01
    # Expected child / parent line numbers before the insert
    parent_intf_before = {
        # Line 11 is Serial1/0, child is line 13
        13: 11,
        # Line 15 is GigabitEthernet4/1
        16: 15,
        17: 15,
        18: 15,
        19: 15,
        # Line 21 is GigabitEthernet4/2
        22: 21,
        23: 21,
        24: 21,
        25: 21,
    }
    # Expected child / parent line numbers after the insert

    # Validate line numbers *before* inserting
    for obj in cfg.find_objects(''):
        result_correct = parent_intf_before.get(obj.linenum, False)
        if result_correct:
            test_result = obj.parent.linenum
            ## Does this object parent's line number match?
            assert result_correct==test_result

    # Insert lines here...
    for intf_obj in cfg.find_objects('^interface\sGigabitEthernet'):
        # Configured with an access vlan...
        if ' switchport access vlan 100' in set(map(attrgetter('text'), intf_obj.children)):
            intf_obj.insert_after(' spanning-tree portfast')
    cfg.atomic()

    parent_intf_after = {
        # Line 11 is Serial1/0, child is line 13
        13: 11,
        # Line 15 is GigabitEthernet4/1
        16: 15,
        17: 15,
        18: 15,
        19: 15,
        # Line 22 is GigabitEthernet4/2
        23: 22,
        24: 22,
        25: 22,
        26: 22,
    }
    # Validate line numbers *after* inserting
    for obj in cfg.find_objects(''):
        result_correct = parent_intf_after.get(obj.linenum, False)
        if result_correct:
            test_result = obj.parent.linenum
            ## Does this object parent's line number match?
            assert result_correct==test_result


def testValues_find_lines(parse_c01):
    c01_intf = ['interface Serial 1/0']
    c01_find_gige_no_exactmatch = [
        'interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8']
    find_lines_Values = (
            # Ensure exact matches work regardless of the exactmatch boolean
            ({'linespec': "interface Serial 1/0",
                'exactmatch': False}, c01_intf),
            ({'linespec': "interface Serial 1/0",
                'exactmatch': True}, c01_intf),

            # Ensure we can find string matches inside an interface config block
            ({'linespec': "encapsulation",
                'exactmatch': False}, [' encapsulation ppp']),

            # Ensure exactmatch=False catches beginning phrases in the config
            ({'linespec': "interface GigabitEthernet4/",
                'exactmatch': False}, c01_find_gige_no_exactmatch),
            # Ensure exactmatch=False catches single words in the config
            ({'linespec': "igabitEthernet",
                'exactmatch': False}, c01_find_gige_no_exactmatch),
            # Negative test: matches are Case-Sensitive
            ({'linespec': "GigaBitEtherNeT",
                'exactmatch': False}, []),
            # Negative test for exactmatch=True
            ({'linespec': "interface GigabitEthernet4/",
                'exactmatch': True}, []),
            # Negative test for exactmatch=True and ignore_ws=False
            ({'linespec': "interface Serial1/0",
                'exactmatch': True, 'ignore_ws': False}, []),
        )

    for args, result_correct in find_lines_Values:
        test_result = parse_c01.find_lines(**args)
        assert result_correct==test_result

def testValues_find_children(parse_c01):
    c01_pmap_children = [
        'policy-map QOS_1',
        ' class GOLD',
        ' class SILVER',
        ' class BRONZE',
        ]

    find_children_Values = (
        ({'linespec': "policy-map", 'exactmatch': False},
            c01_pmap_children),
        ({'linespec': "policy-map", 'exactmatch': True}, []),
    )
    for args, result_correct in find_children_Values:
        test_result = parse_c01.find_children(**args)
        assert result_correct==test_result




def testValues_find_all_children01(parse_c01):
    ## test find_all_chidren
    c01_pmap_all_children = [
        'policy-map QOS_1',
        ' class GOLD',
        '  priority percent 10',
        ' class SILVER',
        '  bandwidth 30',
        '  random-detect',
        ' class BRONZE',
        '  random-detect',
        ]

    find_all_children_Values = (
        ({'linespec': "policy-map", 'exactmatch': False},
            c01_pmap_all_children),
        ({'linespec': "policy-map", 'exactmatch': True}, []),
    )

    for args, result_correct in find_all_children_Values:
        test_result = parse_c01.find_all_children(**args)
        assert result_correct==test_result


def testValues_find_all_chidren02():
    """Ensure we don't need a comment at the end of a """
    """  parent / child block to identify the end of the family"""
    CONFIG = ['thing1',
        ' foo',
        '  bar',
        '   100',
        '   200',
        '   300',
        '   400',
        'thing2',]
    RESULT_CORRECT = ['thing1',
        ' foo',
        '  bar',
        '   100',
        '   200',
        '   300',
        '   400',]
    cfg = CiscoConfParse(CONFIG)
    test_result = cfg.find_all_children('^thing1')
    assert RESULT_CORRECT==test_result

def testValues_find_blocks(parse_c01):
    result_correct = [
        'banner login ^C',
        'This is a router, and you cannot have it.',
        'Log off now while you still can type. I break the fingers',
        'of all tresspassers.',
        '^C',
    ]

    test_result = parse_c01.find_blocks('tresspasser')
    assert result_correct==test_result

def testValues_find_parents_w_child(parse_c01):
    c01_parents_w_child_power = [
        'interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
    ] 
    c01_parents_w_child_voice = [
        'interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
    ]

    find_parents_w_child_Values = (
        ({'parentspec': "interf", 'childspec': "power inline"},
            c01_parents_w_child_power),
        ({'parentspec': "interf", 'childspec': " switchport voice"},
            c01_parents_w_child_voice),
        ({'parentspec': "^interface$", 'childspec': "switchport voice"},
            []),
    )

    ## test find_parents_w_child
    for args, result_correct in find_parents_w_child_Values:
        test_result = parse_c01.find_parents_w_child(**args)
        assert result_correct==test_result

def testValues_find_parents_wo_child(parse_c01):
    c01_parents_wo_child_power = [
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    find_parents_wo_child_Values = (
        ({'parentspec': "interface Gig", 'childspec': "power inline"},
            c01_parents_wo_child_power),
    )

    ## test find_parents_wo_child
    for args, result_correct in find_parents_wo_child_Values:
        test_result = parse_c01.find_parents_wo_child(**args)
        assert result_correct==test_result

def testValues_find_children_w_parents(parse_c01):
    c01_children_w_parents_switchport = [
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
    ]
    find_children_w_parents_Values = (
        ({'parentspec': "^interface GigabitEthernet4/1",
            'childspec': "switchport"},
            c01_children_w_parents_switchport),
        )
    ## test find_children_w_parents
    for args, result_correct in find_children_w_parents_Values:
        test_result = parse_c01.find_children_w_parents(**args)
        assert result_correct==test_result

def testValues_find_objects_w_parents(parse_c01):
    c01_children_w_parents_switchport = [
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
    ]
    find_objects_w_parents_Values = (
        ({'parentspec': "^interface GigabitEthernet4/1",
            'childspec': "switchport"},
            c01_children_w_parents_switchport),
        )
    ## test find_children_w_parents
    for args, result_correct in find_objects_w_parents_Values:
        test_result = list(map(attrgetter('text'), 
            parse_c01.find_objects_w_parents(**args)))
        assert result_correct==test_result



def testValues_replace_lines_01(parse_c01):
    c01_replace_gige_no_exactmatch = [
            'interface GigabitEthernet8/1',
            'interface GigabitEthernet8/2',
            'interface GigabitEthernet8/3',
            'interface GigabitEthernet8/4',
            'interface GigabitEthernet8/5',
            'interface GigabitEthernet8/6',
            'interface GigabitEthernet8/7',
            'interface GigabitEthernet8/8'
    ]
    replace_lines_Values01 = (
        # Ensure basic replacements work
        ({'linespec': r"interface Serial 1/0",
            'replacestr': "interface Serial 2/0"},
            ['interface Serial 2/0']),
        # Ensure we make multiple replacements as required
        ({'linespec': "GigabitEthernet4/",
            'replacestr': "GigabitEthernet8/", 'exactmatch': False},
            c01_replace_gige_no_exactmatch),
    )
    # We have to parse multiple times because of replacements
    for args, result_correct in replace_lines_Values01:
        test_result = parse_c01.replace_lines(**args)
        assert result_correct==test_result

def testValues_replace_lines_02(parse_c01):
    c01_replace_gige_exclude = [
        'interface GigabitEthernet8/1',
        'interface GigabitEthernet8/2',
        'interface GigabitEthernet8/3',
        'interface GigabitEthernet8/7',
        'interface GigabitEthernet8/8'
    ]
    replace_lines_Values02 = (
        # Ensure exactmatch rejects substrings
        ({'linespec': "interface Serial 1/",
            'replacestr': "interface Serial 2/", 'exactmatch': True},
            []),
        # Ensure we exclude lines which match excludespec
        ({'linespec': "GigabitEthernet4/",
            'excludespec': r'/4|/5|/6',
            'replacestr': "GigabitEthernet8/", 'exactmatch': False},
            c01_replace_gige_exclude),
    )
    for args, result_correct in replace_lines_Values02:
        test_result = parse_c01.replace_lines(**args)
        assert result_correct==test_result

def testValues_replace_lines_03(parse_c01):
    """Ensure we can use a compiled regexp in excludespec"""
    c01_replace_gige_exclude = [
        'interface GigabitEthernet8/1',
        'interface GigabitEthernet8/2',
        'interface GigabitEthernet8/3',
        'interface GigabitEthernet8/7',
        'interface GigabitEthernet8/8'
    ]
    replace_lines_Values03 = (
        # Ensure we can use a compiled regexp in excludespec...
        ({'linespec': "GigabitEthernet4/",
            'excludespec': re.compile(r'/4|/5|/6'),
            'replacestr': "GigabitEthernet8/", 'exactmatch': False},
            c01_replace_gige_exclude),
    )
    for args, result_correct in replace_lines_Values03:
        test_result = parse_c01.replace_lines(**args)
        assert result_correct==test_result

def testValues_replace_children_01(parse_c01):
    """Test child line replacement"""
    c01_replace_children = [
        ' power inline static max 30000',
        ' power inline static max 30000'
    ]
    replace_children_Values = (
        ({'parentspec': "GigabitEthernet4/",
            'childspec': 'max 7000',
            'excludespec': re.compile(r'/4|/5|/6'),
            'replacestr': "max 30000", 'exactmatch': False},
            c01_replace_children),
    )
    # We have to parse multiple times because of replacements
    for args, result_correct in replace_children_Values:
        test_result = parse_c01.replace_children(**args)
        assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_01(parse_c01):
    ## test sync_diff as a drop-in replacement for req_cfgspec_excl_diff()
    ##   This test mirrors testValues_req_cfgspec_excl_diff()
    result_correct = ['no logging 1.1.3.17',
        'logging 1.1.3.4',
        'logging 1.1.3.6',
    ]
    test_result = parse_c01.sync_diff(
        [
        'logging 1.1.3.4',
        'logging 1.1.3.5',
        'logging 1.1.3.6',
        ],
        r"^logging\s+",
        r"logging\s+\d+\.\d+\.\d+\.\d+",
        )
    assert result_correct==test_result


@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_03():
    ## config_01 is the starting point
    config_01 = ['!',
    'interface GigabitEthernet 1/5',
    ' ip address 1.1.1.2 255.255.255.0',
    ' standby 5 ip 1.1.1.1',
    ' standby 5 preempt',
    '!']

    required_config = ['!',
    'interface GigabitEthernet 1/5',
    ' switchport',
    ' switchport mode access',
    ' switchport access vlan 5',
    ' switchport nonegotiate',
    '!',
    'interface Vlan5',
    ' no shutdown',
    ' ip address 1.1.1.2 255.255.255.0',
    ' standby 5 ip 1.1.1.1',
    ' standby 5 preempt',
    '!',
    ]

    result_correct = ['interface GigabitEthernet 1/5',
        ' no ip address 1.1.1.2 255.255.255.0',
        ' no standby 5 ip 1.1.1.1',
        ' no standby 5 preempt',
        'interface GigabitEthernet 1/5',
        ' switchport',
        ' switchport mode access',
        ' switchport access vlan 5',
        ' switchport nonegotiate',
        'interface Vlan5',
        ' no shutdown',
        ' ip address 1.1.1.2 255.255.255.0',
        ' standby 5 ip 1.1.1.1',
        ' standby 5 preempt',
    ]

    linespec = r''
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_04():
    """Test diffs against double-spacing for children (such as NXOS)"""
    ## config_01 is the starting point
    config_01 = ['!',
    'interface GigabitEthernet 1/5',
    '  ip address 1.1.1.2 255.255.255.0',
    '  standby 5 ip 1.1.1.1',
    '  standby 5 preempt',
    '!']

    required_config = ['!',
    'interface GigabitEthernet 1/5',
    '  switchport',
    '  switchport mode access',
    '  switchport access vlan 5',
    '  switchport nonegotiate',
    '!',
    'interface Vlan5',
    '  no shutdown',
    '  ip address 1.1.1.2 255.255.255.0',
    '  standby 5 ip 1.1.1.1',
    '  standby 5 preempt',
    '!',
    ]

    result_correct = ['interface GigabitEthernet 1/5',
        '  no ip address 1.1.1.2 255.255.255.0',
        '  no standby 5 ip 1.1.1.1',
        '  no standby 5 preempt',
        'interface GigabitEthernet 1/5',
        '  switchport',
        '  switchport mode access',
        '  switchport access vlan 5',
        '  switchport nonegotiate',
        'interface Vlan5',
        '  no shutdown',
        '  ip address 1.1.1.2 255.255.255.0',
        '  standby 5 ip 1.1.1.1',
        '  standby 5 preempt',
    ]

    linespec = r''
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_05():
    ## config_01 is the starting point
    config_01 = ['!',
    'vlan 51',
    ' state active',
    'vlan 53',
    '!']

    required_config = ['!',
    'vlan 51',
    ' name SOME-VLAN',
    ' state active',
    'vlan 52',
    ' name BLAH',
    ' state active',
    '!',]

    result_correct = ['no vlan 53', 'vlan 51', ' name SOME-VLAN', 'vlan 52', 
        ' name BLAH', ' state active']

    linespec = r'vlan\s+\S+|name\s+\S+|state.+'
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_06():
    """Test diffs against double-spacing for children (such as NXOS)"""
    ## config_01 is the starting point
    config_01 = ['!',
    'vlan 51',
    '  state active',
    'vlan 53',
    '!',
    ]

    required_config = ['!',
    'vlan 51',
    '  name SOME-VLAN',
    '  state active',
    'vlan 52',
    '  name BLAH',
    '  state active',
    '!',]

    result_correct = ['no vlan 53', 'vlan 51', '  name SOME-VLAN', 'vlan 52', 
        '  name BLAH', '  state active']

    linespec = r'vlan\s+\S+|name\s+\S+|state.+'
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_07():
    """Test diffs with remove_lines=False"""
    ## config_01 is the starting point
    config_01 = ['!',
    'vlan 51',
    ' state active',
    'vlan 53',
    '!',
    'vtp mode transparent',
    ]

    required_config = ['!',
    'vlan 51',
    ' name SOME-VLAN',
    ' state active',
    'vlan 52',
    ' name BLAH',
    ' state active',
    '!',]

    result_correct = ['vlan 51', ' name SOME-VLAN', 'vlan 52', 
        ' name BLAH', ' state active']

    linespec = r'vlan\s+\S+|name\s+\S+|state.+'
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec, remove_lines=False)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_08():
    """Test diffs with explicit ignore_order=False"""
    ## config_01 is the starting point
    config_01 = ['!',
    'vlan 51',
    ' state active',
    'vlan 53',
    '!',
    'vtp mode transparent',
    ]

    required_config = ['!',
    'vtp mode transparent',
    'vlan 52',
    ' name BLAH',
    ' state active',
    'vlan 51',
    ' name SOME-VLAN',
    ' state active',
    '!',]

    result_correct = ['no vlan 53', 
        'vlan 52', 
        ' name BLAH', 
        ' state active',
        'vlan 51', 
        ' name SOME-VLAN', 
        ]

    linespec = r'vlan\s+\S+|name\s+\S+|state.+|vtp'
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec, ignore_order=False)
    assert result_correct==test_result

@pytest.mark.xfail(sys.version_info[0]==3,
                   reason="Difflib.SequenceMatcher is broken in Python3")
def testValues_sync_diff_09():
    """Test diffs with explicit ignore_order=True"""
    ## config_01 is the starting point
    config_01 = ['!',
    'vlan 51',
    ' state active',
    'vlan 53',
    '!',
    'vtp mode transparent',
    ]

    required_config = ['!',
    'vtp mode transparent',
    'vlan 51',
    ' name SOME-VLAN',
    ' state active',
    'vlan 52',
    ' name BLAH',
    ' state active',
    '!',]

    result_correct = [
        'no vlan 53', 
        'vlan 51', 
        ' name SOME-VLAN', 
        'vlan 52', 
        ' name BLAH', 
        ' state active',
        ]

    linespec = r'vlan\s+\S+|name\s+\S+|state.+|vtp'
    parse = CiscoConfParse(config_01)
    test_result = parse.sync_diff(required_config, linespec, linespec, ignore_order=True)
    assert result_correct==test_result

def testValues_req_cfgspec_excl_diff(parse_c01):
        ## test req_cfgspec_excl_diff
    result_correct = ['no logging 1.1.3.17',
        'logging 1.1.3.4',
        'logging 1.1.3.6',
    ]
    test_result = parse_c01.req_cfgspec_excl_diff(
        "^logging\s+",
        "logging\s+\d+\.\d+\.\d+\.\d+",
        [
        'logging 1.1.3.4',
        'logging 1.1.3.5',
        'logging 1.1.3.6',
        ]
        )
    assert result_correct==test_result

def testValues_req_cfgspec_all_diff(parse_c01):
    ## test req_cfgspec_all_diff
    result_correct = [
        'logging 1.1.3.4',
        'logging 1.1.3.6',
    ]
    test_result = parse_c01.req_cfgspec_all_diff(
        [
        'logging 1.1.3.4',
        'logging 1.1.3.5',
        'logging 1.1.3.6',
        ]
        )
    assert result_correct==test_result


def testValues_ignore_ws():
    ## test find_lines with ignore_ws flag
    config = ['set snmp community read-only     myreadonlystring']
    result_correct = config
    cfg = CiscoConfParse(config)
    test_result = cfg.find_lines(
        'set snmp community read-only myreadonlystring',
        ignore_ws = True
        )
    assert result_correct==test_result

def testValues_negative_ignore_ws():
    """test find_lines WITHOUT ignore_ws"""
    config = ['set snmp community read-only     myreadonlystring']
    result_correct = list()
    cfg = CiscoConfParse(config)
    test_result = cfg.find_lines(
        'set snmp community read-only myreadonlystring',
        ignore_ws = False
        )
    assert result_correct==test_result

def testValues_IOSCfgLine_all_parents(parse_c01):
    """Ensure IOSCfgLine.all_parents finds all parents, recursively"""
    result_correct = list()
    # mockobj pretends to be the IOSCfgLine object
    with patch(__name__+'.'+'IOSCfgLine') as mockobj:
        vals = [('policy-map QOS_1', 0), (' class SILVER', 4)]
        # fakeobj pretends to be an IOSCfgLine instance at the given line number
        for idx, fakeobj in enumerate(map(deepcopy, repeat(mockobj, len(vals)))):
            fakeobj.text = vals[idx][0]
            fakeobj.linenum = vals[idx][1]
            fakeobj.classname = "IOSCfgLine"

            result_correct.append(fakeobj)

    cfg = parse_c01
    obj = cfg.find_objects('bandwidth 30')[0]
    ## Removed _find_parent_OBJ on 20140202
    #test_result = cfg._find_parent_OBJ(obj)
    test_result = obj.all_parents
    for idx, testobj in enumerate(test_result):
        assert result_correct[idx].text==test_result[idx].text
        assert result_correct[idx].linenum==test_result[idx].linenum
        assert result_correct[idx].classname==test_result[idx].classname


def testValues_find_objects(parse_c01):
    lines = [
          ('interface Serial 1/0', 11),
          ('interface GigabitEthernet4/1', 15),
          ('interface GigabitEthernet4/2', 21),
          ('interface GigabitEthernet4/3', 27),
          ('interface GigabitEthernet4/4', 32),
          ('interface GigabitEthernet4/5', 35),
          ('interface GigabitEthernet4/6', 39),
          ('interface GigabitEthernet4/7', 43),
          ('interface GigabitEthernet4/8', 47),
          ]
    c01_find_objects = list()
    for line, linenum in lines:
        # Mock up the correct object
        obj = IOSCfgLine()
        obj.text = line
        obj.linenum = linenum
        c01_find_objects.append(obj)

    ## test whether find_objects returns correct IOSCfgLine objects
    result_correct = c01_find_objects
    test_result = parse_c01.find_objects('^interface')
    assert result_correct==test_result

def testValues_find_objects_replace_01():
    """test whether find_objects we can correctly replace object values using native IOSCfgLine object methods"""
    config01 = ['!',
        'boot system flash slot0:c2600-adventerprisek9-mz.124-21a.bin',
        'boot system flash bootflash:c2600-adventerprisek9-mz.124-21a.bin',
        '!',
        'interface Ethernet0/0',
        ' ip address 172.16.1.253 255.255.255.0',
        '!',
        'ip route 0.0.0.0 0.0.0.0 172.16.1.254',
        '!',
        'end',
        ]
    result_correct = ['!',
        '! old boot image flash slot0:c2600-adventerprisek9-mz.124-21a.bin',
        '! old boot image flash bootflash:c2600-adventerprisek9-mz.124-21a.bin',
        '!',
        'interface Ethernet0/0',
        ' ip address 172.16.1.253 255.255.255.0',
        '!',
        'ip route 0.0.0.0 0.0.0.0 172.16.1.254',
        '!',
        'end',
        ]
    cfg = CiscoConfParse(config01)
    for obj in cfg.find_objects('boot system'):
        obj.replace('boot system', '! old boot image')
    test_result = cfg.ioscfg
    assert result_correct==test_result

def testValues_find_objects_delete_01():
    """Test whether IOSCfgLine.delete() recurses through children correctly"""
    config = [
        '!',
        'interface Serial1/0',
        ' encapsulation ppp',
        ' ip address 1.1.1.1 255.255.255.252',
        ' no ip proxy-arp',
        '!',
        'interface Serial1/1',
        ' encapsulation ppp',
        ' ip address 1.1.1.5 255.255.255.252',
        '!',
    ]
    result_correct = ['!', '!', '!']
    cfg = CiscoConfParse(config)
    for intf in cfg.find_objects(r'^interface'):
        # Delete all the interface objects
        intf.delete(recurse=True)  # recurse=True is the default
    test_result = cfg.ioscfg
    assert result_correct==test_result

def testValues_insert_after_atomic_02(parse_c01):
    """We expect insert_after(atomic=True) to correctly parse children"""
    ## See also -> testValues_insert_after_nonatomic_02()
    result_correct = [
        'interface GigabitEthernet4/1',
        ' shutdown',
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
        ' power inline static max 7000',
        ]
    linespec = 'interface GigabitEthernet4/1'
    parse_c01.insert_after(linespec, ' shutdown', exactmatch=True, atomic=True)
    test_result = parse_c01.find_children(linespec)

    assert result_correct==test_result

def testValues_insert_after_atomic_factory_01(parse_c01_factory):
    """Ensure that comments which are added, assert is_comment"""
    # mockobj pretends to be the IOSCfgLine object
    with patch(__name__+'.'+'IOSCfgLine') as mockobj:
        result_correct01 = mockobj
        result_correct01.linenum = 16
        result_correct01.text = ' ! TODO: some note to self'
        result_correct01.classname = 'IOSCfgLine'
        result_correct01.is_comment = True

    linespec = 'interface GigabitEthernet4/1'
    parse_c01_factory.insert_after(linespec, ' ! TODO: some note to self',
        exactmatch=True, atomic=True)
    test_result01 = parse_c01_factory.find_objects('TODO')[0]
    assert result_correct01.linenum==test_result01.linenum
    assert result_correct01.text==test_result01.text
    assert result_correct01.classname==test_result01.classname
    assert result_correct01.is_comment==test_result01.is_comment

    result_correct02 = [
        'interface GigabitEthernet4/1',
        ' ! TODO: some note to self',
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
        ' power inline static max 7000',
        ]
    test_result02 = parse_c01_factory.find_children(linespec)
    assert result_correct02==test_result02

def testValues_insert_after_atomic_01(parse_c01):
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        test_result = parse_c01.insert_after(linespec, ' shutdown',
            exactmatch=True, atomic=False)
        result_correct = [inputs[idx]]
        assert result_correct==test_result
    parse_c01.commit()

    ## Ensure we inserted the text at the right line number
    ##   i.e. it should be immediately below the interface line
    result_correct_dict = {
        23: ' shutdown',
        30: ' shutdown',
        36: ' shutdown',
        40: ' shutdown',
        45: ' shutdown',
        50: ' shutdown',
        55: ' shutdown',
    }
    for idx, result_correct in result_correct_dict.items():
        assert parse_c01.ConfigObjs[idx].text==result_correct

        # The parent line should be immediately above it
        correct_parent = parse_c01.ConfigObjs[idx-1]
        assert parse_c01.ConfigObjs[idx].parent==correct_parent


def testValues_insert_after_nonatomic_01(parse_c01):
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        test_result = parse_c01.insert_after(linespec, ' shutdown',
            exactmatch=True, atomic=False)
        result_correct = [inputs[idx]]
        assert result_correct==test_result
    ## NOTE: We DO NOT commit here to test as a non-atomic change

    ## Ensure we inserted the text at the right line number
    ##   i.e. it should be immediately below the interface line
    result_correct_dict = {
        23: ' shutdown',
        30: ' shutdown',
        36: ' shutdown',
        40: ' shutdown',
        45: ' shutdown',
        50: ' shutdown',
        55: ' shutdown',
    }
    for idx, result_correct in result_correct_dict.items():
        assert parse_c01.ConfigObjs[idx].text==result_correct

def testValues_insert_after_nonatomic_02(parse_c01):
    """Negative test.  We expect insert_after(atomic=False) to miss any children added like this at some point in the future I might fix insert_after so it knows how to correctly parse children"""
    result_correct = ['interface GigabitEthernet4/1',
        #' shutdown',   <--- Intentionally commented out
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
        ' power inline static max 7000',
        ]
    linespec = 'interface GigabitEthernet4/1'
    parse_c01.insert_after(linespec, ' shutdown', exactmatch=True, 
        atomic=False)
    test_result = parse_c01.find_children(linespec)
    ## NOTE: We DO NOT commit here to test as a non-atomic change

    # the interface should *not* be shutdown, because I made a non-atomic change
    assert result_correct==test_result

def testValues_insert_after_child_atomic_01(parse_c01):
    """We expect insert_after_child(atomic=True) to correctly parse children"""
    result_correct = [
        'interface GigabitEthernet4/1',
        ' switchport',
        ' switchport access vlan 100',
        ' switchport voice vlan 150',
        ' power inline static max 7000',
        ' shutdown',
        ]
    linespec = 'interface GigabitEthernet4/1'
    parse_c01.insert_after_child(linespec, 'power', ' shutdown', exactmatch=True, atomic=True)
    test_result = parse_c01.find_children(linespec)

    assert result_correct==test_result


def testValues_insert_before_nonatomic_01(parse_c01):
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        test_result = parse_c01.insert_before(linespec, 'default '+linespec,
            exactmatch=True, atomic=False)
        result_correct = [inputs[idx]]
        assert result_correct==test_result

def testValues_insert_before_atomic_01(parse_c01):
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        test_result = parse_c01.insert_before(linespec, 'default '+linespec,
            exactmatch=True, atomic=True)
        result_correct = [inputs[idx]]
        assert result_correct==test_result

c01_default_gigabitethernets = """policy-map QOS_1
 class GOLD
  priority percent 10
 !
 class SILVER
  bandwidth 30
  random-detect
 !
 class BRONZE
  random-detect
!
interface Serial 1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
default interface GigabitEthernet4/1
interface GigabitEthernet4/1
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
default interface GigabitEthernet4/2
interface GigabitEthernet4/2
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
default interface GigabitEthernet4/3
interface GigabitEthernet4/3
 switchport
 switchport access vlan 100
 switchport voice vlan 150
!
default interface GigabitEthernet4/4
interface GigabitEthernet4/4
 shutdown
!
default interface GigabitEthernet4/5
interface GigabitEthernet4/5
 switchport
 switchport access vlan 110
!
default interface GigabitEthernet4/6
interface GigabitEthernet4/6
 switchport
 switchport access vlan 110
!
default interface GigabitEthernet4/7
interface GigabitEthernet4/7
 switchport
 switchport access vlan 110
!
default interface GigabitEthernet4/8
interface GigabitEthernet4/8
 switchport
 switchport access vlan 110
!
access-list 101 deny tcp any any eq 25 log
access-list 101 permit ip any any
!
!
logging 1.1.3.5
logging 1.1.3.17
!
banner login ^C
This is a router, and you cannot have it.
Log off now while you still can type. I break the fingers
of all tresspassers.
^C
alias exec showthang show ip route vrf THANG""".splitlines()

def testValues_renumbering_insert_before_nonatomic_01(parse_c01, 
    c01_default_gigethernets):
    """Ensure we renumber lines after insert_before(atomic=False)"""
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        parse_c01.insert_before(linespec, 'default '+linespec,
            exactmatch=True, atomic=False)
    test_result = parse_c01.ioscfg
    result_correct = c01_default_gigabitethernets
    assert result_correct==test_result

def testValues_renumbering_insert_before_nonatomic_02(parse_c01, 
    c01_default_gigethernets):
    """Ensure we renumber lines after insert_before(atomic=False)"""
    inputs = ['interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/4',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
        'interface GigabitEthernet4/7',
        'interface GigabitEthernet4/8',
        ]
    for idx, linespec in enumerate(inputs):
        parse_c01.insert_before(linespec, 'default '+linespec,
            exactmatch=True, atomic=True)
    test_result = parse_c01.ioscfg
    result_correct = c01_default_gigabitethernets
    assert result_correct==test_result

def testValues_find_objects_factory_01(parse_c01_factory):
    """Test whether find_objects returns the correct objects"""
    # mockobj pretends to be the IOSIntfLine object
    with patch(__name__+'.'+'IOSIntfLine') as mockobj:
        vals = [('interface GigabitEthernet4/1', 15),
            ('interface GigabitEthernet4/2', 21),
            ('interface GigabitEthernet4/3', 27),
            ('interface GigabitEthernet4/4', 32),
            ('interface GigabitEthernet4/5', 35),
            ('interface GigabitEthernet4/6', 39),
            ('interface GigabitEthernet4/7', 43),
            ('interface GigabitEthernet4/8', 47),
            ]
        ## Build fake IOSIntfLine objects to validate unit tests...
        result_correct = list()
        # deepcopy a unique mock for every val with itertools.repeat()
        mockobjs = map(deepcopy, repeat(mockobj, len(vals)))
        # mock pretends to be an IOSCfgLine so we can test against it
        for idx, obj in enumerate(mockobjs):
            obj.text     = vals[idx][0]  # Check the text
            obj.linenum  = vals[idx][1]  # Check the line numbers
            # append the fake IOSIntfLine object to result_correct
            result_correct.append(obj)

        test_result = parse_c01_factory.find_objects('^interface GigabitEther')
        for idx, test_result_object in enumerate(test_result):
            # Check line numbers
            assert result_correct[idx].linenum==test_result_object.linenum
            # Check text
            assert result_correct[idx].text==test_result_object.text

def testValues_IOSIntfLine_find_objects_factory_01(parse_c01_factory):
    """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
    # mockobj pretends to be the IOSIntfLine object
    with patch(__name__+'.'+'IOSIntfLine') as mockobj:
        # the mock pretends to be an IOSCfgLine so we can test against it
        result_correct = mockobj
        result_correct.linenum = 11
        result_correct.text = 'interface Serial 1/0'
        result_correct.classname = 'IOSIntfLine'
        result_correct.ipv4_addr_object = IPv4Obj('1.1.1.1/30',
            strict=False)

        # this test finds the IOSIntfLine instance for 'Serial 1/0'
        test_result = parse_c01_factory.find_objects('^interface Serial 1/0')[0]

        assert result_correct.linenum==test_result.linenum
        assert result_correct.text==test_result.text
        assert result_correct.classname==test_result.classname
        assert result_correct.ipv4_addr_object==test_result.ipv4_addr_object

def testValues_IOSIntfLine_find_objects_factory_02(parse_c01_factory,
    c01_insert_serial_replace):
    """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
    with patch(__name__+'.'+'IOSIntfLine') as mockobj:
        # the mock pretends to be an IOSCfgLine so we can test against it
        result_correct01 = mockobj
        result_correct01.linenum = 12
        result_correct01.text = 'interface Serial 2/0'
        result_correct01.classname = 'IOSIntfLine'
        result_correct01.ipv4_addr_object = IPv4Obj('1.1.1.1/30',
            strict=False)

        result_correct02 = c01_insert_serial_replace

        # Insert a line above the IOSIntfLine object
        parse_c01_factory.insert_before('interface Serial 1/0', 'default interface Serial 1/0')
        # Replace text in the IOSIntfLine object
        parse_c01_factory.replace_lines('interface Serial 1/0', 'interface Serial 2/0', exactmatch=False)

        test_result01 = parse_c01_factory.find_objects('^interface Serial 2/0')[0]
        test_result02 = parse_c01_factory.ioscfg

        # Check attributes of the IOSIntfLine object
        assert result_correct01.linenum==test_result01.linenum
        assert result_correct01.text==test_result01.text
        assert result_correct01.classname==test_result01.classname
        assert result_correct01.ipv4_addr_object==test_result01.ipv4_addr_object

        # Ensure the text configs are exactly what we wanted
        assert result_correct02==test_result02

def testValues_IOSConfigList_insert01(parse_c02):
    result_correct = [
        'hostname LabRouter',
        'policy-map QOS_1', 
        ' class GOLD', 
        '  priority percent 10', 
        ' !', 
        ' class SILVER', 
        '  bandwidth 30', 
        '  random-detect', 
        ' !', 
        ' class BRONZE', 
        '  random-detect', 
        '!', 
        'interface GigabitEthernet4/1', 
        ' switchport', 
        ' switchport access vlan 100', 
        ' switchport voice vlan 150', 
        ' power inline static max 7000', 
        '!',
    ]
    iosconfiglist = parse_c02.ConfigObjs

    # insert at the beginning
    iosconfiglist.insert(0, 'hostname LabRouter')
    test_result = list(map(attrgetter('text'), iosconfiglist))

    assert test_result==result_correct


def testValues_IOSConfigList_insert02(parse_c02):
    result_correct = [
        'policy-map QOS_1', 
        ' class GOLD', 
        '  priority percent 10', 
        ' !', 
        ' class SILVER', 
        '  bandwidth 30', 
        '  random-detect', 
        ' !', 
        ' class BRONZE', 
        '  random-detect', 
        '!', 
        'interface GigabitEthernet4/1', 
        ' switchport', 
        ' switchport access vlan 100', 
        ' switchport voice vlan 150', 
        ' power inline static max 7000', 
        'hostname LabRouter',
        '!',
    ]
    iosconfiglist = parse_c02.ConfigObjs

    # insert at the end
    iosconfiglist.insert(-1, 'hostname LabRouter')
    test_result = list(map(attrgetter('text'), iosconfiglist))

    assert test_result==result_correct

def testValues_IOSConfigLine_ioscfg01(parse_c02):
    result_correct = [
        'interface GigabitEthernet4/1', 
        ' switchport', 
        ' switchport access vlan 100', 
        ' switchport voice vlan 150', 
        ' power inline static max 7000', 
    ]
    test_result = parse_c02.find_objects(r'^interface\sGigabitEthernet4/1', 
        exactmatch=True)[0].ioscfg
    assert test_result==result_correct

def testValues_CiscoPassword():
    ep = "04480E051A33490E"
    test_result_01 = CiscoPassword(ep).decrypt()
    test_result_02 = CiscoPassword().decrypt(ep)

    result_correct = cisco_type7(0).decode(ep)
    assert result_correct==test_result_01
    assert result_correct==test_result_02
