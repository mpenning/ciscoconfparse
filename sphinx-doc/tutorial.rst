================================
:class:`CiscoConfParse` Tutorial
================================

This is a brief tutorial which will cover the features that most :class:`CiscoConfParse` users care about.  We make a couple of assumptions throughout this tutorial...

- You already know a scripting language like Python or Perl
- You (naturally) have a basic understanding of Cisco IOS

Overview
----------------------

:class:`CiscoConfParse` reads in an IOS configuration and breaks it into a list of parent-child relationships.  Used correctly, these relationships can find a lot of useful information in a router or switch configuration.  The concept of IOS parent and child is pretty intuitive, but we'll go through a simple example for clarity.

.. code-block:: none
   :linenos:

   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !

In the configuration above, Line 1 is a parent, and its children are lines 2, 4, and 7.  Line 2 is also a parent, and it only has one child: line 3.

:class:`CiscoConfParse` uses these parent-child relationships to build queries.  For instance, you can find a list of all parents with or without a child; or you can find all the configuration elements that are required to reconfigure a certain class-map.

This tutorial will run all the queries against a sample configuration, which is shown below.

.. code-block:: none
   :linenos:

   ! Filename: /tftpboot/bucksnort.conf
   !
   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !
   interface Ethernet0/0
    ip address 1.1.2.1 255.255.255.0
    no cdp enable
   !
   interface Serial1/0
    encapsulation ppp
    ip address 1.1.1.1 255.255.255.252
   !
   interface Serial1/1
    encapsulation ppp
    ip address 1.1.1.5 255.255.255.252
    service-policy output QOS_1
   !
   interface Serial1/2
    encapsulation hdlc
    ip address 1.1.1.9 255.255.255.252
   !
   class-map GOLD
    match access-group 102
   class-map SILVER
    match protocol tcp
   !
   access-list 101 deny tcp any any eq 25 log
   access-list 101 permit ip any any
   !
   access-list 102 permit tcp any host 1.5.2.12 eq 443
   access-list 102 deny ip any any
   !
   logging 1.2.1.10
   logging 1.2.1.11
   logging 1.2.1.12

A note about Python
----------------------

If you are coming from Perl or another language (many people do), you may not be familiar with Python's interpreter interface.  To access the interpreter, just issue ``python`` at the command-line; this drops you into the interpreter, where you can issue commands interactively.  Use ``quit()`` to leave the interpreter.

.. parsed-literal::

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

.. parsed-literal::

   #!/usr/bin/env python

   print "Hello world"

Installing ciscoconfparse
------------------------------

All the examples below assume you have imported ciscoconfparse at the interpreter before you start...

.. parsed-literal::

   >>> from ciscoconfparse import CiscoConfParse

Try importing `CiscoConfParse` in the python interpreter now.  If it doesn't work, then you'll need to install ciscoconfparse.

If your python installation already has ``easy_install``, you can type ``easy_install -U ciscoconfparse`` as root.  If you don't have ``easy_install`` you will need to download the ciscoconfparse compressed tarball, extract it, and run the following command in the ciscoconfparse directory: ``python ./setup.py install`` as root.

Simple Usage
----------------------

Finding interface names that match a substring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following script will load a configuration file from ``/tftpboot/bucksnort.conf`` and use :func:`CiscoConfParse.find_lines` to parse it for the names of all serial interfaces.  Note that the ``^`` symbol at the beginning of the search string is a regular expression; ``^interface Serial`` tells python to limit it's search to lines that *begin* with ``interface Serial``.

Going forward, I will assume that you know how to use regular expressions; if you would like to know more about regular expressions, the `Mastering Regular Expressions (O'Reilly) <http://www.amazon.com/Mastering-Regular-Expressions-Jeffrey-Friedl/dp/0596528124/>`_ book is very good.

.. parsed-literal::

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> serial_intfs = parse.find_lines("^interface Serial")

The assuming we use the configuration in the example above, :func:`CiscoConfParse.find_lines` scans the configuration for matching lines and returns the following results:

.. parsed-literal::

   >>> serial_intfs
   ['interface Serial1/0', 'interface Serial1/1', 'interface Serial1/2']

Finding parents with a specific child
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The last example was a good start, but if this was all :class:`CiscoConfParse` could do, then it's easier to use ``grep``.

Let's suppose you need to find all interfaces that are configured to use ``service-policy QOS_1`` in the output direction.  We will use :func:`CiscoConfParse.find_parents_w_child` to search the config.

:func:`CiscoConfParse.find_parents_w_child` requires at least two different arguments:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child

If the arguments above match both the parent and child respectively, then :func:`CiscoConfParse.find_parents_w_child` will add the parent's line to a list.  This list is returned after :func:`CiscoConfParse.find_parents_w_child` finishes analyzing the configuration.

In this case, we need to find parents that begin with ``^interface`` and have a child matching ``service-policy output QOS_1``.  One might wonder why we chose to put a caret (``^``) in front of the parent's regex, but not in front of the child's regex.  We did this because of the way IOS indents commands in the configuration.  Interface commands always show up at the top of the heirarchy in the configuration; interfaces do not get indented.  On the other hand, the commands applied to the interface, such as a service-policy *are* indented.  If we put a caret in front of ``service-policy output QOS_1``, it would not match anything because we would be forcing a beginning-of-the-line match.  The search and result is shown below.

