r""" test_CiscoConfParse.py - Parse, Query, Build, and Modify IOS-style configs
     Copyright (C) 2021-2023 David Michael Pennington
     Copyright (C) 2019-2021 David Michael Pennington at Cisco Systems / ThousandEyes
     Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
     Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corporation

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

from passlib.hash import cisco_type7
import pytest

from ciscoconfparse.ciscoconfparse import CiscoConfParse
from ciscoconfparse.ciscoconfparse import IOSCfgLine, IOSIntfLine
from ciscoconfparse.ciscoconfparse import parse_line_braces
from ciscoconfparse.ciscoconfparse import CiscoPassword
from ciscoconfparse.ciscoconfparse import Diff
from ciscoconfparse.models_junos import JunosCfgLine
from ciscoconfparse.ccp_util import IPv4Obj
from ciscoconfparse.ccp_abc import BaseCfgLine

from ciscoconfparse.errors import InvalidParameters

from operator import attrgetter
from itertools import repeat
from copy import deepcopy
try:
    from unittest.mock import patch
except ImportError:
    from unittest.mock import patch
import re
import os

THIS_TEST_PATH = os.path.dirname(os.path.abspath(__file__))


def testParse_valid_config_blanklines_01(parse_n01_w_blanklines):
    """Test reading a config with blank lines"""
    assert len(parse_n01_w_blanklines.ioscfg) == 126


def testParse_valid_filepath_01():
    """Test reading a cisco ios config-file on disk (without the config keyword); ref github issue #262."""
    parse = CiscoConfParse(f"{THIS_TEST_PATH}/fixtures/configs/sample_01.ios")
    assert len(parse.ioscfg) == 450


def testParse_valid_filepath_02():
    """Test reading a cisco ios config-file on disk (from filename in the config parameter); ref github issue #262."""
    parse = CiscoConfParse(config=f"{THIS_TEST_PATH}/fixtures/configs/sample_01.ios")
    assert len(parse.ioscfg) == 450


def testParse_valid_filepath_03():
    """Test reading an f5 config-file on disk (without the config keyword); ref github issue #262."""
    parse = CiscoConfParse(f"{THIS_TEST_PATH}/fixtures/configs/sample_01.f5", comment="#", syntax="junos")
    assert len(parse.ioscfg) == 16


def testParse_valid_filepath_04():
    """Test reading an f5 config-file on disk (from filename in the config parameter); ref github issue #262."""
    parse = CiscoConfParse(config=f"{THIS_TEST_PATH}/fixtures/configs/sample_01.f5", comment="#", syntax="junos")
    assert len(parse.ioscfg) == 16


def testParse_valid_filepath_05():
    """Test reading a junos config-file on disk (without the config keyword); ref github issue #262."""
    parse = CiscoConfParse(f"{THIS_TEST_PATH}/fixtures/configs/sample_01.junos", comment="#", syntax="junos")
    assert len(parse.ioscfg) == 79


def testParse_valid_filepath_06():
    """Test reading a junos config-file on disk (from filename in the config parameter); ref github issue #262."""
    parse = CiscoConfParse(config=f"{THIS_TEST_PATH}/fixtures/configs/sample_01.junos", comment="#", syntax="junos")
    assert len(parse.ioscfg) == 79


def testParse_syntax_ios_nofactory_01():
    """Ensure successful parse of IOS with no factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.ios",
        syntax="ios",
        comment="!",
        factory=False,
    )
    # No Factory ignores blank lines
    assert len(parse.objs) == 450


def testParse_syntax_ios_factory_01():
    """Ensure successful parse of IOS with factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.ios",
        syntax="ios",
        comment="!",
        factory=True,
    )
    # Factory allows blank lines to exist... the banner has a blank line
    assert len(parse.objs) == 451


def testParse_syntax_nxos_nofactory_01():
    """Ensure successful parse of NXOS with no factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.nxos",
        syntax="nxos",
        comment="!",
        factory=False,
    )
    assert len(parse.objs) == 998


def testParse_syntax_nxos_factory_01():
    """Ensure successful parse of NXOS with factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.nxos",
        syntax="nxos",
        comment="!",
        factory=True,
    )
    assert len(parse.objs) == 998


def testParse_syntax_iosxr_nofactory_01():
    """Ensure successful parse of IOS XR with no factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.iosxr",
        syntax="iosxr",
        comment="!",
        factory=False,
    )
    assert len(parse.objs) == 468


def testParse_syntax_iosxr_factory_01():
    """Ensure successful parse of IOS XR with factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.iosxr",
        syntax="iosxr",
        comment="!",
        factory=True,
    )
    assert len(parse.objs) == 476


def testParse_syntax_asa_nofactory_01():
    """Ensure successful parse of ASA with no factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.asa",
        syntax="asa",
        comment="!",
        factory=False,
    )
    assert len(parse.objs) == 422


def testParse_syntax_asa_factory_01():
    """Ensure successful parse of ASA with factory"""
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.asa",
        syntax="asa",
        comment="!",
        factory=True,
    )
    assert len(parse.objs) == 422


def testParse_parse_line_braces_01():
    uut = parse_line_braces("ltm pool FOO {", comment_delimiter="#")
    assert uut == (0, 1, "ltm pool FOO ")


def testParse_parse_line_braces_02():
    uut = parse_line_braces("}", comment_delimiter="#")
    assert uut == (-1, -1, "")


def testParse_parse_syntax_f5_as_junos_nofactory_ioscfg_01():
    """Parse fixtures/configs/sample_01.f5 as `syntax='junos'`, `factory=False` and test rendering as Cisco-IOS"""
    result_correct_ioscfg = [
        "ltm virtual ACME",
        "    destination 192.168.1.191:http",
        "    ip-protocol tcp",
        "    mask 255.255.255.255",
        "    pool pool1",
        "    profiles",
        "        http",
        "        tcp",
        "    rules",
        "        MOBILE",
        "    source 0.0.0.0/0",
        "    source-address-translation",
        "        type automap",
        "    translate-address enabled",
        "    translate-port enabled",
        "    vs-index 17",
    ]
    parse = CiscoConfParse(
        "fixtures/configs/sample_01.f5",
        syntax="junos",
        comment="#",
        factory=False,
    )
    uut = parse.ioscfg
    assert uut == result_correct_ioscfg


def testParse_parse_syntax_junos_as_junos_nofactory_ioscfg_01():
    config = """## Last commit: 2015-06-28 13:00:59 CST by mpenning
