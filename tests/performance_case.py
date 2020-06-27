#!/usr/bin/env python

from cProfile import run
import sys
import os

THIS_DIR = os.path.dirname(__file__)
# sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))
sys.path.insert(0, "..")


# IGNORE PyFlake's barking here
from ciscoconfparse.ciscoconfparse import CiscoConfParse

if sys.argv[1] == "1":
    run("CiscoConfParse('../configs/sample_01.ios')", sort=2)
elif sys.argv[1] == "5":
    # python -m cProfile -s time test_speed.py
    run("CiscoConfParse('../configs/sample_05.ios')", sort=2)
elif sys.argv[1] == "6":
    # python -m cProfile -s time test_speed.py
    run(
        "CiscoConfParse('../configs/sample_06.ios', syntax='ios', factory=True)", sort=2
    )
else:
    raise ValueError
