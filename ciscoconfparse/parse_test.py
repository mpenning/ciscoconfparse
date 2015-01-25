from ciscoconfparse import CiscoConfParse
import sys

if sys.argv[1]=="1":
    parse = CiscoConfParse('../configs/sample_01.ios', syntax='ios', factory=False)
    for line in parse.objs:
        print line
elif sys.argv[1]=="2":
    parse = CiscoConfParse('../configs/sample_01.ios', syntax='ios', factory=True)
    for line in parse.objs:
        print line
elif sys.argv[1]=="3":
    parse = CiscoConfParse('../configs/sample_01.iosxr', syntax='ios', factory=True)
    for line in parse.objs:
        print line
