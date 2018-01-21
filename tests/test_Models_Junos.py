import sys
import re
import os
THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))

from ciscoconfparse import CiscoConfParse
from ccp_util import IPv4Obj
import pytest

@pytest.mark.xfail(True,
                   reason="Junos factory parsing is not supported yet")
def testVal_JunosIntfLine_dna(parse_j01_factory):
    cfg = parse_j01_factory
    obj = cfg.find_objects_w_child('interfaces', 'ge-0/0/1')[0]
    assert obj.dna == 'JunosIntfLine'

@pytest.mark.xfail(True,
                   reason="Junos configs currently use IOSCfgLine objects")
def testVal_JunosCfgLine_dna(parse_j01):
    cfg = parse_j01
    obj = cfg.find_objects_w_child('interfaces', 'ge-0/0/1')[0]
    assert obj.dna == 'JunosCfgLine'

def testVal_find_objects_w_parents(parse_j01):
    cfg = parse_j01
    obj = cfg.find_objects_w_parents('interfaces', 'ge-0/0/1')[0]
    assert not ('{' in set(obj.text))  # Ensure there are no braces on this line
    assert len(obj.all_children)==6

# test for Github issue #49
def testVal_parse_F5():
    """Test for Github issue #49"""
    config = [
        'ltm virtual virtual1 {',
        '    profiles {',
        '        test1 { }',
        '    }',
        '}',
        'ltm virtual virtual2 {',
        '    profiles2 {',
        '        test2 { }',
        '    }',
        '}',
    ]
    parse = CiscoConfParse(config, syntax='junos')
    retval = parse.find_objects('profiles2')[0].children
    assert retval[0].text=='    test2 '
