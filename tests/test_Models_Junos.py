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

def testVal_find_objects_w_child(parse_j01):
    cfg = parse_j01
    obj = cfg.find_objects_w_child('interfaces', 'ge-0/0/1')[0]
