import sys
import re
import os

sys.path.insert(0, "..")

from ciscoconfparse.ciscoconfparse import CiscoConfParse
from ciscoconfparse.ccp_util import IPv4Obj
import pytest

r""" test_Models_Junos.py - Parse, Query, Build, and Modify IOS-style configs

     Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
     Copyright (C) 2019      David Michael Pennington at ThousandEyes
     Copyright (C) 2015-2019 David Michael Pennington at Samsung Data Services

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



@pytest.mark.xfail(True, reason="Junos factory parsing is not supported yet")
def testVal_JunosIntfLine_dna(parse_j01_factory):
    cfg = parse_j01_factory
    obj = cfg.find_objects_w_child("interfaces", "ge-0/0/1")[0]
    assert obj.dna == "JunosIntfLine"


@pytest.mark.xfail(True, reason="Junos configs currently use IOSCfgLine objects")
def testVal_JunosCfgLine_dna(parse_j01):
    cfg = parse_j01
    obj = cfg.find_objects_w_child("interfaces", "ge-0/0/1")[0]
    assert obj.dna == "JunosCfgLine"


def testVal_find_objects_w_parents(parse_j01):
    cfg = parse_j01
    obj = cfg.find_objects_w_parents("interfaces", "ge-0/0/1")[0]
    assert not ("{" in set(obj.text))  # Ensure there are no braces on this line
    assert len(obj.all_children) == 6


# test for Github issue #49
def testVal_parse_F5():
    """Test for Github issue #49"""
    config = [
        "ltm virtual virtual1 {",
        "    profiles {",
        "        test1 { }",
        "    }",
        "}",
        "ltm virtual virtual2 {",
        "    profiles2 {",
        "        test2 { }",
        "    }",
        "}",
    ]
    parse = CiscoConfParse(config, syntax="junos")
    retval = parse.find_objects("profiles2")[0].children
    assert retval[0].text.strip() == "test2"
