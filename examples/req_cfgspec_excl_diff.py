#!/usr/bin/env python

from ciscoconfparse import CiscoConfParse

# req_cfgspec_excl_diff(self, linespec, unconfspec, configspec)
#
# Require all lines in configspec to be in the configuration; any lines matching
# linespec will be EXCLUDED from the configuration unless they are in 
# configspec.  **All** other config lines matching the linespec that are 
# *not* listed in the cfgspec will be removed with the uncfgspec regex.
# 'no ' is automatically prepended to lines
# matching unconfspec. This command returns diffs to ensure that the wrong 
# lines are unconfigured (via unconfspec).

#
# unconfspec is used to highlight which portion of linespec unconfigures the 
# command.  When diffs are returned, lines matching linespec
# show up prepended with 'no ', which will remove them.
#
# The following example ensures that the ONLY logging destinations are those
# in configspec.  non-conforming logging lines are removed, and missing logging 
# lines will be returned as diffs.

config = """service timestamps debug datetime localtime
service timestamps log datetime localtime
service password-encryption
!
hostname Foo
!
boot system flash sup-bootflash:c6sup22-jsv-mz.121-11b.EX1
ip classless
ip route 0.0.0.0 0.0.0.0 172.24.8.1
no ip http server
!
ip radius source-interface Loopback0
logging trap debugging
logging 172.28.26.15
snmp-server community public1 RO
snmp-server community private1 RW
snmp-server community public2 RO
snmp-server community private2 RW
snmp-server enable traps slb
snmp-server enable traps rf
snmp-server host 172.28.26.15 public1
snmp-server host 172.28.26.15 public2 
!
end"""

p = CiscoConfParse(config.split('\n'))
required_lines = [
    "logging 172.16.1.5", 
    "logging 1.10.20.30", 
    "logging 192.168.1.1",
    ]
linespec   = "logging\s+\d+\.\d+\.\d+\.\d+"  # limit to match ip addresses...
unconfspec = linespec
diffs = p.req_cfgspec_excl_diff(linespec, unconfspec, required_lines)

# Note that diffs includes a line with 'no logging 172.28.26.15', as well
# as configuring the requried logging servers...
for line in diffs:
   print(line)

