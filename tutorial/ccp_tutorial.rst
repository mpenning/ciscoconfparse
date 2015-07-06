
CiscoConfParse Tutorial
=======================

* Search your Cisco configurations with `Python <http://python.org/>`_
* Code repo on `github <http://github.com/mpenning/ciscoconfparse/>`_
* `Documentation <http://www.pennington.net/py/ciscoconfparse/>`_
* Author: Mike Pennington <mike@pennington.net>
* Date: 2015-07-04

Why CiscoConfParse?
===================

* Do you think python is useful?
* Do you manage a lot of routers, switches or firewalls?
* If you answered yes to both questions, use CiscoConfParse.  It helps python understand Cisco (and other vendor) text configs

Installation
============

* Assume you're running linux and already have ``pip`` installed
* The next command will download and install the latest version from `pypi <http://pypi.python.org/pypi/ciscoconfparse/>`_
* ``pip install --ugprade ciscoconfparse``

Examples
=========

Search configs
--------------

.. class:: prettyprint lang-python

::

   [mpenning@localhost]$ python
   Python 2.7.3 (default, Mar 14 2014, 11:57:14) 
   [GCC 4.7.2] on linux2
   Type "help", "copyright", "credits" or "license" for more information.
   >>>
   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/path/to/the/config', syntax='ios')
   >>>
   >>> # Find all interfaces with an access-list...
   >>> parse.find_parents_w_child(r'interface', r'access-group')
   ['interface FastEthernet0/0', 'interface Dialer1']
   >>>

Modify configs
--------------

.. class:: prettyprint lang-python

::

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

Diff configs
------------

.. class:: prettyprint lang-python

::

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


Notes about diffs
=================

* The diffs use python's standard `difflib <https://docs.python.org/2/library/difflib.html>`_
* The diffs are kindof dumb...

  - We didn't need to delete the ip address before adding another one
  - We did't need to configure ``interface GigabitEthernet0/1`` twice

* CiscoConfParse's diffs assume 'no ...' removes lines (i.e. Cisco-style)
* Proof-reading is encouraged... don't assume CiscoConfParse does what you want

Parsing Junos
=============

* Is it possible?  Yes (after `Github issue #17 <https://github.com/mpenning/ciscoconfparse/issues/17>`_)
* Be aware that this will convert your Junos configuration to a Cisco-IOS style

.. class:: prettyprint lang-python

::

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('configs/sample_01.junos', syntax='junos', comment='#!')
   >>> print '\n'.join(parse.ioscfg[0:5])
   !# Last commit: 2015-06-28 13:00:59 CST by mpenning
   system 
       host-name TEST01_EX
       domain-name pennington.net
       domain-search [ pennington.net lab.pennington.net ]
   >>>

Other Features
==============

DNS Lookups
-----------

* Most people need DNS for their router and switch addresses
* Thus, it's helpful to have DNS functionality in CiscoConfParse
* DNS lookup support:

  - Use ciscoconfparse.ccp_util.dns_lookup() for IPv4
  - Use ciscoconfparse.ccp_util.dns6_lookup() for IPv6

Lookup DNS A-Record
-------------------

.. class:: prettyprint lang-python

::

   >>> from ciscoconfparse.ccp_util import dns_lookup
   >>>
   >>> # Return a dictionary with all info...
   >>> dns_lookup('extfw')
   {'addrs': ['10.10.255.1'], 'name': 'extfw', 'error': ''}
   >>> dns_lookup('extfw')['addrs']
   ['10.10.255.1']
   >>>
   >>> # Get the first address...
   >>> dns_lookup('extfw')['addrs'][0]
   '10.10.255.1'
   >>> 


Lookup DNS PTR-Record
---------------------

.. class:: prettyprint lang-python

::

   >>> from ciscoconfparse.ccp_util import reverse_dns_lookup
   >>>
   >>> # Return a dictionary with all info...
   >>> reverse_dns_lookup('10.10.255.1')
   {'addr': '10.10.255.1', 'lookup': '1.255.10.10.in-addr.arpa', 
   'name': 'extfw.pennington.net.', 'error': ''}
   >>> 
   >>> reverse_dns_lookup('10.10.255.1')['name']
   'extfw.pennington.net.'
   >>>

Factory option
==============

IOSCfgLine
----------

* By default, CiscoConfParse stores config lines in something called an `IOSCfgLine() <http://www.pennington.net/py/ciscoconfparse/api_IOSCfgLine.html>`_

  - ``IOSCfgLine()`` knows the line number
  - ``IOSCfgLine()`` knows where the parents and children are
  - ``IOSCfgLine()`` *doesn't automatically know details such as what IP address is on an interface, or whether proxy-arp is configured on it*

IOSCFGLINE() objects
--------------------

* By default `IOSCfgLine() <http://www.pennington.net/py/ciscoconfparse/api_IOSCfgLine.html>`_ objects don't pre-parse rich information about the config

.. class:: prettyprint lang-python

::

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/path/to/config')
   >>> intf = parse.find_objects('interface GigabitEthernet0/1')[0]
   >>> intf
   <IOSCfgLine # 0 'interface GigabitEthernet0/1'>
   >>> intf.name
   Traceback (most recent call last):
     File "<stdin>", line 1, in <module>
   AttributeError: 'IOSCfgLine' object has no attribute 'name'
   >>>

Custom line objects
-------------------

* Parsing with ``CiscoConfParse(CONFIG, factory=True)`` assigns customized objects to some configuration lines

.. class:: prettyprint lang-python

::

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/path/to/config', factory=True)
   >>> intf = parse.find_objects('interface GigabitEthernet0/1')[0]
   >>> intf
   <IOSIntfLine # 0 'GigabitEthernet0/1' info: '10.0.0.1/24'>
   >>> intf.name
   'GigabitEthernet0/1'
   >>> intf.ipv4_addr
   '10.0.0.1'
   >>> intf.ipv4_netmask
   '255.255.255.0
   >>>

Important information
---------------------

* Parsing with ``factory=True`` is *BETA* functionality

  - Read the source code for documentation
  - Only `Cisco IOS <https://github.com/mpenning/ciscoconfparse/blob/master/ciscoconfparse/models_cisco.py>`_ and `Cisco ASA <https://github.com/mpenning/ciscoconfparse/blob/master/ciscoconfparse/models_asa.py>`_ have parsers
  - Functionality is limited and I'm *slowly* adding more

* ``factory=True`` syntax is somewhat unstable

  - I might change the APIs whenever I want to
  - If you care about things changing then don't use ``factory=True``

