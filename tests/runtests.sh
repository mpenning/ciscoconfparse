#!/bin/bash

set -eu

# Change into your virtualenv before running the script
py.test -s -x -l --cov=cisco --show-capture=all --tb=long test_CiscoConfParse.py
sleep 0.05
py.test -s -x -l --show-capture=all --tb=long test_Ccp_Util.py
sleep 0.05
py.test -s -x -l --show-capture=all --tb=long test_Models_Cisco.py
sleep 0.05
py.test -s -x -l --show-capture=all --tb=long test_Models_Asa.py
sleep 0.05
py.test -s -x -l --show-capture=all --tb=long test_Models_Junos.py
