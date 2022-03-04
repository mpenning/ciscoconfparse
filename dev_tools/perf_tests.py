from timeit import timeit
import sys
import re
import os

iterations = 1000

sys.path.insert(0, "../")

CONFIG_FILEPATH = None
# Set CONFIG_FILEPATH as a relative path
for base_dir, dirs, files in os.walk("../"):
    for filename in files:
        if filename=="sample_01.ios":
            CONFIG_FILEPATH = '{}/{}'.format(base_dir, filename)
            break

if CONFIG_FILEPATH is None:
    raise RuntimeError('RuntimeError - Could not find a config to parse')

# Regarding how to import a variable into timeit(),
#     (for example: 'from __main__ import CONFIG_FILEPATH'),
#     see https://stackoverflow.com/a/18882784/667301
list_cast = timeit(
    stmt="list(map(attrgetter('text'), parse.ConfigObjs))",
    setup="from __main__ import CONFIG_FILEPATH;from ciscoconfparse import CiscoConfParse;from operator import methodcaller, attrgetter;parse=CiscoConfParse(config=CONFIG_FILEPATH)",
    number=iterations,
)

list_comprehension = timeit(
    stmt="[ii.text for ii in parse.ConfigObjs]",
    setup="from __main__ import CONFIG_FILEPATH;from ciscoconfparse import CiscoConfParse;from operator import methodcaller, attrgetter;parse=CiscoConfParse(config=CONFIG_FILEPATH)",
    number=iterations,
)

list_comprehension_getattr = timeit(
    "[getattr(ii, 'text') for ii in parse.ConfigObjs]",
    setup="from __main__ import CONFIG_FILEPATH;from ciscoconfparse import CiscoConfParse;from operator import methodcaller, attrgetter;parse=CiscoConfParse(config=CONFIG_FILEPATH)",
    number=iterations,
)

print("CAST TO LIST", list_cast)
print("LIST COMPREHENSION", list_comprehension)
print("LIST COMPREHENSION GETATTR", list_comprehension_getattr)

vlan_text = "1-1000,1001-2000,2001-3000,3001-4000,4001-4094"
time_CiscoRange_all_vlans_int = timeit(
    'CiscoRange(text="%s", result_type=int)' % vlan_text,
    setup="from ciscoconfparse.ccp_util import CiscoRange",
    number=iterations,
)
print("SAMPLE", time_CiscoRange_all_vlans_int)

result_special_1 = timeit(
    'ss = rr.search("FoMike12325234234nananana");rr.captured',
    setup=r'import re;from ciscoconfparse import ccp_re;rr = ccp_re(r"^(\w+?)(?P<numbers1>\d+)(\S+?)$")',
    number=iterations,
)
print("SPECIAL REGEX1 ", round(result_special_1, 4))

result_special_2 = timeit(
    'ss = rr.search("FoMike12325234234nananana");rr.captured',
    setup=r'import re;from ciscoconfparse import ccp_re;rr = ccp_re(r"^(\w+?)(?P<numbers2>\d+)(\S+?)$")',
    number=iterations,
)
print("SPECIAL REGEX2 ", round(result_special_2, 4))

result_standard = timeit(
    #'rr = re.compile(r"(\w?)(?P<numbers>\d+)(\S+)");ss=rr.search("");ss.groups();ss.groupdict()',
    'ss = rr.search("FoMike12325234234nananana");ss.groups();ss.groupdict()',
    setup=r'import re;rr = re.compile(r"(\w?)(?P<numbers3>\d+)(\S+)")',
    number=iterations,
)
print("STANDARD REGEX", result_standard)
