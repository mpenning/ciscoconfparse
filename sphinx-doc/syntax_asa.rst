.. _syntax_asa:

============
syntax='asa'
============

``syntax='asa'`` should be used for Cisco ASA configurations.  By default ``syntax='ios'`` is used and it's
a good default for many vendor configurations (without braces); however, ``syntax='asa'`` handles situations as described below.

This configuration parse reads the configuration as ``asa`` syntax.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02fw01.conf', syntax='asa')
   >>>

This is the same as using:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02fw01.conf', syntax='asa', factory=False)
   >>>


When using ``syntax='asa'`` also consider the ``factory`` setting; for more information, see the :ref:`factory` page.


syntax='asa', factory=True example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Documentation for ``ASAIntfLine`` properties: :class:`~ciscoconfparse.models_asa.ASAIntfLine()`.
- This is an example of getting an :class:`~ciscoconfparse.ccp_util.IPv4Obj()` for an :class:`~ciscoconfparse.models_asa.ASAIntfLine()` that was parsed with ``factory=True``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_01.asa", syntax="asa", factory=True)
   >>> ipv4_intfs = parse.find_parent_objects("interface", " ip address")
   >>>
   >>> ipv4_intfs[2]
   <ASAIntfLine # 78 'interface Vlan200' info: '<IPv4Obj 192.0.2.1/24>'>
   >>>
   >>> ipv4_intfs[2].ipv4
   <IPv4Obj 192.0.2.1/24>
   >>>

syntax='asa', factory=False example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the same operation with ``factory=False``; we expect an ``AttributeError`` because ``factory=False`` returns :class:`~ciscoconfparse.models_asa.ASACfgLine()` instances instead of :class:`~ciscoconfparse.models_asa.ASAIntfLine()` instances (which have the ``ipv4`` attribute).

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_01.asa", syntax="asa", factory=False)
   >>> ipv4_intfs = parse.find_parent_objects("interface", " ip address")
   >>>
   >>> ipv4_intfs[2]
   <NXOSCfgLine # 78 'interface Vlan200'>
   >>>
   >>> ipv4_intfs[2].ipv4
   2023-11-18 07:00:21.216 | ERROR    | ciscoconfparse.ccp_abc:__getattr__:142 - The ipv4 attribute does not exist
   2023-11-18 07:00:21.217 | ERROR    | __main__:<module>:1 - An error has been caught in function '<module>', process 'MainProcess' (111007), thread 'MainThread' (139675861627520):
   Traceback (most recent call last):

     File "/home/mpenning/fixme/ciscoconfparse/ciscoconfparse/ccp_abc.py", line 138, in __getattr__
       retval = getattr(object, attr)
                                └ 'ipv4'

   AttributeError: type object 'object' has no attribute 'ipv4'
   >>>

