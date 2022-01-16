
"""Test performance of find_object_branches()"""

setup_fn_call = """
import sys
sys.path.insert(0, "../")
from ciscoconfparse import CiscoConfParse

global parse
parse = CiscoConfParse("../configs/sample_04.junos", syntax='junos', comment="#")

# We will call get_inteface_addrs...
def get_interface_addrs():
    branchspec = (r"^interfaces", r"\s+(\S+)", r"unit\s+(\d+)", r"family\s+(inet\d*)", r"address\s+(\S+)")
    for branch in parse.find_object_branches(branchspec, regex_groups=True):
        pass
"""

if __name__=="__main__":
    import timeit

    # Iterate over stmt this many times...
    number_of_stmt_calls= 1000

    # Build a list with run-times...
    runtime_list = timeit.Timer(stmt='get_interface_addrs()', setup=setup_fn_call).repeat(repeat=5, number=number_of_stmt_calls)

    # Raymond Hettinger said that even Guido prefers to benchmark against
    # the minimum time from a set of timeit runs...
    # Source
    #    -> https://stackoverflow.com/a/8220943/667301
    print(runtime_list)
    minimum_runtime = min(runtime_list)
    print("Best run of %s stmt calls: %s seconds" % (number_of_stmt_calls, min(runtime_list)))
    print("       Time per stmt call: %s seconds" % (float(minimum_runtime)/float(number_of_stmt_calls)))
