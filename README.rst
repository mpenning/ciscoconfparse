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

Introduction: What is ciscoconfparse?
=====================================

ciscoconfparse_ parses, queries, builds, or modifies Cisco IOS 
configurations.

For instance, suppose you have a large switched network and
need to run audits on your configurations; perhaps you need to build 
configurations for any access switchports missing ``storm-control`` or
``port-security``.  You can accomplish this using ciscoconfparse_ with a 
modest script...

.. code:: python

   from ciscoconfparse import CiscoConfParse

   parse = CiscoConfParse('edge-6509.conf')

   ## Walk all interfaces, and add missing configs
   for intf in parse.find_objects(r'^interface'):

       ## Identify missing features
       has_portsecurity = bool(parse.find_parents_w_child(r'^%s$' % line,
          r'port-security'))
       has_stormcontrol = bool(parse.find_parents_w_child(r'^%s$' % line,
          r'storm-control'))
       is_switchport_access = bool(parse.find_parents_w_child(r'^%s$' % line,
          r'^ switchport mode access'))

       ## Add missing features
       if is_switchport_access and (not has_portsecurity):
          parse.insert_after(r'^%s$' % line,
              ' switchport port-security maximum 2')
          parse.insert_after(r'^%s$' % line,
              ' switchport port-security violation restrict')
          parse.insert_after(r'^%s$' % line, 
              ' switchport port-security')

       if is_switchport_access and (not has_stormcontrol):
          parse.insert_after(r'^%s$' % line,
              ' storm-control broadcast level 0.4 0.3')
          parse.insert_after(r'^%s$' % line,
              ' storm-control multicast level 0.5 0.3')

   ## Write the new configuration
   with open('edge-6509.conf.new', 'w') as newconf:
       for line in parse.ioscfg:
           newconf.write(line+'\n')


Pre-requisites
==============

ciscoconfparse_ needs only Python to run. It works with Python versions 2.6, 
2.7 and 3.2+ on Linux and Windows.  If you're inclined to run under a 
virtualenv_, it's been heavily tested in that environment as well.

Docs
====

The latest copy of the docs are `archived on the web <http://www.pennington.net/py/ciscoconfparse/>`_

Installing
==========

The best way to get ciscoconfparse is with setuptools_ or pip_.  If you 
already have setuptools_, you can install as usual:

::

      # Substitute whatever version you like...
      easy_install -U ciscoconfparse==0.9.14

Alternatively you can install with pip_:

::

      pip install ciscoconfparse

Otherwise `download it from PyPi <https://pypi.python.org/pypi/ciscoconfparse>`_, extract it and run the ``setup.py`` script:

::

      python setup.py install

If you're interested in the source, you can always pull from the `github repo`_
or `bitbucket repo`_:

- From bitbucket:
  ::

      hg init
      hg clone https://bitbucket.org/mpenning/ciscoconfparse

- From github:
  ::

      git clone git://github.com//mpenning/ciscoconfparse


FAQ
===

- Q1: Is there a way to use this module with perl?
- A1: Yes, I do this myself. Install the python package as you normally would and import it into perl with ``Inline.pm`` and ``Inline::Python`` from CPAN.

- Q2: When I use ``find_children("interface GigabitEthernet3/2")``, I'm getting all interfaces beginning with 3/2, including 3/21, 3/22, 3/23 and 3/24. How can I limit my results?
- A2. There are two ways... the simplest is to use the 'exactmatch' option...  ``find_children("interface GigabitEthernet3/2", exactmatch=True)``. Another way is to utilize regex expansion that is native to many methods... ``find_children("interface GigabitEthernet3/2$")``

Testing
=======

I use the `Travis CI project <https://travis-ci.org>`_ to continuously test ciscoconfparse on Python versions 2.6 through 3.3.

Click the image below for details; the current build status is:

.. image:: https://travis-ci.org/mpenning/ciscoconfparse.png?branch=master
   :align: center
   :target: https://travis-ci.org/mpenning/ciscoconfparse
   :alt: Travis CI Status

Author and Thanks
=================

ciscoconfparse_ was written by David Michael Pennington (mike [~at~] 
pennington [/dot\] net).

Thanks to David Muir Sharnoff for his suggestion about making a special case 
for IOS banners. Thanks to Alan Cownie for his API suggestions. Thanks to 
everyone in advance for their bug reports and patience. Sola Dei Gloria.

.. _ciscoconfparse: https://pypi.python.org/pypi/ciscoconfparse

.. _setuptools: https://pypi.python.org/pypi/setuptools

.. _pip: https://pypi.python.org/pypi/pip

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

.. _`github repo`: https://github.com/mpenning/ciscoconfparse

.. _`bitbucket repo`: https://bitbucket.org/mpenning/ciscoconfparse
