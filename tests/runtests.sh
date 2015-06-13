#!/bin/sh

# Change into your virtualenv before running the script
py.test -s test_CiscoConfParse.py
sleep 0.05
py.test -s test_Ccp_Util.py
sleep 0.05
py.test -s test_Models_Cisco.py
sleep 0.05
py.test -s test_Models_Asa.py
sleep 0.05
py.test -s test_Models_Junos.py
