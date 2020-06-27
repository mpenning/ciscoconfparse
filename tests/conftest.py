import platform
import sys
import os

THIS_DIR = os.path.dirname(__file__)
sys.path.insert(0, "..")


import pytest
from ciscoconfparse.ciscoconfparse import CiscoConfParse


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

j01 = """## Last commit: 2015-06-28 13:00:59 CST by mpenning
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
access-group OUTSIDE_in in interface OUTSIDE
access-group INSIDE_in in interface INSIDE
!""".splitlines()

a02 = """: Saved
: Written by mpenning at 05:37:43.184 CDT Sun Jun 29 2015
!
ASA Version 9.0(3) 
!
command-alias exec slog show log | i Deny|denied
command-alias exec sacl sh access-list INSIDE_out | e hitcnt=0 |remark|elements
hostname fw
domain-name pennington.net
enable password 2KFQnbNIdI.2KYOU encrypted
xlate per-session deny tcp any4 any4
xlate per-session deny tcp any4 any6
xlate per-session deny tcp any6 any4
xlate per-session deny tcp any6 any6
xlate per-session deny udp any4 any4 eq domain
xlate per-session deny udp any4 any6 eq domain
xlate per-session deny udp any6 any4 eq domain
xlate per-session deny udp any6 any6 eq domain
passwd 2KFQnbNIdI.2KYOU encrypted
names
name 192.0.2.13 Machine01 description machine01
name 192.0.2.17 Machine02_Windows
name 10.0.0.6 Machine03
name 74.125.130.125 GTalk01 description Google talk server
name 74.125.134.125 GTalk02 description Google talk server
name 74.125.139.125 GTalk03 description Google Talk server
name 74.125.142.125 GTalk04 description Google Talk server
name 74.125.192.125 GTalk05 description Google Talk server
name 74.125.140.125 GTalk06 description Google Talk server
name 74.125.137.125 GTalk07
name 74.125.138.125 GTalk08
name 74.125.141.125 GTalk09
name 74.125.136.125 GTalk10
name 74.125.135.125 GTalk11
name 108.160.160.0 AS19679_Dropbox__108-160-160-0__20
name 199.47.216.0 AS19679_Dropbox__199.47.216.0__22
name 173.194.64.109 GmailSMTP01
name 173.194.64.108 GmailSMTP02
name 128.223.51.103 route-views.oregon-ix.net description Route-Views route server
ip local pool SSL_VPN_ADDRS 10.1.1.240-10.1.1.241 mask 255.255.255.0
!
interface Ethernet0/0
 description Internet ISP
 switchport access vlan 100
!
interface Ethernet0/1
 switchport access vlan 200
!
interface Ethernet0/2
 switchport access vlan 200
 shutdown
!
interface Ethernet0/3
 switchport access vlan 200
!
interface Ethernet0/4
 switchport access vlan 200
!
interface Ethernet0/5
 switchport access vlan 200
!
interface Ethernet0/6
 switchport access vlan 200
!
interface Ethernet0/7
 shutdown
!
interface Vlan1
 no nameif
 no security-level
 no ip address
!
interface Vlan100
 mac-address 0030.dead.beef
 nameif OUTSIDE
 security-level 0
 ip address dhcp setroute 
!
interface Vlan200
 nameif INSIDE
 security-level 100
 ip address 192.0.2.1 255.255.255.0 
!
banner motd 
banner motd Test banner for $(hostname)
banner motd 
banner motd *******************************
boot system disk0:/asa903-k8.bin
ftp mode passive
clock timezone CST -6
clock summer-time CDT recurring
dns domain-lookup INSIDE
dns server-group DefaultDNS
 name-server Machine01
 domain-name pennington.net
object network GTalk01
 host 74.125.130.125
 description Created during name migration
object network GTalk02
 host 74.125.134.125
 description Created during name migration
object network GTalk03
 host 74.125.139.125
 description Created during name migration
object network GTalk04
 host 74.125.142.125
 description Created during name migration
object network GTalk05
 host 74.125.192.125
 description Created during name migration
object network GTalk06
 host 74.125.140.125
 description Created during name migration
object network GTalk07
 host 74.125.137.125
 description Created during name migration
object network GTalk08
 host 74.125.138.125
 description Created during name migration
object network GTalk09
 host 74.125.141.125
 description Created during name migration
object network GTalk10
 host 74.125.136.125
 description Created during name migration
object network GTalk11
 host 74.125.135.125
 description Created during name migration
object network AS19679_Dropbox__108-160-160-0__20
 subnet 108.160.160.0 255.255.240.0
 description Created during name migration
object network AS19679_Dropbox__199.47.216.0__22
 subnet 199.47.216.0 255.255.252.0
 description Created during name migration
object network Machine01
 host 192.0.2.5
 description Created during name migration
object network obj_any
 subnet 0.0.0.0 0.0.0.0
object network Machine02_Windows
 host 192.0.2.17
 description Created during name migration
object-group network GoogleTalk
 network-object object GTalk01
 network-object object GTalk02
 network-object object GTalk03
 network-object object GTalk04
 network-object object GTalk05
 network-object object GTalk06
 network-object object GTalk07
 network-object object GTalk08
 network-object object GTalk09
 network-object object GTalk10
 network-object object GTalk11
object-group service GoogleTalkPorts
 service-object tcp destination eq 5222 
 service-object tcp destination eq https 
 service-object udp destination range 19302 19309 
object-group network Inside
 network-object 192.0.2.0 255.255.255.0
 network-object 192.0.22.0 255.255.255.0
 network-object 192.0.23.0 255.255.255.0
object-group network DROPBOX_AS19679
 network-object object AS19679_Dropbox__108-160-160-0__20
 network-object object AS19679_Dropbox__199.47.216.0__22
object-group network GOOGLE_addrs
 description dig -t TXT _netblocks.google.com 8.8.8.8
 network-object 216.239.32.0 255.255.224.0
 network-object 64.233.160.0 255.255.224.0
 network-object 66.249.80.0 255.255.240.0
 network-object 72.14.192.0 255.255.192.0
 network-object 209.85.128.0 255.255.128.0
 network-object 66.102.0.0 255.255.240.0
 network-object 74.125.0.0 255.255.0.0
 network-object 64.18.0.0 255.255.240.0
 network-object 207.126.144.0 255.255.240.0
 network-object 173.194.0.0 255.255.0.0
object-group network SSH_addrs
 network-object 192.168.1.0 255.255.255.0
object-group network ANY_addrs
 network-object 0.0.0.0 0.0.0.0
object-group network INSIDE_addrs
 network-object 192.0.2.0 255.255.255.0
 network-object 10.0.0.0 255.0.0.0
object-group service GOOGLE_svc
 description Google's push service for Android
 service-object tcp destination eq www 
 service-object tcp destination eq https 
 service-object tcp destination eq 5228 
 service-object tcp destination eq 5222 
 service-object tcp destination eq 587 
object-group service TELNET_svc
 service-object tcp destination eq telnet 
object-group service WHOIS_svc
 service-object tcp destination eq whois 
object-group service SSH_svc
 service-object tcp destination eq ssh 
object-group service WEB_svc
 description Standard web services - http, https, ftp
 service-object tcp destination eq ftp 
 service-object tcp destination eq www 
 service-object tcp destination eq https 
 service-object icmp 
object-group service DNS_svc
 service-object udp destination eq domain 
 service-object tcp destination eq domain 
object-group network MACHINE01_addrs
 network-object object Machine01
object-group service ANDROID_svc
 description Google's push service for Android
 service-object tcp destination eq 5228 
object-group service GMAILSMTP_svc
 service-object tcp destination eq 2525 
object-group service NTP_svc
 service-object udp destination eq ntp 
object-group service SKYPE_svc
 service-object udp destination eq 5555 
object-group service XBOX_svc
 service-object tcp destination eq domain 
 service-object udp destination eq domain 
 service-object udp destination eq 88 
 service-object tcp destination eq 3074 
 service-object udp destination eq 3074 
object-group network ANY
object-group service NaverLine_svc
 service-object udp destination eq 11000 
 service-object udp destination range 9401 9405 
object-group network NaverLine_addrs
 network-object 174.35.127.0 255.255.255.0
object-group network Facebook_addrs
 network-object 66.220.144.0 255.255.240.0
 network-object 69.63.176.0 255.255.248.0
 network-object 69.63.184.0 255.255.248.0
 network-object 69.171.224.0 255.255.240.0
 network-object 69.171.239.0 255.255.255.0
 network-object 69.171.240.0 255.255.240.0
 network-object 69.171.253.0 255.255.255.0
 network-object 69.171.255.0 255.255.255.0
 network-object 74.119.76.0 255.255.252.0
 network-object 103.4.96.0 255.255.252.0
 network-object 173.252.64.0 255.255.192.0
 network-object 204.15.20.0 255.255.252.0
 network-object 31.13.24.0 255.255.248.0
 network-object 31.13.64.0 255.255.192.0
 network-object 31.13.96.0 255.255.224.0
object-group service IP_SLA_PathTrace_svc
 service-object udp destination range 33400 33499 
object-group service FTP_svc
 service-object tcp destination eq ftp 
object-group service TeamViewerPorts
 service-object tcp destination eq 5938 
object-group service SSLVPN_svc
 service-object udp destination eq 443 
object-group service TEST_PORTS tcp
 port-object eq domain
 port-object eq smtp
access-list SPLIT_TUNNEL_NETS remark [[ destinations available via the VPN ]]
access-list SPLIT_TUNNEL_NETS standard permit 192.0.2.0 255.255.255.0 
access-list NO_SSLVPN_NAT remark [[ prevent inadvertent nat of sslvpn traffic ]]
access-list NO_SSLVPN_NAT extended permit ip 192.0.2.0 255.255.255.0 192.0.2.0 255.255.255.0 
access-list INSIDE_in extended deny object-group SKYPE_svc object-group INSIDE_addrs object-group ANY_addrs log disable 
access-list INSIDE_in extended permit object-group GOOGLE_svc object-group INSIDE_addrs object-group GOOGLE_addrs log 
access-list INSIDE_in extended permit object-group ANDROID_svc object-group INSIDE_addrs object-group GOOGLE_addrs log 
access-list INSIDE_in extended permit object-group IP_SLA_PathTrace_svc any host 4.2.2.2 log 
access-list INSIDE_in extended permit object-group DNS_svc object-group INSIDE_addrs object-group ANY_addrs log 
access-list INSIDE_in extended permit object-group NTP_svc object-group INSIDE_addrs object-group ANY_addrs log 
access-list INSIDE_in extended permit object-group TELNET_svc object-group INSIDE_addrs host 128.223.51.103 log 
access-list INSIDE_in extended permit object-group FTP_svc object-group INSIDE_addrs object-group ANY_addrs log 
access-list INSIDE_in extended permit object-group WEB_svc object-group INSIDE_addrs object-group ANY_addrs log 
access-list INSIDE_in extended permit object-group SSH_svc object-group INSIDE_addrs object-group SSH_addrs log 
access-list INSIDE_in extended permit object-group GMAILSMTP_svc object-group TSUNAMI_addrs object-group ANY_addrs log 
access-list INSIDE_in extended permit object-group WHOIS_svc object-group TSUNAMI_addrs object-group ANY_addrs log 
access-list INSIDE_in extended deny ip any4 any4 log 
access-list ANY extended permit ip object-group Inside any4 
access-list ANY extended permit ip any4 object-group Inside 
access-list VOIP extended permit object-group GoogleTalkPorts object-group Inside object-group GoogleTalk 
access-list VOIP extended permit object-group GoogleTalkPorts object-group GoogleTalk object-group Inside 
access-list MAINTENANCE extended deny ip any4 any4 log 
access-list OUTSIDE_in extended deny ip host 4.2.2.2 any4 log 
access-list OUTSIDE_in extended permit icmp any4 0.0.0.0 0.0.0.0 unreachable log interval 1 
access-list OUTSIDE_in extended permit icmp any4 0.0.0.0 0.0.0.0 time-exceeded log interval 1 
access-list OUTSIDE_in extended deny ip any4 any4 log 
pager lines 23
logging enable
logging timestamp
logging buffer-size 1048576
logging buffered informational
logging trap informational
logging asdm informational
logging facility 22
logging host INSIDE Machine01
logging class sys buffered informational 
no logging message 302021
no logging message 302020
mtu OUTSIDE 1500
mtu INSIDE 1500
ip verify reverse-path interface INSIDE
icmp unreachable rate-limit 1 burst-size 1
asdm image disk0:/asdm-645.bin
no asdm history enable
arp timeout 14400
no arp permit-nonconnected
!
object network obj_any
 nat (INSIDE,OUTSIDE) dynamic interface
access-group OUTSIDE_in in interface OUTSIDE
access-group INSIDE_in in interface INSIDE
route INSIDE 10.0.0.0 255.0.0.0 192.0.2.2 1
timeout xlate 3:00:00
timeout pat-xlate 0:00:30
timeout conn 1:00:00 half-closed 0:59:00 udp 0:02:00 icmp 0:00:02
timeout sunrpc 0:10:00 h323 0:05:00 h225 1:00:00 mgcp 0:05:00 mgcp-pat 0:05:00
timeout sip 0:30:00 sip_media 0:02:00 sip-invite 0:03:00 sip-disconnect 0:02:00
timeout sip-provisional-media 0:02:00 uauth 0:05:00 absolute
timeout tcp-proxy-reassembly 0:01:00
timeout floating-conn 0:00:00
dynamic-access-policy-record DfltAccessPolicy
user-identity default-domain LOCAL
aaa authentication ssh console LOCAL 
aaa authentication enable console LOCAL 
aaa authentication http console LOCAL 
aaa authorization command LOCAL 
aaa local authentication attempts max-fail 16
filter java 1-65535 192.0.2.0 255.255.255.0 0.0.0.0 0.0.0.0 
http server enable
http 192.0.2.0 255.255.255.0 INSIDE
snmp-server host INSIDE Machine01 poll community public
snmp-server location ServerRoom
snmp-server contact mike@pennington.net
snmp-server community public
snmp-server enable traps snmp authentication linkup linkdown coldstart
crypto ipsec security-association pmtu-aging infinite
crypto ca trustpoint LOCAL_CERT_fw
 enrollment self
 fqdn fw.pennington.net
 subject-name CN=fw.pennington.net
 crl configure
crypto ca trustpool policy
telnet timeout 5
ssh scopy enable
ssh 192.0.2.0 255.255.255.0 INSIDE
ssh 10.0.0.0 255.0.0.0 INSIDE
ssh timeout 60
ssh version 2
console timeout 5
no vpn-addr-assign aaa
no vpn-addr-assign dhcp

dhcpd dns 68.94.156.1 Machine01
dhcpd lease 604800
dhcpd domain pennington.net
dhcpd auto_config OUTSIDE
!
threat-detection basic-threat
threat-detection scanning-threat shun duration 30
threat-detection statistics host
threat-detection statistics port
threat-detection statistics protocol
threat-detection statistics access-list
no threat-detection statistics tcp-intercept
ntp server 17.151.16.20
ntp server 17.151.16.21
ntp server 17.151.16.22
ntp server 17.151.16.23
group-policy SSL_VPN_Policy01 internal
group-policy SSL_VPN_Policy01 attributes
 dns-server value 192.0.2.13
 vpn-idle-timeout none
 vpn-filter none
 vpn-tunnel-protocol ssl-client ssl-clientless
 split-tunnel-policy tunnelspecified
 split-tunnel-network-list value SPLIT_TUNNEL_NETS
 default-domain value pennington.net
 webvpn
  anyconnect keep-installer installed
  anyconnect ssl rekey time 30
  anyconnect ssl rekey method ssl
  anyconnect ask none default anyconnect
username mpenning password dXRTaA5wrZ3OL8gz encrypted privilege 15
tunnel-group DefaultWEBVPNGroup general-attributes
 address-pool SSL_VPN_ADDRS
 default-group-policy SSL_VPN_Policy01
!
!
policy-map type inspect dns preset_dns_map
 parameters
  message-length maximum client auto
  message-length maximum 512
policy-map global_policy
 class inspection_default
  inspect dns preset_dns_map 
  inspect h323 h225 
  inspect h323 ras 
  inspect rsh 
  inspect rtsp 
  inspect esmtp 
  inspect sqlnet 
  inspect skinny  
  inspect sunrpc 
  inspect xdmcp 
  inspect sip  
  inspect netbios 
  inspect tftp 
  inspect ip-options 
  inspect icmp 
  inspect http 
!
service-policy global_policy global
prompt hostname context 
no call-home reporting anonymous
call-home
 profile CiscoTAC-1
  no active
  destination address http https://tools.cisco.com/its/service/oddce/services/DDCEService
  destination address email callhome@cisco.com
  destination transport-method http
  subscribe-to-alert-group diagnostic
  subscribe-to-alert-group environment
  subscribe-to-alert-group inventory periodic monthly
  subscribe-to-alert-group configuration periodic monthly
  subscribe-to-alert-group telemetry periodic daily
Cryptochecksum:571d01b7b08342e35db838e9acec00f6
: end""".splitlines()

