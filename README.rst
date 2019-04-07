==============
ciscoconfparse
==============

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. image:: https://img.shields.io/pypi/v/ciscoconfparse.svg
   :target: https://pypi.python.org/pypi/ciscoconfparse/
   :alt: Version

.. image:: http://img.shields.io/badge/license-GPLv3-blue.svg
   :target: https://www.gnu.org/copyleft/gpl.html
   :alt: License

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

.. image:: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
   :target: https://raw.githubusercontent.com/mpenning/ciscoconfparse/master/sphinx-doc/_static/ciscoconfparse_overview_75pct.png
   :alt: CiscoConfParse Parent / Child relationships

What if we don't use Cisco?
===========================

Don't let that stop you.

As of CiscoConfParse 1.2.4, you can parse `brace-delimited configurations`_ 
into a Cisco IOS style (see `Github Issue #17`_), which means that 
CiscoConfParse understands these configurations:

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

.. _Pre-Requisites:

Pre-requisites
==============

ciscoconfparse_ requires Python versions 2.7 or 3.4+ (note: version 3.7.0 has 
a bug - ref Github issue #117, but version 3.7.1 works); the OS should not 
matter.

.. _Installation:

Installation and Downloads
==========================

You can install into Python2.x with pip_:

::

      pip install --upgrade ciscoconfparse

Use ``pip3`` for Python3.x...

::

      pip3 install --upgrade ciscoconfparse

If you don't want to use pip_, you can install with `easy_install`:

::

      easy_install -U ciscoconfparse


Otherwise `download it from PyPi <https://pypi.python.org/pypi/ciscoconfparse>`_, extract it and run the ``setup.py`` script:

::

      python setup.py install

If you're interested in the source, you can always pull from the `github repo`_
or `bitbucket repo`_:


- From github_:
  ::

      git clone git://github.com//mpenning/ciscoconfparse


.. _FAQ:

FAQ
===

#) *QUESTION*: I want to use ciscoconfparse_ with Python3; is that safe?  *ANSWER*: *ANSWER*: Yes.

#) *QUESTION*: Some of the code in the documentation looks different than what I'm used to seeing.  Did you change something?  *ANSWER*: Yes, starting around ciscoconfparse_ v0.9.10 I introducted more methods directly on ``IOSConfigLine()`` objects; going forward, these methods are the preferred way to use ciscoconfparse_.  Please start using the new methods shown in the example, since they're faster, and you type much less code this way.

#) *QUESTION*: ciscoconfparse_ saved me a lot of time, I want to give money.  Do you have a donation link?  *ANSWER*:  I love getting emails like this; helping people get their jobs done is why I wrote the module.  However, I'm not accepting donations.

#) *QUESTION*: Is there a way to use this module with perl?  *ANSWER*: Yes, I do this myself. Install the python package as you normally would and import it into perl with ``Inline.pm`` and ``Inline::Python`` from CPAN.

#) *QUESTION*: When I use ``find_children("interface GigabitEthernet3/2")``, I'm getting all interfaces beginning with 3/2, including 3/21, 3/22, 3/23 and 3/24. How can I limit my results?  *ANSWER*: There are two ways... the simplest is to use the 'exactmatch' option...  ``find_children("interface GigabitEthernet3/2", exactmatch=True)``. Another way is to utilize regex expansion that is native to many methods... ``find_children("interface GigabitEthernet3/2$")``

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

`Travis CI project <https://travis-ci.org>`_ tests ciscoconfparse on Python versions 2.7 through 3.7, as well as a `pypy JIT`_ executable.

Click the image below for details; the current build status is:

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :align: center
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. _`License and Copyright`:

License and Copyright
=====================

ciscoconfparse_ is licensed GPLv3_; Copyright `David Michael Pennington`_, 
2007-2019.

ciscoconfparse_ is not affiliated with Cisco Systems in any way; the word "Cisco" is a registered trademark of Cisco Systems


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

.. _`Center for Internet Security Benchmarks`: https://learn.cisecurity.org/benchmarks

.. _`Team CYMRU`: http://www.team-cymru.org/

.. _`Cisco TAC`: http://cisco.com/go/support

.. _`Juniper networks`: http://www.juniper.net/

.. _`Cisco's Guide to hardening IOS devices`: http://www.cisco.com/c/en/us/support/docs/ip/access-lists/13608-21.html

