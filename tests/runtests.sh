#!/bin/bash

set -eu

# Change into your virtualenv before running the script

# --durations=5 triggers a report for the five slowest tests...
py.test -sxl --durations=5 --show-capture=all --tb=long test_CiscoConfParse.py
sleep 0.05
py.test -sxl --durations=5 --show-capture=all --tb=long test_Ccp_Util.py
sleep 0.05
py.test -sxl --durations=5 --show-capture=all --tb=long test_Models_Cisco.py
sleep 0.05
py.test -sxl --durations=5 --show-capture=all --tb=long test_Models_Asa.py
sleep 0.05
py.test -sxl --durations=5 --show-capture=all --tb=long test_Models_Junos.py