n01 = """

feature tacacs+
feature interface-vlan
feature vpc
feature fex
feature lacp
feature lldp
feature ospf
no feature telnet

ip domain-lookup
ip domain-name pennington.net
ip name-server 10.0.0.10

vrf context management
  ip route 0.0.0.0/0 10.0.0.1

vrf context vpc-peerkeepalive

tacacs-server key 0 DontTreadOnMe
ip tacacs source-interface Vlan10
tacacs-server host 10.0.0.32
tacacs-server host 10.0.0.33
aaa group server tacacs+ TACACS_GROUP
  server 10.0.0.32
  server 10.0.0.33
  use-vrf management
  source-interface mgmt0

aaa authentication login default group TACACS_GROUP
aaa authentication login console group TACACS_GROUP
aaa authorization commands default group TACACS_GROUP
aaa accounting default group TACACS_GROUP
aaa authentication login error-enable

logging event link-status default

vpc domain 999
  role priority 100
  system-priority 1
  auto-recovery
  peer-keepalive destination 1.1.1.2

fex 115
  desc FEX115
  pinning max-links 1

interface loopback0
  ip address 10.1.1.1/32

interface mgmt0
  ip address 10.0.0.5/24

interface port-channel1
  vpc peer-link
  switchport mode trunk
  spanning-tree port type network
  description [vPC PEER LINK]

interface port-channel21
  description Uplink to core
  switchport mode trunk
  switchport trunk native vlan 999
  switchport trunk allowed vlan 13,31-38,155
  mtu 9216
  vpc 21

interface port-channel115
  switchport mode fex-fabric
  fex associate 115

interface Ethernet1/1
  switchport mode trunk
  spanning-tree port type network
  channel-group 1 mode active

interface Ethernet1/2
  switchport mode trunk
  spanning-tree port type network
  channel-group 1 mode active

interface Ethernet1/3
  ip address 192.0.2.0/31

interface Ethernet1/4
  switchport mode trunk
  switchport trunk native vlan 999
  switchport trunk allowed vlan 13,31-38,15
  channel-group 21 mode active
  mtu 9216

interface Ethernet1/5
  switchport mode trunk
  switchport trunk native vlan 999
  switchport trunk allowed vlan 13,31-38,15
  channel-group 21 mode active
  mtu 9216

interface Ethernet1/6
 switchport mode fex-fabric
 fex associate 115
 channel-group 115

interface Ethernet1/7
  switchport mode access
  switchport access vlan 100
  mtu 9216

interface Ethernet1/8
  switchport mode access
  switchport access vlan 102
  mtu 9216

interface Ethernet1/9
  ip address 10.1.2.6/30
  mtu 9216

interface Ethernet1/10
  encapsulation dot1Q 200
  bandwidth 100000000
  delay 200
  beacon
  ip address 10.1.2.2/30
  mpls ip
  mtu 9216
""".splitlines()


