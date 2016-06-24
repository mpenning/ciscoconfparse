@echo off
@cls
REM Change into your virtualenv before running the script
py.test -s test_CiscoConfParse.py
sleep 1
py.test -s test_Ccp_Util.py
sleep 1
py.test -s test_Models_Cisco.py
sleep 1
py.test -s test_Models_Asa.py
sleep 1
py.test -s test_Models_Junos.py
pause