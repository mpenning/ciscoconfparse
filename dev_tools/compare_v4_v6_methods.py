
import sys
import os
sys.path.insert(0, "../")   # add the path to the local git repo copy
                            # from this dev_tools/ directory
environ = os.environ['VIRTUAL_ENV']
print("ENV", environ)

print(str(os.environ['PYTHONPATH']))
from ciscoconfparse import IPv4Obj, IPv6Obj

v4_list = dir(IPv4Obj("127.0.0.1"))
v6_list = dir(IPv6Obj("::1"))

for ii_v4 in v4:
    if not (ii_v4 in v6_list):
        print("IPv6Obj() is missing method:", ii_v4)

for ii_v6 in v6:
    if not (ii_v6 in v4_list):
        print("IPv4Obj() is missing method:", ii_v6)
