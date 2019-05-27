=====================================================
:class:`~ciscoconfparse.CiscoConfParse` Legacy Syntax
=====================================================

This section will cover the legacy :class:`~ciscoconfparse.CiscoConfParse()`
syntax; these were the original methods before version 1.0.0; legacy
methods always returned text strings.  This makes them easier to learn, but
harder to write complex scripts with.  There is nothing wrong with continuing to use these methods; however, you will probably find that your scripts are more 
efficient if you use the newer methods that manipulate 
:class:`~models_cisco.IOSCfgLine()` objects, which were introduced in 
version 1.0.0.

Baseline configuration
----------------------

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

Finding interface names that match a substring
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following script will load a configuration file from 
``/tftpboot/bucksnort.conf`` and use 
:func:`~ciscoconfparse.CiscoConfParse.find_lines` to find the 
Serial interfaces.

Note that the ``^`` symbol at the beginning of the search string is a regular 
expression; ``^interface Serial`` tells python to limit the search to lines 
that *begin* with ``interface Serial``.

To find matching interface statements, use this code...

.. code-block:: python
   :emphasize-lines: 3
  
   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> serial_lines = parse.find_lines("^interface Serial")
   >>> serial_lines
   ['interface Serial1/0', 'interface Serial1/1', 'interface Serial1/2']

Going forward, I will assume that you know how to use regular expressions; if 
you would like to know more about regular expressions, O'Reilly's 
`Mastering Regular Expressions <http://www.amazon.com/Mastering-Regular-Expressions-Jeffrey-Friedl/dp/0596528124/>`_ book is very good.


Finding parents with a specific child
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The last example was a nice start, but if this was all 
:class:`~ciscoconfparse.CiscoConfParse` could do, then it's easier to 
use ``grep``.

Let's suppose you need to find all interfaces that are configured with 
``service-policy QOS_1`` in the output direction.  We will use 
:func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child` to search the 
config.

:func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child` requires at least 
two different arguments:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child

If the arguments above match both the parent and child respectively, then 
:func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child` will add the 
parent's line to a list.  This list is returned after 
:func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child` finishes analyzing 
the configuration.

In this case, we need to find parents that begin with ``^interface`` and have a child matching ``service-policy output QOS_1``.  One might wonder why we chose to put a caret (``^``) in front of the parent's regex, but not in front of the child's regex.  We did this because of the way IOS indents commands in the configuration.  Interface commands always show up at the top of the heirarchy in the configuration; interfaces do not get indented.  On the other hand, the commands applied to the interface, such as a service-policy *are* indented.  If we put a caret in front of ``service-policy output QOS_1``, it would not match anything because we would be forcing a beginning-of-the-line match.  The search and result is shown below.

.. code-block:: python
    
   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> qos_intfs = parse.find_parents_w_child( "^interf", "service-policy output QOS_1" )

Results:

.. code-block:: python

   >>> qos_intfs
   ['interface Serial1/1']


Finding parents *without* a specific child
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Let's suppose you wanted a list of all interfaces that have CDP enabled; this implies a couple of things:

1.  CDP has not been disabled globally with ``no cdp run``
2.  The interfaces in question are not configured with ``no cdp enable``

:func:`~ciscoconfparse.CiscoConfParse.find_parents_wo_child` is a function to 
find parents without a specific child; it requires arguments similar to 
:func:`~ciscoconfparse.CiscoConfParse.find_parents_w_child`:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child's *exclusion*

Since we need to find parents that do not have ``no cdp enable``, we will use 
:func:`~ciscoconfparse.CiscoConfParse.find_parents_wo_child` for this query.  
Note that the script below makes use of a special property of python lists... 
empty lists test False in Python; thus, we can 
use ``if not bool(parse.find_lines('no cdp run'))`` to ensure that CDP is 
running globally on this device.

.. code-block:: python

   >>> if not bool(parse.find_lines('no cdp run')):
   ...     cdp_intfs = parse.find_parents_wo_child('^interface', 'no cdp enable')

Results:

.. code-block:: python

   >>> cdp_intfs
   ['interface Serial1/0', 'interface Serial1/1', 'interface Serial1/2']


Finding children
~~~~~~~~~~~~~~~~

Let's suppose you needed to look at the children of a particular parent, but 
you didn't want the children's children.  
:func:`~ciscoconfparse.CiscoConfParse.find_children` was made for this purpose.

.. code-block:: python

   >>> children = parse.find_children('policy-map QOS_1')

Results:

.. code-block:: python

   >>> children
   ['policy-map QOS_1', ' class GOLD', ' class SILVER', ' class default']

If you *do* want the children (recursively), then use 
:func:`~ciscoconfparse.CiscoConfParse.find_all_children`.

.. code-block:: python

   >>> all_children = parse.find_all_children('policy-map QOS_1')

.. code-block:: python

   >>> all_children
   ['policy-map QOS_1', ' class GOLD', '  priority percent 10', ' class SILVER', '  bandwidth 30', '  random-detect', ' class default']



Checking Passwords
------------------------------

Sometimes you find yourself wishing you could decrypt vty or console passwords to ensure that they conform to the corporate standard.  :class:`~ciscoconfparse.CiscoConfParse` comes with a :class:`~ciscoconfparse.CiscoPassword` class that can decrypt some Cisco IOS type 7 passwords.

.. note::

   Cisco IOS Type 7 passwords were never meant to be secure; these passwords only protect against shoulder-surfing.  When you add users and enable passwords to your router, be sure to use Cisco IOS Type 5 passwords; these are much more secure and cannot be decrypted.

.. warning::

   :class:`CiscoPassword` also cannot decrypt all Type 7 passwords.  If the passwords exceed a certain length, the algorithm I have ceases to work.  An error is printed to the console when this happens.  In a future version of the script I will raise a python error when this happens.

Simple example... let's suppose you have this configuration...

.. parsed-literal::

   line con 0
    login
    password 107D3D232342041E3A
    exec-timeout 15 0

We need to ensure that the password on the console is correct.  This is easy with the :class:`~ciscoconfparse.CiscoPassword` class

.. code-block:: python

   >>> from ciscoconfparse import CiscoPassword
   >>> dp = CiscoPassword()
   >>> decrypted_passwd = dp.decrypt('107D3D232342041E3A')

Result:

.. code-block:: python

   >>> decrypted_passwd
   'STZF5vuV'

