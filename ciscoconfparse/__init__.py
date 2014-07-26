import sys
if sys.version_info[0]==2:
    from ciscoconfparse import *
else:
    from .ciscoconfparse import *
