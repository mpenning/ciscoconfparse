import sys
import os

THIS_DIR = os.path.dirname(__file__)
# sys.path.insert(0, os.path.join(os.path.abspath(THIS_DIR), "../ciscoconfparse/"))
sys.path.insert(0, "..")


from ciscoconfparse.ciscoconfparse import CiscoConfParse

if sys.argv[1] == "1":
    parse = CiscoConfParse("../configs/sample_01.ios", syntax="ios", factory=False)
    for line in parse.objs:
        print(line)
elif sys.argv[1] == "2":
    parse = CiscoConfParse("../configs/sample_01.ios", syntax="ios", factory=True)
    for line in parse.objs:
        print(line)
elif sys.argv[1] == "3":
    parse = CiscoConfParse("../configs/sample_01.iosxr", syntax="ios", factory=True)
    for line in parse.objs:
        print(line)