system {
    host-name TEST01_EX;
    domain-name pennington.net;
    domain-search [ pennington.net lab.pennington.net ];
    location {
        country-code 001;
        building HQ_005;
        floor 1;
    }
    root-authentication {
        encrypted-password "$1$y7ArHxKU$zUbdeLfBirgkCsKiOJ5Qa0"; ## SECRET-DATA
    }
    name-server {
        172.16.3.222;
    }
    login {
        announcement "Test Lab Switch";
        message "Unauthorized access is prohibited";
        user mpenning {
            full-name "Mike Pennington";
            uid 1000;
            class super-user;
            authentication {
                encrypted-password "$1$y7ArHxKU$zUbdeLfBirgkCsKiOJ5Qa0"; ## SECRET-DATA
            }
        }
    }
    services {
        ssh {
            root-login allow;
        }
    }
    syslog {
        user * {
            any emergency;
        }
        file messages {
            any notice;
            authorization info;
        }
        file interactive-commands {
            interactive-commands any;
        }
    }
    ntp {
        server 172.16.8.3;
    }
}
vlans {
    Management {
        vlan-id 1;
        interface {
            ge-0/0/0.0;
        }
    }
    VLAN_FOO {
        vlan-id 5;
    }
}
interfaces {
    ge-0/0/0 {
        unit 0 {
            family ethernet-switching {
                port-mode access;
                vlan {
                    members VLAN_FOO;
                }
            }
        }
    }
    ge-0/0/1 {
        unit 0 {
            family ethernet-switching {
                port-mode access;
                vlan {
                    members VLAN_FOO;
                }
            }
        }
    }
    ge-0/0/2 {
        unit 0 {
            family ethernet-switching {
                port-mode access;
                vlan {
                    members VLAN_FOO;
                }
            }
        }
    }
}
routing-options {
    static {
        route 0.0.0.0/0 next-hop 172.16.12.1;
        route 192.168.36.0/25 next-hop 172.16.12.1;
    }
}
"""

    result_correct_ioscfg = [
        '## Last commit: 2015-06-28 13:00:59 CST by mpenning',
        'system',
        '    host-name TEST01_EX',
        '    domain-name pennington.net',
        '    domain-search [ pennington.net lab.pennington.net ]',
        '    location',
        '        country-code 001',
        '        building HQ_005',
        '        floor 1',
        '    root-authentication',
        '        encrypted-password "$1$y7ArHxKU$zUbdeLfBirgkCsKiOJ5Qa0"; ## '
        'SECRET-DATA',
        '    name-server',
        '        172.16.3.222',
        '    login',
        '        announcement "Test Lab Switch"',
        '        message "Unauthorized access is prohibited"',
        '        user mpenning',
        '            full-name "Mike Pennington"',
        '            uid 1000',
        '            class super-user',
        '            authentication',
        '                encrypted-password "$1$y7ArHxKU$zUbdeLfBirgkCsKiOJ5Qa0"; ## '
        'SECRET-DATA',
        '    services',
        '        ssh',
        '            root-login allow',
        '    syslog',
        '        user *',
        '            any emergency',
        '        file messages',
        '            any notice',
        '            authorization info',
        '        file interactive-commands',
        '            interactive-commands any',
        '    ntp',
        '        server 172.16.8.3',
        'vlans',
        '    Management',
        '        vlan-id 1',
        '        interface',
        '            ge-0/0/0.0',
        '    VLAN_FOO',
        '        vlan-id 5',
        'interfaces',
        '    ge-0/0/0',
        '        unit 0',
        '            family ethernet-switching',
        '                port-mode access',
        '                vlan',
        '                    members VLAN_FOO',
        '    ge-0/0/1',
        '        unit 0',
        '            family ethernet-switching',
        '                port-mode access',
        '                vlan',
        '                    members VLAN_FOO',
        '    ge-0/0/2',
        '        unit 0',
        '            family ethernet-switching',
        '                port-mode access',
        '                vlan',
        '                    members VLAN_FOO',
        'routing-options',
        '    static',
        '        route 0.0.0.0/0 next-hop 172.16.12.1',
        '        route 192.168.36.0/25 next-hop 172.16.12.1',
    ]
    uut = CiscoConfParse(
        config.splitlines(),
        syntax="junos",
        comment="#",
        factory=False,
    )
    assert uut.ioscfg == result_correct_ioscfg
    assert uut.find_child_objects("interfaces", "ge-0/0/1",)[0].text == "    ge-0/0/1"
    assert uut.find_parent_objects("interfaces", "ge-0/0/1")[0].text == "interfaces"
    assert len(uut.find_parent_objects_wo_child("interfaces", "vlan", recurse=True)) == 0


def testParse_invalid_filepath_01():
    """Test that ciscoconfparse raises an error if the filepath is invalid"""
    # REMOVED caplog arg

    # Use a filename that should not exist...
    bad_filename = "./45faa63b-92e0-4449-a247-f20510d50c1b.txt"
    assert os.path.isfile(bad_filename) is False

    # ccp_logger_control(action="disable")  # Silence logs about the missing file error

    # Test that CiscoConfParse raises an error for an invalid filename...
    with pytest.raises(FileNotFoundError, match=""):
        # Normally logs to stdout... using logging.CRITICAL to hide errors...
        CiscoConfParse(bad_filename)


def testParse_invalid_filepath_02():
    # FIXME
    bad_filename = "this is not a filename or list"
    # Ensure the bad filename does not exist...
    assert os.path.isfile(bad_filename) is False

    # Test that we get FileNotFoundError() from CiscoConfParse(bad_filename)
    with pytest.raises(FileNotFoundError, match=""):
        CiscoConfParse(bad_filename)


def testParse_invalid_config_01():
    """test that we do not raise an error when parsing an empty config list"""
    parse = CiscoConfParse([])
    assert len(parse.objs) == 0


def testValues_IOSCfgLine_01():
    """test that default factory=False config inserts IOSCfgLine objects"""
    parse = CiscoConfParse(["1"], factory=False)
    assert len(parse.objs) == 1
    assert isinstance(parse.objs[0], IOSCfgLine) is True
    assert parse.objs[0].linenum == 0


def testValues_IOSCfgLine_02():
    """test that default factory=False config inserts a new IOSCfgLine object if a string is submitted"""
    parse = CiscoConfParse(["1"], factory=False)
    parse.append_line("2")
    assert len(parse.objs) == 2
    assert isinstance(parse.objs[1], IOSCfgLine) is True
    assert parse.objs[1].linenum == 1


def testValues_IOSCfgLine_03():
    """test that default factory=False config inserts a new IOSCfgLine object if an int is submitted"""
    parse = CiscoConfParse(["1"], factory=False)
    parse.append_line(2)
    assert len(parse.objs) == 2
    assert isinstance(parse.objs[1], IOSCfgLine) is True
    assert parse.objs[1].linenum == 1


def testValues_IOSCfgLine_04():
    """test that default factory=False config inserts a new IOSCfgLine object if a float is submitted"""
    parse = CiscoConfParse(["1"], factory=False)
    parse.append_line(2.0)
    assert len(parse.objs) == 2
    assert isinstance(parse.objs[1], IOSCfgLine) is True
    assert parse.objs[1].linenum == 1


def testValues_IOSCfgLine_07():
    """test that a bool in the config list and factory=False is rejected with a InvalidParameters()"""
    with pytest.raises(InvalidParameters):
        _ = CiscoConfParse([False], factory=False)

    with pytest.raises(InvalidParameters):
        _ = CiscoConfParse([True], factory=False)


def testValues_IOSCfgLine_08():
    """test that a bool in the config list and factory=True is rejected with a InvalidParameters()"""
    with pytest.raises(InvalidParameters):
        _ = CiscoConfParse([False], factory=True)


def testParse_f5_as_ios_00(parse_f01_ios):
    assert len(parse_f01_ios.objs) == 20


def testParse_f5_as_ios_02(parse_f02_ios_01):
    """
    Test parsing a brace-delimited f5 config with ios syntax.  Use fixtures/configs/sample_02.f5 as the test config.  That f5 config is pre-parsed in conftest.py as 'parse_f02_ios'.

    This Config Parsing Syntax:
    parse_f02_ios = CiscoConfParse('fixtures/configs/sample_02.f5', syntax='ios', factory=False)

    Ensure that line numbers, parent line numbers, and config text line up
    correctly... important note... closing curly-braces should be assigned as
    a child of the opening curly-brace.
    """

    correct_result = [
        "ltm profile udp DNS-UDP {",
        "    app-service none",
        "    datagram-load-balancing disabled",
        "    idle-timeout 31",
        "}",
        "ltm rule contrail-monitor {",
        "    when HTTP_REQUEST {",
        "                if {[active_members APN-DNS-TCP] > 0 & [active_members APN-DNS-UDP] > 0  } {",
        '''                        HTTP::respond 200 content "up"''',
        "                }",
        "        }",
        "}",
        "ltm rule contrail-monitor1 {",
        "    when HTTP_REQUEST {",
        "                if {[active_members APN-DNS-TCP] >= 0 & [active_members APN-DNS-UDP] >= 0  } {",
        '''                        HTTP::respond 200 content "up"''',
        "                }",
        "        }",
        "}",
        "ltm tacdb licenseddb licensed-tacdb {",
        "    partition none",
        "}",
        "ltm virtual ACME_VIP {",
        "    destination 192.168.1.191:http",
        "    ip-protocol tcp",
        "    mask 255.255.255.255",
        "    pool pool1",
        "    profiles {",
        "        http { }",
        "        tcp { }",
        "    }",
        "    rules {",
        "        MOBILE",
        "    }",
        "    source 0.0.0.0/0",
        "    source-address-translation {",
        "        type automap",
        "    }",
        "    translate-address enabled",
        "    translate-port enabled",
        "    vs-index 17",
        "}",
        "sys state-mirroring { }",
        "sys syslog {",
        '''    include "''',
        '''template t_remotetmpl {''',
        '''template (\"<$PRI>$STAMP $HOST $FACILITY[$PID]: $MSGONLY\"); template_escape(no);''',
        "};",
        "filter f_remote_loghost {",
        "level(info..emerg);",
        "};",
        "destination d_remote_loghost {",
        "udp(\"102.223.51.181\" port(519) template(t_remotetmpl));",
        "};",
        "log {",
        "source(s_syslog_pipe);",
        "filter(f_remote_loghost);",
        "destination(d_remote_loghost);",
        "};",
        '''"''',
        "remote-servers {",
        "        JSA {",
        "            host 102.223.51.181",
        "        }",
        "    }",
        "}",
        "sys url-db download-schedule urldb { }",
    ]
    # Close curly-braces should be assigned as children of the open curly-brace
    correct_result_linenum_dict = {
        0: {'linenum': 1, 'parent_linenum': 1},
        1: {'linenum': 2, 'parent_linenum': 1},
        2: {'linenum': 3, 'parent_linenum': 1},
        3: {'linenum': 4, 'parent_linenum': 1},
        4: {'linenum': 5, 'parent_linenum': 1},
        5: {'linenum': 6, 'parent_linenum': 6},
        6: {'linenum': 7, 'parent_linenum': 6},
        7: {'linenum': 8, 'parent_linenum': 7},
        8: {'linenum': 9, 'parent_linenum': 8},
        9: {'linenum': 10, 'parent_linenum': 8},
        10: {'linenum': 11, 'parent_linenum': 7},
        11: {'linenum': 12, 'parent_linenum': 6},
        12: {'linenum': 13, 'parent_linenum': 13},
        13: {'linenum': 14, 'parent_linenum': 13},
        14: {'linenum': 15, 'parent_linenum': 14},
        15: {'linenum': 16, 'parent_linenum': 15},
        16: {'linenum': 17, 'parent_linenum': 15},
        17: {'linenum': 18, 'parent_linenum': 14},
        18: {'linenum': 19, 'parent_linenum': 13},
        19: {'linenum': 20, 'parent_linenum': 20},
        20: {'linenum': 21, 'parent_linenum': 20},
        21: {'linenum': 22, 'parent_linenum': 20},
        22: {'linenum': 23, 'parent_linenum': 23},
        23: {'linenum': 24, 'parent_linenum': 23},
        24: {'linenum': 25, 'parent_linenum': 23},
        25: {'linenum': 26, 'parent_linenum': 23},
        26: {'linenum': 27, 'parent_linenum': 23},
        27: {'linenum': 28, 'parent_linenum': 23},
        28: {'linenum': 29, 'parent_linenum': 28},
        29: {'linenum': 30, 'parent_linenum': 28},
        30: {'linenum': 31, 'parent_linenum': 28},
        31: {'linenum': 32, 'parent_linenum': 23},
        32: {'linenum': 33, 'parent_linenum': 32},
        33: {'linenum': 34, 'parent_linenum': 32},
        34: {'linenum': 35, 'parent_linenum': 23},
        35: {'linenum': 36, 'parent_linenum': 23},
        36: {'linenum': 37, 'parent_linenum': 36},
        37: {'linenum': 38, 'parent_linenum': 36},
        38: {'linenum': 39, 'parent_linenum': 23},
        39: {'linenum': 40, 'parent_linenum': 23},
        40: {'linenum': 41, 'parent_linenum': 23},
        41: {'linenum': 42, 'parent_linenum': 23},
        42: {'linenum': 43, 'parent_linenum': 43},
        43: {'linenum': 44, 'parent_linenum': 44},
        44: {'linenum': 45, 'parent_linenum': 44},
        45: {'linenum': 46, 'parent_linenum': 46},
        46: {'linenum': 47, 'parent_linenum': 47},
        47: {'linenum': 48, 'parent_linenum': 46},
        48: {'linenum': 49, 'parent_linenum': 49},
        49: {'linenum': 50, 'parent_linenum': 50},
        50: {'linenum': 51, 'parent_linenum': 49},
        51: {'linenum': 52, 'parent_linenum': 52},
        52: {'linenum': 53, 'parent_linenum': 53},
        53: {'linenum': 54, 'parent_linenum': 52},
        54: {'linenum': 55, 'parent_linenum': 55},
        55: {'linenum': 56, 'parent_linenum': 56},
        56: {'linenum': 57, 'parent_linenum': 57},
        57: {'linenum': 58, 'parent_linenum': 58},
        58: {'linenum': 59, 'parent_linenum': 55},
        59: {'linenum': 60, 'parent_linenum': 60},
        60: {'linenum': 61, 'parent_linenum': 61},
        61: {'linenum': 62, 'parent_linenum': 61},
        62: {'linenum': 63, 'parent_linenum': 62},
        63: {'linenum': 64, 'parent_linenum': 62},
        64: {'linenum': 65, 'parent_linenum': 61},
        65: {'linenum': 66, 'parent_linenum': 44},
        66: {'linenum': 67, 'parent_linenum': 67},
    }
    assert len(parse_f02_ios_01.objs) == 67
    for dict_idx, obj in enumerate(parse_f02_ios_01.objs):
        assert dict_idx == obj.linenum

        # Be sure to strip off any double-spacing before comparing to obj.text
        tmp = correct_result[dict_idx]
        indent = len(tmp.rstrip()) - len(tmp.strip())
        assert indent == obj.indent
        assert correct_result[dict_idx] == obj.text

        assert correct_result_linenum_dict[dict_idx]['linenum'] == obj.linenum + 1
        assert correct_result_linenum_dict[dict_idx]['parent_linenum'] == obj.parent.linenum + 1


def testParse_f5_as_junos(parse_f01_junos_01):
    """Test parsing f5 config as junos syntax"""
    assert len(parse_f01_junos_01.objs) == 16


def testParse_asa_as_ios(config_a02):
    """Test for Github issue #42 parse asa banner with ios syntax"""
    parse = CiscoConfParse(config_a02, syntax="ios", factory=False)
    assert (parse is not None)


def testParse_asa_as_asa(config_a02):
    parse = CiscoConfParse(config_a02, syntax="asa", factory=False)
    assert (parse is not None)


def testValues_find_objects_dna(parse_c01_factory):
    """Test to find an object by its dna"""
    obj = parse_c01_factory.find_objects_dna("IOSIntf")[0]
    assert isinstance(obj, IOSIntfLine)


