from timeit import timeit

vlan_text = "1-1000,1001-2000,2001-3000,3001-4000,4001-4094"
time_CiscoRange_all_vlans_int = timeit(
    'CiscoRange(text="%s", result_type=int)' % vlan_text,
    setup='from ciscoconfparse.ccp_util import CiscoRange',
    number=1000)
print(time_CiscoRange_all_vlans_int)