@pytest.yield_fixture(scope="session")
def c01_default_gigethernets(request):
    yield config_c01_default_gige


@pytest.yield_fixture(scope="session")
def c01_insert_serial_replace(request):
    yield config_c01_insert_serial_replace


@pytest.yield_fixture(scope="function")
def parse_c01(request):
    """Preparsed c01"""
    parse_c01 = CiscoConfParse(c01, factory=False)

    yield parse_c01


@pytest.yield_fixture(scope="function")
def parse_c01_factory(request):
    """Preparsed c01 with factory option"""
    parse_c01_factory = CiscoConfParse(c01, factory=True)

    yield parse_c01_factory


@pytest.yield_fixture(scope="function")
def parse_c02(request):
    """Preparsed c02"""
    parse_c02 = CiscoConfParse(c02, factory=False)

    yield parse_c02


@pytest.yield_fixture(scope="function")
def parse_c02_factory(request):
    """Preparsed c02"""
    parse_c02 = CiscoConfParse(c02, factory=True)

    yield parse_c02


## parse_c03 yields configs/sample_01.ios
@pytest.yield_fixture(scope="function")
def parse_c03(request):
    """Preparsed c03"""
    parse_c03 = CiscoConfParse(c03, factory=False)

    yield parse_c03


## parse_c03_factory yields configs/sample_01.ios
@pytest.yield_fixture(scope="function")
def parse_c03_factory(request):
    """Preparsed c01 with factory option"""
    parse_c03_factory = CiscoConfParse(c03, factory=True)

    yield parse_c03_factory