def testValues_macro_01():
    CONFIG = """!
interface FastEthernet 0/1
 ip address 172.16.1.1 255.255.255.0
 no ip proxy-arp
!
macro name THIS_MACRO
do sh ip int brief
@
macro name THAT_MACRO
do sh int status
@
line vty 0 4
 transport preferred none
end""".splitlines()
    parse = CiscoConfParse(CONFIG)
    mobjs = parse.find_objects("^macro")

    assert mobjs[0].linenum == 5
    assert parse.objs[6].parent == mobjs[0]
    assert parse.objs[6].linenum == 6
    assert parse.objs[7].parent == mobjs[0]
    assert parse.objs[7].linenum == 7

    assert mobjs[1].linenum == 8
    assert parse.objs[9].parent == mobjs[1]
    assert parse.objs[9].linenum == 9
    assert parse.objs[10].parent == mobjs[1]
    assert parse.objs[10].linenum == 10


def testValues_banner_delimiter_01():
    # Test banner delimiter on the same lines
    CONFIG = ["!", "banner motd ^   trivial banner here ^", "end"]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects("^banner")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER


def testValues_banner_delimiter_02():
    # Test multiple banner delimiters on the same lines
    CONFIG = ["!", "banner motd ^   trivial banner here ^^", "end"]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects("^banner")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER


def testValues_banner_delimiter_03():
    # Test banner delimiter on different lines
    CONFIG = ["!", "banner motd ^", "    trivial banner here ^", "end"]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects("^banner")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER


def testValues_banner_delimiter_04():
    # Test multiple banner delimiters on different lines
    CONFIG = ["!", "banner motd ^", "    trivial banner here ^^", "end"]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects("^banner")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER


def testValues_banner_delimiter_05():
    # Test multiple banners
    CONFIG = [
        "!",
        "banner motd ^",
        "    trivial banner1 here ^",
        "banner exec ^",
        "    trivial banner2 here ^",
        "end",
    ]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects(r"^banner\smotd")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER

    bannerobj = parse.find_objects(r"^banner\sexec")[0]
    BANNER_LINE_NUMBER = 3
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER


def testValues_banner_delimiter_06():
    """Test banners with a literal cntl-c delimiter"""
    ### WARNING: Be very careful editing this because vim eats cntl-c easily
    CONFIG = """!
banner motd 
================================================================================
# #
# This banner uses a literal control-c character to test cntl-c handling #
# #
================================================================================

!
line con 0
 authorization exec AAA_METHOD
 login authentication AAA_METHOD
!
end""".splitlines()
    parse = CiscoConfParse(CONFIG, ignore_blank_lines=True)
    assert parse.find_objects(r"banner")[0].text == "banner motd "
    assert parse.find_objects(r"banner")[0].children[-1].text == ""


def testValues_banner_delimiter_07():
    """
    Test banners with blank lines in them regardless of the setting in ignore_blank_lines.
    """
    CONFIG = """!
banner motd z

================================================================================

# This banner has blank lines to ensure that parsing this preserves the blanks

================================================================================

z
!
line con 0
 authorization exec AAA_METHOD
 login authentication AAA_METHOD
!
end""".splitlines()
    # Blank lines in banner should always be accepted, even if
    # ignore_blank_lines is True.
    # See Github Issue #229
    parse = CiscoConfParse(CONFIG, ignore_blank_lines=True, factory=True)
    assert len(parse.find_objects(r"banner")[0].children) == 8

    parse = CiscoConfParse(CONFIG, ignore_blank_lines=False, factory=True)
    assert len(parse.find_objects(r"banner")[0].children) == 8


def testValues_aaa_authfailmsg_delimiter_01():
    # Test auth fail-message delimiter on the same line...
    CONFIG = ["!", "aaa authentication fail-message ^   trivial banner here ^", "end"]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects(r"^aaa\sauthentication\sfail-message")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER
    assert len(bannerobj.children) == 0


def testValues_aaa_authfailmsg_delimiter_02():
    # Test multiple banner delimiters on different lines
    CONFIG = [
        "!",
        "aaa authentication fail-message ^",
        "    trivial banner here ^",
        "end",
    ]
    parse = CiscoConfParse(CONFIG)
    bannerobj = parse.find_objects(r"^aaa\sauthentication\sfail-message")[0]
    BANNER_LINE_NUMBER = 1
    assert bannerobj.linenum == BANNER_LINE_NUMBER
    for obj in bannerobj.children:
        assert obj.parent.linenum == BANNER_LINE_NUMBER
    assert len(bannerobj.children) == 1


def testValues_aaa_authfailmsg_delete_01():
    # Ensure  aa authentication fail-message banners are correctly deleted
    CONFIG = [
        "!",
        "aaa authentication fail-message ^",
        "    trivial banner1 here ^",
        "interface GigabitEthernet0/0",
        " ip address 192.0.2.1 255.255.255.0",
        "banner exec ^",
        "    trivial banner2 here ^",
        "end",
    ]
    parse = CiscoConfParse(CONFIG)
    for obj in parse.find_objects(r"^aaa\sauthentication\sfail-message"):
        obj.delete()
    parse.commit()
    assert parse.find_objects(r"^aaa\sauthentication\sfail-message") == []


def testValues_banner_delete_01():
    # Ensure multiline banners are correctly deleted
    CONFIG = [
        "!",
        "banner motd ^",
        "    trivial banner1 here ^",
        "interface GigabitEthernet0/0",
        " ip address 192.0.2.1 255.255.255.0",
        "banner exec ^",
        "    trivial banner2 here ^",
        "end",
    ]
    parse = CiscoConfParse(CONFIG)
    for obj in parse.find_objects("^banner"):
        obj.delete()
    parse.commit()
    assert parse.find_objects("^banner") == []


def testValues_banner_delete_02():
    # Ensure multiline banners are correctly deleted
    #
    # Check for Github issue #37
    CONFIG = [
        "!",
        "interface GigabitEthernet0/0",
        " ip address 192.0.2.1 255.255.255.0",
        "banner motd ^",
        "    trivial banner1 here ^",
        "interface GigabitEthernet0/1",
        " ip address 192.0.2.1 255.255.255.0",
        "banner exec ^",
        "    trivial banner2 here ^",
        "end",
    ]
    parse = CiscoConfParse(CONFIG)
    for obj in parse.find_objects("^banner"):
        obj.delete()
    parse.commit()

    assert parse.find_objects("^banner") == []

    # Github issue #37 assigned Gi0/1's child to Gi0/0 after deleting
    #  the banner motd line...
    for obj in parse.find_objects("^interface"):
        assert len(obj.children) == 1


def testValues_certificate_delete_01():
    """
    Test to ensure we have fixed Github Issue #253 (Cannot delete TLS certificates)
    """
    CONFIG = """hostname Test
!
!
crypto pki certificate chain TP-self-signed-1217560721
 certificate self-signed 01
  30820330 30820218 A0030201 02020101 300D0609 2A864886 F70D0101 05050030
  31312F30 2D060355 04031326 494F532D 53656C66 2D536967 6E65642D 43657274
  69666963 6174652D 31323137 35363037 3231301E 170D3232 31303037 31333535
  31305A17 0D333030 31303130 30303030 305A3031 312F302D 06035504 03132649
  4F532D53 656C662D 5369676E 65642D43 65727469 66696361 74652D31 32313735
  36303732 31308201 22300D06 092A8648 86F70D01 01010500 0382010F 00308201
  0A028201 0100D2F1 B72AD4AD 557B0956 8D006C61 447DD41E 52175C9C 75E56205
  54CD6D99 ABDAA952 1133A2C8 D245D15E 8C9BFBFC E21B2811 26410C50 CD52D073
  4ABE9B6B 33F47714 C88AC9E6 01EABCFD 688F08F1 17A63DD4 4C6C8416 56B043B5
  6CF35E52 2C3D7F4E 059B45CB 1162B9C2 AF804480 B3713E76 9E845B81 2BD7EF88
  C1A872D4 0BF0B63E CA88DA64 C892B965 B5B8F1AF AF71E3A1 2C2A6DC3 FDA0672D
  2FFA036D EF94E340 7FC9A746 5CD0FFD2 D7D16D1A C58001F5 5A1DB510 FF998F1F
  C4165A97 1A8A3B40 885F2752 CABF837D BF75FB8B 0A0F0FA4 081EFDE1 67CDD801
  F6E21BAF 9F19297E D01C2692 569159DD 943F575B F746CB38 84BDE01D 5E2A2464
  3CE33532 7AD50203 010001A3 53305130 0F060355 1D130101 FF040530 030101FF
  301F0603 551D2304 18301680 14408E61 23AA43B2 61472E1E 5521B74C BB659795
  BA301D06 03551D0E 04160414 408E6123 AA43B261 472E1E55 21B74CBB 659795BA
  300D0609 2A864886 F70D0101 05050003 82010100 93267903 B1EF6723 35AFE2BF
  B28584E6 6F5A5D22 58BECAC5 B5909FA2 D7A595E8 213DDAE0 EC096934 C48C9DC4
  D48F2155 3F94DA6E 7BDC97A6 AC4CC8DF FDB9ABD6 1105CCE3 979D022A 31266354
  458478A9 03809811 63D7B908 F24F2051 AEB28A9C DD88DB8F 054ECA02 B6D493B2
  4759ACD7 DEE2B5A3 0E1AED64 F148ABA5 4FD4BCEB 470E0C6F 22BB2099 6333BD7D
  F5459643 846729E5 EA0870B9 823F21C5 B1848871 C821F188 4425B123 B2F1C47F
  9B361B90 2065E3E9 29E39003 C3FF8525 914DD546 D3DDA987 8BC6089F 161477D9
  BC2BCCC6 28B2201A C1B8581D F372F062 288608BC 5099014D 430DE9C9 EF7B3A49
  B03CA0EF 2F7997B8 41799073 B33E96BC A88C6B97
        quit
crypto pki certificate chain SLA-TrustPoint
 certificate ca 01
  30820321 30820209 A0030201 02020101 300D0609 2A864886 F70D0101 0B050030
  32310E30 0C060355 040A1305 43697363 6F312030 1E060355 04031317 43697363
  6F204C69 63656E73 696E6720 526F6F74 20434130 1E170D31 33303533 30313934
  3834375A 170D3338 30353330 31393438 34375A30 32310E30 0C060355 040A1305
  43697363 6F312030 1E060355 04031317 43697363 6F204C69 63656E73 696E6720
  526F6F74 20434130 82012230 0D06092A 864886F7 0D010101 05000382 010F0030
  82010A02 82010100 A6BCBD96 131E05F7 145EA72C 2CD686E6 17222EA1 F1EFF64D
  CBB4C798 212AA147 C655D8D7 9471380D 8711441E 1AAF071A 9CAE6388 8A38E520
  1C394D78 462EF239 C659F715 B98C0A59 5BBB5CBD 0CFEBEA3 700A8BF7 D8F256EE
  4AA4E80D DB6FD1C9 60B1FD18 FFC69C96 6FA68957 A2617DE7 104FDC5F EA2956AC
  7390A3EB 2B5436AD C847A2C5 DAB553EB 69A9A535 58E9F3E3 C0BD23CF 58BD7188
  68E69491 20F320E7 948E71D7 AE3BCC84 F10684C7 4BC8E00F 539BA42B 42C68BB7
  C7479096 B4CB2D62 EA2F505D C7B062A4 6811D95B E8250FC4 5D5D5FB8 8F27D191
  C55F0D76 61F9A4CD 3D992327 A8BB03BD 4E6D7069 7CBADF8B DF5F4368 95135E44
  DFC7C6CF 04DD7FD1 02030100 01A34230 40300E06 03551D0F 0101FF04 04030201
  06300F06 03551D13 0101FF04 05300301 01FF301D 0603551D 0E041604 1449DC85
  4B3D31E5 1B3E6A17 606AF333 3D3B4C73 E8300D06 092A8648 86F70D01 010B0500
  03820101 00507F24 D3932A66 86025D9F E838AE5C 6D4DF6B0 49631C78 240DA905
  604EDCDE FF4FED2B 77FC460E CD636FDB DD44681E 3A5673AB 9093D3B1 6C9E3D8B
  D98987BF E40CBD9E 1AECA0C2 2189BB5C 8FA85686 CD98B646 5575B146 8DFC66A8
  467A3DF4 4D565700 6ADF0F0D CF835015 3C04FF7C 21E878AC 11BA9CD2 55A9232C
  7CA7B7E6 C1AF74F6 152E99B7 B1FCF9BB E973DE7F 5BDDEB86 C71E3B49 1765308B
  5FB0DA06 B92AFE7F 494E8A9E 07B85737 F3A58BE1 1A48A229 C37C1E69 39F08678
  80DDCD16 D6BACECA EEBC7CF9 8428787B 35202CDC 60E4616A B623CDBD 230E3AFB
  418616A9 4093E049 4D10AB75 27E86F73 932E35B5 8862FDAE 0275156F 719BB2F0
  D697DF7F 28
        quit
!
!
router bgp 1
 address-family ipv4 unicast
  neighbor 1.2.3.4 remote-as 1
 address-family ipv6 unicast
  neighbor 2600::1 remote-as 1
!
end""".splitlines()
    parse = CiscoConfParse(CONFIG, syntax='ios')

    tls_heads = parse.find_objects(r"crypto pki certificate")
    for obj in tls_heads:
        obj.delete()

    len_correct = 12
    assert len(parse.objs) == len_correct


