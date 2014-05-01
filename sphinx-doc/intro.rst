=============
Introduction
=============

Overview
---------
ciscoconfparse parses through Cisco IOS-style configurations.  It can:

- Retrieve portions of the configuration
- Modify existing configurations
- Build new configurations

The package will process an IOS-style config and break it into a set of linked 
parent / child relationships; each configuration line is stored in a different 
:class:`models_cisco.IOSCfgLine` object.

Then you issue queries against these relationships using a familiar family 
syntax model. Queries can either be in the form of a simple string, or you can 
use `regular expressions`_. The API provides powerful query tools, including 
the ability to find all parents that have or do not have children matching a 
certain criteria.

The package also provides a set of methods to query and manipulate the 
:class:`models_cisco.IOSCfgLine` objects themselves. This gives you a flexible 
mechanism to build your own custom queries, because the 
:class:`models_cisco.IOSCfgLine` objects store all the parent / child 
hierarchy in them.

What is ciscoconfparse good for?
----------------------------------
After several network evolutions, you may have a tangled mess of conflicting or misconfigured Cisco devices.  Misconfigurations of proxy-arp, FHRP timers, routing protocols, duplicated subnets, cdp, console passwords, or aaa schemes have a measurable affect on uptime and beg for a tool to audit them. However, manually scrubbing configurations is a long and error-prone process.

Audits aren't the only use for ciscoconfparse.  Let's suppose you are working on a design and need a list of dot1q trunks on a switch with more than 400 interfaces.  You can't grep for them because you need the interface names of layer2 trunks.  With ciscoconfparse, it's really this easy...

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/largeConfig.conf')
   >>> trunks = parse.find_parents_w_child("^interface", "switchport trunk")
   >>> for intf in trunks:
   ...     print intf
   interface GigabitEthernet 1/7
   interface GigabitEthernet 1/23
   interface GigabitEthernet 1/24
   interface GigabitEthernet 1/30
   interface GigabitEthernet 3/2
   interface GigabitEthernet 5/10
   <and so on...>

So you may be saying, that all sounds great, but I have no idea what you did with that code up there.  If so, don't worry... There is a tutorial following this intro.  For more depth, I highly recommend `Dive into Python`_ and `Dive into Python3`_.

.. _`Dive into Python`: http://www.diveintopython.net/
.. _`Dive into Python3`: http://www.diveintopython3.net/
.. _`regular expressions`: https://docs.python.org/2/howto/regex.html