.. parsed-literal::
    
   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> qos_intfs = parse.find_parents_w_child( "^interf", "service-policy output QOS_1" )

Results:

.. parsed-literal::

   >>> qos_intfs
   ['interface Serial1/1']


Finding parents *without* a specific child
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's suppose you wanted a list of all interfaces that have CDP enabled; this implies a couple of things:

1.  CDP has not been disabled globally with ``no cdp run``
2.  The interfaces in question are not configured with ``no cdp enable``

:func:`CiscoConfParse.find_parents_wo_child` is a function to find parents without a specific child; it requires arguments similar to :func:`CiscoConfParse.find_parents_w_child`:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child's *exclusion*

Since we need to find parents that do not have ``no cdp enable``, we will use :func:`CiscoConfParse.find_parents_wo_child` for this query.  Note that the script below makes use of a special property of python lists... empty lists test False in Python; thus, we can use ``if not bool(parse.find_lines('no cdp run'))`` to ensure that CDP is running globally on this device.

.. parsed-literal::

   >>> if not bool(parse.find_lines('no cdp run')):
   ...     cdp_intfs = parse.find_parents_wo_child('^interface', 'no cdp enable')

Results:

.. parsed-literal::

   >>> cdp_intfs
   ['interface Serial1/0', 'interface Serial1/1', 'interface Serial1/2']


Finding children
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's suppose you needed to look at the children of a particular parent, but you didn't want the children's children.  :func:`CiscoConfParse.find_children` was made for this purpose.

.. parsed-literal::

   >>> children = parse.find_children('policy-map QOS_1')

Results:

.. parsed-literal::

   >>> children
   ['policy-map QOS_1', ' class GOLD', ' class SILVER', ' class default']

If you *do* want the children (recursively), then use :func:`CiscoConfParse.find_all_children`.

.. parsed-literal::

   >>> all_children = parse.find_all_children('policy-map QOS_1')

.. parsed-literal::

   >>> all_children
   ['policy-map QOS_1', ' class GOLD', '  priority percent 10', ' class SILVER', '  bandwidth 30', '  random-detect', ' class default']


CiscoConfParse options
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Several of :class:`CiscoConfParse`'s functions support one of these options:

- exactmatch
- ignore_ws

:option:`exactmatch` - This can either be :const:`True` or :const:`False` (the default).  When :option:`exactmatch` is set :const:`True`, CiscoConfParse requires an exact match of the whole string (instead of a sub-string match, which is the default).

:option:`ignore_ws` - This can either be :const:`True` or :const:`False` (the default).  When :option:`ignore_ws` is set :const:`True`, CiscoConfParse will ignore differences in whitespace between the query string and the IOS configuration.

Not all functions support the options above; please consult the API documentation for specifics.


Checking Passwords
------------------------------

Sometimes you find yourself wishing you could decrypt vty or console passwords to ensure that they conform to the corporate standard.  :class:`CiscoConfParse` comes with a :class:`CiscoPassword` class that can decrypt some Cisco IOS type 7 passwords.

.. NOTE::

   Cisco IOS Type 7 passwords were never meant to be secure; these passwords only protect against shoulder-surfing.  When you add users and enable passwords to your router, be sure to use Cisco IOS Type 5 passwords; these are much more secure and cannot be decrypted.

.. NOTE::

   :class:`CiscoPassword` also cannot decrypt all Type 7 passwords.  If the passwords exceed a certain length, the algorithm I have ceases to work.  An error is printed to the console when this happens.  In a future version of the script I will raise a python error when this happens.

Simple example... let's suppose you have this configuration...

.. parsed-literal::

   line con 0
    login
    password 107D3D232342041E3A
    exec-timeout 15 0

We need to ensure that the password on the console is correct.  This is easy with the :class:`CiscoPassword` class

.. parsed-literal::


   >>> from ciscoconfparse import CiscoPassword
   >>> dp = CiscoPassword()
   >>> decrypted_passwd = dp.decrypt('107D3D232342041E3A')

Result:

.. parsed-literal::

   >>> decrypted_passwd
   'STZF5vuV'


Integrated Example
------------------------------

Let's suppose we need to find all serial interfaces in a certain address range and configure them for the MPLS LDP protocol.  We will assume that all serial interfaces in 1.1.1.0/24 need to be configured with LDP.

The script below will build a list of serial interfaces, check to see whether they are in the correct address range.  If so, the script will build a diff to enable LDP.

.. parsed-literal::

   from ciscoconfparse import CiscoConfParse

   cfgdiffs = []

   parse = CiscoConfParse('/tftpboot/bucksnort.conf')
   ser_intfs = parse.find_lines("^interface Serial")
   for intf in ser_intfs:
      ## Find children of the interface called intf
      famobj = CiscoConfParse(parse.find_children(intf, exactmatch=True))
      if(famobj.find_lines("address 1\\.1\\.1")):
         cfgdiffs.append(intf)
         cfgdiffs.append(" mpls ip")

Result:

.. parsed-literal::

   >>> cfgdiffs
   ['interface Serial1/0', ' mpls ip', 'interface Serial1/1', ' mpls ip', 'interface Serial1/2', ' mpls ip']
   >>> for line in cfgdiffs:
   ...     print line
   ... 
   interface Serial1/0
    mpls ip
   interface Serial1/1
    mpls ip
   interface Serial1/2
    mpls ip
   >>>

