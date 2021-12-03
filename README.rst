==============
ciscoconfparse
==============

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. image:: https://img.shields.io/pypi/v/ciscoconfparse.svg
   :target: https://pypi.python.org/pypi/ciscoconfparse/
   :alt: Version

.. image:: https://pepy.tech/badge/ciscoconfparse
   :target: https://pepy.tech/project/ciscoconfparse
   :alt: Downloads

.. image:: http://img.shields.io/badge/license-GPLv3-blue.svg
   :target: https://www.gnu.org/copyleft/gpl.html
   :alt: License

.. contents::

.. _introduction:

Introduction: What is ciscoconfparse?
=====================================

Short answer: ciscoconfparse is a Python_ library that helps you quickly answer questions like these about your configurations:

- What interfaces are shutdown?
- Which interfaces are in trunk mode?
- What address and subnet mask is assigned to each interface?
- Which interfaces are missing a critical command?
- Is this configuration missing a standard config line?

It can help you:

- Audit existing router / switch / firewall / wlc configurations
- Modify existing configurations
- Build new configurations

Speaking generally, the library examines an IOS-style config and breaks it 
into a set of linked parent / child relationships.  You can perform complex 
queries about these relationships.

.. image:: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
   :target: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
   :alt: CiscoConfParse Parent / Child relationships

Usage
=====

The following code will parse a configuration stored in 'exampleswitch.conf'
and select interfaces that are shutdown.

.. code:: python

    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    for intf_obj in parse.find_objects_w_child('^interface', '^\s+shutdown'):
        print("Shutdown: " + intf_obj.text)


The next example will find the IP address assigned to interfaces.

.. code:: python

    from ciscoconfparse import CiscoConfParse

    parse = CiscoConfParse('exampleswitch.conf', syntax='ios')

    for intf_obj in parse.find_objects('^interface'):

        intf_name = intf_obj.re_match_typed('^interface\s+(\S.+?)$')

        # Search children of all interfaces for a regex match and return 
        # the value matched in regex match group 1.  If there is no match, 
        # return a default value: ''
        intf_ip_addr = intf_obj.re_match_iter_typed(
            r'ip\saddress\s(\d+\.\d+\.\d+\.\d+)\s', result_type=str,
            group=1, default='')
        print("{0}: {1}".format(intf_name, intf_ip_addr))

What if we don't use Cisco?
===========================

Don't let that stop you.

As of CiscoConfParse 1.2.4, you can parse `brace-delimited configurations`_ 
into a Cisco IOS style (see `Github Issue #17`_), which means that 
CiscoConfParse can parse these configurations:

- Juniper Networks Junos
- Palo Alto Networks Firewall configurations
- F5 Networks configurations

CiscoConfParse also handles anything that has a Cisco IOS style of configuration, which includes:

- Cisco IOS, Cisco Nexus, Cisco IOS-XR, Cisco IOS-XE, Aironet OS, Cisco ASA, Cisco CatOS
- Arista EOS
- Brocade
- HP Switches
- Force 10 Switches
- Dell PowerConnect Switches
- Extreme Networks
- Enterasys
- Screenos

Docs
====

- The latest copy of the docs are `archived on the web <http://www.pennington.net/py/ciscoconfparse/>`_
- There is also a `CiscoConfParse Tutorial <http://pennington.net/tutorial/ciscoconfparse/ccp_tutorial.html>`_

Building the Package
====================

- ``cd`` into the root ciscoconfparse directory
- Edit the version number in `pyproject.toml` (as required)
- ``git commit`` all pending changes
- ``make test``
- ``make repo-push``
- ``make pypi``

.. _Pre-Requisites:

Pre-requisites
==============