def testValues_banner_child_parsing_01(parse_c01):
    """Associate banner lines as parent / child"""
    correct_result = {
        59: 58,
        60: 58,
        61: 58,
        62: 58,
        63: 63,  # Ensure the line *after* the banner isn't a child
    }
    banner_obj = parse_c01.find_objects("^banner")[0]

    # Check banner's parent line (should be its line number)
    assert banner_obj.parent.linenum == 58
    for child in banner_obj.all_children:
        test_result = child.parent.linenum
        assert correct_result[child.linenum] == test_result


def testValues_banner_child_parsing_02():
    ## Test for Github issue #115
    config = """!
banner exec ^
!!! You should leave now !!!
In case you haven't heard me, I'll give you another reason...
!!! I have been known to be violent when I'm hungry !!!
This router is protected by a hungry admin
^
!
"""
    parse = CiscoConfParse(config.splitlines(), syntax="ios")

    # parent_intf_dict keeps track of child to parent line number mappings
    parent_intf_dict = {
        # Line 0's parent should be 0
        0: 0,
        # Line 1's parent should be 1
        1: 1,
        # Line 2's parent should be 1, etc...
        2: 1,
        3: 1,
        4: 1,
        5: 1,
        6: 1,
        7: 7,
    }
    for obj in parse.find_objects(""):

        correct_result = parent_intf_dict.get(obj.linenum, -1)
        if correct_result:
            test_result = obj.parent.linenum
            ## Does this object parent's line number match?
            assert correct_result == test_result


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
    for obj in parse_c01.find_objects(""):
        correct_result = parent_intf.get(obj.linenum, False)
        if correct_result:
            test_result = obj.parent.linenum
            ## Does this object parent's line number match?
            assert correct_result == test_result


def testValues_parent_child_parsing_02():

    config = """!
interface Serial 1/0
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
interface GigabitEthernet4/1
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
interface GigabitEthernet4/2
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!
interface GigabitEthernet4/3
 shutdown
!
end"""
    cfg = CiscoConfParse(config.splitlines(), syntax="ios", factory=False)
    # Expected child / parent line numbers before the insert
    parent_before_dict = {
        0: 0,
        # Line 1 is Serial1/0, child is line 13
        1: 1,
        2: 1,
        3: 1,
        4: 4,
        # Line 5 is GigabitEthernet4/1
        5: 5,
        6: 5,
        7: 5,
        8: 5,
        9: 5,
        # Line 10 is comment
        10: 10,
        # Line 11 is GigabitEthernet4/2
        11: 11,
        12: 11,
        13: 11,
        14: 11,
        15: 11,
        # Line 16 is comment
        16: 16,
        # Line 17 is GigabitEthernet4/3
        17: 17,
        18: 17,
        # Line 19 is comment
        19: 19,
        # Line 20 is end
        20: 20,
    }

    # Validate line numbers *before* inserting
    for obj in cfg.find_objects(""):
        correct_result = parent_before_dict.get(obj.linenum, -1)
        test_result = obj.parent.linenum
        ## Does this object parent's line number match?
        assert correct_result == test_result


    # Dictionary of parent linenumber assignments below...
    parent_after_dict = {
        # dictionary format...
        # - key (integer) is CHILD line number
        # - value (integer) is PARENT line number
        0: 0,
        # Line 1 is Serial1/0, child is line 13
        1: 1,
        2: 1,
        3: 1,
        4: 4,
        # Line 5 is GigabitEthernet4/1
        5: 5,
        6: 5,
        7: 5,
        8: 5,
        9: 5,
        10: 5,
        # Line 11 is comment
        11: 11,
        # Line 12 is GigabitEthernet4/2
        12: 12,
        13: 12,
        14: 12,
        15: 12,
        16: 12,
        17: 12,
        # Line 18 is comment
        18: 18,
        # Line 19 is GigabitEthernet4/3
        19: 19,
        20: 19,
        # Line 21 is comment
        21: 21,
        # Line 22 is end
        22: 22,
    }

    # Insert lines here...
    for intf_obj in cfg.find_objects(r"^interface\sGigabitEthernet"):
        # Configured with an access vlan...
        if " switchport access vlan 100" in {ii.text for ii in intf_obj.children}:
            intf_obj.insert_after(" spanning-tree portfast")
    cfg.commit()

    # Validate line numbers *after* inserting
    for parent_obj in cfg.find_objects(""):
        for child_obj in parent_obj.all_children:
            # correct_result is the **correct parent line number** after insert...
            correct_result = parent_after_dict.get(child_obj.linenum, -1)

            test_result = child_obj.parent.linenum
            ## Does this object parent's line number match?
            assert correct_result == test_result


def testValues_find_lines(parse_c01):
    c01_intf = ["interface Serial 1/0"]
    c01_find_gige_no_exactmatch = [
        "interface GigabitEthernet4/1",
        "interface GigabitEthernet4/2",
        "interface GigabitEthernet4/3",
        "interface GigabitEthernet4/4",
        "interface GigabitEthernet4/5",
        "interface GigabitEthernet4/6",
        "interface GigabitEthernet4/7",
        "interface GigabitEthernet4/8",
    ]
    find_lines_Values = (
        # Ensure exact matches work regardless of the exactmatch boolean
        ({"linespec": "interface Serial 1/0", "exactmatch": False}, c01_intf),
        ({"linespec": "interface Serial 1/0", "exactmatch": True}, c01_intf),
        # Ensure we can find string matches inside an interface config block
        ({"linespec": "encapsulation", "exactmatch": False}, [" encapsulation ppp"]),
        # Ensure exactmatch=False catches beginning phrases in the config
        (
            {"linespec": "interface GigabitEthernet4/", "exactmatch": False},
            c01_find_gige_no_exactmatch,
        ),
        # Ensure exactmatch=False catches single words in the config
        (
            {"linespec": "igabitEthernet", "exactmatch": False},
            c01_find_gige_no_exactmatch,
        ),
        # Negative test: matches are Case-Sensitive
        ({"linespec": "GigaBitEtherNeT", "exactmatch": False}, []),
        # Negative test for exactmatch=True
        ({"linespec": "interface GigabitEthernet4/", "exactmatch": True}, []),
        # Negative test for exactmatch=True and ignore_ws=False
        (
            {"linespec": "interface Serial1/0", "exactmatch": True, "ignore_ws": False},
            [],
        ),
    )

    for args, correct_result in find_lines_Values:
        test_result = parse_c01.find_lines(**args)
        assert correct_result == test_result


def testValues_obj_insert_before_01():
    """test whether we can insert before IOSCfgLine() elements"""
    c01 = [
        "b",
        "c",
        "d",
        "e",
    ]
    parse = CiscoConfParse(c01, syntax="ios")
    obj = parse.find_objects("b")[0]
    obj.insert_before('a')
    assert parse.ConfigObjs[0].text == 'a'


def testValues_obj_insert_01():
    """test whether we can insert list elements"""
    c01 = [
        "b",
        "c",
        "d",
        "e",
    ]
    parse = CiscoConfParse(c01, syntax="ios")
    parse.find_objects('b')[0].insert_before('a')
    parse.find_objects('e')[0].insert_after('f')
    assert parse.ConfigObjs[0].text == 'a'
    assert parse.ConfigObjs[-1].text == 'f'


def testValues_obj_insert_02():
    """test whether we can insert and find objects after the insert"""
    c01 = [
        "b",
        "c",
        "d",
        "e",
    ]
    parse = CiscoConfParse(c01, syntax="ios")
    parse.find_objects('b')[0].insert_before('a')
    parse.find_objects('e')[0].insert_after('f')
    parse.commit()

    all_objs = parse.find_objects(r"^e")
    assert len(all_objs) == 1
    assert all_objs[0].text == "e"

    assert parse.ConfigObjs[0].text == 'a'
    assert parse.ConfigObjs[-1].text == 'f'


def testValues_obj_insert_03():
    """test whether we can insert a new child list element"""
    c01 = ["b", "c", "d", "e",]
    parse = CiscoConfParse(c01, syntax="ios")

    # ' f' is the new child of 'e'...
    parse.find_objects('e')[0].insert_after(' f')
    parse.commit()
    assert parse.ConfigObjs[-1].text == ' f'

    obj = parse.find_objects(r"^e")[0]
    assert obj.all_children[0].text == ' f'


def testValues_obj_insert_04():
    """Test whether a new interface can be inserted and all new children assigned to it instead of the original parent"""
    this_syntax = "ios"
    config = """interface GigabitEthernet0/6
     no shutdown
     no nameif
     no security-level
     no ip address"""

    parse = CiscoConfParse(config.splitlines(), syntax=this_syntax)
    obj = parse.find_objects(r'^interface\s+GigabitEthernet0/6\s*$')[0]
    obj.insert_after('interface GigabitEthernet0/6.30')
    parse.commit()
    assert parse.ConfigObjs[0].text == "interface GigabitEthernet0/6"
    assert parse.ConfigObjs[1].text == "interface GigabitEthernet0/6.30"
    assert parse.ConfigObjs[2].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[3].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[4].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[5].parent == parse.ConfigObjs[1]


