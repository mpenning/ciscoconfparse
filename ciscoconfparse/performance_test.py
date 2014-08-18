#!/usr/bin/env python

from cProfile import run
from ciscoconfparse import CiscoConfParse

# python -m cProfile -s time test_speed.py
run("CiscoConfParse('../configs/sample_05.ios')", sort=1)
