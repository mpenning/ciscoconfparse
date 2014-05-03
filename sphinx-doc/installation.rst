============
Installation
============

A note about Python
----------------------

If you are coming from Perl or another language (many people do), you may not be familiar with Python's interpreter interface.  To access the interpreter, just issue ``python`` at the command-line; this drops you into the interpreter, where you can issue commands interactively.  Use ``quit()`` to leave the interpreter.

.. code-block:: python

   [mpenning@mpenning-S10 ~]$ python
   Python 2.5.2 (r252:60911, Dec  5 2008, 11:57:32)
   [GCC 3.4.6 [FreeBSD] 20060305] on freebsd6
   Type "help", "copyright", "credits" or "license" for more information.
   >>>
   >>> print "Hello world"
   Hello world
   >>> quit()
   [mpenning@mpenning-S10 ~]$

The same commands could be used in an executable script saved to disk...

.. code-block:: python

   #!/usr/bin/env python

   print "Hello world"

Using :mod:`ciscoconfparse`
---------------------------

All the examples assume you have imported 
:class:`~ciscoconfparse.CiscoConfParse` at the interpreter before you start...

.. code-block:: python

   >>> from ciscoconfparse import CiscoConfParse

Try importing `CiscoConfParse` in the python interpreter now.  If it doesn't work, then you'll need to install ciscoconfparse.

Installing :mod:`ciscoconfparse`
--------------------------------

If your python installation already has ``easy_install``, you can type 
``easy_install -U ciscoconfparse`` as root.  If you don't have 
``easy_install`` you will need to 
`download the ciscoconfparse compressed tarball`_, extract it, and run the 
following command in the ciscoconfparse directory: 
``python ./setup.py install`` as root.

.. _`download the ciscoconfparse compressed tarball`: https://pypi.python.org/pypi/ciscoconfparse/ 