def testValues_obj_insert_05():
    """Test whether a new NXOS interface can be inserted and all new children assigned to it instead of the original parent"""
    config = """interface GigabitEthernet0/6
     no shutdown
     no nameif
     no security-level
     no ip address"""

    parse = CiscoConfParse(
        config.splitlines(),
        syntax='nxos',
        ignore_blank_lines=False,
    )
    obj = parse.find_objects(r'^interface\s+GigabitEthernet0/6\s*$')[0]
    obj.insert_after('interface GigabitEthernet0/6.30')
    parse.commit()
    assert parse.ConfigObjs[0].text == "interface GigabitEthernet0/6"
    assert parse.ConfigObjs[1].text == "interface GigabitEthernet0/6.30"
    assert parse.ConfigObjs[2].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[3].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[4].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[5].parent == parse.ConfigObjs[1]


def testValues_list_insert_06():
    """Test whether a new ASA interface can be inserted and all new children assigned to it instead of the original parent"""
    this_syntax = "asa"
    config = """interface GigabitEthernet0/6
     no shutdown
     no nameif
     no security-level
     no ip address"""

    parse = CiscoConfParse(config.splitlines(), syntax=this_syntax)
    obj = parse.find_objects(r'^interface\s+GigabitEthernet0/6\s*$')[0]
    obj.insert_after('interface GigabitEthernet0/6.30')
    parse.commit()
    assert parse.ConfigObjs[0].text == "interface GigabitEthernet0/6"
    assert parse.ConfigObjs[1].text == "interface GigabitEthernet0/6.30"
    assert parse.ConfigObjs[2].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[3].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[4].parent == parse.ConfigObjs[1]
    assert parse.ConfigObjs[5].parent == parse.ConfigObjs[1]


def testValues_find_object_branches_01():
    """Basic test: find_object_branches() - only look for object text matching (90% solution)"""
    config = [
        "ltm pool FOO {",
        "  members {",
        "    k8s-05.localdomain:8443 {",
        "      address 192.0.2.5",
        "      session monitor-enabled",
        "      state up",
        "    }",
        "    k8s-06.localdomain:8443 {",
        "      address 192.0.2.6",
        "      session monitor-enabled",
        "      state down",
        "    }",
        "  }",
        "}",
        "ltm pool BAR {",
        "  members {",
        "    k8s-07.localdomain:8443 {",
        "      address 192.0.2.7",
        "      session monitor-enabled",
        "      state down",
        "    }",
        "  }",
        "}",
    ]
    parse = CiscoConfParse(config, syntax="junos", comment="#")
    branchspec = (r"^ltm\spool\s+(\S+)", r"(members)", r"(\S+?):(\d+)", r"state\s(up|down)")
    test_result = parse.find_object_branches(branchspec=branchspec, regex_groups=True)

    assert len(test_result) == 3

    # Test first family branch result...
    assert test_result[0][0] == ("FOO",)
    assert test_result[0][1] == ("members",)
    assert test_result[0][2] == ("k8s-05.localdomain", "8443",)
    assert test_result[0][3] == ("up",)

    # Test second family branch result...
    assert test_result[1][0] == ("FOO",)
    assert test_result[1][1] == ("members",)
    assert test_result[1][2] == ("k8s-06.localdomain", "8443",)
    assert test_result[1][3] == ("down",)  # 'state down' != 'state up'

    # Test third family branch result...
    assert test_result[2][0] == ("BAR",)
    assert test_result[2][1] == ("members",)
    assert test_result[2][2] == ("k8s-07.localdomain", "8443",)
    assert test_result[2][3] == ("down",)  # 'state down' != 'state up'


def testValues_find_object_branches_02():
    """Basic test: find_object_branches() - only look for object text matching (90% solution)"""
    config = [
        "ltm pool FOO {",
        "  members {",
        "    k8s-05.localdomain:8443 {",
        "      address 192.0.2.5",
        "      session monitor-enabled",
        "      state up",
        "    }",
        "    k8s-06.localdomain:8443 {",
        "      address 192.0.2.6",
        "      session monitor-enabled",
        "      state down",
        "    }",
        "  }",
        "}",
        "ltm pool BAR {",
        "  members {",
        "    k8s-07.localdomain:8443 {",
        "      address 192.0.2.7",
        "      session monitor-enabled",
        "      state down",
        "    }",
        "  }",
        "}",
    ]

    parse = CiscoConfParse(config, syntax="junos", comment="#")
    # Test negative lookahead matching in the first regex term... Dont match
    # 'ltm pool BAR'...
    branchspec = (r"ltm\spool\s(?!BAR)", r"members", r"\S+?:\d+", r"state\sup")
    test_result = parse.find_object_branches(branchspec=branchspec)

    assert len(test_result) == 2

    # Test first family branch result...
    assert test_result[0][0].text.strip() == "ltm pool FOO"
    assert test_result[0][1].text.strip() == "members"
    assert test_result[0][2].text.strip() == "k8s-05.localdomain:8443"
    assert test_result[0][3].text.strip() == "state up"

    # Test second family branch result...
    assert test_result[1][0].text.strip() == "ltm pool FOO"
    assert test_result[1][1].text.strip() == "members"
    assert test_result[1][2].text.strip() == "k8s-06.localdomain:8443"
    assert test_result[1][3] is None  # 'state down' != 'state up'


def testValues_find_object_branches_03(parse_c01):
    """Basic test: find_object_branches() - Test for multiple matches to a vague branchspec term..."""

    # NOTE This is NOT a good example of how to use find_object_branches... I'm
    # testing to ensure we get the right matches for a vague regular expression...
    # this winds up returning a lot of different match object types in the
    # last branch term
    branchspec = (
        r"^interface",
        r"switchport",
    )
    test_result = parse_c01.find_object_branches(branchspec=branchspec)

    assert len(test_result) == 19

    assert test_result[0][0].text.strip() == "interface Serial 1/0"
    assert test_result[0][1] is None  # Serial is not a switchport :)

    assert test_result[1][0].text.strip() == "interface GigabitEthernet4/1"
    assert test_result[1][1].text.strip() == "switchport"

    assert test_result[2][0].text.strip() == "interface GigabitEthernet4/1"
    assert test_result[2][1].text.strip() == "switchport access vlan 100"

    assert test_result[3][0].text.strip() == "interface GigabitEthernet4/1"
    assert test_result[3][1].text.strip() == "switchport voice vlan 150"

    assert test_result[4][0].text.strip() == "interface GigabitEthernet4/2"
    assert test_result[4][1].text.strip() == "switchport"

    assert test_result[5][0].text.strip() == "interface GigabitEthernet4/2"
    assert test_result[5][1].text.strip() == "switchport access vlan 100"

    assert test_result[6][0].text.strip() == "interface GigabitEthernet4/2"
    assert test_result[6][1].text.strip() == "switchport voice vlan 150"

    assert test_result[7][0].text.strip() == "interface GigabitEthernet4/3"
    assert test_result[7][1].text.strip() == "switchport"

    assert test_result[8][0].text.strip() == "interface GigabitEthernet4/3"
    assert test_result[8][1].text.strip() == "switchport access vlan 100"

    assert test_result[9][0].text.strip() == "interface GigabitEthernet4/3"
    assert test_result[9][1].text.strip() == "switchport voice vlan 150"

    assert test_result[10][0].text.strip() == "interface GigabitEthernet4/4"
    assert test_result[10][1] is None  # Gi4/4 isn't a switchport (ref regex term)

    assert test_result[11][0].text.strip() == "interface GigabitEthernet4/5"
    assert test_result[11][1].text.strip() == "switchport"

    assert test_result[12][0].text.strip() == "interface GigabitEthernet4/5"
    assert test_result[12][1].text.strip() == "switchport access vlan 110"

    assert test_result[13][0].text.strip() == "interface GigabitEthernet4/6"
    assert test_result[13][1].text.strip() == "switchport"

    assert test_result[14][0].text.strip() == "interface GigabitEthernet4/6"
    assert test_result[14][1].text.strip() == "switchport access vlan 110"

    assert test_result[15][0].text.strip() == "interface GigabitEthernet4/7"
    assert test_result[15][1].text.strip() == "switchport"

    assert test_result[16][0].text.strip() == "interface GigabitEthernet4/7"
    assert test_result[16][1].text.strip() == "switchport access vlan 110"

    assert test_result[17][0].text.strip() == "interface GigabitEthernet4/8"
    assert test_result[17][1].text.strip() == "switchport"

    assert test_result[18][0].text.strip() == "interface GigabitEthernet4/8"
    assert test_result[18][1].text.strip() == "switchport access vlan 110"


def testValues_find_object_branches_04(parse_c01):
    """Basic test: find_object_branches() - Test that non-existent regex child levels return `None`"""

    # NOTE This is NOT a good example of using find_object_branches()... I'm
    # negative testing to ensure we get the right matches for NO regex
    # matches...
    branchspec = (r"this", r"dont", "match", "at", "all")
    test_result = parse_c01.find_object_branches(branchspec=branchspec)
    correct_result = [[None, None, None, None, None]]
    assert test_result == correct_result


def testValues_find_object_branches_05():
    """Basic test: find_object_branches() - Test that non-existent regex child levels are returned if allow_none=True (see Github Issue #178)"""
    test_data = ['thisis',
                 '    atest',
                 '        ofbranchsearch',
                 'thisis',
                 '    atest',
                 '        matchthis']

    parse = CiscoConfParse(test_data)

    branchspec = (r"^this", r"^\s+atest", r"^\s+matchthis")
    test_result = parse.find_object_branches(branchspec)

    assert len(test_result) == 2
    assert test_result[0][0].text.strip() == "thisis"
    assert test_result[0][1].text.strip() == "atest"
    assert test_result[0][2] is None
    assert test_result[1][0].text.strip() == "thisis"
    assert test_result[1][1].text.strip() == "atest"
    assert test_result[1][2].text.strip() == "matchthis"


def testValues_find_objects_w_parents(parse_c01):
    correct_result = [
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
    ]
    ## test find_children_w_parents
    test_result = [ii.text for ii in parse_c01.find_objects_w_parents("interface GigabitEthernet4/1", "switchport")]
    assert correct_result == test_result


def testValues_find_objects_w_all_children(parse_c01):
    correct_result = parse_c01.find_objects(r"^interface GigabitEthernet4/[12]")
    test_result = parse_c01.find_objects_w_all_children(
        "^interface", ["switchport voice", "power inline"]
    )
    assert test_result == correct_result


def testValues_delete_children_matching():
    config = [
        '!',
        'interface Serial1/0',
        ' description Some lame description',
        ' ip address 1.1.1.1 255.255.255.252',
        '!',
        'interface Serial1/1',
        ' description Another lame description',
        ' ip address 1.1.1.5 255.255.255.252',
        '!',
    ]
    correct_result = [
        '!',
        'interface Serial1/0',
        ' ip address 1.1.1.1 255.255.255.252',
        '!',
        'interface Serial1/1',
        ' ip address 1.1.1.5 255.255.255.252',
        '!',
    ]
    parse = CiscoConfParse(config, syntax="ios")
    for obj in parse.find_objects(r'^interface'):
        obj.delete_children_matching('description')
    assert parse.ioscfg == correct_result


def testValues_delete_lines_01():
    """Catch bugs similar to those fixed by https://github.com/mpenning/ciscoconfparse/pull/140"""
    config = [
        "interface FastEthernet0/2",
        " switchport port-security maximum 2",
        " switchport port-security violation restrict",
        " switchport port-security",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "end",
    ]

    correct_result = [
        "interface FastEthernet0/2",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, syntax="ios")
    parse.delete_lines("port-security")  # Delete lines from config
    assert parse.ioscfg == correct_result


