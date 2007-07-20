#!/usr/bin/env python

from ciscoconfparse import *

# require_cfgspec_all_diff( self, configspec )
#
# Require all lines in configspec to be in the configuration; however, do NOT
# remove any lines that are absent from configspec.  This command will produce
# a set of diffs (if required) to ensure all configspec entries are present.
#
# linespec is used when searching the configuration for lines to match against
#
#
p = CiscoConfParse("../configs/sample_01.ios")
diffs = p.req_cfgspec_all_diff( [ 
             "logging 172.16.1.5", 
             "logging 1.10.20.30", 
             "logging 192.168.1.1"
		 ] )

for line in diffs:
   print line
