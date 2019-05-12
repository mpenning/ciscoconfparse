from __future__  import absolute_import
""" protocol_values.py - Parse, Query, Build, and Modify IOS-style configurations
     Copyright (C) 2014-2015 David Michael Pennington

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

## Ref: http://www.cisco.com/c/en/us/td/docs/security/asa/asa84/configuration/guide/asa_84_cli_config/ref_ports.html
ASA_IP_PROTOCOLS = {
  'ah': 51,
  'eigrp': 88,
  'esp': 50,
  'gre': 47,
  'icmp': 1,
  'icmp6': 58,
  'igmp': 2,
  'igrp': 9,
  'ip': 0,
  'ipinip': 4,
  'ipsec': 50,
  'nos': 94,
  'ospf': 89,
  'pcp': 108,
  'pim': 103,
  'pptp': 47,
  'snp': 109,
  'tcp': 6,
  'udp': 17,
}

## Ref: https://supportforums.cisco.com/discussion/11242756/cisco-asa-acl-built-port-name-number-mapping
ASA_TCP_PORTS = {
    'aol': 5190,
    'bgp': 179,
    'chargen': 19,
    'cifs': 3020,
    'citrix-ica': 1494,
    'cmd': 514,
    'ctiqbe': 2748,
    'daytime': 13,
    'discard': 9,          
    'domain': 53,
    'echo': 7,
    'exec': 512,
    'finger': 79,
    'ftp': 20,
    'ftp-data': 21,
    'gopher': 70,
    'h323': 1720,
    'hostname': 101,
    'http': 80,
    'https': 443,
    'ident': 113,
    'imap4': 143,
    'irc': 194,
    'kerberos': 88,
    'klogin': 543,
    'kshell': 544,
    'ldap': 389,
    'ldaps': 636,
    'login': 513,
    'lotusnotes': 1352,
    'lpd': 515,
    'netbios-ssn': 139,
    'nfs': 2049,
    'nntp': 119,
    'pcanywhere-data': 5631,
    'pim-auto-rp': 496,
    'pop2': 109,
    'pop3': 110,
    'pptp': 1723,
    'rsh': 514,
    'rtsp': 554,
    'sip': 5060,
    'smtp': 25,
    'sqlnet': 1521,
    'ssh': 22,
    'sunrpc': 111,
    'tacacs': 49,
    'talk': 517,
    'telnet': 23,
    'uucp': 540,
    'whois': 43,
    'www': 80,
}

ASA_UDP_PORTS = {
    'biff': 512,
    'bootpc': 68,
    'bootps': 67,
    'cifs': 3020,
    'discard': 9,
    'dnsix': 90,
    'domain': 53,
    'echo': 7,
    'http': 80,
    'isakmp': 500,
    'kerberos': 88,
    'mobile-ip': 434,
    'nameserver': 42,
    'netbios-dgm': 138,
    'netbios-ns': 137,
    'nfs': 2049,
    'ntp': 123,
    'pcanywhere-status': 5632,
    'pim-auto-rp': 496,
    'radius': 1812,
    'radius-acct': 1813,
    'rip': 520,
    'rtsp': 5004,
    'secureid-udp': 5500,
    'sip': 5060,
    'snmp': 161,
    'snmptrap': 162,
    'sunrpc': 111,
    'syslog': 514,
    'tacacs': 49,
    'talk': 517,
    'tftp': 69,
    'time': 37,
    'who': 513,
    'www': 80,
    'xdmcp': 177,
}
