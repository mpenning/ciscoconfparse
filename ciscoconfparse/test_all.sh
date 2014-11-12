#!/bin/sh

# Change into your virtualenv before running the script
python testCiscoConfParse.py
sleep 1
python testCcp_Util.py
sleep 1
python testModels_Cisco.py
sleep 1
python testModels_Asa.py
