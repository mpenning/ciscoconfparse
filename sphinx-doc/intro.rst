=============
Introduction
=============

Overview
---------
ciscoconfparse is a Python package for parsing through Cisco IOS-style configurations and retrieving portions of the config based on a variety of query methods.

The package will process an IOS-style config and break it into a set of linked parent / child relationships. Then you issue queries against these relationships using a familiar family syntax model. Queries can either be in the form of a simple string, or you can use regular expressions. The API provides powerful query tools, including the ability to find all parents that have or do not have children matching a certain criteria.

The package also provides a set of methods to query and manipulate the 
IOSConfigLine objects themselves. This gives you a flexible mechanism to build 
your own custom queries, because the IOSConfigLine objects store all the 
parent / child hierarchy in them.

What is ciscoconfparse good for?
----------------------------------
ciscoconfparse is primarily made to generate and audit Cisco IOS configurations.  Many companies deploy hundreds of IOS devices in their network.  These same entities may be governed by corporate compliance rules, which mandate certain configuration best practices.

After ten or more years of network evolutions, other companies may find that they have a tangled mess of potentially conflicting or misconfigured devices; meanwhile, executives demand more uptime.  Misconfigurations of proxy-arp, routing protocols, duplicated subnets, cdp, console passwords, or aaa schemes have a measurable affect on uptime and beg for a tool to audit them. However, manually scrubbing configurations is a long and error-prone process.

Audits aren't the only use for ciscoconfparse.  Let's suppose you are working on a design and need a list of dot1q trunks on a switch with more than 400 interfaces.  You can't grep for them because you need the interface names of layer2 trunks, and CiscoWorks makes you throw things.  With ciscoconfparse, it's really this easy...

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

So you may be saying, that all sounds great, but I have no idea what you did with that code up there.  If so, don't worry... There is a tutorial following this intro.  For more depth, I highly recommend `Dive into Python`_

.. _`Dive into Python`: http://www.diveintopython.org/

A little history... and a Python apologetic
--------------------------------------------
ciscoconfparse was born from audit requirements.  I was contracting for a company with hundreds of devices; PCI compliance obligated us to perform security audits on the configs and management wanted it done quarterly.  Our company was supposed to have an automated tool, but nobody could get it to work.  I offered to build an audit and diff script instead of our entire team spending hundreds of man-hours on a manual task each quarter.

At first, I tried using a canned Perl config-parsing library; it was great when it worked, but the library suffered from mysterious crashes on certain configs.  I tried auditing the troublesome configs maually, but dealing with the crashes put me behind schedule.  I reached a point where I realized the audit results were going to be late if something didn't change, so I wrote the author for help, but he literally said that he wasn't really sure how the library works. [#]_ 

With the deadline approaching, I wound up spending a full weekend of my own time writing my first endeavor in Python.  It worked so well, I found myself building similar tools for other accounts that weren't even mine.  After more work, I ultimately I published this as open-source software.  ciscoconfparse is available to anyone who wants to invest a little effort on the front-end.  Many companies in the US and Europe are already using it to audit their configs; I only ask that you drop me a line [#]_ and let me know if you like it and how I can improve the library.

.. [#] *This is not so much a slam on the module or author; it's part of Perl syntax.  After six months, most people have a hard time remembering the meaning of those quirky idioms that make their code tick.*

.. [#] *mike [~at~] pennington [~dot~] net*
