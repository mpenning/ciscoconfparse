==============
ciscoconfparse
==============

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. image:: https://badge.fury.io/py/ciscoconfparse.png
   :target: https://pypi.python.org/pypi/ciscoconfparse/
   :alt: Version

.. image:: https://pypip.in/license/ciscoconfparse/badge.png
   :target: https://pypi.python.org/pypi/ciscoconfparse/
   :alt: License

.. image:: https://pypip.in/d/ciscoconfparse/badge.png
   :target: https://pypi.python.org/pypi/ciscoconfparse
   :alt: Downloads

.. contents::

.. _introduction:

Introduction: What is ciscoconfparse?
=====================================

ciscoconfparse is a Python_ library, which parses through Cisco IOS-style
(and other vendor) configurations.  It can:

- Audit existing router / switch / firewall / wlc configurations
- Retrieve portions of the configuration
- Modify existing configurations
- Build new configurations

The library examines an IOS-style config and breaks it into a set of linked
parent / child relationships.  You can perform complex queries about these 
relationships.

.. image:: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview.png
   :target: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview.png
   :alt: CiscoConfParse Parent / Child relationships

Quotes
======

These are a few selected public mentions about CiscoConfParse; I usually try not to share private emails without asking, thus the quotes aren't long at this time.

   <a href="https://github.com/mpenning/ciscoconfparse/issues/13#issuecomment-71340177"><img src="https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/crackerjackmack.png" width="800" alt="CiscoConfParse Github issue #13"></a><br>

We don't use Cisco
==================

Don't let that stop you.  CiscoConfParse parses anything that has a Cisco IOS 
style of configuration, which includes:

- Cisco IOS, Cisco Nexus, Cisco IOS-XR, Cisco IOS-XE, Aironet OS, Cisco ASA, Cisco CatOS
- Arista EOS
- Brocade
- HP Switches
- Force 10 Switches
- Dell PowerConnect Switches
- Extreme Networks
- Enterasys

As of CiscoConfParse 1.2.4, you can parse `brace-delimited configurations`_ 
into a Cisco IOS style (see `Github Issue #17`_), which means that 
CiscoConfParse understands these configurations too:

- Juniper Networks Junos, and Screenos
- F5 Networks configurations

Docs
====

The latest copy of the docs are `archived on the web <http://www.pennington.net/py/ciscoconfparse/>`_

.. _Pre-Requisites:

Pre-requisites
==============

ciscoconfparse_ requires Python versions 2.6, 2.7 or 3.2+; the OS should not
matter. If you want to run it under a Python virtualenv_, it's been heavily 
tested in that environment as well.

.. _`Bug-Tracker-and-Support`:

Bug Tracker and Support
=======================

- Please report any suggestions, bug reports, or annoyances with ciscoconfparse_ through the `github bug tracker`_.
- If you're having problems with general python issues, consider searching for a solution on `Stack Overflow`_.  If you can't find a solution for your problem or need more help, you can `ask a question`_.
- If you're having problems with your Cisco devices, you can open a case with `Cisco TAC`_; if you prefer crowd-sourcing, you can ask on the Stack Exchange `Network Engineering`_ site.


.. _`License and Copyright`:

License and Copyright
=====================

ciscoconfparse_ is licensed GPLv3_; Copyright `David Michael Pennington`_, 
2007-2014.

The `ipaddr`_ module is distributed with ciscoconfparse_ to facilitate unit
tests. `ipaddr`_ uses the `ASF License 2.0`_; `ipaddr`_ is part of the Python
standard library, starting in Python 3.3 (it's called ``ipaddress`` in Python3).


.. _ciscoconfparse: https://github.com/mpenning/ciscoconfparse/

.. _pypy: http://pypy.org/

.. _CrackerJackMack: https://github.com/CrackerJackMack

.. _`Github Issue #13`: https://github.com/mpenning/ciscoconfparse/issues/13

.. _`Github Issue #14`: https://github.com/mpenning/ciscoconfparse/issues/14

.. _`Github Issue #17`: https://github.com/mpenning/ciscoconfparse/issues/17

.. _`David Michael Pennington`: http://pennington.net/

.. _setuptools: https://pypi.python.org/pypi/setuptools

.. _pip: https://pypi.python.org/pypi/pip

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

.. _`github repo`: https://github.com/mpenning/ciscoconfparse

.. _`bitbucket repo`: https://bitbucket.org/mpenning/ciscoconfparse

.. _bitbucket: https://bitbucket.org/mpenning/ciscoconfparse

.. _github: https://github.com/mpenning/ciscoconfparse

.. _mercurial: http://mercurial.selenic.com/

.. _`github bug tracker`: https://github.com/mpenning/ciscoconfparse/issues

.. _`hg-git`: http://hg-git.github.io/

.. _`regular expressions`: http://docs.python.org/2/howto/regex.html

.. _`docs`: http://www.pennington.net/py/ciscoconfparse/

.. _`ipaddr`: https://code.google.com/p/ipaddr-py/

.. _`GPLv3`: http://www.gnu.org/licenses/gpl-3.0.html

.. _`ASF License 2.0`: http://www.apache.org/licenses/LICENSE-2.0

.. _`Dive into Python3`: http://www.diveintopython3.net/

.. _`Network Engineering`: http://networkengineering.stackexchange.com/

.. _`Stack Overflow`: http://stackoverflow.com/

.. _`ask a question`: http://stackoverflow.com/questions/ask

.. _`Secure IOS Template`: https://www.cymru.com/Documents/secure-ios-template.html

.. _`Team CYMRU`: http://www.team-cymru.org/

.. _`Cisco TAC`: http://cisco.com/go/support

.. _`Juniper networks`: http://www.juniper.net/

.. _`Cisco's Guide to hardening IOS devices`: http://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html

