#!/bin/sh

# Change into your virtualenv before running the script
python test_CiscoConfParse.py
sleep 1
python test_Ccp_Util.py
sleep 1
python test_Models_Cisco.py
sleep 1
python test_Models_Asa.py
