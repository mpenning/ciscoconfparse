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

## For historical reasons, I'm use c03 for configs/sample_01.ios (i.e. c01 was
##    already taken)
c03 = """!
service timestamps debug datetime msec localtime show-timezone
service timestamps log datetime msec localtime show-timezone
!
errdisable recovery cause bpduguard
errdisable recovery interval 400
!
aaa new-model
!
ip vrf TEST_100_001
 route-target 100:1
 rd 100:1
!
interface Serial 1/0
 description Uplink to SBC F923X2K425
 bandwidth 1500
 clock rate 1500
 delay 70
 encapsulation ppp
 ip address 1.1.1.1 255.255.255.252
!
interface Serial 1/1
 description Uplink to AT&T
 encapsulation hdlc
 ip address 1.1.1.9 255.255.255.254
 hold-queue 1000 in
 hold-queue 1000 out
 mpls mtu 1540
 ip mtu 1500
 mpls ip
!
interface GigabitEthernet4/1
 description
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
 speed 100
 duplex full
!
interface GigabitEthernet4/3
 mtu 9216
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
 switchport port-security
 switchport port-security maximum 3
 switchport port-security mac-address sticky
 switchport port-security mac-address 1000.2000.3000
 switchport port-security mac-address 1000.2000.3001
 switchport port-security mac-address 1000.2000.3002
 switchport port-security violation shutdown
!
interface GigabitEthernet4/6
 description Simulate a Catalyst6500 access port
 switchport
 switchport access vlan 110
 switchport mode access
 switchport nonegotiate
 switchport port-security
 switchport port-security maximum 2
 switchport port-security violation restrict
 switchport port-security aging type inactivity
 switchport port-security aging time 5
 spanning-tree portfast
 spanning-tree portfast bpduguard
 storm-control action shutdown
 storm-control broadcast level 0.40
 storm-control multicast level 0.35
!
interface GigabitEthernet4/7
 description Dot1Q trunk allowing vlans 2-4,7,10,11-19,21-4094
 switchport
 switchport trunk encapsulation dot1q
 switchport mode trunk
 switchport trunk native vlan 4094
 switchport trunk allowed vlan remove 1,5-10,20
 switchport trunk allowed vlan add 7,10
 switchport nonegotiate
!
interface GigabitEthernet4/8.120
 no switchport
 encapsulation dot1q 120
 ip vrf forwarding TEST_100_001
 ip address 1.1.2.254 255.255.255.0
!
interface ATM5/0/0
 no ip address
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 load-interval 30
 carrier-delay msec 100
 no atm ilmi-keepalive
 bundle-enable
 max-reserved-bandwidth 100
 hold-queue 500 in
!
interface ATM5/0/0.32 point-to-point
 ip address 1.1.1.5 255.255.255.252
 no ip redirects
 no ip unreachables
 no ip proxy-arp
 ip accounting access-violations
 pvc 0/32
  vbr-nrt 704 704
!
interface ATM5/0/1
 shutdown
!
router ospf 100 vrf TEST_100_001
 router-id 1.1.2.254
 network 1.1.2.0 0.0.0.255 area 0
!
policy-map QOS_1
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
!
alias exec showthang show ip route vrf THANG""".splitlines()

j01 = """system {
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
        telnet;
        web-management {
            http;
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
    Management {
        vlan-id 1;
        interface {
            ge-0/0/0.0;
            ge-0/0/1.0;
            ge-0/0/2.0;
            ge-0/0/3.0;                 
        }
    }
    VLAN_FOO {
        vlan-id 5;
    }
    vlan1 {
        vlan-id 1;
        l3-interface vlan.1;
    }
    vlan800 {
        vlan-id 800;
    }
}
ethernet-switching-options {
    storm-control {
        interface all;
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
                port-mode trunk;
                vlan {
                    members all;
                }
                native-vlan-id 1;
            }
        }
    }
    vlan {
        unit 0 {
            family inet {
                address 172.16.15.5/22;
            }
        }
    }
}
routing-options {
    static {
        route 0.0.0.0/0 next-hop 172.16.12.1;
        route 192.168.36.0/25 next-hop 172.16.12.1;
    }
}""".splitlines()

