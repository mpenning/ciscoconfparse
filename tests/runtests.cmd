@echo off
@cls
py.test -s test_CiscoConfParse.py
ping -n 1 127.0.0.1 > NUL
py.test -s test_Ccp_Util.py
ping -n 1 127.0.0.1 > NUL
py.test -s test_Models_Cisco.py
ping -n 1 127.0.0.1 > NUL
py.test -s test_Models_Asa.py
ping -n 1 127.0.0.1 > NUL
py.test -s test_Models_Junos.py
pause