==============
ciscoconfparse
==============

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. image:: https://pypip.in/v/ciscoconfparse/badge.png
   :target: https://pypi.python.org/pypi/ciscoconfparse
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

ciscoconfparse_ parses, queries, builds, or modifies Cisco IOS 
configurations.

Usage: A contrived config audit
===============================

Suppose you have a large switched network and
need to run audits on your configurations; assume you need to build 
configurations which conform to the following criteria:

* Access switchports *must* be configured with ``storm-control``
* Trunk ports *must not* have port-security
* Timestamps must be enabled on logging and debug messages

You should follow the following steps.

#) Assume that you start with the following Cisco IOS configuration saved as ``short.conf``: ::

    !
    interface FastEthernet0/1
     switchport mode access
     switchport access vlan 532
    !
    interface FastEthernet0/2
     switchport mode trunk
     switchport trunk allowed 300,532
     switchport nonegotiate
     switchport port-security maximum 2
     switchport port-security violation restrict
     switchport port-security
    !
    interface FastEthernet0/3
     switchport mode access
     switchport access vlan 300
    !
    end


#) Next, we build this script to read and change the config: ::

    # required if running Python 2.6...
    from __future__ import with_statement

    from ciscoconfparse import CiscoConfParse

    def standardize_intfs(parse):

        ## Search all switch interfaces and modify them
        #
        # r'^interface.+?thernet' is a regular expression, for ethernet intfs
        for intf in parse.find_objects(r'^interface.+?thernet'):

            has_stormcontrol = intf.has_child_with(r' storm-control broadcast')
            is_switchport_access = intf.has_child_with(r'switchport mode access')
            is_switchport_trunk = intf.has_child_with(r'switchport mode trunk')

            ## Add missing features
            if is_switchport_access and (not has_stormcontrol):
                intf.append_to_family(' storm-control action trap')
                intf.append_to_family(' storm-control broadcast level 0.4 0.3')

            ## Remove dot1q trunk misconfiguration...
            elif is_switchport_trunk:
                intf.delete_children_matching('port-security')

    ## Parse the config
    parse = CiscoConfParse('short.conf')

    ## Add a new switchport at the bottom of the config...
    obj = parse.find_objects('^end').pop()  # Find the last object in the config
    obj.insert_before('interface FastEthernet0/4')
    obj.insert_before(' switchport')
    obj.insert_before(' switchport mode access')
    obj.insert_before('!')
    parse.commit()     # commit() **must** be called before searching again

    ## Search and standardize the interfaces...
    standardize_intfs(parse)
    parse.commit()     # commit() **must** be called before searching again

    ## I'm illustrating regular expression usage in has_line_with()
    if not parse.has_line_with(r'^service\stimestamp'):
        ## prepend_line() adds a line at the top of the configuration
        parse.prepend_line('service timestamps debug datetime msec localtime show-timezone')
        parse.prepend_line('service timestamps log datetime msec localtime show-timezone')

    ## Write the new configuration
    parse.save_as('short.conf.new')

Normally, `regular expressions`_ should be used in ``.has_child_with()``; 
however, you can technically get away with the bare strings that I used in 
``standardize_intfs()`` in some cases.  That said, `regular expressions`_ are 
more powerful, and reliable when searching text.  Usage of 
the ``has_line_with()`` and ``find_objects()`` methods illustrate regular 
expression syntax.

#) After the script runs, the new configuration (``short.conf.new``) looks like this: ::

    service timestamps log datetime msec localtime show-timezone
    service timestamps debug datetime msec localtime show-timezone
    !
    interface FastEthernet0/1
     switchport mode access
     switchport access vlan 532
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    interface FastEthernet0/2
     switchport mode trunk
     switchport trunk allowed 300,532
     switchport nonegotiate
    !
    interface FastEthernet0/3
     switchport mode access
     switchport access vlan 300
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    interface FastEthernet0/4
     switchport
     switchport mode access
     storm-control broadcast level 0.4 0.3
     storm-control action trap
    !
    end

The script:

 * *Added* a switchport named FastEthernet0/4
 * *Added* storm-control to Fa0/1, Fa0/3, and Fa0/4
 * *Removed* port-security from Fa0/2
 * *Added* timestamps to logs and debug messages

Docs
====

The latest copy of the docs_ are `archived on the web <http://www.pennington.net/py/ciscoconfparse/>`_

.. _Pre-Requisites:

Pre-requisites
==============

ciscoconfparse_ needs  Python versions 2.6, 2.7 or 3.2+; the OS should not
matter. If you want to run it under a Python virtualenv_, it's been heavily 
tested in that environment as well.

.. _Installation:

Installation and Downloads
==========================

The best way to get ciscoconfparse is with setuptools_ or pip_.  If you 
already have setuptools_, you can install as usual:

::

      # Substitute whatever ciscoconfparse version you like...
      easy_install -U ciscoconfparse==0.9.17

Alternatively you can install with pip_:

::

      pip install ciscoconfparse

Otherwise `download it from PyPi <https://pypi.python.org/pypi/ciscoconfparse>`_, extract it and run the ``setup.py`` script:

::

      python setup.py install

