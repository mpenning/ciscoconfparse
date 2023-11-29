.. _syntax_ios:

============
syntax='ios'
============

``syntax='ios'`` should be used for IOS-style configurations.  By default ``syntax='ios'`` is used and it's
a good default for many vendor configurations (without braces).

This configuration parse reads the configuration as ``ios`` syntax by default:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02rtr01.conf')
   >>>

This is the same as using:

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse('/tftpboot/sfob09f02rtr01.conf', syntax='ios', factory=False)
   >>>


When using ``syntax='ios'`` also consider the ``factory`` setting; for more information, see the :ref:`factory` page.


syntax='ios', factory=True example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Documentation for ``IOSIntfLine`` properties: :class:`~ciscoconfparse.models_cisco.IOSIntfLine()`.
- This is an example of getting an :class:`~ciscoconfparse.ccp_util.IPv4Obj()` for an :class:`~ciscoconfparse.models_cisco.IOSIntfLine()` that was parsed with ``factory=True``.

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_08.ios", syntax="ios", factory=True)
   >>> hsrp_intfs = parse.find_parent_objects("interface", " standby")
   >>>
   >>> hsrp_intfs[0]
   <IOSIntfLine # 231 'interface FastEthernet0/0' primary_ipv4: '172.16.2.1/24'>
   >>>
   >>> hsrp_intfs[0].ipv4
   <IPv4Obj 172.16.2.1/24>
   >>>

syntax='ios', factory=False example
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the same operation with ``factory=False``; we expect an ``AttributeError`` because ``factory=False`` returns :class:`~ciscoconfparse.models_cisco.IOSCfgLine()` instances instead of :class:`~ciscoconfparse.models_cisco.IOSIntfLine()` instances (which have the ``ipv4`` attribute).

.. sourcecode:: python

   >>> from ciscoconfparse import CiscoConfParse
   >>> parse = CiscoConfParse("tests/fixtures/configs/sample_08.ios", syntax="ios", factory=False)
   >>> hsrp_intfs = parse.find_parent_objects("interface", " standby")
   >>>
   >>> hsrp_intfs[0]
   <IOSCfgLine # 231 'interface FastEthernet0/0'>
   >>>
   >>> hsrp_intfs[0].ipv4
   2023-11-18 07:00:21.216 | ERROR    | ciscoconfparse.ccp_abc:__getattr__:142 - The ipv4 attribute does not exist
   2023-11-18 07:00:21.217 | ERROR    | __main__:<module>:1 - An error has been caught in function '<module>', process 'MainProcess' (111007), thread 'MainThread' (139675861627520):
   Traceback (most recent call last):

     File "/home/mpenning/fixme/ciscoconfparse/ciscoconfparse/ccp_abc.py", line 138, in __getattr__
       retval = getattr(object, attr)
                                └ 'ipv4'

   AttributeError: type object 'object' has no attribute 'ipv4'
   >>>

