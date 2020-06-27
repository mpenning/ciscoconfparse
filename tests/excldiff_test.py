from ciscoconfparse import CiscoConfParse

## this is not a valid test yet, because we don't detect parents of a line
## that is missing (i.e. 'no passive-interface Vlan500' below)

config = [
    "!",
    "router ospf 102",
    " ispf",
    " passive-interface default",
    " no passive-interface TenGigabitEthernet1/49",
    " auto-cost reference-bandwidth 100000",
    "!",
]
p = CiscoConfParse(config)

required_lines = [
    "router ospf 102",
    " ispf",
    " passive-interface default",
    " no passive-interface TenGigabitEthernet1/49",
    " no passive-interface Vlan500",
    " auto-cost reference-bandwidth 1000000",
]
# lines matching linespec are enforced
linespec = "router ospf 102|ispf|passive-interface.+?|auto-cost\sreference.+?"

unconfspec = linespec
diffs = p.req_cfgspec_excl_diff(linespec, unconfspec, required_lines)

print(diffs)
