
.. contents::


.. _Examples:

Examples
========

.. _Basic_Usage:

Basic Usage
-----------

`basic_usage.py`_ starts with a typical Cisco IOS configuration and prints out the following values:


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

.. _Lazy_IOS_Audit:

Lazy IOS Audit
--------------

`lazy_ios_audit.py`_ shows how you can audit global configuration settings with a small snippet of python.  When the script finishes, it prints out which configuration statements were missing from the input config.

Syntax:

```python
python lazy_ios_audit.py ~/ciscoconfparse/configs/sample_01.ios
```

.. _`basic_usage.py`: https://github.com/mpenning/ciscoconfparse/blob/master/examples/basic_usage.py
.. _`lazy_ios_audit.py`: https://github.com/mpenning/ciscoconfparse/blob/master/examples/lazy_ios_audit.py
