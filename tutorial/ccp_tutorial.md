# CiscoConfParse Tutorial

-   Search your Cisco configurations with [Python]
-   Code repo on [github]
-   [Documentation]
-   Author: Mike Pennington &lt;<mike@pennington.net>&gt;
-   Date: 2019-02-25
-   This presentation created with [landslide]

---

# Installation

-   Assume you're running linux and already have `pip` installed
-   The next command will download and install the latest version from
    [pypi]
-   Python2.7 - `pip install -U ciscoconfparse`
-   Python3.x - `pip3 install -U ciscoconfparse`

---

# Example Configuration

The following examples will use this configuration:

    ! filename:exampleswitch.conf
    !
    hostname ExampleSwitch
    !
    interface GigabitEthernet 1/1
     switchport mode trunk
     shutdown
    !
    interface GigabitEthernet 1/2
     switchport mode access
     switchport access vlan 20
     switchport nonegotiate
     no cdp enable
    !
    interface GigabitEthernet 1/3
     no switchport
     ip address 192.0.2.1 255.255.255.0

---

# Example: Find interfaces

Use `find_objects()` to give us a list of interface objects:

    !python
    from ciscoconfparse import CiscoConfParse

    # Parse the config into objects
    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    # Iterate over all the interface objects
    for intf_obj in parse.find_objects('^interface'):
        print("ciscoconfparse object: " + intf_obj)

Output:

    ciscoconfparse object: <IOSCfgLine # 4 'interface GigabitEthernet 1/1'>
    ciscoconfparse object: <IOSCfgLine # 8 'interface GigabitEthernet 1/2'>
    ciscoconfparse object: <IOSCfgLine # 14 'interface GigabitEthernet 1/3'>

---

# Example: Use object properties

Use `intf_obj.children` to iterate over an object's children:

    !python
    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', sytax='ios')

    # Choose the first interface (parent) object
    for intf_obj in parse.find_objects('^interface')[0:1]:
        print("Parent obj: " + str(intf_obj))

        # Iterate over all the child objects of that parent object
        for c_obj in intf_obj.children:
            print("Child obj :    " + str(c_obj))


Output:

    Parent obj: <IOSCfgLine # 4 'interface GigabitEthernet 1/1'>
    Child obj :    <IOSCfgLine # 5 ' switchport mode trunk' (parent is # 4)>
    Child obj :    <IOSCfgLine # 6 ' shutdown' (parent is # 4)>

---

# Example: Use object properties

Use `intf_obj.text` to get the object's configuration text

    !python
    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    # Choose the first interface (parent) object
    for intf_obj in parse.find_objects('^interface')[0:1]:
        print(intf_obj.text)

Output:

    interface GigabitEthernet 1/1

---

# Example: Find shutdown interfaces

Use `find_objects_w_child()` to give us a list of shutdown interfaces:

    !python
    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    for intf_obj in parse.find_objects_w_child('^interface', '^\s+shutdown'):
        print("Shutdown: " + intf_obj.text)

Output:

    Shutdown: interface GigabitEthernet1/1

---

# Example: Extract an interface address

Use `re_match_iter_typed()` to extract values with a regex match group
----------------------------------------------------------------------

    !python
    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    intf_obj = parse.find_objects('interface\s+GigabitEthernet1\/3$')

    # Search children of GigabitEthernet1/3 for a regex match and return
    # the value matched in regex match group 1.  If there is no match, return a
    # default value: ''
    intf_ip_addr = intf_obj.re_match_iter_typed(
        r'ip\saddress\s(\d+\.\d+\.\d+\.\d+)\s', result_type=str,
        group=1, default='')
    print("ip addr: " + intf_ip_addr)

Output:

    ip addr: 192.0.2.1

---

# Using `factory=True`

-   Parsing with `CiscoConfParse('exampleswitch.conf', syntax='ios', factory=True)` gives you more information
-   See next slide for an example

---

# Example: `factory=True`

parsing with `factory=True` automatically extracts interface values
-------------------------------------------------------------------

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('exampleswitch', syntax='ios', factory=True)
    >>> intf = parse.find_objects('interface\sGigabitEthernet0/3$')[0]
    >>> intf
    <IOSIntfLine # 14 'GigabitEthernet1/3' info: '192.0.2.1/24'>
    >>> intf.name
    'GigabitEthernet1/3'
    >>> intf.ipv4_addr
    '192.0.2.1'
    >>> intf.ipv4_netmask
    '255.255.255.0
    >>>

---

