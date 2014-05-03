====================================================
:class:`~ciscoconfparse.CiscoConfParse` Fundamentals
====================================================

IOS Parent-child relationships
------------------------------

:class:`~ciscoconfparse.CiscoConfParse()` reads an IOS configuration and breaks 
it into a list of parent-child relationships.  Used correctly, these 
relationships can reveal a lot of useful information.  The concept of IOS 
parent and child is pretty intuitive, but we'll go through a simple example 
for clarity.

Line 1 is a parent:

.. code-block:: none
   :emphasize-lines: 1

   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !

Child lines are indented more than parent lines; thus, lines 2, 4 and 7 
are children of line 1:

.. code-block:: none
   :emphasize-lines: 2,4,7

   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !

Furthermore, line 3 (highlighted) is a child of line 2:

.. code-block:: none
   :emphasize-lines: 3

   policy-map QOS_1
    class GOLD
     priority percent 10
    class SILVER
     bandwidth 30
     random-detect
    class default
   !

In short:

- Line 1 is a parent, and its children are lines 2, 4, and 7.
- Line 2 is also a parent, and it only has one child: line 3.

:class:`~ciscoconfparse.CiscoConfParse()` uses these parent-child relationships 
to build queries.  For instance, you can find a list of all parents with or 
without a child; or you can find all the configuration elements that are 
required to reconfigure a certain class-map.

:class:`~models_cisco.IOSCfgLine` objects
-----------------------------------------

When :class:`~ciscoconfparse.CiscoConfParse()` reads a configuration, it stores
parent-child relationships as a special :class:`~models_cisco.IOSCfgLine` 
object.  These objects are very powerful.

:class:`~models_cisco.IOSCfgLine` objects remember:

- The original IOS configuration line
- The parent configuration line
- All child configuration lines

:class:`~models_cisco.IOSCfgLine` objects also know about child indentation, 
and they keep special configuration query methods in the object itself.  For 
instance, if you found an :class:`~models_cisco.IOSCfgLine` object with 
children, you can search the children directly from the parent by using 
:func:`~models_cisco.IOSCfgLine.re_search_children()`.

Baseline configuration for these examples
-----------------------------------------

This tutorial will run all the queries against a sample configuration, which is shown below.

.. code-block:: none

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

Finding interface names that match a substring
----------------------------------------------

The following script will load a configuration file from 
``/tftpboot/bucksnort.conf`` and use 
:func:`~ciscoconfparse.CiscoConfParse.find_objects` to find the 
Serial interfaces.

Note that the ``^`` symbol at the beginning of the search string is a regular expression; ``^interface Serial`` tells python to limit the search to lines that 
*begin* with ``interface Serial``.

.. code-block:: python
   :emphasize-lines: 3

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> serial_objs = parse.find_objects("^interface Serial")

The assuming we use the configuration in the example above, 
:func:`~ciscoconfparse.CiscoConfParse.find_objects()` scans the configuration 
for matching config objects and stores a list of 
:class:`~models_cisco.IOSCfgLine` objects in ``serial_objs``.

.. code-block:: python

   >>> serial_objs
   [<IOSCfgLine # 14 'interface Serial1/0'>, 
   <IOSCfgLine # 18 'interface Serial1/1'>, 
   <IOSCfgLine # 23 'interface Serial1/2'>]

As you can see, the config statements are stored inside 
:class:`~models_cisco.IOSCfgLine` objects.  If you want to access the
text inside the :class:`~models_cisco.IOSCfgLine` objects, just call their
``text`` attribute.  For example...

.. code-block:: python
   :emphasize-lines: 2

   >>> for obj in serial_objs:
   ...     print obj.text
   ...
   interface Serial1/0
   interface Serial1/1
   interface Serial1/2

Going forward, I will assume that you know how to use regular expressions; if 
you would like to know more about regular expressions, O'Reilly's 
`Mastering Regular Expressions <http://www.amazon.com/Mastering-Regular-Expressions-Jeffrey-Friedl/dp/0596528124/>`_ book is very good.

Finding parents with a specific child
-------------------------------------

Suppose we need to find interfaces with the ``QOS_1`` service-policy applied
outbound...

.. code-block:: python
   :emphasize-lines: 2,5

   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> all_intfs = parse.find_objects(r"^interf")
   >>> qos_intfs = list()
   >>> for obj in all_intfs:
   ...     if obj.re_search_children(r"service-policy\soutput\sQOS_1"):
   ...         qos_intfs.append(obj)
   ...
   >>> qos_intfs
   [<IOSCfgLine # 18 'interface Serial1/1'>]

This script iterates over the interface objects, and searches the children for
the qos policy.  It's worth mentioning that Python also has something called a 
`list-comprehension`_, which makes the script for this task a little more 
compact...

.. code-block:: python
   :emphasize-lines: 2,3

   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> qos_intfs = [obj for obj in parse.find_objects(r"^interf") \
   ...     if obj.re_search_children(r"service-policy\soutput\sQOS_1")]
   ...
   >>> qos_intfs
   [<IOSCfgLine # 18 'interface Serial1/1'>]

You can choose either method to accomplish your task... sometimes a 
`list-comprehension`_ is a better fit.  Other times, you may want a bare 
for-loop.

.. _`list-comprehension`: https://docs.python.org/2/tutorial/datastructures.html#list-comprehensions