def testValues_delete_lines_02():
    """Catch bugs similar to those fixed by https://github.com/mpenning/ciscoconfparse/pull/140"""
    config = [
        "interface FastEthernet0/2",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        " switchport port-security maximum 2",
        " switchport port-security violation restrict",
        " switchport port-security",
        "!",
        "end",
    ]

    correct_result = [
        "interface FastEthernet0/2",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, syntax="ios")
    parse.delete_lines("port-security")  # Delete lines from config
    assert parse.ioscfg == correct_result


def testValues_delete_lines_03():
    """Catch bugs similar to those fixed by https://github.com/mpenning/ciscoconfparse/pull/140"""
    config = [
        "! port-security",
        "interface FastEthernet0/2",
        " switchport port-security maximum 2",
        " switchport port-security violation restrict",
        " switchport port-security",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "interface FastEthernet0/3",
        " switchport port-security maximum 2",
        " switchport port-security violation restrict",
        " switchport port-security",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "end",
    ]

    correct_result = [
        "interface FastEthernet0/2",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "interface FastEthernet0/3",
        " switchport mode trunk",
        " switchport trunk allowed 300,532",
        " switchport nonegotiate",
        "!",
        "end",
    ]

    parse = CiscoConfParse(config, syntax="ios")
    parse.delete_lines("port-security")  # Delete lines from config
    assert parse.ioscfg == correct_result


def testValues_replace_lines_01(parse_c01):
    c01_replace_gige_no_exactmatch = [
        "interface GigabitEthernet8/1",
        "interface GigabitEthernet8/2",
        "interface GigabitEthernet8/3",
        "interface GigabitEthernet8/4",
        "interface GigabitEthernet8/5",
        "interface GigabitEthernet8/6",
        "interface GigabitEthernet8/7",
        "interface GigabitEthernet8/8",
    ]
    replace_lines_Values01 = (
        # Ensure basic replacements work
        (
            {"linespec": r"interface Serial 1/0", "replacestr": "interface Serial 2/0"},
            ["interface Serial 2/0"],
        ),
        # Ensure we make multiple replacements as required
        (
            {
                "linespec": "GigabitEthernet4/",
                "replacestr": "GigabitEthernet8/",
                "exactmatch": False,
            },
            c01_replace_gige_no_exactmatch,
        ),
    )
    # We have to parse multiple times because of replacements
    for args, correct_result in replace_lines_Values01:
        test_result = parse_c01.replace_lines(**args)
        assert correct_result == test_result


def testValues_replace_lines_02(parse_c01):
    c01_replace_gige_exclude = [
        "interface GigabitEthernet8/1",
        "interface GigabitEthernet8/2",
        "interface GigabitEthernet8/3",
        "interface GigabitEthernet8/7",
        "interface GigabitEthernet8/8",
    ]
    replace_lines_Values02 = (
        # Ensure exactmatch rejects substrings
        (
            {
                "linespec": "interface Serial 1/",
                "replacestr": "interface Serial 2/",
                "exactmatch": True,
            },
            [],
        ),
        # Ensure we exclude lines which match excludespec
        (
            {
                "linespec": "GigabitEthernet4/",
                "excludespec": r"/4|/5|/6",
                "replacestr": "GigabitEthernet8/",
                "exactmatch": False,
            },
            c01_replace_gige_exclude,
        ),
    )
    for args, correct_result in replace_lines_Values02:
        test_result = parse_c01.replace_lines(**args)
        assert correct_result == test_result


def testValues_replace_lines_03(parse_c01):
    """Ensure we can use a compiled regexp in excludespec"""
    c01_replace_gige_exclude = [
        "interface GigabitEthernet8/1",
        "interface GigabitEthernet8/2",
        "interface GigabitEthernet8/3",
        "interface GigabitEthernet8/7",
        "interface GigabitEthernet8/8",
    ]
    replace_lines_Values03 = (
        # Ensure we can use a compiled regexp in excludespec...
        (
            {
                "linespec": "GigabitEthernet4/",
                "excludespec": re.compile(r"/4|/5|/6"),
                "replacestr": "GigabitEthernet8/",
                "exactmatch": False,
            },
            c01_replace_gige_exclude,
        ),
    )
    for args, correct_result in replace_lines_Values03:
        test_result = parse_c01.replace_lines(**args)
        assert correct_result == test_result


def testValues_replace_children_01(parse_c01):
    """Test child line replacement"""
    c01_replace_children = [
        " power inline static max 30000",
        " power inline static max 30000",
    ]
    replace_children_Values = (
        (
            {
                "parentspec": "GigabitEthernet4/",
                "childspec": "max 7000",
                "excludespec": re.compile(r"/4|/5|/6"),
                "replacestr": "max 30000",
                "exactmatch": False,
            },
            c01_replace_children,
        ),
    )
    # We have to parse multiple times because of replacements
    for args, correct_result in replace_children_Values:
        test_result = parse_c01.replace_children(**args)
        assert correct_result == test_result


