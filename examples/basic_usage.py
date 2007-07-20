#!/usr/bin/env python
from ciscoconfparse import *

parse = CiscoConfParse("../configs/sample_01.ios")

# Return a list of all ATM interfaces and subinterfaces
atm_intfs = parse.find_lines("^interface\sATM")

# Return a list of all interfaces with a certain QOS policy
qos_intfs = parse.find_parents_w_child( "^interf", "service-policy" )

# Return a list of all active interfaces (i.e. not shutdown)
active_intfs = parse.find_parents_wo_child( "^interf", "shutdown" )