# `factory=True`: Important caveats

-   Parsing with `factory=True` is *BETA* functionality
-   Read the source code for documentation
-   Only Cisco IOS, Cisco NXOS, and Cisco ASA have custom parsers
-   Functionality is limited and I'm slowly adding more
-   I might change the APIs whenever I want to
-   If you care about things changing, then don't use `factory=True`

---

# Modify configs

    !python
    [mpenning@localhost]$ python
    Python 2.7.3 (default, Mar 14 2014, 11:57:14)
    [GCC 4.7.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>>
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/the/config', syntax='ios')
    >>>
    >>> # Standardize switchport configs with 0.5% broadcast storm control
    >>> parse.replace_children(r'^interface\s\S+?thernet',
    ...     r'broadcast\slevel\s\S+', 'broadcast level 0.5')
    ...
    [' storm-control broadcast level 0.5']
    >>>
    >>> # Now save the new version...
    >>> parse.save_as('/path/to/the/newconfig')

---


# Diff configs

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> BASELINE = """!
    ... interface GigabitEthernet0/1
    ...  ip address 10.0.0.1 255.255.255.0
    ... !""".splitlines()
    >>> REQUIRED_CONFIG = """!
    ... interface GigabitEthernet0/1
    ...  ip address 172.16.1.1 255.255.255.0
    ...  no ip proxy-arp
    ... !""".splitlines()
    >>> parse = CiscoConfParse(BASELINE)
    >>>
    >>> # Build diffs to convert the BASELINE to the REQUIRED config
    >>> print '\n'.join(parse.sync_diff(REQUIRED_CONFIG, ''))
    interface GigabitEthernet0/1
     no ip address 10.0.0.1 255.255.255.0
    interface GigabitEthernet0/1
     ip address 172.16.1.1 255.255.255.0
     no ip proxy-arp
    >>>

---

# Notes about diffs

-   The diffs use python's standard [difflib]
-   As you may have noticed, the diffs are kindof dumb... We didn't need to
    delete the ip address before adding another one.  We did't need to
    configure `interface GigabitEthernet0/1` twice.

---

# Cisco Ranges

`CiscoRange()` can help you iterate over ranges of values

    !python
    >>> from ciscoconfparse.ccp_util import CiscoRange
    >>> intfs = CiscoRange('Gi1/0/1-5')
    >>> for ii in intfs:
    ...     print ii
    ...
    Gi1/0/1
    Gi1/0/2
    Gi1/0/3
    Gi1/0/4
    Gi1/0/5
    >>> 'Gi1/0/2' in intfs
    True
    >>> 'Gi1/0/8' in intfs
    False
    >>>

---

# DNS Lookups

-   Most people need DNS for their router and switch addresses
-   Thus, it's helpful to have DNS functionality in CiscoConfParse
-   DNS lookup support: Use `dns_query()`

---

# DNS Query Example

    !python
    >>> from ciscoconfparse.ccp_util import dns_query
    >>> dns_query('www.pennington.net', 'A', '4.2.2.2')
    set([<DNSResponse 'A' result_str='65.19.187.2'>])
    >>> answer = dns_query('www.pennington.net', 'A', '4.2.2.2')
    >>> str(answer.pop())
    '65.19.187.2'
    >>>

---

# Parsing Junos

-   Is it possible?  Yes (after [Github issue #17])
-   Be aware that this will convert your Junos configuration to a Cisco-IOS style
-   See next slide for an example

---

# Parsing Junos (example)

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('configs/sample_01.junos', syntax='junos',
    ...     comment='#!')
    >>> print '\n'.join(parse.ioscfg[0:5])
    !# Last commit: 2015-06-28 13:00:59 CST by mpenning
    system
        host-name TEST01_EX
        domain-name pennington.net
        domain-search [ pennington.net lab.pennington.net ]
    >>>



  [Python]: http://python.org/
  [github]: http://github.com/mpenning/ciscoconfparse/
  [Documentation]: http://www.pennington.net/py/ciscoconfparse/
  [pypi]: http://pypi.python.org/pypi/ciscoconfparse/
  [landslide]: https://github.com/adamzap/landslide
  [difflib]: https://docs.python.org/2/library/difflib.html
  [Github issue #17]: https://github.com/mpenning/ciscoconfparse/issues/17
  [IOSCfgLine]: http://www.pennington.net/py/ciscoconfparse/api_IOSCfgLine.html
  [run into parsing problems]: https://github.com/mpenning/ciscoconfparse/issues/138
