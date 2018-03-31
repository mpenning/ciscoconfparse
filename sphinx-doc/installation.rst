CiscoConfParse Installation and Python Basics
=============================================

A note about Python
-------------------

If you are coming from Perl or another language (many people do), you may not 
be familiar with Python's interpreter interface.  To access the interpreter, 
just issue ``python`` at the Windows or unix command-line; this drops you into 
an interactive interpreter, where you can issue python commands.  Use 
``quit()`` to leave the interpreter.

When you see ``>>>`` preceding python statements, that means the example is run
from within the python interpreter.

.. code-block:: python

   >>>
   >>> print "Hello world"

If you don't see ``>>>`` preceding python statements, that means the example
is run from a file saved to disk.

Using the Python in Unix
~~~~~~~~~~~~~~~~~~~~~~~~

This is a "Hello World" example from within a unix Python interpreter.

.. code-block:: python
   :emphasize-lines: 3,8

   [mpenning@mpenning-S10 ~]$ which python
   /usr/local/bin/python
   [mpenning@mpenning-S10 ~]$ python
   Python 2.5.2 (r252:60911, Dec  5 2008, 11:57:32)
   [GCC 3.4.6 [FreeBSD] 20060305] on freebsd6
   Type "help", "copyright", "credits" or "license" for more information.
   >>>
   >>> print "Hello world"
   Hello world
   >>> quit()
   [mpenning@mpenning-S10 ~]$

The same commands could be used in an executable script (mode 755) saved to 
disk... and run from the unix shell.

.. code-block:: python

   #!/usr/bin/env python

   print "Hello world"

Using the Python in Windows
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Please see the official `Python on Windows`_ documentation.

Using :mod:`ciscoconfparse`
---------------------------

Once you know how to find and use python on your system, it's time to ensure 
you have a copy of :mod:`ciscoconfparse`.   Many of the examples assume you 
have imported :class:`~ciscoconfparse.CiscoConfParse` at the interpreter 
before you start...

.. code-block:: python

   >>> from ciscoconfparse import CiscoConfParse

Try importing `CiscoConfParse` in the python interpreter now.  If it doesn't 
work, then you'll need to install ciscoconfparse.

Installing :mod:`ciscoconfparse`
--------------------------------

ciscoconfparse_ needs  Python versions 2.6, 2.7 or 3.2+; the OS should not
matter. If you want to run it under a Python virtualenv_, it's been heavily
tested in that environment as well. 

You can check your python version with the ``-V`` switch...

.. code-block:: none

   [mpenning@Mudslide ~]$ python -V
   Python 2.7.3
   [mpenning@Mudslide ~]$

The best way to get ciscoconfparse is with pip_ or setuptools_.

Install with pip
~~~~~~~~~~~~~~~~

If you already have pip_, you can install as usual:

Alternatively you can install with pip_: :: 

      pip install --upgrade ciscoconfparse

If you have a specific version of ciscoconfparse in mind, you can specify that
at the command-line ::

      pip install ciscoconfparse==1.3.11


Install with setuptools
~~~~~~~~~~~~~~~~~~~~~~~

If you don't have pip_, you can use setuptools_...  ::

      # Substitute whatever ciscoconfparse version you like...
      easy_install -U ciscoconfparse

If you have a specific version of ciscoconfparse in mind, you can specify that
at the command-line ::

      easy_install -U ciscoconfparse==1.2.39

Install from the source
~~~~~~~~~~~~~~~~~~~~~~~

If you don't have either pip_ or setuptools_, you can 
`download the ciscoconfparse compressed tarball`_, extract it and 
run the ``setup.py`` script in the tarball: ::

      python setup.py install

Github and Bitbucket
~~~~~~~~~~~~~~~~~~~~

If you're interested in the source, you can always pull from the `github repo`_
or `bitbucket repo`_:

- From bitbucket_ (this also assumes you have mercurial_):
  ::

      hg init
      hg clone https://bitbucket.org/mpenning/ciscoconfparse

- From github_:
  ::

      git clone git://github.com//mpenning/ciscoconfparse


.. _`download the ciscoconfparse compressed tarball`: https://pypi.python.org/pypi/ciscoconfparse/ 

.. _`Python on Windows`: https://docs.python.org/2/faq/windows.html

.. _setuptools: https://pypi.python.org/pypi/setuptools

.. _pip: https://pypi.python.org/pypi/pip

.. _`github repo`: https://github.com/mpenning/ciscoconfparse

.. _`bitbucket repo`: https://bitbucket.org/mpenning/ciscoconfparse

.. _bitbucket: https://bitbucket.org/mpenning/ciscoconfparse

.. _github: https://github.com/mpenning/ciscoconfparse

.. _mercurial: http://mercurial.selenic.com/

.. _virtualenv: https://pypi.python.org/pypi/virtualenv

.. _ciscoconfparse: https://pypi.python.org/pypi/ciscoconfparse


