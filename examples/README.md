
Table of Contents
=================

  * [Examples](#examples)
    * [Basic Usage](#basic_usage)
    * [Lazy IOS Audit](#lazy_ios_audit)

<a name="examples"/>

Examples
========

The following examples should get you started using [`ciscoconfparse`][ciscoconfparse]

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

[ciscoconfparse]: https://github.com/mpenning/ciscoconfparse
[basic_usage]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/basic_usage.py
[lazy_ios_audit]: https://github.com/mpenning/ciscoconfparse/blob/master/examples/lazy_ios_audit.py
