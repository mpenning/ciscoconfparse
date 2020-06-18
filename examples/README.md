
Table of Contents
=================

  * [Examples](#examples)
    * [Basic Usage](#basic_usage)
    * [Lazy IOS Audit](#lazy_ios_audit)
    * [Parse Interface Addresses: JunOS](#parse_intf_addrs_junos)
    * [Parse Switchport Addrs: IOS](#parse_switchport_addrs_ios)

<a name="examples"/>

Examples
========

The following examples should get you started using [`ciscoconfparse`][ciscoconfparse].

* You need to be sure you're using Python 3 (Python 2 went end-of-life in January 2020).
* Please ensure you have the latest version of ciscoconfparse installed.

<a name="basic_usage"/>

Basic Usage
-----------

[`basic_usage.py`][basic_usage] starts with a typical Cisco IOS configuration and prints out the following values:


```
-----
Object: <IOSCfgLine # 1 'interface Serial 1/0'>
  Interface config line: interface Serial 1/0
  Interface mode: routed
  IP address: 1.1.1.1
  IP mask: 255.255.255.252
-----
Object: <IOSCfgLine # 5 'interface GigabitEthernet4/1'>
  Interface config line: interface GigabitEthernet4/1
  Interface mode: switchport
  IP address: N/A
  IP mask: N/A
-----
Object: <IOSCfgLine # 11 'interface GigabitEthernet4/2'>
  Interface config line: interface GigabitEthernet4/2
  Interface mode: switchport
  IP address: N/A
  IP mask: N/A
```

<a name="lazy_ios_audit"/>

Lazy IOS Audit
--------------

[`lazy_ios_audit.py`][lazy_ios_audit] shows how you can audit global IOS configuration settings with a small snippet of python.  When the script finishes, it prints out which configuration statements were missing from the input config.

Syntax:

```python
python lazy_ios_audit.py ~/ciscoconfparse/configs/sample_01.ios
```

<a name="parse_intf_addrs_junos"/>

Parse Interface Addresses: JunOS
--------------------------------

[`parse_intf_addrs_junos.py`][parse_intf_addrs_junos] illusatrates how you can take a typical JunOS configuration and extract information from it with [`find_object_branches()`](http://www.pennington.net/py/ciscoconfparse/api_CiscoConfParse.html?highlight=find_object_branches#ciscoconfparse.CiscoConfParse.find_object_branches).

When you're finished paring the configuration, you will see output like this:

```
xe-0/0/0.0 inet 1.1.1.6/31
xe-0/0/0.0 inet6 FD00:DEAD:CAFE:6000::4/127
xe-0/0/1.0 inet 2.2.2.10/31
xe-0/0/1.0 inet6 FD00:DEAD:CAFE:7903::2/64
xe-0/0/2.0 inet 3.3.3.14/31
xe-0/0/2.0 inet6 FD00:DEAD:CAFE:6000::26/127
```

<a name="parse_switchport_addrs_ios"/>

Parse Switchport Addrs: IOS
---------------------------

[`parse_switchport_addrs_ios.py`][parse_switchport_addrs_ios] illusatrates how you can take a typical Cisco IOS configuration and extract interface information with [`re_match_iter_typed()`][re_match_iter_typed].

When you're finished paring the configuration, you will see output like this:

```
GigabitEthernet 0/1     10.0.20.1 255.255.255.0
GigabitEthernet 0/2.12     10.0.12.1 255.255.255.0
GigabitEthernet 0/2.16     10.0.16.1 255.255.255.0
```

<a name="portmover"/>

Portmover
---------

[`portmover.py`][portmover] is an example of how you can move port configurations from an old switch config to a new switch config.

The script is called like this: `python portmover.py -o ../configs/sample_07.ios -n new.conf -m port_map.csv`

These are the arguments:
```
usage: portmover.py [-h] -o OLD -n NEW -m MAP

required:
  -o OLD, --old OLD  Old config filename
  -n NEW, --new NEW  New config filename
  -m MAP, --map MAP  CSV file which maps old to new ports
```

The script iterates over the old ports in the csv map file and writes a new configuration using new interface names listed in the csv map file.

[ciscoconfparse]: https://github.com/mpenning/ciscoconfparse
[re_match_iter_typed]: http://www.pennington.net/py/ciscoconfparse/api_IOSCfgLine.html?highlight=re_match_iter_typed#ciscoconfparse.models_cisco.IOSCfgLine.re_match_iter_typed
[basic_usage]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/basic_usage.py
[lazy_ios_audit]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/lazy_ios_audit.py
[parse_intf_addrs_junos]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/parse_intf_addrs_junos.py
[parse_switchport_addrs_ios]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/parse_switchport_addrs_ios.py
[portmover]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/portmover.py
