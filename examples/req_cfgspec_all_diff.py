#!/usr/bin/env python

from ciscoconfparse import *

# req_cfgspec_all_diff(self, configspec)
#
# Require all lines in configspec to be in the configuration; however, do NOT
# remove any lines that are absent from configspec.  This command will produce
# a set of diffs (if required) to ensure all configspec entries are present.
#
# If you must remove non-conforming lines, use req_cfgspec_excl_diff()
config = """!
version 12.4
service nagle
no service pad
service tcp-keepalives-in
service tcp-keepalives-out
service timestamps debug datetime msec localtime show-timezone
service timestamps log datetime msec localtime show-timezone
service password-encryption
service internal
!
hostname Foo
!
boot-start-marker
boot-end-marker
!
logging facility local6
logging source-interface Loopback0
logging 172.16.1.5
logging 172.16.1.7
!
end"""
p = CiscoConfParse(config.split('\n'))
required_lines = [
    "logging 172.16.1.5",
    "logging 1.10.20.30",
    "logging 192.168.1.1",
    ]
diffs = p.req_cfgspec_all_diff(required_lines)

# Note that diffs does *not* include 'logging 172.16.1.5', because it is
# already configured...
for line in diffs:
    print(line)

