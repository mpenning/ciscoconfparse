========================================================================================
:class:`~ciscoconfparse.CiscoConfParse` Fundamentals: Using Parent / Child Relationships
========================================================================================

IOS Parent-child relationships
------------------------------

:class:`~ciscoconfparse.CiscoConfParse()` reads an IOS configuration and breaks 
it into a list of parent-child relationships.  Used correctly, these 
relationships can reveal a lot of useful information.  The concept of IOS 
parent and child is pretty intuitive, but we'll go through a simple example 
for clarity.

.. note:: CiscoConfParse assumes the configuration is in the *exact format* rendered by Cisco IOS devices when you use ``show runn`` or ``show start``.

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

Example: Retrieving text from an :class:`~models_cisco.IOSCfgLine` object
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This example:

- Parses through a configuration
- Finds an :class:`~models_cisco.IOSCfgLine` object with :func:`~ciscoconfparse.CiscoConfParse.find_objects()`
- Retrieves the configuration text from that object (highlighted in yellow)

.. code-block:: python
   :emphasize-lines: 9

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse([
   ...     '!',
   ...     'interface Serial1/0', 
   ...     ' ip address 1.1.1.5 255.255.255.252'
   ...     ])
   >>> for obj in parse.find_objects(r"interface"):
   ...     print "Object:", obj
   ...     print "Config text:", obj.text
   ...
   Object: <IOSCfgLine # 1 'interface Serial1/0'>
   Config text: interface Serial1/0
   >>>
   >>> quit()
   [mpenning@tsunami ~]$

In the example, ``obj.text`` refers to the :class:`~models_cisco.IOSCfgLine` 
``text`` attribute, which retrieves the text of the original IOS configuration 
statement.



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

Example Usage: Finding interface names that match a substring
-------------------------------------------------------------

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

Example Usage: Finding parents with a specific child
----------------------------------------------------

Suppose we need to find interfaces with the ``QOS_1`` service-policy applied
outbound...

Method 1: for-loop to iterate over objects and search children
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Method 2: `list-comprehension`_ to iterate over objects and search children
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :emphasize-lines: 2,3

   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> qos_intfs = [obj for obj in parse.find_objects(r"^interf") \
   ...     if obj.re_search_children(r"service-policy\soutput\sQOS_1")]
   ...
   >>> qos_intfs
   [<IOSCfgLine # 18 'interface Serial1/1'>]

Method 3: :func:`~ciscoconfparse.CiscoConfParse.find_objects_w_child()`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python
   :emphasize-lines: 2,3

   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> qos_intfs = parse.find_objects_w_child(parentspec=r"^interf", \
   ...     childspec=r"service-policy\soutput\sQOS_1")
   ...
   >>> qos_intfs
   [<IOSCfgLine # 18 'interface Serial1/1'>]

You can choose any of these methods to accomplish your task... 
some might question why we cover the first two methods when 
:func:`~ciscoconfparse.CiscoConfParse.find_objects_w_child()` solves 
the problem completely.  In this case, they have a point; however, 
:func:`~ciscoconfparse.CiscoConfParse.find_objects_w_child()` is much slower 
when you have more than one child line to inspect per interface, because 
:func:`~ciscoconfparse.CiscoConfParse.find_objects_w_child()` performs a 
line-by-line search of the whole configuration line each time it is called.  
By contrast, Method 1 is more efficient because you could simply call 
:func:`~models_cisco.IOSCfgLine.re_search_children()` multiple times for each 
interface object.  :func:`~models_cisco.IOSCfgLine.re_search_children()`
only searches the child lines of that :func:`~models_cisco.IOSCfgLine`
interface object.

Example Usage: Finding parents *without* a specific child
---------------------------------------------------------

Let's suppose you wanted a list of all interfaces that have CDP enabled; this implies a couple of things:

1.  CDP has not been disabled globally with ``no cdp run``
2.  The interfaces in question are not configured with ``no cdp enable``

:func:`~ciscoconfparse.CiscoConfParse.find_objects_wo_child` is a function to 
find parents without a specific child; it requires arguments similar to 
:func:`~ciscoconfparse.CiscoConfParse.find_objects_w_child`:

- The first argument is a regular expression to match the parents
- The second argument is a regular expression to match the child's *exclusion*

Since we need to find parents that do not have ``no cdp enable``, we will use 
:func:`~ciscoconfparse.CiscoConfParse.find_objects_wo_child` for this query.  
Note that the script below makes use of a special property of python lists... 
empty lists test False in Python; thus, we can 
use ``if not bool(parse.find_objects(r'no cdp run'))`` to ensure that CDP is 
running globally on this device.

.. code-block:: python
   :emphasize-lines: 2-4

   >>> parse = CiscoConfParse("/tftpboot/bucksnort.conf")
   >>> if not bool(parse.find_objects(r'no cdp run')):
   ...     cdp_intfs = parse.find_objects_wo_child(r'^interface', 
   ...         r'no cdp enable')

Results:

.. code-block:: python

   >>> cdp_intfs
   [<IOSCfgLine # 14 'interface Serial1/0'>, <IOSCfgLine # 18 'interface Serial1/1'>, <IOSCfgLine # 23 'interface Serial1/2'>]

.. _`list-comprehension`: https://docs.python.org/3/tutorial/datastructures.html#list-comprehensions
