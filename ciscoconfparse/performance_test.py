#!/usr/bin/env python

from cProfile import run
import sys

# IGNORE PyFlake's barking here
from ciscoconfparse import CiscoConfParse

if sys.argv[1]=="1":
    run("CiscoConfParse('../configs/sample_01.ios')", sort=2)
elif sys.argv[1]=="5":
    # python -m cProfile -s time test_speed.py
    run("CiscoConfParse('../configs/sample_05.ios')", sort=2)
elif sys.argv[1]=="6":
    # python -m cProfile -s time test_speed.py
    run("CiscoConfParse('../configs/sample_06.ios', syntax='ios', factory=True)", sort=2)
else:
    raise ValueError