If you're interested in the source, you can always pull from the `github repo`_
or `bitbucket repo`_:

- From bitbucket_:
  ::

      hg init
      hg clone https://bitbucket.org/mpenning/ciscoconfparse

- From github_:
  ::

      git clone git://github.com//mpenning/ciscoconfparse


.. _`License and Copyright`:

License and Copyright
=====================

ciscoconfparse_ is licensed GPLv3_; Copyright `David Michael Pennington`_, 
2007-2014.

The `ipaddr`_ module is distributed with ciscoconfparse_ to facilitate unit
tests. `ipaddr`_ uses the `ASF License 2.0`_; `ipaddr`_ is part of the Python
standard library, starting in Python 3.3.

.. _FAQ:

FAQ
===

#) *QUESTION*: I want to use ciscoconfparse_ with Python3; is that safe?  *ANSWER*: As long as you're using Python 3.2 or higher, it's safe. I test every release against Python 3.2+.

#) *QUESTION*: The example in this ``README.rst`` file looks different than what I'm used to seeing.  Did you change something?  *ANSWER*: Yes, starting around ciscoconfparse_ v0.9.10 I introducted more methods directly on ``IOSConfigLine`` objects; going forward, these methods are the preferred way to use ciscoconfparse_, although the sphinx docs_ on my website haven't been updated yet.  Please start using the new methods shown in the example, since they're faster, and you type much less code this way.  Eventually I'm going to deprecate the original style ciscoconfparse_ methods, but that's not going to happen yet.

#) *QUESTION*: ciscoconfparse_ saved me a lot of time, I want to give money.  Do you have a donation link?  *ANSWER*:  I love getting emails like this; helping people get their jobs done is why I wrote the module.  However, I'm not accepting donations.

#) *QUESTION*: Is there a way to use this module with perl?  *ANSWER*: Yes, I do this myself. Install the python package as you normally would and import it into perl with ``Inline.pm`` and ``Inline::Python`` from CPAN.

#) *QUESTION*: When I use ``find_children("interface GigabitEthernet3/2")``, I'm getting all interfaces beginning with 3/2, including 3/21, 3/22, 3/23 and 3/24. How can I limit my results?  *ANSWER*: There are two ways... the simplest is to use the 'exactmatch' option...  ``find_children("interface GigabitEthernet3/2", exactmatch=True)``. Another way is to utilize regex expansion that is native to many methods... ``find_children("interface GigabitEthernet3/2$")``

.. _`Other-Resources`:

Other Resources
===============

 * `Dive into Python3`_ is a good way to learn Python
 * `Team CYMRU`_ has a `Secure IOS Template`_, which is especially useful for external-facing routers / switches


.. _`Bug-Tracker-and-Support`:

Bug Tracker and Support
=======================

ciscoconfparse Support
----------------------

Please report any suggestions, bug reports, or annoyances with 
ciscoconfparse_ through the `bitbucket bug tracker`_.

Python Support
--------------

If you're having problems with general python issues, consider searching for
a solution on `Stack Overflow`_.  If you can't find a solution for your problem
or need more help, you can `ask a question`_.

Cisco Support
-------------

If you're having problems with your Cisco devices, you can open a case with 
`Cisco TAC`_; if you prefer crowd-sourcing, you can ask on the Stack Exchange 
`Network Engineering`_ site.

.. _Contributing:

Contributing
============

ciscoconfparse_ is developed with mercurial_, and pushed to bitbucket_.  
`hg-git`_ keeps `github repo`_ and bitbucket_ in sync, so it shouldn't 
matter if you just want to fork the `github repo`_.

Due to real-life time limitations, the docs_ are getting behind the bitbucket_
repo.  Even if you think your Python isn't good enough to contribute directly, 
I also value thoughtful improvements to the docs_.

.. _Unit-Tests:

Unit-Tests
==========

I use the `Travis CI project <https://travis-ci.org>`_ to continuously test ciscoconfparse on Python versions 2.6 through 3.3.

Click the image below for details; the current build status is:

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :align: center
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

.. _Author:

Author and Thanks
=================

ciscoconfparse_ was written by David Michael Pennington (mike [~at~] 
pennington [/dot\] net).

Special thanks:

 * Thanks to David Muir Sharnoff for his suggestion about making a special case for IOS banners.
 * Thanks to Alan Cownie for his API suggestions.
 * Sola Dei Gloria.


.. _ciscoconfparse: https://pypi.python.org/pypi/ciscoconfparse

.. _`David Michael Pennington`: http://pennington.net/

.. _setuptools: https://pypi.python.org/pypi/setuptools

.. _pip: https://pypi.python.org/pypi/pip

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

.. _`github repo`: https://github.com/mpenning/ciscoconfparse

.. _`bitbucket repo`: https://bitbucket.org/mpenning/ciscoconfparse

.. _bitbucket: https://bitbucket.org/mpenning/ciscoconfparse

.. _github: https://github.com/mpenning/ciscoconfparse

.. _mercurial: http://mercurial.selenic.com/

.. _`bitbucket bug tracker`: https://bitbucket.org/mpenning/ciscoconfparse/issues

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
