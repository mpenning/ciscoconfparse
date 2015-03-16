import platform
import sys
import os
THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))
sys.path.insert(0, os.path.abspath(THIS_DIR))


import pytest
from ciscoconfparse import CiscoConfParse


c01 = """policy-map QOS_1
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
 switchport
 switchport access vlan 100
 switchport voice vlan 150
!
interface GigabitEthernet4/4
 shutdown
!
interface GigabitEthernet4/5
 switchport
 switchport access vlan 110
!
interface GigabitEthernet4/6
 switchport
 switchport access vlan 110
!
interface GigabitEthernet4/7
 switchport
 switchport access vlan 110
!
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

config_c01_default_gige = """policy-map QOS_1
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

config_c01_insert_serial_replace = """policy-map QOS_1
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
default interface Serial 2/0
interface Serial 2/0
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
 switchport
 switchport access vlan 100
 switchport voice vlan 150
!
interface GigabitEthernet4/4
 shutdown
!
interface GigabitEthernet4/5
 switchport
 switchport access vlan 110
!
interface GigabitEthernet4/6
 switchport
 switchport access vlan 110
!
interface GigabitEthernet4/7
 switchport
 switchport access vlan 110
!
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

# A smaller version of c01...
c02 = """policy-map QOS_1
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
interface GigabitEthernet4/1
 switchport
 switchport access vlan 100
 switchport voice vlan 150
 power inline static max 7000
!""".splitlines()

@pytest.yield_fixture(scope='session')
def c01_default_gigethernets(request):
    yield config_c01_default_gige

@pytest.yield_fixture(scope='session')
def c01_insert_serial_replace(request):
    yield config_c01_insert_serial_replace

@pytest.yield_fixture(scope='function')
def parse_c01(request):
    """Preparsed c01"""
    parse_c01 = CiscoConfParse(c01, factory=False)
     
    yield parse_c01

@pytest.yield_fixture(scope='function')
def parse_c01_factory(request):
    """Preparsed c01 with factory option"""
    parse_c01_factory = CiscoConfParse(c01, factory=True)
     
    yield parse_c01_factory

@pytest.yield_fixture(scope='function')
def parse_c02(request):
    """Preparsed c02"""
    parse_c02 = CiscoConfParse(c02, factory=False)
     
    yield parse_c02

@pytest.yield_fixture(scope='function')
def parse_c02_factory(request):
    """Preparsed c02"""
    parse_c02 = CiscoConfParse(c02, factory=True)
     
    yield parse_c02

@pytest.mark.skipif(sys.version_info[0]>=3,
    reason="No Python3 MockSSH support")
@pytest.mark.skipif('windows' in platform.system().lower(),
    reason="No Windows MockSSH support")
@pytest.yield_fixture(scope='session')
def cisco_sshd_mocked(request):
    """Mock Cisco IOS SSH"""
    from fixtures.devices.mock_cisco import start_cisco_mock, stop_cisco_mock

    try:
        ## Start the SSH Server
        start_cisco_mock()
        yield True
    except:
        yield False
        stop_cisco_mock()
    stop_cisco_mock()
