from getpass import getpass
from glob import glob
import sys
import os

from ciscoconfparse import CiscoConfParse

"""Demo of how to build a lazy Cisco IOS audit for common recommended config"""

# This is called a lazy audit, because this example skips things that are
# local to your environment (i.e. SNMP ACLs, SNMP Community, etc...)
#
# Also note that the RECOMMENDED config lines below are exact matches (no regex)
RECOMMENDED = """!
no service pad
service tcp-keepalives-in
service tcp-keepalives-out
service timestamps debug datetime msec localtime show-timezone year
service timestamps log datetime msec localtime show-timezone year
service password-encryption
!
! note: Cisco routers use somewhat different vstack syntax
no vstack
!
no ip domain-lookup
no ip source-route
ip options drop
!
logging snmp-authfail
!
ip tcp path-mtu-discovery
ip tcp synwait-time 5
ip tcp selective-ack
ip tcp timestamp
ip tcp queuemax 50
!
ip ssh version 2
ip ssh logging events
!
no ip http server
no ip http secure-server
!
! default critical memory reservation is 100KB, this reserves 4MB
memory reserve critical 4096
!
no logging console
! log buffer at debug level
logging buffered 500000
! log remote at debug level
logging trap debugging
!
line con 0
 logging synchronous
 transport preferred none
line vty 0 4
 logging synchronous
 transport preferred none
!""".splitlines()

try:
    CONFIG_PATH = glob(sys.argv[1])
except IndexError:
    raise ValueError("This script must be called with a config path-glob to be audited as the argument")
secret = getpass('Enable Secret: ')

for filename in CONFIG_PATH:
    print "--- {0} ---".format(filename)
    parse = CiscoConfParse(filename)

    # Print out simple diff conditions - i.e. no regexp matching...
    print os.linesep.join(parse.sync_diff(RECOMMENDED, '', remove_lines=False))

    # Default enable secret config...
    default_enab_sec = 'enable secret {0}'.format(secret)
    try:
        # Build an enable secret string...
        enab_sec_regex = r'^enable\s+secret\s+(\d+)\s+\S+'
        # Get the encryption level as an int...
        enab_sec_level = parse.find_objects(enab_sec_regex,
            )[0].re_match_typed(enab_sec_regex, group=1, default=-1, 
            result_type=int)
        if enab_sec_level==0:
            print default_enab_sec
    except IndexError:
        print default_enab_sec