a01 = """hostname TEST-FW
!
name 1.1.2.20 loghost01
name 1.1.3.10 dmzsrv00
name 1.1.3.11 dmzsrv01
name 1.1.3.12 dmzsrv02
name 1.1.3.13 dmzsrv03
!
interface Ethernet0/0
 description Uplink to SBC F923X2K425
 nameif OUTSIDE
 security-level 0
 delay 70
 ip address 1.1.1.1 255.255.255.252
!
interface Ethernet0/1
 nameif INSIDE
 security-level 100
 ip address 1.1.2.1 255.255.255.0
!
interface Ethernet0/2
 switchport access vlan 100
!
interface VLAN100
 nameif DMZ
 security-level 50
 ip address 1.1.3.1 255.255.255.0
!
object-group network ANY_addrs
 network-object 0.0.0.0 0.0.0.0
!
object-group network INSIDE_addrs1
 network-object host 1.1.2.1
 network-object 1.1.2.2 255.255.255.255
 network-object 1.1.2.0 255.255.255.0
!
object-group network INSIDE_addrs1
 network-object host 1.1.2.1
 network-object 1.1.2.2 255.255.255.255
 network-object 1.1.2.0 255.255.255.0
!
object-group service DNS_svc
 service-object udp destination eq dns
!
object-group service NTP_svc
 service-object udp destination eq ntp
!
object-group service FTP_svc
 service-object tcp destination eq ftp
!
object-group service HTTP_svc
 service-object tcp destination eq http
!
object-group service HTTPS_svc
 service-object tcp destination eq https
!
access-list INSIDE_in extended permit object-group FTP_svc object-group INSIDE_addrs1 object-group ANY_addrs log
access-list INSIDE_in remark Overlap for test purposes
access-list INSIDE_in extended permit ip object-group INSIDE_addrs1 object-group ANY_addrs log
access-list INSIDE_in extended deny ip any any log
!
!
clock timezone CST -6
clock summer-time CDT recurring
!
logging enable
logging timestamp
logging buffer-size 1048576
logging buffered informational
logging trap informational
logging asdm informational
logging facility 22
logging host INSIDE loghost01
no logging message 302021
!
banner login ^CThis is a router, and you cannot have it.
Log off now while you still can type. I break the fingers
of all tresspassers.
^C
!
access-group OUTSIDE_in in interface OUTSIDE
access-group INSIDE_in in interface INSIDE
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

## parse_c03 yields configs/sample_01.ios
@pytest.yield_fixture(scope='function')
def parse_c03(request):
    """Preparsed c03"""
    parse_c03 = CiscoConfParse(c03, factory=False)
     
    yield parse_c03

## parse_c03_factory yields configs/sample_01.ios
@pytest.yield_fixture(scope='function')
def parse_c03_factory(request):
    """Preparsed c01 with factory option"""
    parse_c03_factory = CiscoConfParse(c03, factory=True)
     
    yield parse_c03_factory

## parse_j01 yields configs/sample_01.junos
@pytest.yield_fixture(scope='function')
def parse_j01(request):
    """Preparsed j01"""
    parse_j01 = CiscoConfParse(j01, factory=False)
     
    yield parse_j01

## parse_j01_factory yields configs/sample_01.junos
@pytest.yield_fixture(scope='function')
def parse_j01_factory(request):
    """Preparsed j01 with factory option"""
    parse_j01_factory = CiscoConfParse(j01, syntax='junos', factory=True)
     
    yield parse_j01_factory

## parse_a01 yields the asa configuration
@pytest.yield_fixture(scope='function')
def parse_a01(request):
    """Preparsed a01"""
    parse_a01_factory = CiscoConfParse(a01, syntax='asa', factory=False)
     
    yield parse_a01_factory

## parse_a01_factory yields the asa configuration
@pytest.yield_fixture(scope='function')
def parse_a01_factory(request):
    """Preparsed a01 with factory option"""
    parse_a01_factory = CiscoConfParse(a01, syntax='asa', factory=True)
     
    yield parse_a01_factory

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
