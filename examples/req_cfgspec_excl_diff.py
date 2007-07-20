#!/usr/bin/env python

from ciscoconfparse import *

# require_cfgspec_excl_diff( self, linespec, unconfspec, configspec )
#
# Require all lines in configspec to be in the configuration; any lines matching
# linespec will be EXCLUDED from the configuration unless they are in 
# configspec.  This command will generate appropriate diffs to ensure that
# the lines are unconfigured.
#
# This is the purpose of unconfspec; it is used to highlight which portion of
# linespec is used to unconfigure the command.
#
#
# The following example ensures that the ONLY logging destinations are those
# in configspec.  All non-conforming and absent lines will be returned as diffs.

p = CiscoConfParse("../configs/sample_04.ios")
violations = p.req_cfgspec_excl_diff( "logging\s+\d+\.\d+\.\d+\.\d+", 
             "logging\s+\d+\.\d+\.\d+\.\d+", [ 
             "logging 172.16.1.5", 
             "logging 1.10.20.30", 
             "logging 192.168.1.1"
		 ] )

for line in violations:
   print line
