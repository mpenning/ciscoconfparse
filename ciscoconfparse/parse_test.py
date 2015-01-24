from ciscoconfparse import CiscoConfParse

parse = CiscoConfParse('../configs/sample_01.ios', syntax='ios', factory=True)
for line in parse.objs:
    print line