ciscoconfparse_ requires Python versions 3.5+ (note: version 3.7.0 has 
a bug - ref Github issue #117, but version 3.7.1 works); the OS should not 
matter.

.. _Installation:

Installation and Downloads
==========================

- Use ``poetry`` for Python3.x...
  ::

      python -m pip install ciscoconfparse


If you're interested in the source, you can always pull from the `github repo`_:

- From github_ source download:
  ::

      git clone git://github.com/mpenning/ciscoconfparse
      cd ciscoconfparse/
      python -m pip install .


.. _`Other-Resources`:

Other Resources
===============

- `Dive into Python3`_ is a good way to learn Python
- `Team CYMRU`_ has a `Secure IOS Template`_, which is especially useful for external-facing routers / switches
- `Cisco's Guide to hardening IOS devices`_
- `Center for Internet Security Benchmarks`_ (An email address, cookies, and javascript are required)

.. _`Bug-Tracker-and-Support`:

Bug Tracker and Support
=======================

- Please report any suggestions, bug reports, or annoyances with ciscoconfparse_ through the `github bug tracker`_.
- If you're having problems with general python issues, consider searching for a solution on `Stack Overflow`_.  If you can't find a solution for your problem or need more help, you can `ask a question`_.
- If you're having problems with your Cisco devices, you can open a case with `Cisco TAC`_; if you prefer crowd-sourcing, you can ask on the Stack Exchange `Network Engineering`_ site.

.. _Unit-Tests:

Unit-Tests
==========

`Travis CI project <https://travis-ci.org>`_ tests ciscoconfparse on Python versions 3.6 and higher, as well as a `pypy JIT`_ executable.

Click the image below for details; the current build status is:

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :align: center
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. _`License and Copyright`:

License and Copyright
=====================

ciscoconfparse_ is licensed GPLv3_

- Copyright (C) 2021      David Michael Pennington
- Copyright (C) 2020-2021 David Michael Pennington at Cisco Systems
- Copyright (C) 2019      David Michael Pennington at ThousandEyes
- Copyright (C) 2012-2019 David Michael Pennington at Samsung Data Services
- Copyright (C) 2011-2012 David Michael Pennington at Dell Computer Corp
- Copyright (C) 2007-2011 David Michael Pennington

The word "Cisco" is a registered trademark of Cisco Systems

.. _Author:

Author and Thanks
=================

ciscoconfparse_ was written by David Michael Pennington (mike [~at~] 
pennington [/dot\] net).

Special thanks:

- Thanks to David Muir Sharnoff for his suggestion about making a special case for IOS banners.
- Thanks to Alan Cownie for his API suggestions.
- Thanks to CrackerJackMack_ for reporting `Github Issue #13`_
- Soli Deo Gloria


.. _ciscoconfparse: https://pypi.python.org/pypi/ciscoconfparse

.. _Python: http://python.org/

.. _`pypy JIT`: http://pypy.org/

.. _`Github Issue #13`: https://github.com/mpenning/ciscoconfparse/issues/13

.. _`Github Issue #14`: https://github.com/mpenning/ciscoconfparse/issues/14

.. _`Github Issue #17`: https://github.com/mpenning/ciscoconfparse/issues/17

.. _`brace-delimited configurations`: https://github.com/mpenning/ciscoconfparse/blob/master/configs/sample_01.junos

.. _CrackerJackMack: https://github.com/CrackerJackMack

.. _`David Michael Pennington`: http://pennington.net/

.. _pip: https://pypi.python.org/pypi/pip

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

.. _`github repo`: https://github.com/mpenning/ciscoconfparse

.. _github: https://github.com/mpenning/ciscoconfparse

.. _`github bug tracker`: https://github.com/mpenning/ciscoconfparse/issues

.. _`regular expressions`: http://docs.python.org/2/howto/regex.html

.. _`docs`: http://www.pennington.net/py/ciscoconfparse/

.. _`ipaddr`: https://code.google.com/p/ipaddr-py/

.. _`GPLv3`: http://www.gnu.org/licenses/gpl-3.0.html

.. _`ASF License 2.0`: http://www.apache.org/licenses/LICENSE-2.0

.. _`Dive into Python3`: http://www.diveintopython3.net/

.. _`Network Engineering`: http://networkengineering.stackexchange.com/

.. _`Stack Overflow`: http://stackoverflow.com/

.. _`ask a question`: http://stackoverflow.com/questions/ask

.. _`ciscoconfparse NetworkToCode slack channel`: https://app.slack.com/client/T09LQ7E9E/C015B4U8MMF/

.. _`Secure IOS Template`: https://www.cymru.com/Documents/secure-ios-template.html

.. _`Center for Internet Security Benchmarks`: https://learn.cisecurity.org/benchmarks

.. _`Team CYMRU`: http://www.team-cymru.org/

.. _`Cisco TAC`: http://cisco.com/go/support

.. _`Juniper networks`: http://www.juniper.net/

.. _`Cisco's Guide to hardening IOS devices`: http://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html

