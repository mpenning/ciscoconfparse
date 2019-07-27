# CiscoConfParse Tutorial

-   Search your Cisco configurations with [Python]
-   Code repo on [github]
-   [Documentation]
-   Author: Mike Pennington &lt;<mike@pennington.net>&gt;
-   Date: 2019-02-25
-   This presentation created with [landslide]

---

# Why CiscoConfParse?

-   Do you think python is useful?
-   Do you manage a lot of routers, switches or firewalls?
-   If you answered yes to both questions, use CiscoConfParse. It helps
    python understand Cisco (and other vendor) text configs

---

# Installation

-   Assume you're running linux and already have `pip` installed
-   The next command will download and install the latest version from
    [pypi]
-   Python2.7 - `pip install -U ciscoconfparse`
-   Python3.x - `pip3 install -U ciscoconfparse`

---

# Config Parsing Notes

- Configurations can be parsed from a file
- Configurations can also be parsed from a list of strings
- Sometimes you should declare the syntax of config being parsed
- After parsing, the parse variable contains a list of [IOSCfgLine] objects

---

# Declare the config syntax

- When parsing, you can declare the syntax as: ios, nxos, asa, or junos
- Default syntax is ios
- The syntax changes how banners are parsed
- For ASA configs, if you don't declare the syntax, you may [run into parsing problems]

An ASA Config example:

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/configfile', syntax='asa')

---

# `IOSCfgLine()` objects

- [IOSCfgLine] objects know the config's line number
- [IOSCfgLine] objects know where the parents and children of that line are
- [IOSCfgLine] objects have special methods to retrieve information about the line and its children
- [IOSCfgLine] objects *don't automatically know details such as what IP address is on an interface, or whether proxy-arp is configured on it*

---

# `IOSCfgLine()` Example

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/configfile')
    >>> intf = parse.find_objects(r'interface GigabitEthernet0/1$')[0]
    >>> intf
    <IOSCfgLine # 0 'interface GigabitEthernet0/1'>
    >>> # Use the text property on a `IOSCfgLine()` to get the config text
    >>> intf.text
    'interface GigabitEthernet0/1'
    >>>

---

# Examples

Parsing configurations
----------------------

    !python
    [mpenning@localhost]$ python
    Python 2.7.3 (default, Mar 14 2014, 11:57:14) 
    [GCC 4.7.2] on linux2
    Type "help", "copyright", "credits" or "license" for more information.
    >>>
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/the/config', syntax='ios')
    >>>


---

# Examples

Use `find_objects_w_child()` to identify ports that are shutdown
----------------------------------------------------------------

    !python
    >>> # Find all interfaces IOSCfgLine() objects that are shutdown
    >>> shutdown_objs = parse.find_objects_w_child(r'^interface', r'shutdown')
    >>>

---

# Examples

Use `find_objects_wo_child()` to identify ports that are not shutdown
---------------------------------------------------------------------

    !python
    >>> # Find all interfaces IOSCfgLine() objects that are not shutdown
    >>> unshut_objs = parse.find_objects_wo_child(r'^interface', r'shutdown')
    >>>


---

# Examples

Use `re_match_iter_typed()` to extract an interface address
-----------------------------------------------------------

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/configfile')
    >>> intfobj = parse.find_objects(r'interface\sGigabitEthernet0/1$')[0]
    >>> 
    >>> ## re_match_iter_typed() will extract results from the re group, below
    >>> addr = intfobj.re_match_iter_typed(r'ip\saddress\s(\d+\.\d+\.\d+\.\d+)',
    ...     group=1, recurse=True, default='__unknown__', result_type=str,
    ...     untyped_default=True)
    >>> addr
    '172.16.4.1'

---

# How does `re_match_iter_typed()` work?

-   Call `re_match_iter_typed()` from a parent object
-   `re_match_iter_typed()` loops over all the children of the parent object
    and tries to match the given regular expression against each child's text.
-   If it finds a match, the value inside the regexp parenthesis is returned.
    In this case, we wanted the value inside the first set of parenthesis.
-   `re_match_iter_typed()` then casts the result as the type supplied in the
    `result_type` argument.

---

# `IOSCfgLine()` with `factory=True`

-   Parsing with `CiscoConfParse('/path/to/configfile', factory=True)` gives you more information
-   See next slide for an example

---

# Example: `factory=True`

parsing with `factory=True` automatically parses interface values
-----------------------------------------------------------------

    !python
    >>> from ciscoconfparse import CiscoConfParse
    >>> parse = CiscoConfParse('/path/to/configfile', factory=True)
    >>> intf = parse.find_objects('interface GigabitEthernet0/1$')[0]
    >>> intf
    <IOSIntfLine # 0 'GigabitEthernet0/1' info: '10.0.0.1/24'>
    >>> intf.name
    'GigabitEthernet0/1'
    >>> intf.ipv4_addr
    '10.0.0.1'
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
