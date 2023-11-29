.. _syntax_nxos:

=============
syntax='nxos'
=============

``syntax='nxos'`` should be used for Cisco NXOS configurations.  By default ``syntax='ios'`` is used and it's
a good default for many vendor configurations (without braces); however, ``syntax='nxos'`` handles situations as described below.

This configuration parse reads the configuration as ``nxos`` syntax.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02rtr01.conf', syntax='nxos')
   >>>

This is the same as using:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02rtr01.conf', syntax='nxos', factory=False)
   >>>


When using ``syntax='nxos'`` also consider the ``factory`` setting; for more information, see the :ref:`factory` page.


syntax='nxos', factory=True example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Documentation for ``NXOSIntfLine`` properties: :class:`~ciscoconfparse.models_nxos.NXOSIntfLine()`.
- This is an example of getting an :class:`~ciscoconfparse.ccp_util.IPv4Obj()` for an :class:`~ciscoconfparse.models_nxos.NXOSIntfLine()` that was parsed with ``factory=True``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_01.nxos", syntax="nxos", factory=True)
   >>> ipv4_intfs = parse.find_parent_objects("interface", " ip address")
   >>>
   >>> ipv4_intfs[0]
   <NXOSIntfLine # 166 'interface mgmt0' info: '10.10.248.50/24'>
   >>>
   >>> ipv4_intfs[0].ipv4
   <IPv4Obj 10.10.248.50/24>
   >>>

syntax='nxos', factory=False example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the same operation with ``factory=False``; we expect an ``AttributeError`` because ``factory=False`` returns :class:`~ciscoconfparse.models_nxos.NXOSCfgLine()` instances instead of :class:`~ciscoconfparse.models_nxos.NXOSIntfLine()` instances (which have the ``ipv4`` attribute).

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_01.nxos", syntax="nxos", factory=False)
   >>> ipv4_intfs = parse.find_parent_objects("interface", " ip address")
   >>>
   >>> ipv4_intfs[0]
   <NXOSCfgLine # 166 'interface mgmt0'>
   >>>
   >>> ipv4_intfs[0].ipv4
   2023-11-18 07:00:21.216 | ERROR    | ciscoconfparse.ccp_abc:__getattr__:142 - The ipv4 attribute does not exist
   2023-11-18 07:00:21.217 | ERROR    | __main__:<module>:1 - An error has been caught in function '<module>', process 'MainProcess' (111007), thread 'MainThread' (139675861627520):
   Traceback (most recent call last):

     File "/home/mpenning/fixme/ciscoconfparse/ciscoconfparse/ccp_abc.py", line 138, in __getattr__
       retval = getattr(object, attr)
                                └ 'ipv4'

   AttributeError: type object 'object' has no attribute 'ipv4'
   >>>