def testValues_Diff_01():
    # config_01 is the starting point
    config_01 = [
        "!",
        "interface GigabitEthernet 1/5",
        " ip address 1.1.1.2 255.255.255.0",
        " standby 5 ip 1.1.1.1",
        " standby 5 preempt",
        "!",
    ]

    required_config = [
        "!",
        "interface GigabitEthernet 1/5",
        " switchport",
        " switchport mode access",
        " switchport access vlan 5",
        " switchport nonegotiate",
        "!",
        "interface Vlan5",
        " no shutdown",
        " ip address 1.1.1.2 255.255.255.0",
        " standby 5 ip 1.1.1.1",
        " standby 5 preempt",
        "!",
    ]

    correct_result = [
        "interface GigabitEthernet 1/5",
        "  no ip address 1.1.1.2 255.255.255.0",
        "  no standby 5 ip 1.1.1.1",
        "  no standby 5 preempt",
        "  switchport",
        "  switchport mode access",
        "  switchport access vlan 5",
        "  switchport nonegotiate",
        "interface Vlan5",
        "  ip address 1.1.1.2 255.255.255.0",
        "  standby 5 ip 1.1.1.1",
        "  standby 5 preempt",
        "  no shutdown",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_02():
    """Test diffs against double-spacing for children (such as NXOS)"""
    # config_01 is the starting point
    config_01 = [
        "!",
        "interface GigabitEthernet 1/5",
        "  ip address 1.1.1.2 255.255.255.0",
        "  standby 5 ip 1.1.1.1",
        "  standby 5 preempt",
        "!",
    ]

    required_config = [
        "!",
        "interface GigabitEthernet 1/5",
        "  switchport",
        "  switchport mode access",
        "  switchport access vlan 5",
        "  switchport nonegotiate",
        "!",
        "interface Vlan5",
        "  no shutdown",
        "  ip address 1.1.1.2 255.255.255.0",
        "  standby 5 ip 1.1.1.1",
        "  standby 5 preempt",
        "!",
    ]

    correct_result = [
        "interface GigabitEthernet 1/5",
        "  no ip address 1.1.1.2 255.255.255.0",
        "  no standby 5 ip 1.1.1.1",
        "  no standby 5 preempt",
        "  switchport",
        "  switchport mode access",
        "  switchport access vlan 5",
        "  switchport nonegotiate",
        "interface Vlan5",
        "  ip address 1.1.1.2 255.255.255.0",
        "  standby 5 ip 1.1.1.1",
        "  standby 5 preempt",
        "  no shutdown",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_03():
    config_01 = ["!", "vlan 51", " state active", "vlan 53", "!"]

    required_config = [
        "!",
        "vlan 51",
        " name SOME-VLAN",
        " state active",
        "vlan 52",
        " name BLAH",
        " state active",
        "!",
    ]

    correct_result = [
        "no vlan 53",
        "vlan 51",
        "  name SOME-VLAN",
        "vlan 52",
        "  name BLAH",
        "  state active",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_04():
    """Test diffs against double-spacing for children (such as NXOS)"""
    # config_01 is the starting point
    config_01 = [
        "!",
        "vlan 51",
        "  state active",
        "vlan 53",
        "!",
    ]

    required_config = [
        "!",
        "vlan 51",
        "  name SOME-VLAN",
        "  state active",
        "vlan 52",
        "  name BLAH",
        "  state active",
        "!",
    ]

    correct_result = [
        "no vlan 53",
        "vlan 51",
        "  name SOME-VLAN",
        "vlan 52",
        "  name BLAH",
        "  state active",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_05():
    """Test diffs with remove_lines=False"""
    # config_01 is the starting point
    config_01 = [
        "!",
        "vlan 51",
        " state active",
        "vlan 53",
        "!",
        "vtp mode transparent",
    ]

    required_config = [
        "!",
        "vlan 51",
        " name SOME-VLAN",
        " state active",
        "vlan 52",
        " name BLAH",
        " state active",
        "!",
    ]

    correct_result = [
        "no vlan 53",
        "no vtp mode transparent",
        "vlan 51",
        "  name SOME-VLAN",
        "vlan 52",
        "  name BLAH",
        "  state active",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_06():
    """Test diffs with global command order mixed up"""
    # config_01 is the starting point
    config_01 = [
        "!",
        "vlan 51",
        " state active",
        "vlan 53",
        "!",
        "vtp mode transparent",
    ]

    required_config = [
        "!",
        "vtp mode transparent",
        "vlan 52",
        " name BLAH",
        " state active",
        "vlan 51",
        " name SOME-VLAN",
        " state active",
        "!",
    ]

    correct_result = [
        "no vlan 53",
        "vlan 52",
        "  name BLAH",
        "  state active",
        "vlan 51",
        "  name SOME-VLAN",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_07():
    """Test diffs with global command order mixed up"""
    # config_01 is the starting point
    config_01 = [
        "!",
        "vlan 51",
        " state active",
        "vlan 53",
        "!",
        "vtp mode transparent",
    ]

    required_config = [
        "!",
        "vtp mode transparent",
        "vlan 51",
        " name SOME-VLAN",
        " state active",
        "vlan 52",
        " name BLAH",
        " state active",
        "!",
    ]

    correct_result = [
        "no vlan 53",
        "vlan 51",
        "  name SOME-VLAN",
        "vlan 52",
        "  name BLAH",
        "  state active",
    ]

    uut = Diff(
        old_config=config_01,
        new_config=required_config,
        syntax='ios')
    assert uut.diff() == correct_result


def testValues_Diff_08():
    """Test Diff() output for matching input configurations"""
    before_config = ["logging 1.1.3.4", "logging 1.1.3.5", "logging 1.1.3.6",]
    after_config = ["logging 1.1.3.4", "logging 1.1.3.5", "logging 1.1.3.6",]
    uut = Diff(
        old_config=before_config,
        new_config=after_config,
        syntax='ios')
    assert uut.diff() == []


def testValues_Diff_09():
    """Test Diff() output for different input global configurations"""
    before_config = ["logging 1.1.3.4", "logging 1.1.3.5", "logging 1.1.3.6",]
    after_config = ["logging 1.1.3.255", "logging 1.1.3.5", "logging 1.1.3.6",]

    uut = Diff(
        old_config=before_config,
        new_config=after_config,
        syntax='ios')
    correct_result = ['no logging 1.1.3.4', 'logging 1.1.3.255']

    assert uut.diff() == correct_result


def testValues_ignore_ws():
    ## test find_lines with ignore_ws flag
    config = ["set snmp community read-only     myreadonlystring"]
    correct_result = config
    cfg = CiscoConfParse(config)
    test_result = cfg.find_lines(
        "set snmp community read-only myreadonlystring", ignore_ws=True
    )
    assert correct_result == test_result


def testValues_negative_ignore_ws():
    """test find_lines WITHOUT ignore_ws"""
    config = ["set snmp community read-only     myreadonlystring"]
    correct_result = list()
    cfg = CiscoConfParse(config)
    test_result = cfg.find_lines(
        "set snmp community read-only myreadonlystring", ignore_ws=False
    )
    assert correct_result == test_result


def testValues_IOSCfgLine_all_parents(parse_c01):
    """Ensure IOSCfgLine.all_parents finds all parents, recursively"""
    correct_result = list()
    # mockobj pretends to be the IOSCfgLine object
    with patch(__name__ + "." + "IOSCfgLine") as mockobj:
        vals = [("policy-map QOS_1", 0), (" class SILVER", 4)]
        # fakeobj pretends to be an IOSCfgLine instance at the given line number
        for idx, fakeobj in enumerate(map(deepcopy, repeat(mockobj, len(vals)))):
            fakeobj.text = vals[idx][0]
            fakeobj.linenum = vals[idx][1]
            fakeobj.classname = "IOSCfgLine"

            correct_result.append(fakeobj)

    cfg = parse_c01
    obj = cfg.find_objects("bandwidth 30")[0]
    ## Removed _find_parent_OBJ on 20140202
    # test_result = cfg._find_parent_OBJ(obj)
    test_result = obj.all_parents
    for idx, testobj in enumerate(test_result):
        assert correct_result[idx].text == test_result[idx].text
        assert correct_result[idx].linenum == test_result[idx].linenum
        assert correct_result[idx].classname == test_result[idx].classname


def testValues_IOSCfgLine_geneology_junos():
    config = """
base_hello {
    that_thing {
       parameter_01 {}
       parameter_02 {}
       parameter_03 {}
    }
}
"""
    parse = CiscoConfParse(config.splitlines(), syntax="junos", comment="#")

    #################################
    # test the .geneology attribute
    #################################
    geneology = parse.find_objects(r"parameter_03")[0].geneology

    # test overall geneology list length
    assert len(geneology) == 3

    # For now, we are abusing IOSCfgLine() by using it in the **junos** parser
    # OLD VALUE ->  result_kindof_correct = IOSCfgLine
    assert isinstance(geneology[0], JunosCfgLine)
    assert isinstance(geneology[1], JunosCfgLine)
    assert isinstance(geneology[2], JunosCfgLine)

    # test individual geneology .text fields
    correct_result = 'base_hello'
    assert geneology[0].text.lstrip() == correct_result
    correct_result = 'that_thing'
    assert geneology[1].text.lstrip() == correct_result

    correct_result = 'parameter_03'
    assert geneology[2].text.lstrip() == correct_result


def testValues_IOSCfgLine_geneology_text_junos():
    config = """
base_hello {
    that_thing {
       parameter_01 {}
       parameter_02 {}
       parameter_03 {}
    }
}
"""
    parse = CiscoConfParse(config.splitlines(), syntax="junos", comment="#")

    #####################################
    # test the .geneology_text attribute
    #####################################
    geneology_text = parse.find_objects(r"parameter_03")[0].geneology_text

    # test overall geneology_text list length
    assert len(geneology_text) == 3

    # FIXME - one day build JunosCfgLine()...
    # For now, we are abusing IOSCfgLine() by using it in the **junos** parser
    correct_result = str
    assert isinstance(geneology_text[0], correct_result)
    assert isinstance(geneology_text[1], correct_result)
    assert isinstance(geneology_text[2], correct_result)

    # test individual geneology .text fields
    correct_result = 'base_hello'
    assert geneology_text[0].lstrip() == correct_result

    correct_result = 'that_thing'
    assert geneology_text[1].lstrip() == correct_result

    correct_result = 'parameter_03'
    assert geneology_text[2].lstrip() == correct_result


def testValues_IOSCfgLine_geneology_ios():
    config = """
base_hello
    that_thing
       parameter_01
       parameter_02
       parameter_03
"""
    parse = CiscoConfParse(config.splitlines(), syntax="ios")

    #################################
    # test the .geneology attribute
    #################################
    geneology = parse.find_objects(r"parameter_03")[0].geneology

    # test overall geneology list length
    assert len(geneology) == 3

    # FIXME - one day build JunosCfgLine()...
    # For now, we are abusing IOSCfgLine() by using it in the **junos** parser
    result_kindof_correct = IOSCfgLine
    assert isinstance(geneology[0], result_kindof_correct)
    assert isinstance(geneology[1], result_kindof_correct)
    assert isinstance(geneology[2], result_kindof_correct)

    # test individual geneology .text fields
    correct_result = 'base_hello'
    assert geneology[0].text.lstrip() == correct_result

    correct_result = 'that_thing'
    assert geneology[1].text.lstrip() == correct_result

    correct_result = 'parameter_03'
    assert geneology[2].text.lstrip() == correct_result


def testValues_IOSCfgLine_geneology_text_ios():
    config = """
base_hello
    that_thing
       parameter_01
       parameter_02
       parameter_03
"""
    parse = CiscoConfParse(config.splitlines(), syntax="ios")

    #####################################
    # test the .geneology_text attribute
    #####################################
    geneology_text = parse.find_objects(r"parameter_03")[0].geneology_text

    # test overall geneology_text list length
    assert len(geneology_text) == 3

    correct_result = str
    assert isinstance(geneology_text[0], correct_result)
    assert isinstance(geneology_text[1], correct_result)
    assert isinstance(geneology_text[2], correct_result)

    # test individual geneology .text fields
    correct_result = 'base_hello'
    assert geneology_text[0].lstrip() == correct_result

    correct_result = 'that_thing'
    assert geneology_text[1].lstrip() == correct_result

    correct_result = 'parameter_03'
    assert geneology_text[2].lstrip() == correct_result


def testValues_syntax_ios_nofactory_find_objects(parse_c01):
    lines = [
        ("interface Serial 1/0", 11),
        ("interface GigabitEthernet4/1", 15),
        ("interface GigabitEthernet4/2", 21),
        ("interface GigabitEthernet4/3", 27),
        ("interface GigabitEthernet4/4", 32),
        ("interface GigabitEthernet4/5", 35),
        ("interface GigabitEthernet4/6", 39),
        ("interface GigabitEthernet4/7", 43),
        ("interface GigabitEthernet4/8", 47),
    ]
    result_correct = list()
    for config_line, linenum in lines:
        # Mock up the correct object
        obj = IOSCfgLine(all_lines=lines, line=config_line)
        obj.linenum = linenum
        result_correct.append(obj)

    ## test whether find_objects returns correct IOSCfgLine objects
    uut = parse_c01.find_objects("^interface")
    assert uut == result_correct


def test_nxos_blank_line_01():
    """
    Test blank line in NXOS parser. See github issue #248
    """

    config = """feature fex

feature lldp"""

    for test_syntax in ["nxos",]:
        if test_syntax == "nxos":
            ignore_blank_lines = False
        else:
            ignore_blank_lines = True
        parse = CiscoConfParse(config.splitlines(),
                               syntax=test_syntax,
                               ignore_blank_lines=ignore_blank_lines)
        ####################################################################
        # Legacy bug in NXOS parser...
        ####################################################################
        assert len(parse.ioscfg) == 3


def test_nxos_blank_line_02():
    """
    Test blank line in NXOS parser. See github issue #248
    """

    config = """logging logfile messages 6
logging server 10.110.180.23
logging server 10.30.183.174
logging source-interface loopback0
logging timestamp milliseconds
logging monitor 6
logging level local6 6
no logging console

scheduler aaa-authentication username VCC_Network_Cisco password 7 redacted

scheduler job name auto_checkpoint
checkpoint

end-job

scheduler job name VCC_NW_Cisco_auto_checkpoint
checkpoint

end-job

scheduler schedule name 8hr_checkpoint
job name auto_checkpoint
time start 2013:03:12:21:14 repeat 0:8:0

scheduler schedule name 8hr_checkpoint_VCC_NW_Cisco
job name VCC_NW_Cisco_auto_checkpoint
time start 2017:06:01:17:42 repeat 0:8:0"""

    for test_syntax in ["nxos",]:

        if test_syntax == "nxos":
            ignore_blank_lines = False
        else:
            ignore_blank_lines = True
        _ = CiscoConfParse(config.splitlines(),
                           syntax=test_syntax,
                           ignore_blank_lines=ignore_blank_lines)


def test_nxos_blank_line_03():

    BASELINE = """interface Ethernet109/1/1
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge
  channel-group 1208

interface Ethernet109/1/2
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge
  channel-group 2208

interface Ethernet109/1/3
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge

interface Ethernet109/1/4
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge

""".splitlines()

    # parse the baseline config with the nxos parser... keep blank lines...
    parse = CiscoConfParse(BASELINE, syntax="nxos", ignore_blank_lines=False)

    # Demonstrate that nxos config blank lines exist at these baseline and
    # test_result indexes...
    for idx in [5, 11, 16, 21,]:

        correct_result = BASELINE[idx]
        test_result = parse.objs[idx].text
        assert correct_result == ""
        assert correct_result == test_result

    # Walk the configuration and validate the test results match expected results
    for idx in range(0, len(BASELINE) - 1):

        correct_result = BASELINE[idx]
        test_result = parse.objs[idx].text
        assert correct_result == test_result


def test_nxos_blank_line_04():
    """Test that blank lines are ignored with `ignore_blank_lines=True`"""

    BASELINE = """interface Ethernet109/1/1
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge
  channel-group 1208

interface Ethernet109/1/2
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge
  channel-group 2208

interface Ethernet109/1/3
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge

interface Ethernet109/1/4
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge

""".splitlines()

    # parse the baseline config with all parsers... **ignore** all blank
    #     lines...
    for syntax in ["ios", "nxos", "asa", "junos",]:
        parse = CiscoConfParse(
            BASELINE,
            syntax=syntax,
            ignore_blank_lines=True,
        )

        # Demonstrate that the syntax with ignored blank lines never returns
        # a blank line... note that we have to reduce the BASELINE config
        # length by four because of four blank lines in the BASELINE
        # configuration.
        for idx in range(0, len(BASELINE) - 4):

            # Ensure that NO line in the config has blank lines
            assert parse.objs[idx].text.strip() != ""


def test_nxos_blank_line_05():
    """Test that blank lines are kept with `ignore_blank_lines=False`"""

    BASELINE = """interface Ethernet109/1/1
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge
  channel-group 1208

interface Ethernet109/1/2
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge
  channel-group 2208

interface Ethernet109/1/3
  switchport mode trunk
  switchport trunk native vlan 201
  spanning-tree port type edge

interface Ethernet109/1/4
  switchport mode trunk
  switchport trunk native vlan 800
  spanning-tree port type edge

""".splitlines()

    # parse the baseline config with all parsers... **keep** all
    #     four blank lines...
    for syntax in ["ios", "nxos", "asa", "junos",]:
        parse = CiscoConfParse(
            BASELINE,
            syntax=syntax,
            ignore_blank_lines=False,
        )

        # Demonstrate that the syntax including blank lines counts
        #     four blank lines in the configuration above...
        blank_count = 0
        for idx in range(0, len(BASELINE) - 0):

            if parse.objs[idx].text.strip() == "":
                blank_count += 1

        assert blank_count == 4


def test_has_line_with_all_syntax():
    config = """
interface GigabitEthernet0/1
 switchport
 switchport mode access
"""

    for test_syntax in ["ios", "nxos", "asa", "junos"]:
        parse = CiscoConfParse(config.splitlines(), syntax=test_syntax)

        param_true = "access"
        ccp_test_value = parse.has_line_with(param_true)
        assert ccp_test_value is True

        objs_test_value = parse.ConfigObjs.has_line_with(param_true)
        assert objs_test_value is True

        param_false = "NONONONONONONONONONONONONONONONONONONO"
        ccp_test_value = parse.has_line_with(param_false)
        assert ccp_test_value is False

        objs_test_value = parse.ConfigObjs.has_line_with(param_false)
        assert objs_test_value is False


def testValues_find_objects_replace_01():
    """test whether find_objects we can correctly replace object values using native IOSCfgLine object methods"""
    config01 = [
        "!",
        "boot system flash slot0:c2600-adventerprisek9-mz.124-21a.bin",
        "boot system flash bootflash:c2600-adventerprisek9-mz.124-21a.bin",
        "!",
        "interface Ethernet0/0",
        " ip address 172.16.1.253 255.255.255.0",
        "!",
        "ip route 0.0.0.0 0.0.0.0 172.16.1.254",
        "!",
        "end",
    ]
    correct_result = [
        "!",
        "! old boot image flash slot0:c2600-adventerprisek9-mz.124-21a.bin",
        "! old boot image flash bootflash:c2600-adventerprisek9-mz.124-21a.bin",
        "!",
        "interface Ethernet0/0",
        " ip address 172.16.1.253 255.255.255.0",
        "!",
        "ip route 0.0.0.0 0.0.0.0 172.16.1.254",
        "!",
        "end",
    ]
    cfg = CiscoConfParse(config01)
    for obj in cfg.find_objects("boot system"):
        obj.replace("boot system", "! old boot image")
    test_result = cfg.ioscfg
    assert correct_result == test_result


def testValues_find_objects_delete_01():
    """Test whether IOSCfgLine.delete() recurses through children correctly"""
    config = [
        "!",
        "interface Serial1/0",
        " encapsulation ppp",
        " ip address 1.1.1.1 255.255.255.252",
        " no ip proxy-arp",
        "!",
        "interface Serial1/1",
        " encapsulation ppp",
        " ip address 1.1.1.5 255.255.255.252",
        "!",
    ]
    correct_result = ["!", "!", "!"]
    cfg = CiscoConfParse(config)
    for intf in cfg.find_objects(r"^interface"):
        # Delete all the interface objects
        intf.delete(recurse=True)  # recurse=True is the default
    test_result = cfg.ioscfg
    assert correct_result == test_result


def testValues_obj_insert_after_atomic_01(parse_c01):
    """We expect IOSCfgLine().insert_after() to correctly parse children"""
    ## See also -> testValues_insert_after_nonatomic_02()
    correct_result = [
        " shutdown",
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
        " power inline static max 7000",
    ]
    obj01 = parse_c01.find_objects("interface GigabitEthernet4/1")[0]
    obj01.insert_after(" shutdown")
    parse_c01.commit()

    obj02 = parse_c01.find_objects("interface GigabitEthernet4/1")[0]
    assert correct_result == [ii.text for ii in obj02.children]


def testValues_insert_after_atomic_factory_01(parse_c01_factory):
    """Ensure that comments which are added, assert is_comment"""
    # mockobj pretends to be the IOSCfgLine object
    with patch(__name__ + "." + "IOSCfgLine") as mockobj:
        correct_result01 = mockobj
        correct_result01.linenum = 16
        correct_result01.text = " ! TODO: some note to self"
        correct_result01.classname = "IOSCfgLine"
        correct_result01.is_comment = True

    linespec = "interface GigabitEthernet4/1"
    obj = parse_c01_factory.find_objects(linespec)[0]
    obj.insert_after(" ! TODO: some note to self")
    parse_c01_factory.commit()

    test_result01 = parse_c01_factory.find_objects("TODO")[0]
    assert correct_result01.linenum == test_result01.linenum
    assert correct_result01.text == test_result01.text
    assert correct_result01.classname == test_result01.classname
    assert correct_result01.is_comment == test_result01.is_comment

    correct_result02 = [
        " ! TODO: some note to self",
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
        " power inline static max 7000",
    ]
    test_result02 = [ii.text for ii in parse_c01_factory.find_objects(linespec)[0].children]
    assert correct_result02 == test_result02



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


def testValues_find_objects_factory_01(parse_c01_factory):
    """Test whether find_objects returns the correct objects"""

    # mockobj pretends to be the IOSIntfLine object
    with patch(__name__ + "." + "IOSIntfLine") as mockobj:
        vals = [
            ("interface GigabitEthernet4/1", 15),
            ("interface GigabitEthernet4/2", 21),
            ("interface GigabitEthernet4/3", 27),
            ("interface GigabitEthernet4/4", 32),
            ("interface GigabitEthernet4/5", 35),
            ("interface GigabitEthernet4/6", 39),
            ("interface GigabitEthernet4/7", 43),
            ("interface GigabitEthernet4/8", 47),
        ]
        ## Simulate correct IOSIntfLine objects...
        correct_result = list()

        # deepcopy a unique mock for every val with itertools.repeat()
        _ = [deepcopy(ii) for ii in repeat(mockobj, len(vals))]
        # correct_intf simulates an IOSCfgLine so we can test against it
        #########for idx, correct_intf in enumerate(mockobjs):
        for idx in range(0, len(vals)):
            correct_intf = BaseCfgLine(text=vals[idx][0])
            correct_intf.linenum = vals[idx][1]  # correct line numbers
            # append all to correct_result
            correct_result.append(correct_intf)

        test_intfs = parse_c01_factory.find_objects("^interface GigabitEther")
        assert len(test_intfs) == len(correct_result)

        for idx, test_intf in enumerate(test_intfs):
            correct_intf = correct_result[idx]
            # Check text
            assert correct_intf.text == test_intf.text
            # Check line numbers
            assert correct_intf.linenum == test_intf.linenum


def testValues_IOSIntfLine_find_objects_factory_01(parse_c01_factory):
    """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
    # mockobj pretends to be the IOSIntfLine object
    with patch(__name__ + "." + "IOSIntfLine") as mockobj:
        # the mock pretends to be an IOSCfgLine so we can test against it
        correct_result = mockobj
        correct_result.linenum = 11
        correct_result.text = "interface Serial 1/0"
        correct_result.classname = "IOSIntfLine"
        correct_result.ipv4_addr_object = IPv4Obj("1.1.1.1/30", strict=False)

        # this test finds the IOSIntfLine instance for 'Serial 1/0'
        test_result = parse_c01_factory.find_objects("^interface Serial 1/0")[0]

        assert correct_result.linenum == test_result.linenum
        assert correct_result.text == test_result.text
        assert correct_result.classname == test_result.classname
        assert correct_result.ipv4_addr_object == test_result.ipv4_addr_object


def testValues_IOSIntfLine_find_objects_factory_02(
    parse_c01_factory, c01_insert_serial_replace
):
    """test whether find_objects() returns correct IOSIntfLine objects and tests IOSIntfLine methods"""
    with patch(__name__ + "." + "IOSIntfLine") as mockobj:
        # the mock pretends to be an IOSCfgLine so we can test against it
        correct_result01 = mockobj
        correct_result01.linenum = 12
        correct_result01.text = "interface Serial 2/0"
        correct_result01.classname = "IOSIntfLine"
        correct_result01.ipv4_addr_object = IPv4Obj("1.1.1.1/30", strict=False)

        correct_result02 = c01_insert_serial_replace

        obj = parse_c01_factory.find_objects("interface Serial 1/0")[0]
        obj.insert_before("default interface Serial 1/0")

        # Replace text in the IOSIntfLine object
        parse_c01_factory.replace_lines(
            "interface Serial 1/0", "interface Serial 2/0", exactmatch=False
        )

        test_result01 = parse_c01_factory.find_objects("^interface Serial 2/0")[0]
        test_result02 = parse_c01_factory.ioscfg

        # Check attributes of the IOSIntfLine object
        assert correct_result01.linenum == test_result01.linenum
        assert correct_result01.text == test_result01.text
        assert correct_result01.classname == test_result01.classname
        assert correct_result01.ipv4_addr_object == test_result01.ipv4_addr_object

        # Ensure the text configs are exactly what we wanted
        assert correct_result02 == test_result02


def testValues_ConfigList_insert01(parse_c02):
    correct_result = [
        "hostname LabRouter",
        "policy-map QOS_1",
        " class GOLD",
        "  priority percent 10",
        " !",
        " class SILVER",
        "  bandwidth 30",
        "  random-detect",
        " !",
        " class BRONZE",
        "  random-detect",
        "!",
        "interface GigabitEthernet4/1",
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
        " power inline static max 7000",
        "!",
    ]
    iosconfiglist = parse_c02.ConfigObjs

    # insert at the beginning
    iosconfiglist.insert(0, "hostname LabRouter")
    test_result = list(map(attrgetter("text"), iosconfiglist))

    assert test_result == correct_result


def testValues_ConfigList_insert02(parse_c02):
    correct_result = [
        "policy-map QOS_1",
        " class GOLD",
        "  priority percent 10",
        " !",
        " class SILVER",
        "  bandwidth 30",
        "  random-detect",
        " !",
        " class BRONZE",
        "  random-detect",
        "!",
        "interface GigabitEthernet4/1",
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
        " power inline static max 7000",
        "hostname LabRouter",
        "!",
    ]
    configlist = parse_c02.ConfigObjs

    # insert at the end
    configlist.insert(-1, "hostname LabRouter")
    test_result = list(map(attrgetter("text"), configlist))

    assert test_result == correct_result


def test_BaseCfgLine_has_child_with(parse_c03):
    correct_result = [
        'interface GigabitEthernet4/1',
        'interface GigabitEthernet4/2',
        'interface GigabitEthernet4/3',
        'interface GigabitEthernet4/5',
        'interface GigabitEthernet4/6',
    ]
    test_output = list()
    for intf in parse_c03.find_objects(r"^interface\s+\w+?thernet"):
        if intf.has_child_with("switchport access vlan"):
            test_output.append(intf.text)

    assert test_output == correct_result


def testValues_IOSCfgLine_ioscfg01(parse_c02):
    correct_result = [
        "interface GigabitEthernet4/1",
        " switchport",
        " switchport access vlan 100",
        " switchport voice vlan 150",
        " power inline static max 7000",
    ]
    test_result = parse_c02.find_objects(
        r"^interface\sGigabitEthernet4/1", exactmatch=True
    )[0].ioscfg
    assert test_result == correct_result


def testValues_CiscoPassword():
    ep = "04480E051A33490E"
    test_result_01 = CiscoPassword(ep).decrypt()
    test_result_02 = CiscoPassword().decrypt(ep)

    correct_result = cisco_type7(0).decode(ep)
    assert correct_result == test_result_01
    assert correct_result == test_result_02