## parse_j01 yields configs/sample_01.junos
@pytest.yield_fixture(scope="function")
def parse_j01(request):
    """Preparsed j01"""
    parse_j01 = CiscoConfParse(j01, syntax="junos", comment="#!", factory=False)

    yield parse_j01


## parse_j01_factory yields configs/sample_01.junos
@pytest.yield_fixture(scope="function")
def parse_j01_factory(request):
    """Preparsed j01 with factory option"""
    parse_j01_factory = CiscoConfParse(j01, syntax="junos", comment="#!", factory=True)

    yield parse_j01_factory


## parse_a01 yields the asa configuration
@pytest.yield_fixture(scope="function")
def parse_a01(request):
    """Preparsed a01"""
    parse_a01_factory = CiscoConfParse(a01, syntax="asa", factory=False)

    yield parse_a01_factory


## parse_a01_factory yields the asa configuration
@pytest.yield_fixture(scope="function")
def parse_a01_factory(request):
    """Preparsed a01 with factory option"""
    parse_a01_factory = CiscoConfParse(a01, syntax="asa", factory=True)

    yield parse_a01_factory


## config_a02 yields an asa configuration
@pytest.yield_fixture(scope="function")
def config_a02(request):
    """Unparsed a02"""
    yield a02


## parse_a02 yields an asa configuration
@pytest.yield_fixture(scope="function")
def parse_a02(request):
    """Preparsed a02"""
    parse_a02_factory = CiscoConfParse(a02, syntax="asa", factory=False)

    yield parse_a02_factory


## parse_a02_factory yields an asa configuration
@pytest.yield_fixture(scope="function")
def parse_a02_factory(request):
    """Preparsed a02 with factory option"""
    parse_a02_factory = CiscoConfParse(a02, syntax="asa", factory=True)

    yield parse_a02_factory


## config_n02 yields a nexus configuration
@pytest.yield_fixture(scope="function")
def config_n01(request):
    """Unparsed n01"""
    yield n01


## parse_n01 yields a nexus configuration
@pytest.yield_fixture(scope="function")
def parse_n01(request):
    """Preparsed n01"""
    parse_n01_factory = CiscoConfParse(n01, syntax="nxos", factory=False)

    yield parse_n01_factory


## parse_n01_factory yields a nexus configuration
@pytest.yield_fixture(scope="function")
def parse_n01_factory(request):
    """Preparsed n01 with factory option"""
    parse_n01_factory = CiscoConfParse(n01, syntax="nxos", factory=True)

    yield parse_n01_factory


@pytest.mark.skipif(sys.version_info[0] >= 3, reason="No Python3 MockSSH support")
@pytest.mark.skipif(
    "windows" in platform.system().lower(), reason="No Windows MockSSH support"
)
@pytest.yield_fixture(scope="session")
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
